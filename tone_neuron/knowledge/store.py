"""Vector stores, MMR retrieval, reranking and the knowledge index."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

from tone_neuron.config import Settings, get_settings
from tone_neuron.knowledge.embeddings import EmbedderUnavailable, get_embedder
from tone_neuron.knowledge.okf import (
    KnowledgeEntry,
    corpus_fingerprint,
    load_entries,
)
from tone_neuron.schemas import Citation

INDEX_VERSION = 1
UNIVERSAL_REGION = "GL"

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "this", "that", "these", "those",
    "is", "are", "was", "were", "be", "been", "to", "of", "in", "on", "for", "with", "as",
    "at", "by", "from", "it", "its", "we", "you", "i", "they", "he", "she", "not", "no",
    "do", "does", "did", "so", "my", "your", "our", "their", "me", "us", "them", "can",
    "will", "would", "should", "could", "please", "email", "message", "region",
}


# --------------------------------------------------------------------------- #
# Vector stores                                                               #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class StoreHit:
    entry_id: str
    score: float
    row: int


class BaseVectorStore:
    name = "base"

    def search(self, vector: np.ndarray, k: int) -> list[StoreHit]:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def build(cls, ids: Sequence[str], vectors: np.ndarray) -> "BaseVectorStore":
        raise NotImplementedError


class NumpyVectorStore(BaseVectorStore):
    """Exact cosine similarity; always available."""

    name = "numpy"

    def __init__(self, ids: Sequence[str], vectors: np.ndarray):
        self.ids = list(ids)
        self.vectors = _normalise_rows(np.asarray(vectors, dtype=np.float32))

    @classmethod
    def build(cls, ids: Sequence[str], vectors: np.ndarray) -> "NumpyVectorStore":
        return cls(ids, vectors)

    def search(self, vector: np.ndarray, k: int) -> list[StoreHit]:
        if not self.ids:
            return []
        query = np.asarray(vector, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(query))
        if norm > 0:
            query = query / norm
        scores = self.vectors @ query
        k = min(k, len(self.ids))
        order = np.argsort(-scores)[:k]
        return [StoreHit(self.ids[int(i)], float(scores[int(i)]), int(i)) for i in order]


class FaissVectorStore(BaseVectorStore):
    name = "faiss"

    def __init__(self, ids: Sequence[str], vectors: np.ndarray):
        import faiss  # type: ignore

        self.ids = list(ids)
        self.vectors = _normalise_rows(np.asarray(vectors, dtype=np.float32))
        self._index = faiss.IndexFlatIP(self.vectors.shape[1])
        self._index.add(self.vectors)

    @classmethod
    def build(cls, ids: Sequence[str], vectors: np.ndarray) -> "FaissVectorStore":
        return cls(ids, vectors)

    def search(self, vector: np.ndarray, k: int) -> list[StoreHit]:
        query = np.asarray(vector, dtype=np.float32).reshape(1, -1)
        norm = float(np.linalg.norm(query))
        if norm > 0:
            query = query / norm
        k = min(k, len(self.ids))
        scores, indices = self._index.search(query, k)
        return [
            StoreHit(self.ids[int(i)], float(s), int(i))
            for s, i in zip(scores[0], indices[0])
            if int(i) >= 0
        ]


class QdrantVectorStore(BaseVectorStore):
    """Qdrant in local (embedded) mode."""

    name = "qdrant"

    def __init__(self, ids: Sequence[str], vectors: np.ndarray, path: Path):
        from qdrant_client import QdrantClient  # type: ignore

        self.ids = list(ids)
        self.vectors = _normalise_rows(np.asarray(vectors, dtype=np.float32))
        self._client = QdrantClient(path=str(path))
        self._collection = "tone_neuron_knowledge"
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams  # type: ignore

        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self.vectors.shape[1], distance=Distance.COSINE),
            )
            self._client.upsert(
                collection_name=self._collection,
                points=[
                    {"id": index, "vector": vector.tolist(), "payload": {"entry_id": self.ids[index]}}
                    for index, vector in enumerate(self.vectors)
                ],
            )

    @classmethod
    def build(cls, ids: Sequence[str], vectors: np.ndarray) -> "QdrantVectorStore":
        return cls(ids, vectors, get_settings().index_dir / "qdrant")

    def search(self, vector: np.ndarray, k: int) -> list[StoreHit]:
        result = self._client.query_points(
            collection_name=self._collection,
            query=np.asarray(vector, dtype=np.float32).reshape(-1).tolist(),
            limit=min(k, len(self.ids)),
        ).points
        hits: list[StoreHit] = []
        for point in result:
            row = int(point.id)
            hits.append(StoreHit(self.ids[row], float(point.score), row))
        return hits


def build_vector_store(kind: str, ids: Sequence[str], vectors: np.ndarray) -> BaseVectorStore:
    kind = (kind or "auto").lower()
    if kind == "auto":
        kind = "numpy"
    if kind == "numpy":
        return NumpyVectorStore.build(ids, vectors)
    if kind == "faiss":
        try:
            return FaissVectorStore.build(ids, vectors)
        except Exception:
            return NumpyVectorStore.build(ids, vectors)
    if kind == "qdrant":
        try:
            return QdrantVectorStore.build(ids, vectors)
        except Exception:
            return NumpyVectorStore.build(ids, vectors)
    raise ValueError(f"unknown vector store: {kind!r}")


def _normalise_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


# --------------------------------------------------------------------------- #
# Reranking                                                                   #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class RetrievedEntry:
    entry: KnowledgeEntry
    score: float
    dense: float = 0.0
    lexical: float = 0.0
    rerank: float = 0.0
    row: int = -1
    retrieval: str = "hybrid+mmr+lexical"

    def citation(self) -> Citation:
        return Citation(
            entry_id=self.entry.id,
            title=self.entry.title,
            region=self.entry.region,
            region_name=self.entry.region_name,
            category=self.entry.category,
            source_path=self.entry.path,
            excerpt=self.entry.excerpt(),
            score=round(float(self.score), 4),
            retrieval=self.retrieval,
        )


def lexical_overlap(query: str, text: str) -> float:
    query_terms = {t for t in _tokenise(query) if t not in _STOPWORDS}
    if not query_terms:
        return 0.0
    text_terms = {t for t in _tokenise(text) if t not in _STOPWORDS}
    if not text_terms:
        return 0.0
    hit = len(query_terms & text_terms)
    return hit / (len(query_terms) ** 0.5 * len(text_terms) ** 0.5) * 3.0


def _tokenise(text: str) -> list[str]:
    import re

    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


class BaseReranker:
    name = "none"

    def rerank(self, query: str, candidates: list[RetrievedEntry], k: int) -> list[RetrievedEntry]:
        return candidates[:k]


class NoReranker(BaseReranker):
    name = "none"


class LexicalReranker(BaseReranker):
    """Cheap, deterministic reranker: dense score blended with query/tag/title overlap."""

    name = "lexical"

    def rerank(self, query: str, candidates: list[RetrievedEntry], k: int) -> list[RetrievedEntry]:
        for cand in candidates:
            text = cand.entry.embed_text()
            lex = min(1.0, lexical_overlap(query, text))
            tag_boost = 0.0
            query_terms = set(_tokenise(query))
            if query_terms & {t.lower() for t in cand.entry.tags}:
                tag_boost += 0.08
            if query_terms & set(_tokenise(cand.entry.title)):
                tag_boost += 0.05
            cand.lexical = lex
            cand.rerank = 0.62 * cand.score + 0.38 * lex + tag_boost
            cand.score = cand.rerank
        return sorted(candidates, key=lambda c: c.score, reverse=True)[:k]


class CrossEncoderReranker(BaseReranker):
    name = "cross-encoder"

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise EmbedderUnavailable("sentence-transformers not installed") from exc
        self._model = CrossEncoder(model_name)
        self.name = f"cross-encoder:{model_name}"

    def rerank(self, query: str, candidates: list[RetrievedEntry], k: int) -> list[RetrievedEntry]:
        if not candidates:
            return []
        pairs = [(query, cand.entry.embed_text()) for cand in candidates]
        scores = self._model.predict(pairs)
        for cand, score in zip(candidates, scores):
            cand.rerank = float(score)
            cand.score = 0.35 * cand.score + 0.65 * _sigmoid(float(score))
            cand.retrieval = "hybrid+mmr+cross-encoder"
        return sorted(candidates, key=lambda c: c.score, reverse=True)[:k]


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + float(np.exp(-value)))


def build_reranker(kind: str) -> BaseReranker:
    kind = (kind or "auto").lower()
    if kind == "auto":
        kind = "lexical"
    if kind == "none":
        return NoReranker()
    if kind == "lexical":
        return LexicalReranker()
    if kind in ("cross-encoder", "crossencoder", "ce"):
        try:
            return CrossEncoderReranker()
        except Exception:
            return LexicalReranker()
    raise ValueError(f"unknown reranker: {kind!r}")


# --------------------------------------------------------------------------- #
# MMR                                                                         #
# --------------------------------------------------------------------------- #
def mmr_select(
    candidates: list[RetrievedEntry],
    vectors: np.ndarray,
    k: int,
    lambda_: float = 0.65,
) -> list[RetrievedEntry]:
    """Maximal Marginal Relevance: relevance minus redundancy."""
    if k <= 0 or not candidates:
        return []
    k = min(k, len(candidates))
    pool = list(candidates)
    selected: list[RetrievedEntry] = []
    while pool and len(selected) < k:
        best = None
        best_score = float("-inf")
        for cand in pool:
            redundancy = 0.0
            if selected:
                redundancy = max(
                    float(np.dot(vectors[cand.row], vectors[other.row])) for other in selected
                )
            score = lambda_ * cand.score - (1.0 - lambda_) * redundancy
            if score > best_score:
                best_score, best = score, cand
        assert best is not None
        selected.append(best)
        pool.remove(best)
    return selected


# --------------------------------------------------------------------------- #
# Index                                                                       #
# --------------------------------------------------------------------------- #
class KnowledgeIndex:
    """Entries + embedder + vector store + reranker, with save/load caching."""

    def __init__(
        self,
        entries: list[KnowledgeEntry],
        embedder,
        vectors: np.ndarray,
        store: BaseVectorStore,
        reranker: BaseReranker,
        mmr_lambda: float = 0.65,
        fingerprint: str = "",
    ):
        self.entries = entries
        self.embedder = embedder
        self.vectors = _normalise_rows(np.asarray(vectors, dtype=np.float32))
        self.store = store
        self.reranker = reranker
        self.mmr_lambda = float(mmr_lambda)
        self.fingerprint = fingerprint or corpus_fingerprint(entries)
        self._by_id = {entry.id: entry for entry in entries}
        self._row_by_id = {entry.id: row for row, entry in enumerate(entries)}

    # -- construction ------------------------------------------------------
    @classmethod
    def build(cls, okf_dir: Path | str | None = None, settings: Settings | None = None):
        settings = settings or get_settings()
        directory = Path(okf_dir) if okf_dir else settings.okf_dir
        entries = load_entries(directory)
        texts = [entry.embed_text() for entry in entries]
        embedder = get_embedder(settings.embedder, corpus=texts, dim=settings.embedding_dim)
        vectors = embedder.encode(texts)
        store = build_vector_store(settings.vector_store, [e.id for e in entries], vectors)
        reranker = build_reranker(settings.reranker)
        return cls(
            entries=entries,
            embedder=embedder,
            vectors=vectors,
            store=store,
            reranker=reranker,
            mmr_lambda=settings.mmr_lambda,
        )

    @classmethod
    def load_or_build(
        cls,
        settings: Settings | None = None,
        force: bool = False,
        okf_dir: Path | str | None = None,
    ) -> "KnowledgeIndex":
        settings = settings or get_settings()
        directory = Path(okf_dir) if okf_dir else settings.okf_dir
        index_dir = settings.index_dir
        meta_path = index_dir / "index.json"
        vectors_path = index_dir / "vectors.npy"

        entries = load_entries(directory)
        fingerprint = corpus_fingerprint(entries)
        resolved_kind = "hashing" if settings.embedder in ("", "auto") else settings.embedder

        if not force and resolved_kind != "tfidf" and meta_path.exists() and vectors_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if (
                    meta.get("version") == INDEX_VERSION
                    and meta.get("fingerprint") == fingerprint
                    and meta.get("embedder") == _embedder_name_for(resolved_kind)
                    and meta.get("ids") == [entry.id for entry in entries]
                ):
                    vectors = np.load(vectors_path)
                    embedder = get_embedder(resolved_kind, dim=settings.embedding_dim)
                    store = build_vector_store(
                        meta.get("vector_store", "numpy"),
                        [entry.id for entry in entries],
                        vectors,
                    )
                    return cls(
                        entries,
                        embedder,
                        vectors,
                        store,
                        build_reranker(settings.reranker),
                        settings.mmr_lambda,
                        fingerprint,
                    )
            except Exception:
                pass  # corrupt cache -> rebuild below

        index = cls.build(directory, settings)
        try:
            index.save(index_dir)
        except OSError:
            pass
        return index

    # -- persistence -------------------------------------------------------
    def save(self, directory: Path | None = None) -> Path:
        directory = Path(directory) if directory else get_settings().index_dir
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "vectors.npy", self.vectors)
        meta = {
            "version": INDEX_VERSION,
            "fingerprint": self.fingerprint,
            "embedder": self.embedder.name,
            "vector_store": self.store.name,
            "ids": [entry.id for entry in self.entries],
            "count": len(self.entries),
            "built_at": datetime.now(timezone.utc).isoformat(),
        }
        (directory / "index.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return directory

    # -- access ------------------------------------------------------------
    @property
    def regions(self) -> list[str]:
        return sorted({entry.region for entry in self.entries if entry.region != UNIVERSAL_REGION})

    def region_name(self, region: str) -> str:
        for entry in self.entries:
            if entry.region == region.upper():
                return entry.region_name
        return region.upper()

    def entry(self, entry_id: str) -> KnowledgeEntry | None:
        return self._by_id.get(entry_id)

    def stats(self) -> dict:
        return {
            "entries": len(self.entries),
            "regions": self.regions,
            "embedder": self.embedder.name,
            "vector_store": self.store.name,
            "reranker": self.reranker.name,
            "mmr_lambda": self.mmr_lambda,
            "fingerprint": self.fingerprint,
        }

    # -- retrieval ---------------------------------------------------------
    def retrieve(
        self,
        query: str,
        k: int | None = None,
        region: str | None = None,
        categories: Sequence[str] | None = None,
        use_mmr: bool = True,
        include_universal: bool = True,
    ) -> list[RetrievedEntry]:
        settings = get_settings()
        k = k or settings.top_k
        query = (query or "").strip()
        if not query or not self.entries:
            return []

        query_vec = self.embedder.encode([query])[0]
        hits = self.store.search(query_vec, max(settings.candidate_k, k * 4))
        candidates: list[RetrievedEntry] = []
        wanted_region = region.upper() if region else None
        for hit in hits:
            entry = self._by_id.get(hit.entry_id)
            if entry is None:
                continue
            if wanted_region:
                allowed = {wanted_region}
                if include_universal:
                    allowed.add(UNIVERSAL_REGION)
                if entry.region not in allowed:
                    continue
            if categories and entry.category not in set(categories):
                continue
            candidates.append(
                RetrievedEntry(
                    entry=entry,
                    score=float(hit.score),
                    dense=float(hit.score),
                    row=self._row_by_id[entry.id],
                )
            )

        if not candidates and wanted_region:
            # fall back to universal-only retrieval rather than returning nothing
            return self.retrieve(query, k=k, region=None, categories=categories, use_mmr=use_mmr)

        if not candidates:
            return []

        if use_mmr:
            candidates = mmr_select(candidates, self.vectors, len(candidates), self.mmr_lambda)
        candidates = self.reranker.rerank(query, candidates, k)
        if self.reranker.name == "none":
            for cand in candidates:
                cand.retrieval = "hybrid+mmr"
        return candidates

    def retrieve_citations(
        self, query: str, k: int | None = None, region: str | None = None, **kwargs
    ) -> list[Citation]:
        return [hit.citation() for hit in self.retrieve(query, k=k, region=region, **kwargs)]


def _embedder_name_for(kind: str) -> str:
    if kind == "hashing":
        return "hashing-ngram"
    if kind == "tfidf":
        return "tfidf-char"
    if kind in ("st", "sentence-transformers"):
        return "sentence-transformers"
    return kind

"""Embedding backends.

Default is a deterministic hashed n-gram embedder so the project runs offline with no model
downloads. ``st`` uses sentence-transformers when installed; ``tfidf`` fits a char n-gram TF-IDF
on the knowledge corpus (useful for small corpora and tests).
"""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

import numpy as np

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_WS_RE = re.compile(r"\s+")


class EmbedderUnavailable(RuntimeError):
    """Raised when an explicitly requested embedder is not installed."""


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbedder:
    """Signed feature hashing over word unigrams/bigrams and character n-grams.

    Deterministic across processes (blake2b, not Python's salted ``hash``), so a persisted index
    stays valid between runs.
    """

    name = "hashing-ngram"
    kind = "hashing"

    def __init__(self, dim: int = 768, char_ngram: int = 4, whole_text_char_ngrams: bool = True):
        self.dim = int(dim)
        self.char_ngram = int(char_ngram)
        self.whole_text_char_ngrams = whole_text_char_ngrams

    def _bucket(self, token: str) -> tuple[int, float]:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        return value % self.dim, 1.0 if (value >> 63) & 1 else -1.0

    def _features(self, text: str) -> list[str]:
        tokens = _tokens(text)
        feats: list[str] = list(tokens)
        feats.extend(f"{a}_{b}" for a, b in zip(tokens, tokens[1:]))
        for token in tokens:
            padded = f"<{token}>"
            n = self.char_ngram
            feats.extend(padded[i : i + n] for i in range(max(0, len(padded) - n + 1)))
        if self.whole_text_char_ngrams:
            compact = _WS_RE.sub(" ", text.lower()).strip()
            n = self.char_ngram
            step = max(1, len(compact) // 600)  # cap work on long documents
            feats.extend(compact[i : i + n] for i in range(0, max(0, len(compact) - n), step))
        return feats

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            counts: dict[int, float] = {}
            for feat in self._features(text):
                idx, sign = self._bucket(feat)
                counts[idx] = counts.get(idx, 0.0) + sign
            for idx, value in counts.items():
                matrix[row, idx] = np.sign(value) * (1.0 + np.log1p(abs(value)))
            norm = float(np.linalg.norm(matrix[row]))
            if norm > 0:
                matrix[row] /= norm
        return matrix


class TfidfEmbedder:
    """Char n-gram TF-IDF fitted on the knowledge corpus (needs ``fit`` before ``encode``)."""

    name = "tfidf-char"
    kind = "tfidf"

    def __init__(self, corpus: Sequence[str] | None = None):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=1
        )
        self.dim = 0
        if corpus:
            self.fit(corpus)

    def fit(self, corpus: Sequence[str]) -> "TfidfEmbedder":
        self._vectorizer.fit(corpus)
        self.dim = len(self._vectorizer.get_feature_names_out())
        return self

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not self.dim:
            raise EmbedderUnavailable("TfidfEmbedder.fit() must be called before encode()")
        matrix = self._vectorizer.transform(texts).astype(np.float32).toarray()
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms


class SentenceTransformerEmbedder:
    """Dense multilingual embeddings (optional dependency)."""

    kind = "st"
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise EmbedderUnavailable(
                "sentence-transformers is not installed; `pip install sentence-transformers` "
                "or set TONE_NEURON_EMBEDDER=hashing"
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.name = f"st:{model_name}"
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        vectors = self._model.encode(
            list(texts), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype=np.float32)


def get_embedder(kind: str = "auto", corpus: Sequence[str] | None = None, dim: int = 768):
    """Return an embedder. ``auto`` stays offline and deterministic."""
    kind = (kind or "auto").lower()
    if kind == "auto":
        kind = "hashing"
    if kind == "hashing":
        return HashingEmbedder(dim=dim)
    if kind == "tfidf":
        if not corpus:
            raise EmbedderUnavailable("tfidf embedder needs the knowledge corpus")
        return TfidfEmbedder(corpus)
    if kind in ("st", "sentence-transformers", "sentence_transformers"):
        from tone_neuron.config import get_settings

        return SentenceTransformerEmbedder(get_settings().sentence_transformer_model)
    raise ValueError(f"unknown embedder kind: {kind!r}")

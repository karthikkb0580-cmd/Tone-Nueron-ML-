from __future__ import annotations

from tone_neuron.config import Settings, get_settings
from tone_neuron.knowledge.okf import load_entries, load_okf_dir
from tone_neuron.knowledge.store import KnowledgeIndex
from tone_neuron.ml import features


def test_seed_corpus_has_eight_regions_plus_universal() -> None:
    docs = load_okf_dir(get_settings().okf_dir)
    regions = {doc.region for doc in docs}
    assert {"JP", "IN", "DE", "US", "UK", "CN", "BR", "AE"} <= regions
    assert "GL" in regions

    entries = load_entries(get_settings().okf_dir)
    assert len(entries) >= 60
    assert len({entry.id for entry in entries}) == len(entries)
    assert all(entry.guidance and entry.path.endswith(".okf.md") for entry in entries)


def test_retrieval_is_region_scoped_and_citable(engine) -> None:
    hits = engine.index.retrieve("polite greeting honorifics", k=3, region="JP")
    assert hits
    assert all(hit.entry.region in {"JP", "GL"} for hit in hits)
    assert any(hit.entry.region == "JP" for hit in hits)

    citation = hits[0].citation()
    assert citation.entry_id
    assert citation.excerpt
    assert citation.source_path.endswith(".okf.md")
    assert 0.0 <= citation.score <= 1.5


def test_mmr_returns_distinct_entries(engine) -> None:
    hits = engine.index.retrieve("meeting deadlines hierarchy feedback", k=5, region="DE")
    assert len(hits) == len({hit.entry.id for hit in hits})


def test_tfidf_embedder_builds_and_persists(tmp_path) -> None:
    settings = Settings(
        embedder="tfidf",
        vector_store="numpy",
        reranker="lexical",
        okf_dir=get_settings().okf_dir,
    )
    index = KnowledgeIndex.build(settings=settings)
    assert index.vectors.shape[0] == len(index.entries)

    hits = index.retrieve("hierarchy feedback meetings", k=2, region="IN")
    assert hits

    index.save(tmp_path)
    assert (tmp_path / "vectors.npy").exists()
    assert (tmp_path / "index.json").exists()


def test_missing_expectation_is_detected() -> None:
    missing = features.missing_expectations(
        "Please send the report by Friday.", "JP", "email_draft"
    )
    assert {expectation.code for expectation in missing} >= {"missing_jp_greeting"}

    satisfied = features.missing_expectations(
        "お世話になっております。田中さん、ご確認をお願いします。", "JP", "email_draft"
    )
    assert all(expectation.code != "missing_jp_greeting" for expectation in satisfied)

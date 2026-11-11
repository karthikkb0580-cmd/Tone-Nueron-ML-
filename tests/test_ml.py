from __future__ import annotations

from tone_neuron.ml.dataset import generate_dataset, split_dataset, summarize
from tone_neuron.ml.infer import analyze


def test_dataset_is_deterministic_balanced_and_hard() -> None:
    first = generate_dataset(n=160, seed=3)
    second = generate_dataset(n=160, seed=3)
    assert [sample.as_dict() for sample in first] == [sample.as_dict() for sample in second]

    summary = summarize(first)
    assert summary["count"] == 160
    assert set(summary["regions"]) == {"JP", "IN", "DE", "US", "UK", "CN", "BR", "AE"}
    assert set(summary["tones"]) == {"polite", "neutral", "blunt", "rude", "sensitive"}
    assert set(summary["risks"]) == {"low", "medium", "high"}

    # hard cases exist: some identity metadata is missing or contradictory
    assert any(sample.receiver_language is None for sample in first)
    assert any("gmail.com" in sample.receiver_email for sample in first)

    train, test = split_dataset(first, test_ratio=0.25, seed=5)
    assert len(train) + len(test) == len(first)
    assert {sample.region for sample in test} == {"JP", "IN", "DE", "US", "UK", "CN", "BR", "AE"}


def test_analyze_matches_public_contract(engine) -> None:
    result = analyze(
        "Hey Tanaka, your work on this is useless. Send the report now.",
        {"surface": "email_draft"},
        {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
    )
    for key in ("region", "confidence", "risk", "flagged_spans", "reasons", "rewrites", "citations"):
        assert key in result

    assert result["region"] == "JP"
    assert result["risk"] == "high"
    assert result["is_guess"] is True

    citation_ids = {citation["entry_id"] for citation in result["citations"]}
    for rewrite in result["rewrites"]:
        assert set(rewrite["citation_ids"]).issubset(citation_ids)


def test_excerpt_is_redacted(engine) -> None:
    result = engine.analyze(
        "Write to kenji.tanaka@example.co.jp about the report.",
        None,
        {"email": "kenji.tanaka@example.co.jp"},
    )
    assert "kenji.tanaka@example.co.jp" not in result.excerpt
    assert "@example.co.jp" in result.excerpt


def test_missing_greeting_expectation_is_reported(engine) -> None:
    result = engine.analyze(
        "Please send the report by Friday.",
        {"surface": "email_draft"},
        {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
    )
    codes = {reason.code for reason in result.reasons}
    assert "missing_jp_greeting" in codes

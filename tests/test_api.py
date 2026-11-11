from __future__ import annotations

JP_DRAFT = {
    "text": "Hey Tanaka, your work on this is useless. Send the Q3 report now, this is unacceptable.",
    "context": {"surface": "email_draft"},
    "receiver_info": {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
}


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["knowledge_entries"] >= 60
    assert "JP" in body["regions"]
    assert body["embedder"]


def test_analyze_returns_full_verdict(client) -> None:
    response = client.post("/analyze", json=JP_DRAFT)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["region"] == "JP"
    assert body["is_guess"] is True
    assert 0 < body["confidence"] <= 0.95
    assert body["risk"] == "high"
    assert body["tone"] in {"rude", "sensitive"}
    assert body["recommended_action"] == "block"
    assert body["flagged_spans"]
    assert body["reasons"]
    assert 1 <= len(body["rewrites"]) <= 3
    assert body["citations"]
    assert all(citation["excerpt"] for citation in body["citations"])
    assert body["excerpt"]


def test_region_override_wins(client) -> None:
    payload = {
        "text": "Send it now.",
        "receiver_info": {
            "name": "Kenji Tanaka",
            "email": "k.tanaka@example.co.jp",
            "region_override": "BR",
        },
    }
    body = client.post("/analyze", json=payload).json()
    assert body["region"] == "BR"
    assert body["region_overridden"] is True


def test_gate_blocks_then_releases_on_confirmation(client) -> None:
    blocked = client.post("/gate", json={**JP_DRAFT, "channel": "email"}).json()
    assert blocked["decision"] == "block"
    assert blocked["requires_confirmation"] is True

    released = client.post(
        "/gate", json={**JP_DRAFT, "channel": "email", "sender_confirmed": True}
    ).json()
    assert released["decision"] == "allow"
    assert released["verified"] is True


def test_call_gate_is_non_intrusive(client) -> None:
    payload = {**JP_DRAFT, "channel": "call", "context": {"surface": "meeting"}}
    body = client.post("/gate", json=payload).json()
    assert body["blocked"] is False
    assert body["decision"] in {"hint", "allow"}
    assert body["mascot_alert"]["placement"] == "side_panel"
    assert body["mascot_alert"]["intrusive"] is False


def test_cards_include_unlocks(client) -> None:
    client.post("/analyze", json=JP_DRAFT)
    body = client.get("/cards").json()
    assert body["total"] == 8
    assert len(body["cards"]) == 8
    assert any(card["unlocked"] for card in body["cards"])
    card = next(card for card in body["cards"] if card["region"] == "JP")
    assert card["dos"] and card["donts"] and card["taboo_topics"]


def test_daily_coaching_review(client) -> None:
    client.post("/analyze", json=JP_DRAFT)
    response = client.post("/coaching/daily", json={"clear_after": True})
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["emails_checked"] >= 1
    assert body["risk_breakdown"]
    assert body["themes"]
    assert body["citations"]
    assert body["privacy_note"]
    # the buffer is cleared, so a second review has no events
    second = client.post("/coaching/daily", json={"clear_after": True}).json()
    assert second["emails_checked"] == 0

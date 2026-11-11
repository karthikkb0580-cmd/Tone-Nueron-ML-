from __future__ import annotations

from tone_neuron.gate import evaluate_gate
from tone_neuron.schemas import GateRequest

JP_RECEIVER = {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"}
DE_RECEIVER = {"name": "Lukas Weber", "email": "l.weber@example.de"}


def _evaluate(engine, text: str, receiver: dict, **kwargs):
    request = GateRequest(text=text, receiver_info=receiver, **kwargs)
    analysis = engine.analyze(request.text, request.context, request.receiver_info)
    return analysis, evaluate_gate(analysis, request)


def test_high_risk_blocks_until_sender_verifies(engine) -> None:
    text = "Hey Tanaka, your work on this is useless. Send the report now, this is unacceptable."
    analysis, gate = _evaluate(engine, text, JP_RECEIVER)

    assert analysis.risk == "high"
    assert gate.decision == "block"
    assert gate.blocked is True
    assert gate.requires_confirmation is True
    assert gate.mascot_alert.state == "worried"
    assert gate.mascot_alert.requires_action is True
    assert analysis.rewrites, "a blocked draft must offer a rewrite"

    _, confirmed = _evaluate(engine, text, JP_RECEIVER, sender_confirmed=True)
    assert confirmed.decision == "allow"
    assert confirmed.blocked is False
    assert confirmed.verified is True


def test_chosen_rewrite_releases_the_block(engine) -> None:
    text = "Hey Tanaka, your work on this is useless. Send the report now."
    analysis, gate = _evaluate(engine, text, JP_RECEIVER)
    assert gate.decision == "block"

    _, released = _evaluate(engine, text, JP_RECEIVER, chosen_rewrite_index=0)
    assert released.decision == "allow"
    assert released.verified is True
    assert released.mascot_alert.rewrite_preview


def test_medium_risk_is_only_a_hint(engine) -> None:
    analysis, gate = _evaluate(
        engine, "Hi Lukas, send the proposal now. I need this today.", DE_RECEIVER
    )
    assert analysis.risk == "medium"
    assert gate.decision == "hint"
    assert gate.blocked is False
    assert gate.requires_confirmation is False
    assert gate.mascot_alert.auto_dismiss_seconds is not None


def test_low_risk_is_allowed(engine) -> None:
    text = (
        "Guten Tag Herr Weber,\n\ncould you please review the proposal by Friday? "
        "Thank you very much.\n\nMit freundlichen Grüßen"
    )
    analysis, gate = _evaluate(engine, text, DE_RECEIVER)
    assert analysis.risk == "low"
    assert gate.decision == "allow"
    assert gate.blocked is False


def test_calls_never_block_and_never_intrude(engine) -> None:
    text = "Hey Tanaka, your work on this is useless. Send it now, this is unacceptable."
    analysis, gate = _evaluate(engine, text, JP_RECEIVER, channel="call")

    assert analysis.risk == "high"
    assert gate.decision in {"hint", "allow"}
    assert gate.blocked is False
    assert gate.requires_confirmation is False
    assert gate.mascot_alert.placement == "side_panel"
    assert gate.mascot_alert.intrusive is False
    assert gate.mascot_alert.requires_action is False

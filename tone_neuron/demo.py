"""One-shot offline demo: analyse, gate, coach, show citations."""

from __future__ import annotations

from tone_neuron.coaching import SessionStore, build_daily_review
from tone_neuron.gate import evaluate_gate
from tone_neuron.ml.infer import get_engine
from tone_neuron.schemas import CoachingRequest, GateRequest

SCENARIOS: list[dict] = [
    {
        "title": "Email draft → Japan (rude, high risk)",
        "text": (
            "Hey Tanaka, your work on this is useless. Send the Q3 report now, "
            "this is unacceptable. I need it today."
        ),
        "receiver": {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
        "channel": "email",
    },
    {
        "title": "Email draft → Germany (blunt, medium risk)",
        "text": "Hi Lukas, send the proposal now. I need this today.",
        "receiver": {"name": "Lukas Weber", "email": "l.weber@example.de"},
        "channel": "email",
    },
    {
        "title": "Email draft → UAE (sensitive, high risk)",
        "text": "Your contract termination will be reviewed on Monday. This is confidential.",
        "receiver": {"name": "Omar Haddad", "email": "o.haddad@example.ae"},
        "channel": "email",
    },
    {
        "title": "Chat → India (polite, low risk)",
        "text": (
            "Dear Mr Sharma,\n\nI hope you and your family are well. Could you please confirm "
            "the invoice by Friday? Thank you.\n\nWarm regards"
        ),
        "receiver": {"name": "Rahul Sharma", "email": "r.sharma@example.co.in"},
        "channel": "chat",
    },
    {
        "title": "Call caption → Japan (side alert only, never blocks)",
        "text": "This is the third time I have asked. Send it now, this is unacceptable.",
        "receiver": {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
        "channel": "call",
    },
]


def _print_scenario(number: int, scenario: dict, analysis, gate) -> None:
    print()
    print(f"== {number}. {scenario['title']} " + "=" * max(4, 62 - len(scenario["title"])))
    print(
        f"Region : {analysis.region} ({analysis.region_name})  "
        f"confidence={analysis.confidence:.2f} ({analysis.confidence_label})  "
        f"guess={analysis.is_guess}"
    )
    print(f"Risk   : {analysis.risk.upper()} (score {analysis.risk_score:.2f})   Tone: {analysis.tone}")
    if analysis.region_evidence:
        evidence = "; ".join(
            f"{signal.kind}={signal.value} (w={signal.weight})" for signal in analysis.region_evidence[:3]
        )
        print(f"Signals: {evidence}")
    if analysis.flagged_spans:
        print("Flags  :")
        for span in analysis.flagged_spans[:5]:
            print(f"  - {span.text!r} [{span.severity}/{span.category}] {span.reason}")
    if analysis.reasons:
        print("Reasons:")
        for reason in analysis.reasons[:4]:
            print(f"  - {reason.message}")
    if analysis.rewrites:
        print("Rewrites (pick one):")
        for rewrite in analysis.rewrites[:2]:
            print(f"  [{rewrite.strategy}] {rewrite.text[:220].replace(chr(10), ' / ')}")
    print("Citations:")
    for citation in analysis.citations[:4]:
        print(f"  - {citation.entry_id} — {citation.title} ({citation.region}) score={citation.score}")
    print(f"Gate   : {gate.decision.upper()}  blocked={gate.blocked} verified={gate.verified}")
    print(f"Mascot : [{gate.mascot_alert.state}] {gate.mascot_alert.title} — {gate.mascot_alert.message[:160]}")
    print(f"         placement={gate.mascot_alert.placement} intrusive={gate.mascot_alert.intrusive}")


def run_demo() -> int:
    engine = get_engine()
    store = SessionStore(engine.settings)

    for index, scenario in enumerate(SCENARIOS, 1):
        request = GateRequest(
            text=scenario["text"],
            receiver_info=scenario["receiver"],
            channel=scenario["channel"],
        )
        analysis = engine.analyze(request.text, request.context, request.receiver_info)
        store.record(analysis, channel=request.channel)
        gate = evaluate_gate(analysis, request)
        _print_scenario(index, scenario, analysis, gate)

    review = build_daily_review(store, engine.index, engine.cards, CoachingRequest(clear_after=False))
    print()
    print("== End-of-day review " + "=" * 44)
    print(review.summary)
    for theme in review.themes:
        print(f"  • theme: {theme.title} ({theme.count}×, {', '.join(theme.regions)})")
    for tip in review.language_tips:
        print(f"  • tip: {tip.focus} — {tip.phrase} → {tip.better}")
    for note in review.work_culture_notes[:3]:
        print(f"  • meeting: {note.region} {note.dimension} — {note.guidance}")
    if review.wins:
        print("  • wins: " + " ".join(review.wins))
    print(f"  citations: {', '.join(citation.entry_id for citation in review.citations[:6])}")
    print(f"  mascot: [{review.mascot_state}]")
    print()
    print("Demo complete. Offline, no content was written to disk.")
    return 0

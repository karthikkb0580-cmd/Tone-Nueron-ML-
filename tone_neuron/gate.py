"""Feature 2: the Pre-Send Gate (block only when it matters).

* **email / chat** — block only when risk is ``high`` *and* the message is genuinely rude or
  sensitive (a rude/sensitive tone or at least one high-severity etiquette flag). The sender must
  verify with the mascot: pick a rewrite or explicitly confirm. Everything else is a hint.
* **call** — never blocks and never takes over the screen: a small side-panel mascot alert with
  ``intrusive=False``.
"""

from __future__ import annotations

from tone_neuron.schemas import (
    AnalyzeResponse,
    GateRequest,
    GateResponse,
    MascotAlert,
    Rewrite,
)

BLOCKING_TONES = {"rude", "sensitive"}
_REGION_NOTES = {
    "JP": "Japanese readers may read urgency without a date as pressure.",
    "IN": "Indian readers may prefer a warm line and a face-saving request.",
    "DE": "German readers value a dated, factual ask over implied urgency.",
    "US": "US readers expect a direct ask with a named owner and deadline.",
    "UK": "UK readers soften requests; 'with all due respect' reads as hostile.",
    "CN": "Chinese readers protect face; direct correction in a group costs standing.",
    "BR": "Brazilian readers expect warmth before the ask.",
    "AE": "Gulf readers expect a relationship-first, face-saving tone.",
}


def _chosen_rewrite(analysis: AnalyzeResponse, request: GateRequest) -> Rewrite | None:
    if request.chosen_rewrite_index is None or not analysis.rewrites:
        return None
    index = min(request.chosen_rewrite_index, len(analysis.rewrites) - 1)
    return analysis.rewrites[index]


def _top_flag(analysis: AnalyzeResponse) -> str | None:
    for span in analysis.flagged_spans:
        if span.severity == "high":
            return span.text
    for span in analysis.flagged_spans:
        if span.severity == "medium":
            return span.text
    return None


def evaluate_gate(analysis: AnalyzeResponse, request: GateRequest) -> GateResponse:
    """Decide allow / hint / block for one draft and build the mascot payload."""
    high_flags = [span for span in analysis.flagged_spans if span.severity == "high"]
    must_block = analysis.risk == "high" and (
        analysis.tone in BLOCKING_TONES or bool(high_flags)
    )
    chosen = _chosen_rewrite(analysis, request)
    verified = bool(request.sender_confirmed or chosen)
    region_note = _REGION_NOTES.get(analysis.region, "")
    flag_text = _top_flag(analysis)

    # ---- calls: never block, never intrude ------------------------------
    if request.channel == "call":
        if analysis.risk == "high":
            state, title = "worried", "Careful wording"
            message = (
                f"That sounded risky for {analysis.region_name} listeners"
                + (f" ('{flag_text}')." if flag_text else ".")
            )
        elif analysis.risk == "medium":
            state, title = "alert", "Tone heads-up"
            message = f"May read as blunt to {analysis.region_name} participants."
        else:
            state, title = "idle", "All good"
            message = "Wording looks appropriate."
        alert = MascotAlert(
            state=state,  # type: ignore[arg-type]
            title=title,
            message=f"{message} {region_note}".strip(),
            placement="side_panel",
            intrusive=False,
            requires_action=False,
            auto_dismiss_seconds=None if analysis.risk == "high" else 5.0,
            rewrite_preview=analysis.rewrites[0].text[:180] if analysis.rewrites else None,
            analysis_id=analysis.analysis_id,
        )
        return GateResponse(
            decision="allow" if analysis.risk == "low" else "hint",
            risk=analysis.risk,
            blocked=False,
            verified=False,
            requires_confirmation=False,
            reason="Calls are never blocked; the mascot shows a non-intrusive side alert.",
            next_steps=[
                "Keep talking; adjust the next sentence if the hint applies.",
                "Review the suggested phrasing after the call.",
            ]
            if analysis.risk != "low"
            else ["No action needed."],
            mascot_alert=alert,
            analysis=analysis,
        )

    # ---- email / chat ----------------------------------------------------
    if must_block and not verified:
        alert = MascotAlert(
            state="worried",
            title="Hold on — this one is sensitive",
            message=(
                f"This reads as {analysis.tone} for a {analysis.region_name} recipient"
                + (f" ('{flag_text}')" if flag_text else "")
                + f". Risk: {analysis.risk}. Confirm or pick a rewrite before sending. {region_note}"
            ).strip(),
            placement="mascot" if request.channel == "email" else "inline",
            intrusive=False,
            requires_action=True,
            auto_dismiss_seconds=None,
            rewrite_preview=analysis.rewrites[0].text[:220] if analysis.rewrites else None,
            analysis_id=analysis.analysis_id,
        )
        return GateResponse(
            decision="block",
            risk=analysis.risk,
            blocked=True,
            verified=False,
            requires_confirmation=True,
            reason=(
                "High-risk wording with sensitive or rude content. The sender must verify with the "
                "mascot before this leaves the building."
            ),
            next_steps=[
                "Choose one of the rewrites (chosen_rewrite_index) and send that instead.",
                "Or resend with sender_confirmed=true if you are sure the wording is intended.",
            ],
            mascot_alert=alert,
            analysis=analysis,
        )

    if must_block and verified:
        how = "selected a rewrite" if chosen else "confirmed the original wording"
        alert = MascotAlert(
            state="thinking",
            title="Verified — you can send",
            message=f"You {how}. Mascot verification recorded for this draft.",
            placement="mascot" if request.channel == "email" else "inline",
            intrusive=False,
            requires_action=False,
            auto_dismiss_seconds=5.0,
            rewrite_preview=chosen.text[:220] if chosen else None,
            analysis_id=analysis.analysis_id,
        )
        return GateResponse(
            decision="allow",
            risk=analysis.risk,
            blocked=False,
            verified=True,
            requires_confirmation=False,
            reason=f"Mascot verification complete: you {how}.",
            next_steps=["Send the verified version.", "The daily review will include this exchange."],
            mascot_alert=alert,
            analysis=analysis,
        )

    if analysis.risk == "medium":
        alert = MascotAlert(
            state="alert",
            title="Gentle hint",
            message=(
                f"Might land as {analysis.tone} for a {analysis.region_name} recipient. "
                f"{analysis.rewrites[0].rationale if analysis.rewrites else ''} {region_note}"
            ).strip(),
            placement="mascot" if request.channel == "email" else "inline",
            intrusive=False,
            requires_action=False,
            auto_dismiss_seconds=7.0,
            rewrite_preview=analysis.rewrites[0].text[:200] if analysis.rewrites else None,
            analysis_id=analysis.analysis_id,
        )
        return GateResponse(
            decision="hint",
            risk=analysis.risk,
            blocked=False,
            verified=False,
            requires_confirmation=False,
            reason="Medium risk: shown as a hint, sending is not blocked.",
            next_steps=[
                "Send as-is, or open the rewrite if it fits.",
                "No verification required for hints.",
            ],
            mascot_alert=alert,
            analysis=analysis,
        )

    alert = MascotAlert(
        state="happy",
        title="Looks good",
        message=f"Low risk for a {analysis.region_name} recipient.",
        placement="mascot",
        intrusive=False,
        requires_action=False,
        auto_dismiss_seconds=4.0,
        rewrite_preview=None,
        analysis_id=analysis.analysis_id,
    )
    return GateResponse(
        decision="allow",
        risk=analysis.risk,
        blocked=False,
        verified=False,
        requires_confirmation=False,
        reason="Low risk: no cultural red flags for this recipient.",
        next_steps=["Send it."],
        mascot_alert=alert,
        analysis=analysis,
    )

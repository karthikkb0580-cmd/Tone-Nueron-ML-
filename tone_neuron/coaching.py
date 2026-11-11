"""Feature 3: end-of-day coaching review.

The session buffer is in-memory only, holds redacted excerpts, is bounded, expires after
``session_ttl_hours`` and is cleared by the daily review. No email content is written to disk.
"""

from __future__ import annotations

import threading
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from tone_neuron.cards import CardBook
from tone_neuron.config import Settings, get_settings
from tone_neuron.knowledge.okf import KnowledgeEntry
from tone_neuron.knowledge.store import KnowledgeIndex
from tone_neuron.ml import features
from tone_neuron.schemas import (
    AnalyzeResponse,
    Citation,
    CoachingRequest,
    CoachingResponse,
    CoachingTheme,
    LanguageTip,
    WorkCultureNote,
)

DIMENSIONS: dict[str, tuple[str, str]] = {
    "punctuality": ("punctuality", "punctuality and deadlines"),
    "hierarchy": ("hierarchy", "seniority and hierarchy"),
    "decision_making": ("hierarchy", "decision-making style"),
    "small_talk": ("small_talk", "small talk"),
    "feedback_style": ("feedback", "feedback style"),
    "formality": ("formality", "formality and address"),
}
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}
_MEETING_SURFACES = {"meeting"}
_EMAIL_SURFACES = {"email_draft", "email_thread", "chat"}


@dataclass(slots=True)
class SessionEvent:
    analysis_id: str
    ts: str
    surface: str
    channel: str
    region: str
    region_name: str
    risk: str
    tone: str
    categories: list[str] = field(default_factory=list)
    severities: list[str] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)
    excerpt: str = ""
    flagged_count: int = 0


class SessionStore:
    """Bounded, in-memory, redacted event buffer for the daily review."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._events: deque[SessionEvent] = deque(maxlen=max(10, self.settings.max_events))
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def record(self, analysis: AnalyzeResponse, channel: str = "email") -> None:
        if not analysis.analysis_id:
            return
        with self._lock:
            if analysis.analysis_id in self._seen:
                return
            self._seen.add(analysis.analysis_id)
            self._events.append(
                SessionEvent(
                    analysis_id=analysis.analysis_id,
                    ts=datetime.now(timezone.utc).isoformat(),
                    surface=analysis.surface,
                    channel=channel,
                    region=analysis.region,
                    region_name=analysis.region_name,
                    risk=analysis.risk,
                    tone=analysis.tone,
                    categories=sorted({span.category for span in analysis.flagged_spans}),
                    severities=[span.severity for span in analysis.flagged_spans],
                    citation_ids=[citation.entry_id for citation in analysis.citations],
                    excerpt=analysis.excerpt,
                    flagged_count=len(analysis.flagged_spans),
                )
            )
            self._prune_locked()

    def _prune_locked(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.settings.session_ttl_hours)
        while self._events:
            try:
                created = datetime.fromisoformat(self._events[0].ts)
            except ValueError:
                self._events.popleft()
                continue
            if created >= cutoff:
                break
            event = self._events.popleft()
            self._seen.discard(event.analysis_id)

    def events(self, include_meetings: bool = True, date: str | None = None) -> list[SessionEvent]:
        with self._lock:
            self._prune_locked()
            events = list(self._events)
        if not include_meetings:
            events = [event for event in events if event.surface not in _MEETING_SURFACES]
        if date:
            events = [event for event in events if event.ts.startswith(date)]
        return events

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._seen.clear()

    def stats(self) -> dict:
        events = self.events()
        return {
            "events": len(events),
            "regions": sorted({event.region for event in events}),
            "max_events": self.settings.max_events,
        }


# --------------------------------------------------------------------------- #
# Review                                                                      #
# --------------------------------------------------------------------------- #
def _find_entry(index: KnowledgeIndex, region: str, category: str) -> KnowledgeEntry | None:
    for entry in index.entries:
        if entry.region == region.upper() and entry.category == category:
            return entry
    for entry in index.entries:
        if entry.region == "GL" and entry.category == category:
            return entry
    return None


def _citation(entry: KnowledgeEntry) -> Citation:
    return Citation(
        entry_id=entry.id,
        title=entry.title,
        region=entry.region,
        region_name=entry.region_name,
        category=entry.category,
        source_path=entry.path,
        excerpt=entry.excerpt(),
        score=0.0,
        retrieval="coaching",
    )


def _themes(events: list[SessionEvent], index: KnowledgeIndex) -> list[CoachingTheme]:
    grouped: dict[str, list[SessionEvent]] = {}
    for event in events:
        for category in event.categories:
            grouped.setdefault(category, []).append(event)

    themes: list[CoachingTheme] = []
    for category, group in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:4]:
        region = Counter(event.region for event in group).most_common(1)[0][0]
        entry = _find_entry(index, region, category)
        severity = "low"
        for event in group:
            for value in event.severities:
                if _SEVERITY_RANK.get(value, 0) > _SEVERITY_RANK.get(severity, 0):
                    severity = value
        title = entry.title if entry else category.replace("_", " ").title()
        detail = (
            f"{len(group)} checked message(s) involved {category.replace('_', ' ')} "
            f"with {region} recipients."
        )
        if entry:
            detail += f" {entry.excerpt(180)}"
        themes.append(
            CoachingTheme(
                code=category,
                title=title,
                detail=detail,
                count=len(group),
                regions=sorted({event.region for event in group}),
                severity=severity,  # type: ignore[arg-type]
                citation_ids=[entry.id] if entry else [],
            )
        )
    return themes


def _language_tips(events: list[SessionEvent], index: KnowledgeIndex) -> list[LanguageTip]:
    tips: list[LanguageTip] = []
    seen: set[str] = set()

    def add(tip: LanguageTip) -> None:
        if tip.id in seen or len(tips) >= 4:
            return
        seen.add(tip.id)
        tips.append(tip)

    for event in events:
        text = event.excerpt or ""
        lowered = text.lower()
        counts = features.lexicon_counts(text)

        if ("asap" in lowered or "immediately" in lowered) and "dated_deadline" not in seen:
            entry = _find_entry(index, event.region, "punctuality")
            add(
                LanguageTip(
                    id="dated_deadline",
                    focus="Deadlines",
                    phrase="asap",
                    better="by Friday 6 March, 17:00 (with a time zone)",
                    why=(
                        "Urgency without a date transfers pressure instead of information, and in "
                        f"many regions it also reads as poor planning. {entry.excerpt(120) if entry else ''}"
                    ).strip(),
                    example="Could you send the report by Friday 6 March, 17:00 CET?",
                    citation_ids=[entry.id] if entry else [],
                )
            )

        if counts["hedge"] >= 3 and "trim_hedges" not in seen:
            entry = _find_entry(index, event.region, "directness")
            add(
                LanguageTip(
                    id="trim_hedges",
                    focus="Clarity",
                    phrase="maybe / perhaps / I think / could",
                    better="one clear request with a reason",
                    why=(
                        "Stacked hedges hide the ask, which slows replies. Softening one clause is "
                        "polite; softening every clause is unclear."
                    ),
                    example="Could you confirm the budget by Thursday so finance can close the month?",
                    citation_ids=[entry.id] if entry else [],
                )
            )

        if event.region in ("JP", "CN") and "honorific" not in seen:
            has_honorific = any(
                cue in text for cue in ("-san", "さん", "様", "经理", "总", "様", "您")
            )
            if not has_honorific and text:
                entry = _find_entry(index, event.region, "formality")
                add(
                    LanguageTip(
                        id="honorific",
                        focus="Address form",
                        phrase="first name only",
                        better="surname + honorific (Tanaka-san / 王经理)",
                        why=(
                            "Address form carries the relationship in Japanese and Chinese business "
                            "writing; dropping it reads as dismissive rather than friendly."
                        ),
                        example="Tanaka-san, could you confirm the figures by Friday?",
                        citation_ids=[entry.id] if entry else [],
                    )
                )

        idiom = next(
            (word for word in ("ballpark", "circle back", "touch base", "reach out") if word in lowered),
            None,
        )
        if idiom and "idioms" not in seen:
            entry = _find_entry(index, event.region, "humor")
            add(
                LanguageTip(
                    id="idioms",
                    focus="Idioms",
                    phrase=idiom,
                    better="plain wording",
                    why=(
                        "English idioms rarely translate literally. Plain wording keeps the request "
                        "clear for a reader working in a second language."
                    ),
                    example="Could you give me an approximate range for the budget?",
                    citation_ids=[entry.id] if entry else [],
                )
            )

    return tips


def _work_culture_notes(events: list[SessionEvent], index: KnowledgeIndex) -> list[WorkCultureNote]:
    meeting_events = [event for event in events if event.surface in _MEETING_SURFACES]
    if not meeting_events:
        return []
    notes: list[WorkCultureNote] = []
    regions = sorted({event.region for event in meeting_events})
    for region in regions:
        regional_events = [event for event in meeting_events if event.region == region]
        for dimension, (category, label) in DIMENSIONS.items():
            entry = _find_entry(index, region, category)
            if entry is None:
                continue
            flagged = [
                event for event in regional_events if category in event.categories
            ]
            if flagged:
                observation = (
                    f"{len(flagged)} exchange(s) in meetings with {entry.region_name} participants "
                    f"touched {label}."
                )
            else:
                observation = (
                    f"{len(regional_events)} meeting exchange(s) with {entry.region_name} "
                    f"participants; no {label} issue detected."
                )
            guidance = entry.dos[0] if entry.dos else entry.excerpt(200)
            notes.append(
                WorkCultureNote(
                    region=region,
                    region_name=entry.region_name,
                    dimension=dimension,  # type: ignore[arg-type]
                    observation=observation,
                    guidance=guidance,
                    citation_ids=[entry.id],
                )
            )
        if len(notes) >= 8:
            break
    return notes[:8]


def build_daily_review(
    store: SessionStore,
    index: KnowledgeIndex,
    cards: CardBook,
    request: CoachingRequest | None = None,
    settings: Settings | None = None,
) -> CoachingResponse:
    request = request or CoachingRequest()
    settings = settings or get_settings()
    today = request.date or datetime.now(timezone.utc).date().isoformat()
    events = store.events(include_meetings=request.include_meetings, date=request.date)
    unlocked = cards.unlocked_regions()

    if not events:
        return CoachingResponse(
            date=today,
            summary=(
                "Nothing checked yet today. Drafts you analyse and meeting lines you check will "
                "show up here as a short review."
            ),
            cards_unlocked=unlocked,
            mascot_state="idle",
            privacy_note="The session buffer is empty; no content is stored.",
        )

    emails = sum(1 for event in events if event.surface in _EMAIL_SURFACES)
    meetings = sum(1 for event in events if event.surface in _MEETING_SURFACES)
    risk_breakdown = Counter(event.risk for event in events)
    high_risk = risk_breakdown.get("high", 0)
    top_regions = [region for region, _ in Counter(event.region for event in events).most_common(3)]

    themes = _themes(events, index)
    tips = _language_tips(events, index)
    notes = _work_culture_notes(events, index)

    citation_ids: list[str] = []
    for theme in themes:
        citation_ids.extend(theme.citation_ids)
    for tip in tips:
        citation_ids.extend(tip.citation_ids)
    for note in notes:
        citation_ids.extend(note.citation_ids)
    citations: list[Citation] = []
    seen_ids: set[str] = set()
    for entry_id in citation_ids:
        if entry_id in seen_ids:
            continue
        entry = index.entry(entry_id)
        if entry is None:
            continue
        seen_ids.add(entry_id)
        citations.append(_citation(entry))

    wins: list[str] = []
    low = risk_breakdown.get("low", 0)
    if low:
        wins.append(f"{low} message(s) already landed at low risk - keep that baseline.")
    if not high_risk:
        wins.append("No high-risk messages were flagged today.")
    if unlocked:
        wins.append(f"Culture cards unlocked: {', '.join(unlocked)}.")

    summary = (
        f"You checked {emails} email/chat message(s) and {meetings} meeting exchange(s) across "
        f"{len(top_regions)} region(s). "
        + (f"{high_risk} high-risk item(s) needed attention. " if high_risk else "Nothing high-risk today. ")
        + (f"Most frequent theme: {themes[0].title}." if themes else "No recurring etiquette theme.")
    )

    if request.clear_after:
        store.clear()

    return CoachingResponse(
        date=today,
        summary=summary,
        emails_checked=emails,
        meetings_checked=meetings,
        high_risk_count=high_risk,
        risk_breakdown=dict(risk_breakdown),
        top_regions=top_regions,
        themes=themes,
        language_tips=tips,
        work_culture_notes=notes,
        wins=wins,
        citations=citations[:12],
        cards_unlocked=unlocked,
        mascot_state="worried" if high_risk else "happy",
        privacy_note=(
            "Session buffer cleared; only aggregate counts remain. Tone Neuron never stores email "
            "content permanently."
            if request.clear_after
            else "Session buffer is in memory only and expires automatically."
        ),
    )

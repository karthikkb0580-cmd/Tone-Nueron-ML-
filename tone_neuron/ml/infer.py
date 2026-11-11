"""Feature 1 + the clean inference API.

``analyze(text, context, receiver_info) -> {region, confidence, risk, flagged_spans, reasons,
rewrites, citations}`` works for Gmail drafts, chat messages and meeting transcripts alike; only
the adapter that builds the input differs.
"""

from __future__ import annotations

import re
import threading
import uuid
from typing import Any

from tone_neuron.cards import CardBook
from tone_neuron.config import Settings, get_settings
from tone_neuron.knowledge.okf import KnowledgeEntry
from tone_neuron.knowledge.store import KnowledgeIndex, RetrievedEntry
from tone_neuron.ml import features
from tone_neuron.ml.region_inference import RegionHypothesis, RegionInference
from tone_neuron.ml.rewrites import RewriteEngine
from tone_neuron.ml.tone import ToneClassifier, TonePrediction, assess_risk
from tone_neuron.privacy import redact
from tone_neuron.schemas import (
    AnalyzeContext,
    AnalyzeResponse,
    Citation,
    FlaggedSpan,
    Reason,
    ReceiverInfo,
    coerce_context,
    coerce_receiver,
)

UNIVERSAL_REGION = "GL"
HIGH_STAKES_TERMS = (
    "salary",
    "termination",
    "harassment",
    "discrimination",
    "lawsuit",
    "fired",
    "redundancy",
    "performance review",
)
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}
_SHOUT_RE = re.compile(r"\b[A-Z]{4,}(?:\s+[A-Z]{4,}){2,}\b")
_EXCLAIM_RE = re.compile(r"!{3,}")


def _citation(entry: KnowledgeEntry, score: float = 0.0, retrieval: str = "direct-scan") -> Citation:
    return Citation(
        entry_id=entry.id,
        title=entry.title,
        region=entry.region,
        region_name=entry.region_name,
        category=entry.category,
        source_path=entry.path,
        excerpt=entry.excerpt(),
        score=round(float(score), 4),
        retrieval=retrieval,
    )


class NeuroEngine:
    """Holds the loaded knowledge index and models; safe to share across requests."""

    def __init__(
        self,
        settings: Settings | None = None,
        index: KnowledgeIndex | None = None,
        cards: CardBook | None = None,
    ):
        self.settings = settings or get_settings()
        self.settings.ensure_dirs()
        self.index = index or KnowledgeIndex.load_or_build(self.settings)
        self.cards = cards or CardBook(self.settings)
        self.region_model = RegionInference.load_or_rules(self.settings)
        self.tone_model = ToneClassifier.load(self.settings)
        self.rewriter = RewriteEngine(self.index, self.settings)

    # -- public API --------------------------------------------------------
    def analyze(
        self,
        text: str,
        context: Any = None,
        receiver_info: Any = None,
        use_llm: bool | None = None,
    ) -> AnalyzeResponse:
        raw_text = text or ""
        context = coerce_context(context)
        receiver = coerce_receiver(receiver_info)
        if use_llm is None:
            use_llm = context.use_llm

        hypothesis = self.region_model.infer(raw_text, receiver, context)
        region = hypothesis.region
        region_name = hypothesis.region_name or self.index.region_name(region)

        retrieved = self.index.retrieve(
            self._query(raw_text, context, receiver), k=self.settings.top_k, region=region
        )
        flag_entries = self._flag_entries(region)
        spans = self._dedupe_spans(
            self._scan_flags(raw_text, flag_entries) + self._heuristic_spans(raw_text, flag_entries)
        )
        spans.sort(key=lambda span: (span.start, -_SEVERITY_RANK.get(span.severity, 0)))

        tone_pred = self._adjust_tone(self.tone_model.predict(raw_text, region), raw_text, spans)
        assessment = assess_risk(tone_pred, spans)

        expectation_reasons = self._expectation_reasons(raw_text, region, context.surface, flag_entries)
        citations = self._citations(retrieved, spans, [])
        rewrites = self.rewriter.suggest(
            raw_text,
            region,
            spans,
            citations=citations,
            receiver_name=receiver.name,
            use_llm=use_llm,
        )
        citations = self._citations(retrieved, spans, rewrites)

        reasons: list[Reason] = [self._region_reason(hypothesis)]
        reasons.extend(self._flag_reasons(spans))
        reasons.extend(expectation_reasons)
        reasons.append(
            Reason(
                code="tone_assessment",
                message=assessment.rationale,
                severity=assessment.risk,
                citation_id=citations[0].entry_id if citations else None,
            )
        )
        if hypothesis.overridden:
            reasons.append(
                Reason(
                    code="region_override",
                    message=f"Region was set by the user to {region}; inference results were ignored.",
                    severity="low",
                )
            )

        risk = assessment.risk
        recommended = "block" if risk == "high" else "hint" if risk == "medium" else "allow"
        mascot_state = "worried" if risk == "high" else "alert" if risk == "medium" else "happy"

        notes = [
            f"Retrieved {len(retrieved)} OKF entries for {region} "
            f"({self.index.embedder.name} → {self.index.store.name} → {self.index.reranker.name}).",
            "Region is a probabilistic guess; use receiver_info.region_override to correct it.",
        ]
        if not citations:
            notes.append("No specific etiquette entry matched; the verdict is conservative.")
        if any(citation.region == UNIVERSAL_REGION for citation in citations):
            notes.append("Some rules come from the universal baseline profile.")

        self.cards.unlock(region)

        return AnalyzeResponse(
            analysis_id=uuid.uuid4().hex,
            excerpt=redact(raw_text, 180),
            region=region,
            region_name=region_name,
            confidence=round(float(hypothesis.confidence), 4),
            confidence_label=hypothesis.confidence_label,
            is_guess=True,
            region_overridden=hypothesis.overridden,
            alternatives=hypothesis.alternatives,
            region_evidence=hypothesis.evidence,
            risk=risk,
            risk_score=assessment.score,
            tone=tone_pred.label,
            tone_probabilities={
                label: round(float(probability), 4)
                for label, probability in tone_pred.probabilities.items()
            },
            flagged_spans=spans,
            reasons=reasons,
            rewrites=rewrites,
            citations=citations,
            mascot_state=mascot_state,
            recommended_action=recommended,
            surface=context.surface,
            knowledge_notes=notes,
        )

    # -- retrieval ---------------------------------------------------------
    @staticmethod
    def _query(text: str, context: AnalyzeContext, receiver: ReceiverInfo) -> str:
        parts = [text[:4000]]
        if context.subject:
            parts.append(context.subject)
        if context.thread_history:
            parts.append(context.thread_history[-1][:1200])
        if receiver.signature:
            parts.append(receiver.signature[:600])
        if context.meeting and context.meeting.agenda:
            parts.append(context.meeting.agenda)
        return "\n".join(part for part in parts if part).strip()

    def _flag_entries(self, region: str) -> list[KnowledgeEntry]:
        regional = [entry for entry in self.index.entries if entry.region == region.upper()]
        universal = [entry for entry in self.index.entries if entry.region == UNIVERSAL_REGION]
        return regional + universal

    # -- flag scanning -----------------------------------------------------
    @staticmethod
    def _scan_flags(text: str, entries: list[KnowledgeEntry]) -> list[FlaggedSpan]:
        if not text:
            return []
        seen: set[tuple[int, int]] = set()
        spans: list[FlaggedSpan] = []
        for entry in entries:
            for rule in entry.flags:
                for match in rule.finditer(text):
                    key = (match.start(), match.end())
                    if key in seen:
                        continue
                    seen.add(key)
                    spans.append(
                        FlaggedSpan(
                            text=match.group(0),
                            start=match.start(),
                            end=match.end(),
                            category=rule.category or entry.category,
                            severity=rule.severity,
                            reason=rule.why or entry.title,
                            citation_id=entry.id,
                            suggested_text=rule.suggested,
                        )
                    )
        return spans

    def _heuristic_spans(self, text: str, entries: list[KnowledgeEntry]) -> list[FlaggedSpan]:
        spans: list[FlaggedSpan] = []
        clarity = self.index.entry("gl.clarity.plain_language")
        for match in _SHOUT_RE.finditer(text):
            spans.append(
                FlaggedSpan(
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    category="directness",
                    severity="low",
                    reason="All-caps emphasis reads as shouting in written messages.",
                    citation_id=clarity.id if clarity else None,
                    suggested_text=None,
                )
            )
        for match in _EXCLAIM_RE.finditer(text):
            spans.append(
                FlaggedSpan(
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    category="directness",
                    severity="low",
                    reason="Repeated exclamation marks amplify the emotional charge.",
                    citation_id=clarity.id if clarity else None,
                    suggested_text=".",
                )
            )
        return spans

    @staticmethod
    def _dedupe_spans(spans: list[FlaggedSpan]) -> list[FlaggedSpan]:
        seen: set[tuple[int, int]] = set()
        unique: list[FlaggedSpan] = []
        for span in spans:
            key = (span.start, span.end)
            if key in seen:
                continue
            seen.add(key)
            unique.append(span)
        return unique

    # -- tone --------------------------------------------------------------
    @staticmethod
    def _adjust_tone(prediction: TonePrediction, text: str, spans: list[FlaggedSpan]) -> TonePrediction:
        high = [span for span in spans if span.severity == "high"]
        if not high:
            return prediction
        lowered = text.lower()
        target = None
        if any(term in lowered for term in HIGH_STAKES_TERMS):
            target = "sensitive"
        elif prediction.label not in ("rude", "sensitive"):
            target = "rude"
        if target:
            prediction.label = target
            prediction.probabilities[target] = max(prediction.probabilities.get(target, 0.0), 0.62)
            total = sum(prediction.probabilities.values()) or 1.0
            prediction.probabilities = {
                label: value / total for label, value in prediction.probabilities.items()
            }
        return prediction

    # -- reasons + citations ----------------------------------------------
    def _region_reason(self, hypothesis: RegionHypothesis) -> Reason:
        evidence = ", ".join(
            f"{signal.kind}={signal.value}" for signal in hypothesis.evidence[:4]
        ) or "no strong signal"
        confidence_pct = round(hypothesis.confidence * 100)
        message = (
            f"Likely {hypothesis.region_name} ({hypothesis.region}) with "
            f"{confidence_pct}% confidence ({hypothesis.confidence_label}). Signals: {evidence}. "
            "This is a guess, not a fact about the person."
        )
        return Reason(code="region_inference", message=message, severity="low")

    @staticmethod
    def _flag_reasons(spans: list[FlaggedSpan]) -> list[Reason]:
        grouped: dict[tuple[str, str | None], list[FlaggedSpan]] = {}
        for span in spans:
            grouped.setdefault((span.category, span.citation_id), []).append(span)
        reasons: list[Reason] = []
        for (category, citation_id), group in list(grouped.items())[:6]:
            phrases = ", ".join(f"'{span.text}'" for span in group[:3])
            reasons.append(
                Reason(
                    code=f"flag:{category}",
                    message=f"{phrases}: {group[0].reason}",
                    severity=max(group, key=lambda span: _SEVERITY_RANK[span.severity]).severity,
                    citation_id=citation_id,
                )
            )
        return reasons

    def _expectation_reasons(
        self,
        text: str,
        region: str,
        surface: str,
        entries: list[KnowledgeEntry],
    ) -> list[Reason]:
        reasons: list[Reason] = []
        for expectation in features.missing_expectations(text, region, surface):
            entry = next((item for item in entries if item.category == expectation.category), None)
            reasons.append(
                Reason(
                    code=expectation.code,
                    message=expectation.message,
                    severity=expectation.severity,  # type: ignore[arg-type]
                    citation_id=entry.id if entry else None,
                )
            )
        return reasons

    def _citations(
        self,
        retrieved: list[RetrievedEntry],
        spans: list[FlaggedSpan],
        rewrites: list[Any],
    ) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[str] = set()
        for hit in retrieved:
            if hit.entry.id in seen:
                continue
            seen.add(hit.entry.id)
            citations.append(hit.citation())

        referenced: list[str] = []
        for span in spans:
            if span.citation_id:
                referenced.append(span.citation_id)
        for rewrite in rewrites:
            referenced.extend(getattr(rewrite, "citation_ids", []) or [])
        for entry_id in referenced:
            if entry_id in seen:
                continue
            entry = self.index.entry(entry_id)
            if entry is None:
                continue
            seen.add(entry_id)
            citations.append(_citation(entry))

        return citations[:10]


# --------------------------------------------------------------------------- #
# Module-level convenience API                                                #
# --------------------------------------------------------------------------- #
_ENGINE: NeuroEngine | None = None
_LOCK = threading.Lock()


def get_engine(settings: Settings | None = None) -> NeuroEngine:
    global _ENGINE
    if _ENGINE is None:
        with _LOCK:
            if _ENGINE is None:
                _ENGINE = NeuroEngine(settings)
    return _ENGINE


def reset_engine() -> None:
    """Drop the cached engine (used by tests and after retraining)."""
    global _ENGINE
    with _LOCK:
        _ENGINE = None


def analyze(text: str, context: Any = None, receiver_info: Any = None) -> dict:
    """Spec-compatible entry point returning a plain dict."""
    return get_engine().analyze(text, context, receiver_info).model_dump()

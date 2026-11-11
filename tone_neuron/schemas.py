"""Pydantic contracts shared by the API, the ML layer and the mascot."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RiskLevel = Literal["low", "medium", "high"]
ToneLabel = Literal["polite", "neutral", "blunt", "rude", "sensitive"]
Surface = Literal["email_draft", "email_thread", "chat", "meeting", "manual"]
Channel = Literal["email", "chat", "call"]
MascotState = Literal["idle", "alert", "thinking", "happy", "worried"]
Decision = Literal["allow", "hint", "block"]
ConfidenceLabel = Literal["low", "moderate", "strong"]


class NMModel(BaseModel):
    """Base model: tolerant of extra keys (older/newer mascot builds)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True, str_strip_whitespace=True)


# --------------------------------------------------------------------------- #
# Evidence                                                                     #
# --------------------------------------------------------------------------- #
class Citation(NMModel):
    """A retrieved OKF entry backing a claim. Every verdict carries at least one."""

    entry_id: str
    title: str
    region: str
    region_name: str
    category: str
    source_path: str
    excerpt: str
    score: float = 0.0
    retrieval: str = "hybrid+mmr+rerank"


class FlaggedSpan(NMModel):
    text: str
    start: int
    end: int
    category: str
    severity: RiskLevel
    reason: str
    citation_id: str | None = None
    suggested_text: str | None = None


class Reason(NMModel):
    code: str
    message: str
    severity: RiskLevel = "low"
    citation_id: str | None = None


class Rewrite(NMModel):
    text: str
    rationale: str
    strategy: Literal["soften", "formalize", "clarify", "localize", "de-escalate"] = "localize"
    citation_ids: list[str] = Field(default_factory=list)
    generated_by: str = "grounded-template"


class AlternativeRegion(NMModel):
    region: str
    region_name: str
    probability: float


class RegionSignal(NMModel):
    kind: str
    value: str
    weight: float
    note: str = ""


# --------------------------------------------------------------------------- #
# Inputs                                                                       #
# --------------------------------------------------------------------------- #
class ReceiverInfo(NMModel):
    name: str | None = None
    email: str | None = None
    domain: str | None = None
    language: str | None = None
    timezone: str | None = None
    signature: str | None = None
    organization: str | None = None
    region_override: str | None = None
    notes: str | None = None

    @field_validator("region_override")
    @classmethod
    def _upper_region(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        return value[:3] or None

    @model_validator(mode="after")
    def _derive_domain(self) -> "ReceiverInfo":
        if not self.domain and self.email and "@" in self.email:
            object.__setattr__(self, "domain", self.email.split("@", 1)[1].lower())
        return self


class MeetingMeta(NMModel):
    title: str | None = None
    participants: list[str] = Field(default_factory=list)
    duration_minutes: float | None = None
    agenda: str | None = None
    captions_are_live: bool = False
    starts_on_time: bool | None = None


class AnalyzeContext(NMModel):
    surface: Surface = "manual"
    subject: str | None = None
    thread_history: list[str] = Field(default_factory=list)
    meeting: MeetingMeta | None = None
    target_language: str | None = None
    sender_region: str | None = None
    use_llm: bool | None = None

    @field_validator("thread_history")
    @classmethod
    def _cap_history(cls, value: list[str]) -> list[str]:
        return [item[:8000] for item in value][-12:]


class AnalyzeRequest(NMModel):
    text: str = Field(min_length=1, max_length=40_000)
    context: AnalyzeContext = Field(default_factory=AnalyzeContext)
    receiver_info: ReceiverInfo = Field(default_factory=ReceiverInfo)


# --------------------------------------------------------------------------- #
# Feature 1 output                                                             #
# --------------------------------------------------------------------------- #
class AnalyzeResponse(NMModel):
    region: str
    region_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel
    is_guess: bool = True
    region_overridden: bool = False
    alternatives: list[AlternativeRegion] = Field(default_factory=list)
    region_evidence: list[RegionSignal] = Field(default_factory=list)

    risk: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    tone: ToneLabel
    tone_probabilities: dict[str, float] = Field(default_factory=dict)

    flagged_spans: list[FlaggedSpan] = Field(default_factory=list)
    reasons: list[Reason] = Field(default_factory=list)
    rewrites: list[Rewrite] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

    mascot_state: MascotState = "idle"
    recommended_action: Decision = "allow"
    surface: Surface = "manual"
    knowledge_notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Feature 2                                                                   #
# --------------------------------------------------------------------------- #
class MascotAlert(NMModel):
    state: MascotState = "idle"
    title: str
    message: str
    placement: Literal["mascot", "side_panel", "inline"] = "mascot"
    intrusive: bool = False
    requires_action: bool = False
    auto_dismiss_seconds: float | None = 6.0
    rewrite_preview: str | None = None
    analysis_id: str | None = None


class GateRequest(NMModel):
    text: str = Field(min_length=1, max_length=40_000)
    context: AnalyzeContext = Field(default_factory=AnalyzeContext)
    receiver_info: ReceiverInfo = Field(default_factory=ReceiverInfo)
    channel: Channel = "email"
    sender_confirmed: bool = False
    chosen_rewrite_index: int | None = Field(default=None, ge=0, le=9)

    @model_validator(mode="after")
    def _sync_channel(self) -> "GateRequest":
        if self.channel == "call" and self.context.surface not in ("meeting", "manual"):
            self.context.surface = "meeting"
        if self.channel in ("email", "chat") and self.context.surface == "manual":
            self.context.surface = "email_draft" if self.channel == "email" else "chat"
        return self


class GateResponse(NMModel):
    decision: Decision
    risk: RiskLevel
    blocked: bool
    verified: bool = False
    requires_confirmation: bool = False
    reason: str
    next_steps: list[str] = Field(default_factory=list)
    mascot_alert: MascotAlert
    analysis: AnalyzeResponse


# --------------------------------------------------------------------------- #
# Feature 3                                                                   #
# --------------------------------------------------------------------------- #
class CoachingRequest(NMModel):
    date: str | None = None
    target_language: str | None = None
    include_meetings: bool = True
    clear_after: bool = False


class CoachingTheme(NMModel):
    code: str
    title: str
    detail: str
    count: int = 0
    regions: list[str] = Field(default_factory=list)
    severity: RiskLevel = "low"
    citation_ids: list[str] = Field(default_factory=list)


class LanguageTip(NMModel):
    id: str
    focus: str
    phrase: str
    better: str
    why: str
    example: str
    citation_ids: list[str] = Field(default_factory=list)


class WorkCultureNote(NMModel):
    region: str
    region_name: str
    dimension: Literal[
        "punctuality",
        "hierarchy",
        "decision_making",
        "small_talk",
        "feedback_style",
        "formality",
    ]
    observation: str
    guidance: str
    citation_ids: list[str] = Field(default_factory=list)


class CoachingResponse(NMModel):
    date: str
    summary: str
    emails_checked: int = 0
    meetings_checked: int = 0
    high_risk_count: int = 0
    risk_breakdown: dict[str, int] = Field(default_factory=dict)
    top_regions: list[str] = Field(default_factory=list)
    themes: list[CoachingTheme] = Field(default_factory=list)
    language_tips: list[LanguageTip] = Field(default_factory=list)
    work_culture_notes: list[WorkCultureNote] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    cards_unlocked: list[str] = Field(default_factory=list)
    mascot_state: MascotState = "happy"
    privacy_note: str = (
        "Session buffer cleared. Tone Neuron never stores email content permanently."
    )


# --------------------------------------------------------------------------- #
# Cards / health                                                              #
# --------------------------------------------------------------------------- #
class CultureCard(NMModel):
    card_id: str
    region: str
    region_name: str
    language: str
    character_name: str
    sprite: str
    greeting_expression: str
    greeting: str
    formality: str
    dos: list[str] = Field(default_factory=list)
    donts: list[str] = Field(default_factory=list)
    taboo_topics: list[str] = Field(default_factory=list)
    caveat: str = ""
    unlocked: bool = False
    unlocked_at: str | None = None


class CardsResponse(NMModel):
    cards: list[CultureCard]
    unlocked_count: int
    total: int
    active_region: str


class CardUnlockRequest(NMModel):
    region: str = Field(min_length=2, max_length=3)
    reason: str = "interaction"


class HealthResponse(NMModel):
    status: Literal["ok", "degraded"] = "ok"
    version: str
    embedder: str
    vector_store: str
    reranker: str
    knowledge_entries: int
    regions: list[str]
    model_loaded: bool
    model_version: str
    llm_enabled: bool
    uptime_seconds: float


# --------------------------------------------------------------------------- #
# Adapters                                                                    #
# --------------------------------------------------------------------------- #
class TranscriptTurn(NMModel):
    speaker: str
    text: str
    timestamp: str | None = None
    is_owner: bool = False


class DraftMessage(NMModel):
    draft_id: str | None = None
    thread_id: str | None = None
    to: list[str] = Field(default_factory=list)
    subject: str | None = None
    body: str
    snippet: str | None = None


def coerce_receiver(value: Any) -> ReceiverInfo:
    if isinstance(value, ReceiverInfo):
        return value
    if value is None:
        return ReceiverInfo()
    if isinstance(value, dict):
        return ReceiverInfo(**value)
    raise TypeError(f"Cannot interpret receiver_info of type {type(value)!r}")


def coerce_context(value: Any) -> AnalyzeContext:
    if isinstance(value, AnalyzeContext):
        return value
    if value is None:
        return AnalyzeContext()
    if isinstance(value, str):
        # convenience: treat a bare string as the surface name
        try:
            return AnalyzeContext(surface=value)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001 - fall back to manual
            return AnalyzeContext()
    if isinstance(value, dict):
        return AnalyzeContext(**value)
    raise TypeError(f"Cannot interpret context of type {type(value)!r}")

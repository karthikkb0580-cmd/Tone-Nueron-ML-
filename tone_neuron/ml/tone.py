"""Task B: tone + risk classification (conditioned on the receiver's region).

Uses a trained artifact when present, and a transparent lexicon/rule model otherwise, so the API
always works. The risk *level* is derived from tone + matched etiquette flags, which keeps the
gate explainable.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tone_neuron.config import Settings, get_settings
from tone_neuron.ml import features
from tone_neuron.ml.baseline_fasttext import load_artifact

TONES: tuple[str, ...] = ("polite", "neutral", "blunt", "rude", "sensitive")


@dataclass(slots=True)
class TonePrediction:
    label: str
    probabilities: dict[str, float]
    source: str = "rules"


def _normalise(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    peak = max(scores.values()) if scores else 0.0
    exps = {label: math.exp((score - peak) / temperature) for label, score in scores.items()}
    total = sum(exps.values()) or 1.0
    return {label: value / total for label, value in exps.items()}


class ToneClassifier:
    def __init__(self, model=None, classes: list[str] | None = None, source: str = "rules"):
        self.model = model
        self.classes = list(classes or TONES)
        self.source = source

    @classmethod
    def load(cls, settings: Settings | None = None) -> "ToneClassifier":
        settings = settings or get_settings()
        meta_path = Path(settings.model_dir) / "tone_best.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                model = load_artifact(meta)
                return cls(
                    model=model,
                    classes=list(getattr(model, "classes_", meta.get("classes", TONES))),
                    source=str(meta.get("backend", "trained")),
                )
            except Exception:
                pass
        return cls(source="rules")

    # -- rules fallback ----------------------------------------------------
    def _rule_probabilities(self, text: str) -> dict[str, float]:
        counts = features.lexicon_counts(text)
        imperatives = features.imperative_score(text)
        scores = {
            "polite": 0.6
            + 1.5 * counts["polite"]
            + 0.8 * counts["hedge"]
            + 1.0 * counts["gratitude"]
            + 0.4 * counts["formal"],
            "neutral": 1.4 + 0.5 * counts["formal"],
            "blunt": 0.4
            + 1.4 * counts["urgency"]
            + 1.1 * imperatives
            + 0.7 * counts["casual"],
            "rude": 0.1
            + 4.0 * counts["insult"]
            + 1.2 * counts["urgency"]
            + 2.0 * counts["threat"],
            "sensitive": 0.1
            + 3.0 * counts["sensitive"]
            + 2.0 * counts["threat"]
            + 1.0 * counts["formal"],
        }
        # a blunt message with a lot of politeness is usually neutral-polite
        if scores["polite"] > scores["blunt"] and counts["urgency"] == 0:
            scores["blunt"] = max(0.0, scores["blunt"] - 0.5)
        return _normalise(scores)

    # -- inference ---------------------------------------------------------
    def predict(self, text: str, region: str = "US") -> TonePrediction:
        if self.model is not None:
            try:
                row = features.tone_feature_text(text, region)
                proba = np.asarray(self.model.predict_proba([row]))[0]
                probabilities = {
                    label: float(proba[self.classes.index(label)])
                    for label in TONES
                    if label in self.classes
                }
                if probabilities:
                    label = max(probabilities, key=probabilities.get)
                    return TonePrediction(label=label, probabilities=probabilities, source=self.source)
            except Exception:
                pass
        probabilities = self._rule_probabilities(text)
        return TonePrediction(
            label=max(probabilities, key=probabilities.get),
            probabilities=probabilities,
            source="rules",
        )


@dataclass(slots=True)
class RiskAssessment:
    risk: str
    score: float
    rationale: str


_BASE_RISK: dict[str, float] = {
    "polite": 0.06,
    "neutral": 0.18,
    "blunt": 0.46,
    "rude": 0.82,
    "sensitive": 0.88,
}


def assess_risk(tone: TonePrediction, flagged) -> RiskAssessment:
    """Blend the tone probability with severity of matched etiquette flags."""
    probabilities = tone.probabilities
    weighted = sum(
        _BASE_RISK.get(label, 0.3) * probability for label, probability in probabilities.items()
    )
    high_flags = [span for span in flagged if span.severity == "high"]
    medium_flags = [span for span in flagged if span.severity == "medium"]
    score = weighted + 0.12 * min(len(high_flags), 3) + 0.04 * min(len(medium_flags), 4)
    score = max(score, _BASE_RISK.get(tone.label, 0.2))
    score = min(1.0, score)

    has_high_signal = bool(high_flags) or tone.label in ("rude", "sensitive")
    if score >= 0.66 and has_high_signal:
        level = "high"
    elif score >= 0.34:
        level = "medium"
    else:
        level = "low"

    rationale = (
        f"Tone {tone.label} ({tone.source}) with {len(high_flags)} high-severity and "
        f"{len(medium_flags)} medium-severity etiquette matches."
    )
    return RiskAssessment(risk=level, score=round(score, 3), rationale=rationale)

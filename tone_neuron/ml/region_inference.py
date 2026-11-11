"""Task A: culture/origin inference.

A transparent evidence model (name, script, TLD, language, time zone, signature, phrasing) is
blended with an optional trained classifier. The output is always a *distribution* with a capped
confidence, never a claim about a person.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tone_neuron.config import Settings, get_settings
from tone_neuron.ml import features
from tone_neuron.ml.baseline_fasttext import load_artifact
from tone_neuron.schemas import (
    AlternativeRegion,
    AnalyzeContext,
    ConfidenceLabel,
    ReceiverInfo,
    RegionSignal,
)


@dataclass(slots=True)
class RegionHypothesis:
    region: str
    region_name: str
    confidence: float
    confidence_label: ConfidenceLabel
    distribution: dict[str, float]
    evidence: list[RegionSignal] = field(default_factory=list)
    alternatives: list[AlternativeRegion] = field(default_factory=list)
    overridden: bool = False
    source: str = "evidence"


def _confidence_label(probability: float, gap: float) -> ConfidenceLabel:
    if probability >= 0.65 and gap >= 0.12:
        return "strong"
    if probability >= 0.42:
        return "moderate"
    return "low"


class RegionInference:
    """Combines rule evidence with an optional trained region classifier."""

    def __init__(
        self,
        classifier=None,
        classes: list[str] | None = None,
        settings: Settings | None = None,
        source: str = "evidence",
    ):
        self.settings = settings or get_settings()
        self.classifier = classifier
        self.classes = list(classes or [])
        self.source = source

    @classmethod
    def load_or_rules(cls, settings: Settings | None = None) -> "RegionInference":
        settings = settings or get_settings()
        meta_path = Path(settings.model_dir) / "region_best.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                model = load_artifact(meta)
                return cls(
                    classifier=model,
                    classes=list(getattr(model, "classes_", meta.get("classes", []))),
                    settings=settings,
                    source=str(meta.get("backend", "trained")),
                )
            except Exception:
                pass
        return cls(settings=settings, source="evidence")

    def _classifier_distribution(
        self, text: str, receiver: ReceiverInfo, context: AnalyzeContext
    ) -> dict[str, float] | None:
        if self.classifier is None or not self.classes:
            return None
        try:
            row = features.region_feature_text(text, receiver, context, include_text=False)
            proba = np.asarray(self.classifier.predict_proba([row]))[0]
            return {
                region: float(proba[self.classes.index(region)])
                for region in features.REGIONS
                if region in self.classes
            }
        except Exception:
            return None

    def infer(
        self,
        text: str,
        receiver: ReceiverInfo | None = None,
        context: AnalyzeContext | None = None,
    ) -> RegionHypothesis:
        receiver = receiver or ReceiverInfo()
        context = context or AnalyzeContext()
        cap = float(self.settings.max_confidence)

        if receiver.region_override:
            region = receiver.region_override.upper()
            distribution = {r: 0.01 for r in features.REGIONS}
            distribution[region] = 0.99
            return RegionHypothesis(
                region=region,
                region_name=features.REGION_NAMES.get(region, region),
                confidence=min(cap, 0.99),
                confidence_label="strong",
                distribution=distribution,
                evidence=[
                    RegionSignal(
                        kind="user_override",
                        value=region,
                        weight=1.0,
                        note="Region set by the user; inference skipped.",
                    )
                ],
                alternatives=[],
                overridden=True,
                source="user_override",
            )

        evidence = features.identity_evidence(text, receiver, context)
        rule_dist = features.softmax_distribution(evidence.scores, temperature=1.0)
        learned = self._classifier_distribution(text, receiver, context)
        if learned:
            distribution = {r: 0.55 * learned.get(r, 0.0) + 0.45 * rule_dist.get(r, 0.0) for r in features.REGIONS}
            total = sum(distribution.values()) or 1.0
            distribution = {r: value / total for r, value in distribution.items()}
            source = f"blend:{self.source}"
        else:
            distribution = rule_dist
            source = self.source

        ordered = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
        region, probability = ordered[0]
        second = ordered[1][1] if len(ordered) > 1 else 0.0
        gap = probability - second
        confidence = min(cap, probability)
        label = _confidence_label(confidence, gap)

        top_signals = sorted(evidence.signals, key=lambda signal: signal.weight, reverse=True)[:6]
        if not top_signals:
            top_signals = [
                RegionSignal(
                    kind="fallback",
                    value=self.settings.home_region,
                    weight=0.0,
                    note="No strong identity signal; defaulting to the home region.",
                )
            ]

        alternatives = [
            AlternativeRegion(
                region=alt_region,
                region_name=features.REGION_NAMES.get(alt_region, alt_region),
                probability=round(float(alt_prob), 4),
            )
            for alt_region, alt_prob in ordered[1:4]
        ]

        return RegionHypothesis(
            region=region,
            region_name=features.REGION_NAMES.get(region, region),
            confidence=round(float(confidence), 4),
            confidence_label=label,
            distribution={r: round(float(v), 5) for r, v in distribution.items()},
            evidence=top_signals,
            alternatives=alternatives,
            overridden=False,
            source=source,
        )

"""Task A/B training: synthetic data, FastText baseline vs Transformer, per-region metrics.

The dataset is synthetic, so the reported numbers measure how learnable the synthetic signal is -
not real-world accuracy. See ``docs/FAIRNESS.md``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

from tone_neuron.config import Settings, get_settings
from tone_neuron.ml import features
from tone_neuron.ml.baseline_fasttext import FastTextBaseline
from tone_neuron.ml.dataset import Sample, generate_dataset, save_jsonl, split_dataset, summarize
from tone_neuron.ml.transformer_model import TransformerTrainer, transformer_available


def region_input(sample: Sample) -> str:
    return features.region_feature_text(sample.text, sample.receiver(), None, include_text=False)


def tone_input(sample: Sample) -> str:
    return features.tone_feature_text(sample.text, sample.region)


def evaluate(
    y_true: list[str],
    y_pred: list[str],
    regions: list[str],
    labels: list[str],
    one_vs_rest: bool = False,
) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    per_class = {
        label: {
            "precision": round(float(precision[index]), 4),
            "recall": round(float(recall[index]), 4),
            "f1": round(float(f1[index]), 4),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }
    per_region: dict[str, dict] = {}
    for region in sorted(set(regions)):
        indices = [index for index, value in enumerate(regions) if value == region]
        if not indices:
            continue
        true_slice = [y_true[index] for index in indices]
        pred_slice = [y_pred[index] for index in indices]
        accuracy = round(float(accuracy_score(true_slice, pred_slice)), 4)
        if one_vs_rest:
            binary_true = [1 if value == region else 0 for value in y_true]
            binary_pred = [1 if value == region else 0 for value in y_pred]
            binary_precision, binary_recall, binary_f1, _ = precision_recall_fscore_support(
                binary_true, binary_pred, average="binary", zero_division=0
            )
            per_region[region] = {
                "support": len(indices),
                "accuracy": accuracy,
                "precision": round(float(binary_precision), 4),
                "recall": round(float(binary_recall), 4),
                "f1": round(float(binary_f1), 4),
                "macro_f1": round(float(binary_f1), 4),
            }
        else:
            per_region[region] = {
                "support": len(indices),
                "accuracy": accuracy,
                "macro_f1": round(
                    float(
                        f1_score(
                            true_slice, pred_slice, labels=labels, average="macro", zero_division=0
                        )
                    ),
                    4,
                ),
            }
    return {
        "n": len(y_true),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
        "per_class": per_class,
        "per_region": per_region,
    }


def train_task(
    name: str,
    train_texts: list[str],
    train_labels: list[str],
    test_texts: list[str],
    test_labels: list[str],
    test_regions: list[str],
    settings: Settings,
    seed: int = 7,
    use_transformer: bool = False,
    transformer_model: str = "distilbert-base-uncased",
    hard_mask: list[bool] | None = None,
) -> dict:
    labels = sorted(set(train_labels))
    baseline = FastTextBaseline(seed=seed).fit(train_texts, train_labels)
    baseline_pred = baseline.predict(test_texts)
    baseline_metrics = evaluate(
        test_labels, baseline_pred, test_regions, labels, one_vs_rest=(name == "region")
    )
    hard_metrics = None
    if hard_mask and any(hard_mask):
        hard_indices = [index for index, flagged in enumerate(hard_mask) if flagged]
        hard_metrics = evaluate(
            [test_labels[index] for index in hard_indices],
            [baseline_pred[index] for index in hard_indices],
            [test_regions[index] for index in hard_indices],
            labels,
            one_vs_rest=(name == "region"),
        )
    baseline_meta = baseline.save(settings.model_dir, f"{name}_fasttext")
    candidates = [
        {"name": f"fasttext-{baseline.backend}", "meta": baseline_meta, "metrics": baseline_metrics}
    ]

    transformer_status: dict = {"status": "disabled", "reason": "enable with --transformer"}
    if use_transformer:
        if not transformer_available():
            transformer_status = {
                "status": "skipped",
                "reason": "torch/transformers not installed (pip install torch transformers)",
            }
        else:
            try:
                trainer = TransformerTrainer(model_name=transformer_model, seed=seed)
                trainer.fit(train_texts, train_labels)
                predicted = trainer.predict(test_texts)
                metrics = evaluate(
                    test_labels, predicted, test_regions, labels, one_vs_rest=(name == "region")
                )
                meta = trainer.save(Path(settings.model_dir) / f"{name}_transformer")
                candidates.append(
                    {
                        "name": f"transformer:{transformer_model}",
                        "meta": meta,
                        "metrics": metrics,
                    }
                )
                transformer_status = {
                    "status": "trained",
                    "model": transformer_model,
                    "accuracy": metrics["accuracy"],
                    "macro_f1": metrics["macro_f1"],
                    "per_region": metrics["per_region"],
                }
            except Exception as exc:  # pragma: no cover - depends on optional stack
                transformer_status = {"status": "failed", "reason": str(exc)[:400]}

    best = max(candidates, key=lambda item: (item["metrics"]["macro_f1"], item["metrics"]["accuracy"]))
    best_meta = dict(best["meta"])
    best_meta.update(
        {
            "task": name,
            "selected": best["name"],
            "accuracy": best["metrics"]["accuracy"],
            "macro_f1": best["metrics"]["macro_f1"],
            "per_region": best["metrics"]["per_region"],
            "per_class": best["metrics"]["per_class"],
            "hard_subset": hard_metrics,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "baseline": {
                "backend": baseline.backend,
                "accuracy": baseline_metrics["accuracy"],
                "macro_f1": baseline_metrics["macro_f1"],
            },
            "transformer": transformer_status,
        }
    )
    (Path(settings.model_dir) / f"{name}_best.json").write_text(
        json.dumps(best_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {
        "labels": labels,
        "selected": best["name"],
        "baseline": baseline_metrics,
        "transformer": transformer_status,
        "hard_subset": hard_metrics,
        "best": best["metrics"],
    }


def train_all(
    n: int = 2400,
    seed: int = 7,
    test_ratio: float = 0.25,
    use_transformer: bool = False,
    transformer_model: str = "distilbert-base-uncased",
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    settings.ensure_dirs()

    samples = generate_dataset(n=n, seed=seed)
    train, test = split_dataset(samples, test_ratio=test_ratio, seed=seed + 1)
    save_jsonl(train, Path(settings.dataset_dir) / "train.jsonl")
    save_jsonl(test, Path(settings.dataset_dir) / "test.jsonl")

    # "hard" slice: contradictory or missing identity metadata (diaspora names, generic inboxes)
    hard_mask = [
        sample.receiver_language is None
        or any(
            generic in sample.receiver_email
            for generic in ("gmail.com", "outlook.com", "proton.me", "yahoo.com")
        )
        for sample in test
    ]

    region_task = train_task(
        "region",
        [region_input(sample) for sample in train],
        [sample.region for sample in train],
        [region_input(sample) for sample in test],
        [sample.region for sample in test],
        [sample.region for sample in test],
        settings,
        seed=seed,
        use_transformer=use_transformer,
        transformer_model=transformer_model,
        hard_mask=hard_mask,
    )
    tone_task = train_task(
        "tone",
        [tone_input(sample) for sample in train],
        [sample.tone for sample in train],
        [tone_input(sample) for sample in test],
        [sample.tone for sample in test],
        [sample.region for sample in test],
        settings,
        seed=seed,
        use_transformer=use_transformer,
        transformer_model=transformer_model,
        hard_mask=hard_mask,
    )

    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": summarize(samples),
        "split": {"train": len(train), "test": len(test), "hard_subset": sum(hard_mask)},
        "tasks": {"region": region_task, "tone": tone_task},
        "environment": {
            "fasttext_installed": FastTextBaseline(backend="auto").backend == "fasttext",
            "transformer_available": transformer_available(),
        },
    }
    (Path(settings.model_dir) / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metrics

"""Optional Transformer trainers (DistilBERT / XLM-R) for the baseline comparison.

Requires ``torch`` + ``transformers`` and a model download. When unavailable, training records a
clear "skipped" status instead of failing the run.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def transformer_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except Exception:
        return False


class TransformerTrainer:
    backend = "transformer"

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        epochs: int = 2,
        batch_size: int = 8,
        lr: float = 2e-5,
        max_length: int = 160,
        seed: int = 0,
    ):
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.max_length = max_length
        self.seed = seed
        self.classes_: list[str] = []
        self._model = None
        self._tokenizer = None
        self._device = None

    def fit(self, texts: list[str], labels: list[str]) -> "TransformerTrainer":
        import torch
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        torch.manual_seed(self.seed)
        self.classes_ = sorted({str(label) for label in labels})
        class_index = {label: index for index, label in enumerate(self.classes_)}
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name, num_labels=len(self.classes_)
        )
        tokenizer = self._tokenizer
        max_length = self.max_length

        class _Dataset(Dataset):
            def __init__(self, texts: list[str], labels: list[str]):
                self.texts = list(texts)
                self.labels = list(labels)

            def __len__(self) -> int:
                return len(self.texts)

            def __getitem__(self, index: int) -> dict:
                encoded = tokenizer(
                    self.texts[index],
                    truncation=True,
                    padding="max_length",
                    max_length=max_length,
                    return_tensors="pt",
                )
                item = {key: value.squeeze(0) for key, value in encoded.items()}
                item["labels"] = torch.tensor(class_index[self.labels[index]])
                return item

        loader = DataLoader(_Dataset(texts, labels), batch_size=self.batch_size, shuffle=True)
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        optimizer = torch.optim.AdamW(self._model.parameters(), lr=self.lr)
        self._model.train()
        for _epoch in range(self.epochs):
            for batch in loader:
                batch = {key: value.to(self._device) for key, value in batch.items()}
                loss = self._model(**batch).loss
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
        return self

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        import torch

        if self._model is None or self._tokenizer is None:
            raise RuntimeError("transformer model is not fitted")
        self._model.eval()
        rows: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(texts), self.batch_size * 2):
                chunk = list(texts[start : start + self.batch_size * 2])
                encoded = self._tokenizer(
                    chunk,
                    truncation=True,
                    padding=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                )
                encoded = {key: value.to(self._device) for key, value in encoded.items()}
                logits = self._model(**encoded).logits
                rows.append(torch.softmax(logits, dim=-1).cpu().numpy())
        if not rows:
            return np.zeros((0, len(self.classes_)))
        return np.vstack(rows)

    def predict(self, texts: list[str]) -> list[str]:
        matrix = self.predict_proba(texts)
        return [self.classes_[int(index)] for index in np.argmax(matrix, axis=1)]

    def save(self, directory: str | Path) -> dict:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        assert self._model is not None and self._tokenizer is not None
        self._model.save_pretrained(str(directory))
        self._tokenizer.save_pretrained(str(directory))
        (directory / "tone_neuron_meta.json").write_text(
            json.dumps(
                {
                    "classes": self.classes_,
                    "model_name": self.model_name,
                    "epochs": self.epochs,
                    "batch_size": self.batch_size,
                    "max_length": self.max_length,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return {"backend": "transformer", "path": str(directory), "classes": list(self.classes_)}

    @classmethod
    def load(cls, directory: str | Path) -> "TransformerTrainer":
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        directory = Path(directory)
        meta = json.loads((directory / "tone_neuron_meta.json").read_text(encoding="utf-8"))
        trainer = cls(
            model_name=str(meta.get("model_name", "distilbert-base-uncased")),
            epochs=int(meta.get("epochs", 2)),
            batch_size=int(meta.get("batch_size", 8)),
            max_length=int(meta.get("max_length", 160)),
        )
        trainer.classes_ = list(meta.get("classes", []))
        trainer._tokenizer = AutoTokenizer.from_pretrained(str(directory))
        trainer._model = AutoModelForSequenceClassification.from_pretrained(str(directory))
        import torch

        trainer._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        trainer._model.to(trainer._device)
        trainer._model.eval()
        return trainer

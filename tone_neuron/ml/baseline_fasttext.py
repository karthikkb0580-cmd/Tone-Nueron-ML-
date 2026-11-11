"""Baseline text classifier: real FastText when installed, else a hashed n-gram SGD model.

Both share the same interface (``fit`` / ``predict_proba`` / ``classes_`` / ``save``) so the
training comparison can swap them without special cases.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np


def _clean(text: str) -> str:
    return " ".join(str(text).replace("\n", " ").split())


class SklearnTextModel:
    """Thin wrapper so sklearn estimators expose the same surface as FastText."""

    backend = "hashed-sgd"
    name = "Hashed n-gram SGD"

    def __init__(self, model, classes: list[str]):
        self._model = model
        self.classes_ = list(classes)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        proba = np.asarray(self._model.predict_proba([_clean(t) for t in texts]), dtype=np.float64)
        model_classes = [str(c) for c in getattr(self._model, "classes_", self.classes_)]
        out = np.zeros((len(texts), len(self.classes_)), dtype=np.float64)
        for column, label in enumerate(model_classes):
            if label in self.classes_:
                out[:, self.classes_.index(label)] = proba[:, column]
        row_sums = out.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return out / row_sums

    def predict(self, texts: list[str]) -> list[str]:
        matrix = self.predict_proba(texts)
        return [self.classes_[int(index)] for index in np.argmax(matrix, axis=1)]


class FastTextBaseline:
    """FastText supervised classifier with a deterministic offline fallback."""

    def __init__(
        self,
        backend: str = "auto",
        seed: int = 0,
        epochs: int = 25,
        lr: float = 0.5,
        dim: int = 64,
        ngram: int = 2,
    ):
        self.seed = seed
        self.epochs = epochs
        self.lr = lr
        self.dim = dim
        self.ngram = ngram
        self.classes_: list[str] = []
        self._model = None
        self._fallback: SklearnTextModel | None = None
        self.backend = backend
        self.name = "FastText"
        if backend in ("auto", "fasttext"):
            try:
                import fasttext  # type: ignore

                self._ft = fasttext
                self.backend = "fasttext"
            except Exception:
                self.backend = "hashed-sgd"

    # -- training ----------------------------------------------------------
    def fit(self, texts: list[str], labels: list[str]) -> "FastTextBaseline":
        self.classes_ = sorted({str(label) for label in labels})
        if self.backend == "fasttext":
            self._fit_fasttext(texts, labels)
        else:
            self._fit_fallback(texts, labels)
        return self

    def _fit_fasttext(self, texts: list[str], labels: list[str]) -> None:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        try:
            for text, label in zip(texts, labels):
                handle.write(f"__label__{str(label).upper()} {_clean(text)}\n")
            handle.close()
            kwargs = dict(
                input=handle.name,
                epoch=self.epochs,
                lr=self.lr,
                wordNgrams=self.ngram,
                dim=self.dim,
                minCount=1,
                loss="softmax",
                thread=1,
                verbose=0,
            )
            try:
                self._model = self._ft.train_supervised(seed=self.seed, **kwargs)
            except TypeError:  # older fasttext builds lack `seed`
                self._model = self._ft.train_supervised(**kwargs)
        finally:
            Path(handle.name).unlink(missing_ok=True)

    def _fit_fallback(self, texts: list[str], labels: list[str]) -> None:
        from sklearn.feature_extraction.text import HashingVectorizer
        from sklearn.linear_model import SGDClassifier
        from sklearn.pipeline import Pipeline

        pipeline = Pipeline(
            [
                (
                    "hash",
                    HashingVectorizer(
                        analyzer="char_wb",
                        ngram_range=(2, 5),
                        n_features=2**18,
                        alternate_sign=False,
                        norm=None,
                    ),
                ),
                (
                    "clf",
                    SGDClassifier(
                        loss="log_loss",
                        alpha=1e-6,
                        max_iter=40,
                        tol=1e-4,
                        random_state=self.seed,
                    ),
                ),
            ]
        )
        pipeline.fit([_clean(t) for t in texts], labels)
        self._fallback = SklearnTextModel(pipeline, self.classes_)
        self._model = pipeline

    # -- inference ---------------------------------------------------------
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if self._fallback is not None:
            return self._fallback.predict_proba(texts)
        if self._model is None:
            raise RuntimeError("model is not fitted")
        matrix = np.zeros((len(texts), len(self.classes_)), dtype=np.float64)
        canonical = {label.lower(): label for label in self.classes_}
        for row, text in enumerate(texts):
            labels, probabilities = self._raw_predict(_clean(text), len(self.classes_))
            for label, probability in zip(labels, probabilities):
                name = str(label).replace("__label__", "").strip()
                mapped = canonical.get(name.lower())
                if mapped is not None:
                    matrix[row, self.classes_.index(mapped)] = float(probability)
            total = matrix[row].sum()
            if total > 0:
                matrix[row] /= total
            else:
                matrix[row] = 1.0 / len(self.classes_)
        return matrix

    def _raw_predict(self, text: str, k: int) -> tuple[list[str], list[float]]:
        """Call the C++ predictor directly.

        ``fasttext-wheel``'s Python ``predict`` wraps results in ``np.array(..., copy=False)``,
        which NumPy 2 rejects. The C++ binding returns plain lists of (prob, label), so this is
        equivalent and version-proof.
        """
        if self._model is None:
            return [], []
        predictions = self._model.f.predict(text, k, 0.0, "strict")
        labels: list[str] = []
        probabilities: list[float] = []
        for probability, label in predictions:
            if isinstance(label, bytes):
                label = label.decode("utf-8", errors="replace")
            labels.append(str(label))
            probabilities.append(float(probability))
        return labels, probabilities

    def predict(self, texts: list[str]) -> list[str]:
        matrix = self.predict_proba(texts)
        return [self.classes_[int(index)] for index in np.argmax(matrix, axis=1)]

    # -- persistence -------------------------------------------------------
    def save(self, directory: str | Path, name: str) -> dict:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        if self.backend == "fasttext" and self._model is not None:
            path = directory / f"{name}.fasttext.bin"
            self._model.save_model(str(path))
            return {
                "backend": "fasttext",
                "path": str(path),
                "classes": list(self.classes_),
                "name": name,
            }
        import joblib

        path = directory / f"{name}.joblib"
        joblib.dump({"model": self._model, "classes": list(self.classes_)}, path)
        return {
            "backend": "hashed-sgd",
            "path": str(path),
            "classes": list(self.classes_),
            "name": name,
        }


def load_artifact(meta: dict):
    """Load either a FastText model or a sklearn pipeline from its metadata dict."""
    backend = str(meta.get("backend", ""))
    path = Path(str(meta["path"]))
    classes = list(meta.get("classes", []))
    if not path.exists():
        raise FileNotFoundError(f"model artifact missing: {path}")
    if backend == "transformer":
        from tone_neuron.ml.transformer_model import TransformerTrainer

        return TransformerTrainer.load(path)
    if backend == "fasttext":
        import fasttext  # type: ignore

        model = FastTextBaseline(backend="fasttext")
        model._model = fasttext.load_model(str(path))
        model.classes_ = classes
        return model
    import joblib

    payload = joblib.load(path)
    if isinstance(payload, dict) and "model" in payload:
        return SklearnTextModel(payload["model"], list(payload.get("classes", classes)))
    return payload

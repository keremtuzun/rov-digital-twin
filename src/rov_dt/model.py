from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


def _softmax(values: list[float]) -> list[float]:
    pivot = max(values)
    exps = [math.exp(value - pivot) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


@dataclass
class Prediction:
    label: str
    confidence: float
    probabilities: dict[str, float]


class SoftmaxWeakPointClassifier:
    """Small dependency-free multiclass model suitable for edge demonstrations."""

    def __init__(self, labels: list[str], feature_names: list[str]):
        self.labels = labels
        self.feature_names = feature_names
        self.feature_transform = "raw_plus_absolute_v1"
        width = len(feature_names) * 2
        self.means = [0.0] * width
        self.scales = [1.0] * width
        self.weights = [[0.0] * (width + 1) for _ in labels]

    def _expand(self, row: list[float]) -> list[float]:
        # Magnitudes make symmetric signatures (positive/negative trim, pitch,
        # yaw, and depth errors) learnable by a compact linear edge model.
        return list(row) + [abs(value) for value in row]

    def _normalize(self, row: list[float]) -> list[float]:
        expanded = self._expand(row)
        return [(value - mean) / scale for value, mean, scale in zip(expanded, self.means, self.scales)]

    def fit(
        self,
        rows: list[list[float]],
        targets: list[str],
        epochs: int = 180,
        learning_rate: float = 0.08,
        l2: float = 0.001,
        seed: int = 42,
    ) -> list[float]:
        if not rows or len(rows) != len(targets):
            raise ValueError("rows and targets must be non-empty and aligned")
        expanded_rows = [self._expand(row) for row in rows]
        width = len(expanded_rows[0])
        self.means = [sum(row[j] for row in expanded_rows) / len(expanded_rows) for j in range(width)]
        self.scales = []
        for j, mean in enumerate(self.means):
            variance = sum((row[j] - mean) ** 2 for row in expanded_rows) / max(1, len(expanded_rows) - 1)
            self.scales.append(max(math.sqrt(variance), 1e-8))
        normalized = [self._normalize(row) + [1.0] for row in rows]
        label_index = {label: index for index, label in enumerate(self.labels)}
        rng = random.Random(seed)
        history: list[float] = []
        for epoch in range(epochs):
            order = list(range(len(rows)))
            rng.shuffle(order)
            eta = learning_rate / (1.0 + 0.015 * epoch)
            total_loss = 0.0
            for i in order:
                x = normalized[i]
                expected = label_index[targets[i]]
                probs = _softmax([sum(w * value for w, value in zip(ws, x)) for ws in self.weights])
                total_loss -= math.log(max(probs[expected], 1e-12))
                for class_index, class_weights in enumerate(self.weights):
                    error = probs[class_index] - (1.0 if class_index == expected else 0.0)
                    for j, value in enumerate(x):
                        regularizer = l2 * class_weights[j] if j < width else 0.0
                        class_weights[j] -= eta * (error * value + regularizer)
            history.append(total_loss / len(rows))
        return history

    def predict(self, row: list[float]) -> Prediction:
        x = self._normalize(row) + [1.0]
        probs = _softmax([sum(w * value for w, value in zip(ws, x)) for ws in self.weights])
        probabilities = dict(zip(self.labels, probs))
        label = max(probabilities, key=probabilities.get)
        return Prediction(label, probabilities[label], probabilities)

    def save(self, output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": "softmax_weak_point_classifier",
            "version": 1,
            "labels": self.labels,
            "feature_names": self.feature_names,
            "feature_transform": self.feature_transform,
            "means": self.means,
            "scales": self.scales,
            "weights": self.weights,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, input_path: str | Path) -> "SoftmaxWeakPointClassifier":
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        model = cls(payload["labels"], payload["feature_names"])
        model.feature_transform = payload.get("feature_transform", "raw_plus_absolute_v1")
        model.means = payload["means"]
        model.scales = payload["scales"]
        model.weights = payload["weights"]
        return model

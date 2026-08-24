from __future__ import annotations

import json
import math
import random
import hashlib
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
    raw_label: str | None = None
    uncertainty: float = 0.0
    out_of_distribution: bool = False


class SoftmaxWeakPointClassifier:
    """Small dependency-free multiclass model suitable for edge demonstrations."""

    def __init__(self, labels: list[str], feature_names: list[str]):
        self.labels = labels
        self.feature_names = feature_names
        self.feature_transform = "physics_interactions_v2"
        width = len(self._expand([0.0] * len(feature_names)))
        self.means = [0.0] * width
        self.scales = [1.0] * width
        self.weights = [[0.0] * (width + 1) for _ in labels]
        self.training_statistics: dict[str, list[float] | int] = {}
        self.model_version = "telemetry-softmax-v2"
        self.dataset_version = "unversioned"
        self.calibration_version = "uncalibrated"
        self.temperature = 1.0
        self.model_hash = "unserialized"

    def _expand(self, row: list[float]) -> list[float]:
        # Keep v1 models loadable while giving v2 models physically meaningful
        # nonlinear evidence: magnitude, energy, propulsion efficiency and power.
        if self.feature_transform == "raw_plus_absolute_v1":
            return list(row) + [abs(value) for value in row]
        values = dict(zip(self.feature_names, row))
        command = abs(values.get("thruster_cmd_mean", 0.0))
        speed = abs(values.get("speed_mps", 0.0))
        current = abs(values.get("current_a", 0.0))
        voltage = max(abs(values.get("voltage_v", 0.0)), 1e-3)
        response = values.get("thruster_response_ratio", 1.0)
        interactions = [
            speed / (command + 0.1),
            current / voltage,
            command * max(0.0, 1.0 - response),
            abs(values.get("depth_error_m", 0.0)) * abs(values.get("vertical_speed_mps", 0.0)),
            abs(values.get("roll_deg", 0.0)) + abs(values.get("pitch_deg", 0.0)),
            abs(values.get("imu_depth_disagreement_m", 0.0)) * (1.0 - values.get("dvl_quality", 0.0)),
        ]
        return list(row) + [abs(value) for value in row] + [value * value for value in row] + interactions

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
        self.training_statistics = {
            "raw_feature_means": [sum(row[j] for row in rows) / len(rows) for j in range(len(rows[0]))],
            "raw_feature_scales": [
                max(
                    math.sqrt(
                        sum((row[j] - sum(item[j] for item in rows) / len(rows)) ** 2 for row in rows)
                        / max(1, len(rows) - 1)
                    ),
                    1e-8,
                )
                for j in range(len(rows[0]))
            ],
            "training_rows": len(rows),
        }
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
        logits = [sum(w * value for w, value in zip(ws, x)) for ws in self.weights]
        probs = _softmax([value / self.temperature for value in logits])
        probabilities = dict(zip(self.labels, probs))
        label = max(probabilities, key=probabilities.get)
        return Prediction(label, probabilities[label], probabilities)

    def save(self, output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": "softmax_weak_point_classifier",
            "version": 2,
            "labels": self.labels,
            "feature_names": self.feature_names,
            "feature_transform": self.feature_transform,
            "means": self.means,
            "scales": self.scales,
            "weights": self.weights,
            "training_statistics": self.training_statistics,
            "model_version": self.model_version,
            "dataset_version": self.dataset_version,
            "calibration_version": self.calibration_version,
            "temperature": self.temperature,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.model_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    @classmethod
    def load(cls, input_path: str | Path) -> "SoftmaxWeakPointClassifier":
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        model = cls(payload["labels"], payload["feature_names"])
        model.feature_transform = payload.get("feature_transform", "raw_plus_absolute_v1")
        model.means = payload["means"]
        model.scales = payload["scales"]
        model.weights = payload["weights"]
        model.training_statistics = payload.get("training_statistics", {})
        model.model_version = payload.get("model_version", "telemetry-softmax-v1")
        model.dataset_version = payload.get("dataset_version", "unversioned")
        model.calibration_version = payload.get("calibration_version", "uncalibrated")
        model.temperature = float(payload.get("temperature", 1.0))
        model.model_hash = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
        return model

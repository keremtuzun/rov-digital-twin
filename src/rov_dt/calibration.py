"""Validation-only temperature scaling and calibration metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass


def _normalize(values: list[float]) -> list[float]:
    total = sum(max(value, 0.0) for value in values)
    if total <= 0:
        return [1.0 / len(values)] * len(values)
    return [max(value, 0.0) / total for value in values]


def apply_temperature(probabilities: list[float], temperature: float) -> list[float]:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    logits = [math.log(max(value, 1e-12)) / temperature for value in _normalize(probabilities)]
    pivot = max(logits)
    exponents = [math.exp(value - pivot) for value in logits]
    return [value / sum(exponents) for value in exponents]


def negative_log_likelihood(rows: list[list[float]], targets: list[int]) -> float:
    if not rows or len(rows) != len(targets):
        raise ValueError("probabilities and targets must be non-empty and aligned")
    return -sum(math.log(max(row[target], 1e-12)) for row, target in zip(rows, targets)) / len(rows)


def brier_score(rows: list[list[float]], targets: list[int]) -> float:
    return sum(
        sum((probability - (1.0 if index == target else 0.0)) ** 2 for index, probability in enumerate(row))
        for row, target in zip(rows, targets)
    ) / len(rows)


def calibration_report(
    rows: list[list[float]], targets: list[int], bins: int = 10
) -> dict[str, object]:
    if bins < 2:
        raise ValueError("bins must be at least two")
    buckets = []
    ece = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [
            (row, target)
            for row, target in zip(rows, targets)
            if low <= max(row) <= high and (index == bins - 1 or max(row) < high)
        ]
        confidence = sum(max(row) for row, _ in members) / len(members) if members else 0.0
        accuracy = (
            sum(max(range(len(row)), key=row.__getitem__) == target for row, target in members)
            / len(members)
            if members
            else 0.0
        )
        ece += len(members) / max(1, len(rows)) * abs(confidence - accuracy)
        buckets.append(
            {"lower": low, "upper": high, "count": len(members), "confidence": confidence, "accuracy": accuracy}
        )
    return {
        "ece": ece,
        "brier_score": brier_score(rows, targets),
        "nll": negative_log_likelihood(rows, targets),
        "reliability_diagram": buckets,
    }


@dataclass(frozen=True)
class TemperatureScaler:
    temperature: float = 1.0

    @classmethod
    def fit(cls, validation_probabilities: list[list[float]], validation_targets: list[int]) -> "TemperatureScaler":
        """Fit only on validation probabilities using deterministic log-grid search."""
        candidates = [math.exp(math.log(0.2) + index / 200 * math.log(25.0)) for index in range(201)]
        best = min(
            candidates,
            key=lambda value: negative_log_likelihood(
                [apply_temperature(row, value) for row in validation_probabilities], validation_targets
            ),
        )
        return cls(best)

    def transform(self, rows: list[list[float]]) -> list[list[float]]:
        return [apply_temperature(row, self.temperature) for row in rows]

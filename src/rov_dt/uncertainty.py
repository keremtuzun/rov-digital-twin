"""Dependency-free uncertainty and out-of-distribution scoring."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

UNKNOWN_LABEL = "unknown_or_out_of_distribution"


@dataclass(frozen=True)
class TrainingDistribution:
    means: tuple[float, ...]
    scales: tuple[float, ...]
    feature_names: tuple[str, ...] = ()

    @classmethod
    def fit(
        cls, rows: Iterable[Iterable[float]], feature_names: Iterable[str] = ()
    ) -> "TrainingDistribution":
        values = [tuple(float(value) for value in row) for row in rows]
        if not values or not values[0]:
            raise ValueError("training rows must be non-empty")
        if any(len(row) != len(values[0]) for row in values):
            raise ValueError("training rows must have equal width")
        means = tuple(sum(row[index] for row in values) / len(values) for index in range(len(values[0])))
        scales = tuple(
            max(
                math.sqrt(
                    sum((row[index] - means[index]) ** 2 for row in values)
                    / max(1, len(values) - 1)
                ),
                1e-8,
            )
            for index in range(len(means))
        )
        return cls(means, scales, tuple(feature_names))

    def score(self, row: Iterable[float], mask: Iterable[bool] | None = None) -> float:
        values = tuple(float(value) for value in row)
        if len(values) != len(self.means):
            raise ValueError("row width differs from training distribution")
        valid = tuple(mask) if mask is not None else (True,) * len(values)
        if len(valid) != len(values):
            raise ValueError("mask width differs from row")
        distances = [
            abs(value - mean) / scale
            for value, mean, scale, is_valid in zip(values, self.means, self.scales, valid)
            if is_valid and math.isfinite(value)
        ]
        if not distances:
            return math.inf
        # RMS z-distance is interpretable while less brittle than maximum z-score.
        return math.sqrt(sum(value * value for value in distances) / len(distances))


def softmax_entropy(probabilities: Iterable[float], *, normalized: bool = True) -> float:
    values = [max(0.0, float(value)) for value in probabilities]
    total = sum(values)
    if total <= 0:
        return 1.0 if normalized else 0.0
    values = [value / total for value in values]
    entropy = -sum(value * math.log(max(value, 1e-12)) for value in values)
    return entropy / math.log(len(values)) if normalized and len(values) > 1 else entropy


def ensemble_disagreement(probability_rows: Iterable[Iterable[float]]) -> float:
    rows = [tuple(float(value) for value in row) for row in probability_rows]
    if not rows:
        return 1.0
    if any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("ensemble probability rows must have equal width")
    means = [sum(row[index] for row in rows) / len(rows) for index in range(len(rows[0]))]
    return sum(
        sum((row[index] - means[index]) ** 2 for row in rows) / len(rows)
        for index in range(len(means))
    ) / len(means)


@dataclass(frozen=True)
class UncertaintyAssessment:
    label: str
    raw_label: str
    maximum_probability: float
    entropy: float
    ood_score: float
    ensemble_disagreement: float
    uncertain: bool
    reasons: tuple[str, ...]


def assess_uncertainty(
    probabilities: dict[str, float],
    *,
    ood_score: float = 0.0,
    disagreement: float = 0.0,
    maximum_probability_threshold: float = 0.55,
    entropy_threshold: float = 0.72,
    ood_threshold: float = 4.0,
    disagreement_threshold: float = 0.02,
) -> UncertaintyAssessment:
    if not probabilities:
        raise ValueError("probabilities cannot be empty")
    raw_label = max(probabilities, key=probabilities.get)
    maximum = float(probabilities[raw_label])
    entropy = softmax_entropy(probabilities.values())
    reasons = []
    if maximum < maximum_probability_threshold:
        reasons.append("low_maximum_probability")
    if entropy > entropy_threshold:
        reasons.append("high_entropy")
    if ood_score > ood_threshold:
        reasons.append("outside_training_distribution")
    if disagreement > disagreement_threshold:
        reasons.append("ensemble_disagreement")
    uncertain = bool(reasons)
    return UncertaintyAssessment(
        label=UNKNOWN_LABEL if uncertain else raw_label,
        raw_label=raw_label,
        maximum_probability=maximum,
        entropy=entropy,
        ood_score=ood_score,
        ensemble_disagreement=disagreement,
        uncertain=uncertain,
        reasons=tuple(reasons),
    )

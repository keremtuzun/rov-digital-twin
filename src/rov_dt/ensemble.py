"""Seed-diverse model ensemble inference with explicit disagreement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .uncertainty import UncertaintyAssessment, assess_uncertainty, ensemble_disagreement


class ProbabilityModel(Protocol):
    def predict(self, row: list[float]): ...


@dataclass(frozen=True)
class EnsemblePrediction:
    probabilities: dict[str, float]
    probability_variance: dict[str, float]
    uncertainty: UncertaintyAssessment


class TelemetryEnsemble:
    def __init__(self, models: list[ProbabilityModel]):
        if len(models) < 2:
            raise ValueError("an ensemble requires at least two models")
        self.models = models

    def predict(self, row: list[float], *, ood_score: float = 0.0) -> EnsemblePrediction:
        predictions = [model.predict(row) for model in self.models]
        labels = tuple(predictions[0].probabilities)
        if any(tuple(prediction.probabilities) != labels for prediction in predictions):
            raise ValueError("ensemble models must expose the same ordered labels")
        vectors = [[prediction.probabilities[label] for label in labels] for prediction in predictions]
        means = {
            label: sum(vector[index] for vector in vectors) / len(vectors)
            for index, label in enumerate(labels)
        }
        variances = {
            label: sum((vector[index] - means[label]) ** 2 for vector in vectors) / len(vectors)
            for index, label in enumerate(labels)
        }
        disagreement = ensemble_disagreement(vectors)
        uncertainty = assess_uncertainty(
            means, ood_score=ood_score, disagreement=disagreement
        )
        return EnsemblePrediction(means, variances, uncertainty)

"""Causal mask-aware telemetry-window classifier.

The implementation uses deterministic temporal pooling (mean, standard deviation, slope and rate of
change) followed by the existing multiclass softmax MLP baseline. This dependency-light architecture is
suited to edge deployment and provides a reproducible baseline before adopting a GRU/1D CNN.
"""

from __future__ import annotations

import math
import json
from dataclasses import dataclass
from typing import Iterable
from pathlib import Path

from .model import SoftmaxWeakPointClassifier
from .uncertainty import TrainingDistribution, UncertaintyAssessment, assess_uncertainty

TEMPORAL_LABELS = (
    "nominal",
    "thruster_degradation",
    "buoyancy_imbalance",
    "sensor_drift",
    "hydrodynamic_drag",
)


@dataclass(frozen=True)
class TemporalPoint:
    timestamp_s: float
    mission_id: str
    values: tuple[float, ...]
    mask: tuple[bool, ...]
    label: str = "nominal"


@dataclass(frozen=True)
class TemporalPrediction:
    label: str
    probabilities: dict[str, float]
    uncertainty: UncertaintyAssessment


class CausalTemporalFeatures:
    def __init__(self, feature_names: Iterable[str], window_seconds: float = 5.0, sampling_hz: float = 10.0):
        if window_seconds <= 0 or sampling_hz <= 0:
            raise ValueError("window_seconds and sampling_hz must be positive")
        self.feature_names = tuple(feature_names)
        self.window_seconds = float(window_seconds)
        self.sampling_hz = float(sampling_hz)
        self.minimum_points = max(2, round(window_seconds * sampling_hz * 0.5))
        suffixes = ("mean", "std", "slope", "rate", "missing_fraction")
        interactions = (
            "command_to_velocity_response",
            "current_to_thrust_response",
            "expected_measured_acceleration_residual",
            "persistent_depth_bias",
            "dvl_imu_disagreement",
            "pressure_fused_depth_disagreement",
            "thruster_response_lag_proxy",
        )
        self.output_names = (
            tuple(f"{name}_{suffix}" for name in self.feature_names for suffix in suffixes)
            + interactions
        )

    def windows(self, points: Iterable[TemporalPoint]) -> list[list[TemporalPoint]]:
        """Return past-only windows ending at each eligible point, grouped by mission."""
        by_mission: dict[str, list[TemporalPoint]] = {}
        for point in points:
            if len(point.values) != len(self.feature_names) or len(point.mask) != len(point.values):
                raise ValueError("point width/mask differs from configured features")
            by_mission.setdefault(point.mission_id, []).append(point)
        output = []
        for mission_points in by_mission.values():
            ordered = sorted(mission_points, key=lambda point: point.timestamp_s)
            for end_index, end in enumerate(ordered):
                start_time = end.timestamp_s - self.window_seconds
                window = [point for point in ordered[: end_index + 1] if point.timestamp_s >= start_time]
                if len(window) >= self.minimum_points:
                    output.append(window)
        return output

    def transform(self, window: list[TemporalPoint]) -> list[float]:
        if len(window) < 2:
            raise ValueError("temporal feature extraction requires at least two points")
        ordered = sorted(window, key=lambda point: point.timestamp_s)
        output: list[float] = []
        summary_means: dict[str, float] = {}
        summary_rates: dict[str, float] = {}
        for index in range(len(self.feature_names)):
            valid = [point for point in ordered if point.mask[index] and math.isfinite(point.values[index])]
            missing_fraction = 1.0 - len(valid) / len(ordered)
            if not valid:
                output.extend((0.0, 0.0, 0.0, 0.0, 1.0))
                summary_means[self.feature_names[index]] = 0.0
                summary_rates[self.feature_names[index]] = 0.0
                continue
            values = [point.values[index] for point in valid]
            mean = sum(values) / len(values)
            std = math.sqrt(sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1))
            duration = valid[-1].timestamp_s - valid[0].timestamp_s
            slope = (values[-1] - values[0]) / duration if duration > 0 else 0.0
            rates = [
                (right.values[index] - left.values[index]) / (right.timestamp_s - left.timestamp_s)
                for left, right in zip(valid, valid[1:])
                if right.timestamp_s > left.timestamp_s
            ]
            rate = sum(abs(value) for value in rates) / len(rates) if rates else 0.0
            output.extend((mean, std, slope, rate, missing_fraction))
            summary_means[self.feature_names[index]] = mean
            summary_rates[self.feature_names[index]] = rate
        command = abs(summary_means.get("thruster_cmd_mean", 0.0))
        speed = abs(summary_means.get("speed_mps", 0.0))
        current = abs(summary_means.get("current_a", 0.0))
        response = summary_means.get("thruster_response_ratio", 0.0)
        output.extend(
            (
                speed / (command + 0.1),
                response / (current + 0.1),
                summary_means.get("observed_acceleration_mps2", 0.0)
                - summary_means.get("expected_acceleration_mps2", 0.0),
                summary_means.get("depth_error_m", 0.0),
                summary_means.get("dvl_speed_mps", 0.0)
                - summary_means.get("imu_integrated_speed_mps", 0.0),
                summary_means.get("pressure_depth_m", 0.0)
                - summary_means.get("depth_m", 0.0),
                summary_rates.get("thruster_cmd_mean", 0.0)
                - summary_rates.get("thruster_response_ratio", 0.0),
            )
        )
        return output


class TemporalFaultModel:
    """Mask-aware causal temporal classifier with explicit OOD rejection."""

    def __init__(self, feature_names: Iterable[str], window_seconds: float = 5.0, sampling_hz: float = 10.0):
        self.extractor = CausalTemporalFeatures(feature_names, window_seconds, sampling_hz)
        self.classifier = SoftmaxWeakPointClassifier(list(TEMPORAL_LABELS), list(self.extractor.output_names))
        self.distribution: TrainingDistribution | None = None

    def fit(self, points: Iterable[TemporalPoint], *, epochs: int = 120, seed: int = 42) -> list[float]:
        windows = self.extractor.windows(points)
        if not windows:
            raise ValueError("no eligible causal windows")
        rows = [self.extractor.transform(window) for window in windows]
        targets = [window[-1].label for window in windows]
        if any(target not in TEMPORAL_LABELS for target in targets):
            raise ValueError("unknown is an inference outcome and cannot be a fitted fault label")
        self.distribution = TrainingDistribution.fit(rows, self.extractor.output_names)
        return self.classifier.fit(rows, targets, epochs=epochs, seed=seed)

    def predict(self, window: list[TemporalPoint]) -> TemporalPrediction:
        row = self.extractor.transform(window)
        prediction = self.classifier.predict(row)
        ood_score = self.distribution.score(row) if self.distribution is not None else math.inf
        uncertainty = assess_uncertainty(prediction.probabilities, ood_score=ood_score)
        return TemporalPrediction(uncertainty.label, prediction.probabilities, uncertainty)

    def save(self, output: str | Path) -> Path:
        if self.distribution is None:
            raise ValueError("fit the temporal model before saving")
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": "causal_temporal_pooling_softmax",
            "model_version": "temporal-v1",
            "feature_names": self.extractor.feature_names,
            "window_seconds": self.extractor.window_seconds,
            "sampling_hz": self.extractor.sampling_hz,
            "labels": self.classifier.labels,
            "means": self.classifier.means,
            "scales": self.classifier.scales,
            "weights": self.classifier.weights,
            "distribution": {
                "means": self.distribution.means,
                "scales": self.distribution.scales,
                "feature_names": self.distribution.feature_names,
            },
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, input_path: str | Path) -> "TemporalFaultModel":
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        model = cls(payload["feature_names"], payload["window_seconds"], payload["sampling_hz"])
        model.classifier.labels = list(payload["labels"])
        model.classifier.means = list(payload["means"])
        model.classifier.scales = list(payload["scales"])
        model.classifier.weights = [list(row) for row in payload["weights"]]
        distribution = payload["distribution"]
        model.distribution = TrainingDistribution(
            tuple(distribution["means"]), tuple(distribution["scales"]),
            tuple(distribution["feature_names"])
        )
        return model

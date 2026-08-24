from dataclasses import dataclass

import pytest

from oceansense.vision_uncertainty import vision_uncertainty
from rov_dt.ensemble import TelemetryEnsemble
from rov_dt.reliability import reliability_report
from rov_dt.runtime_monitor import (
    DeploymentMode,
    RuntimeVersions,
    build_runtime_event,
)


@dataclass(frozen=True)
class _Prediction:
    probabilities: dict[str, float]


class _FixedModel:
    def __init__(self, probabilities: dict[str, float]):
        self.probabilities = probabilities

    def predict(self, _row: list[float]) -> _Prediction:
        return _Prediction(self.probabilities)


def test_ensemble_exposes_disagreement_and_rejects_ambiguous_mean():
    ensemble = TelemetryEnsemble(
        [
            _FixedModel({"nominal": 0.9, "fault": 0.1}),
            _FixedModel({"nominal": 0.1, "fault": 0.9}),
        ]
    )
    prediction = ensemble.predict([1.0])
    assert prediction.probability_variance["nominal"] > 0.1
    assert prediction.uncertainty.label == "unknown_or_out_of_distribution"


def test_shadow_event_can_never_affect_vehicle_behavior():
    versions = RuntimeVersions("m1", "sha256:x", "d1", "c1", "f1", "sim1", "rov1")
    event = build_runtime_event(DeploymentMode.SHADOW, {}, {}, versions)
    assert event.affects_vehicle_behavior is False
    with pytest.raises(PermissionError):
        build_runtime_event(DeploymentMode.AUTONOMOUS_HIGH_LEVEL, {}, {}, versions)


def test_low_quality_or_ambiguous_vision_becomes_unknown():
    assert vision_uncertainty([0.99, 0.01], quality=0.1)["unknown"] is True
    assert vision_uncertainty([0.51, 0.49], quality=1.0)["unknown"] is True


def test_reliability_report_keeps_conditions_separate():
    report = reliability_report(
        [
            {
                "condition": "simulation", "actual": "nominal", "predicted": "nominal",
                "confidence": 0.9, "probabilities": {"nominal": 0.9, "unknown": 0.1},
                "ood_truth": False, "ood_score": 0.1,
            },
            {
                "condition": "field", "actual": "thruster_degradation", "predicted": "unknown",
                "confidence": 0.4, "probabilities": {"thruster_degradation": 0.4, "unknown": 0.6},
                "ood_truth": True, "ood_score": 4.0,
            },
        ]
    )
    assert set(report["by_condition"]) == {"field", "simulation"}
    assert "accuracy" not in report
    assert report["by_condition"]["field"]["safety"]["missed_critical_event_count"] == 1
    assert "false_positive_rate" in report["by_condition"]["field"]["per_class"]["unknown"]
    assert report["by_condition"]["simulation"]["uncertainty"]["brier_score"] is not None

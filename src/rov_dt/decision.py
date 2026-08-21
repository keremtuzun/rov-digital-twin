from __future__ import annotations

from dataclasses import asdict, dataclass

from .advisor import DomainAdvisor
from .model import SoftmaxWeakPointClassifier
from .schema import TelemetrySample


@dataclass(frozen=True)
class Decision:
    weak_point: str
    confidence: float
    risk_level: str
    action: str
    autonomous_execution_allowed: bool
    evidence: list[str]
    recommended_checks: list[str]
    probabilities: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


class SafetyDecisionAgent:
    def __init__(self, model: SoftmaxWeakPointClassifier, confidence_gate: float = 0.72):
        self.model = model
        self.confidence_gate = confidence_gate
        self.advisor = DomainAdvisor()

    def decide(self, sample: TelemetrySample) -> Decision:
        prediction = self.model.predict(sample.features())
        advisory = self.advisor.advise(prediction.label, sample)
        critical = (
            abs(sample.depth_error_m) > 2.0
            or abs(sample.pitch_deg) > 18.0
            or sample.voltage_v < 42.0
            or sample.temperature_c > 58.0
        )
        action_map = {
            "nominal": "continue_mission",
            "thruster_degradation": "degraded_mode_and_operator_review",
            "buoyancy_imbalance": "hold_depth_and_operator_review",
            "sensor_drift": "sensor_cross_check_and_operator_review",
            "hydrodynamic_drag": "reduce_speed_and_operator_review",
        }
        risk = "critical" if critical else ("high" if prediction.label != "nominal" else "low")
        action = "abort_and_surface" if critical else action_map[prediction.label]
        allowed = prediction.label == "nominal" and prediction.confidence >= self.confidence_gate and not critical
        if prediction.confidence < self.confidence_gate and not critical:
            risk = "uncertain"
            action = "hold_position_and_request_operator_review"
            allowed = False
        return Decision(
            weak_point=prediction.label,
            confidence=prediction.confidence,
            risk_level=risk,
            action=action,
            autonomous_execution_allowed=allowed,
            evidence=advisory.evidence,
            recommended_checks=advisory.recommended_checks,
            probabilities=prediction.probabilities,
        )

from __future__ import annotations

from dataclasses import asdict, dataclass

from .advisor import DomainAdvisor
from .data_quality import FieldQuality
from .health_monitor import HealthAssessment
from .model import SoftmaxWeakPointClassifier
from .schema import TelemetrySample
from .uncertainty import TrainingDistribution, assess_uncertainty


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
    uncertainty_reasons: tuple[str, ...] = ()
    model_version: str = "unknown"
    dataset_version: str = "unknown"
    calibration_version: str = "unknown"
    model_hash: str = "unknown"
    feature_transform_version: str = "unknown"
    simulator_profile: str = "unknown"
    vehicle_profile: str = "unknown"

    def to_dict(self) -> dict:
        return asdict(self)


class SafetyDecisionAgent:
    def __init__(self, model: SoftmaxWeakPointClassifier, confidence_gate: float = 0.72):
        self.model = model
        self.confidence_gate = confidence_gate
        self.advisor = DomainAdvisor()

    def decide(
        self,
        sample: TelemetrySample,
        *,
        field_quality: dict[str, FieldQuality] | None = None,
        health: HealthAssessment | None = None,
        communications_stable: bool = True,
    ) -> Decision:
        prediction = self.model.predict(sample.features())
        statistics = self.model.training_statistics
        ood_score = 0.0
        if statistics.get("raw_feature_means") and statistics.get("raw_feature_scales"):
            distribution = TrainingDistribution(
                tuple(statistics["raw_feature_means"]), tuple(statistics["raw_feature_scales"])
            )
            ood_score = distribution.score(sample.features())
        uncertainty = assess_uncertainty(
            prediction.probabilities,
            ood_score=ood_score,
            maximum_probability_threshold=self.confidence_gate,
        )
        effective_label = uncertainty.label
        advisory_label = uncertainty.raw_label
        advisory = self.advisor.advise(advisory_label, sample)
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
            "unknown_or_out_of_distribution": "hold_position_and_request_operator_review",
        }
        unusable_fields = [name for name, quality in (field_quality or {}).items() if not quality.usable]
        failure_first = bool(unusable_fields) or not communications_stable or (
            health is not None and health.status in {"uncertain", "critical"}
        )
        risk = "critical" if critical else ("high" if effective_label != "nominal" else "low")
        action = "abort_and_surface" if critical else action_map[effective_label]
        allowed = effective_label == "nominal" and not critical and not failure_first
        if uncertainty.uncertain and not critical:
            risk = "uncertain"
            action = "hold_position_and_request_operator_review"
            allowed = False
        if failure_first and not critical:
            risk = "critical" if health is not None and health.status == "critical" else "uncertain"
            action = (
                "abort_and_surface"
                if health is not None and health.status == "critical"
                else "hold_position_and_request_operator_review"
            )
            allowed = False
        reasons = list(uncertainty.reasons)
        reasons.extend(f"unusable_field:{name}" for name in unusable_fields)
        if not communications_stable:
            reasons.append("communications_instability")
        if health is not None and health.status != "healthy":
            reasons.extend(health.reasons)
        return Decision(
            weak_point=effective_label,
            confidence=prediction.confidence,
            risk_level=risk,
            action=action,
            autonomous_execution_allowed=allowed,
            evidence=advisory.evidence,
            recommended_checks=advisory.recommended_checks,
            probabilities=prediction.probabilities,
            uncertainty_reasons=tuple(dict.fromkeys(reasons)),
            model_version=self.model.model_version,
            dataset_version=self.model.dataset_version,
            calibration_version=self.model.calibration_version,
            model_hash=self.model.model_hash,
            feature_transform_version=self.model.feature_transform,
            simulator_profile="runtime_supplied",
            vehicle_profile="runtime_supplied",
        )

"""Evidence-only mission decision interface from the Conrad execution guide."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .navigation_contracts import DECISIONS, InspectionTarget, RobotPose


FORBIDDEN_AUTHORITY_KEYS = {"pwm", "motor_voltage", "motor_torque", "thruster_force", "servo_command"}


def _reject_raw_authority(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.lower().replace("individual_", "")
            if normalized in FORBIDDEN_AUTHORITY_KEYS:
                raise ValueError(f"raw actuator authority is prohibited: {key}")
            _reject_raw_authority(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_raw_authority(nested)


@dataclass(frozen=True)
class MissionDecisionInput:
    mission_id: str
    frame_id: str
    robot_pose: RobotPose
    inspection_target: InspectionTarget
    model1_outputs: list[dict[str, Any]]
    model2_outputs: list[dict[str, Any]]
    uncertainty: dict[str, float | bool]
    environment: dict[str, Any]
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.mission_id.strip() or not self.frame_id.strip():
            raise ValueError("mission_id and frame_id are required")
        _reject_raw_authority(asdict(self))


@dataclass(frozen=True)
class MissionDecisionOutput:
    decision: str
    reason: str
    recommended_next_action: str
    confidence: float
    evidence_refs: list[str]
    limitations: str

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError(f"unsupported decision: {self.decision}")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        _reject_raw_authority(asdict(self))


def decide_mission(request: MissionDecisionInput) -> MissionDecisionOutput:
    """Choose a high-level inspection recommendation without low-level control authority."""
    evidence = []
    for output in request.model1_outputs + request.model2_outputs:
        evidence.extend(str(item) for item in output.get("evidence_refs", []))
        if output.get("frame_id"):
            evidence.append(str(output["frame_id"]))
    confidence_values = [
        float(output["confidence"])
        for output in request.model1_outputs + request.model2_outputs
        if output.get("confidence") is not None
    ]
    confidence = min(confidence_values) if confidence_values else 0.0
    entropy = float(request.uncertainty.get("entropy", 0.0))
    unknown = bool(request.uncertainty.get("unknown", False))
    visibility = str(request.environment.get("visibility", "unknown"))
    angle = abs(float(request.inspection_target.current_viewpoint.get("angle_deg", 0.0)))

    if unknown or entropy > 0.75 or not request.model1_outputs:
        decision, reason, action = (
            "flag_unknown", "Evidence is missing or outside the accepted uncertainty envelope.",
            "Pause inspection progression and request operator review.",
        )
    elif visibility in {"poor", "very_poor"} or angle > 60:
        decision, reason, action = (
            "change_viewpoint", "Current visibility or viewpoint cannot support a reliable claim.",
            "Request a safer alternate inspection viewpoint and capture additional frames.",
        )
    elif any(bool(output.get("unknown")) for output in request.model2_outputs):
        decision, reason, action = (
            "request_reinspection", "Temporal/structural evidence is not yet stable.",
            "Reinspect the same target from at least one distinct viewpoint.",
        )
    elif any(float(output.get("risk_score", 0.0)) >= 0.75 for output in request.model2_outputs):
        decision, reason, action = (
            "escalate", "Persistent structural evidence exceeds the research escalation threshold.",
            "Escalate evidence to a qualified human inspector; do not infer confirmed damage.",
        )
    elif confidence >= 0.60:
        decision, reason, action = (
            "accept_detection", "Available model evidence is mutually usable at the configured threshold.",
            "Record the visual indicator and continue the approved inspection plan.",
        )
    else:
        decision, reason, action = (
            "request_reinspection", "Evidence confidence is below the acceptance threshold.",
            "Capture more evidence before making a technical claim.",
        )
    return MissionDecisionOutput(
        decision=decision,
        reason=reason,
        recommended_next_action=action,
        confidence=max(0.0, min(1.0, confidence)),
        evidence_refs=sorted(set(evidence)),
        limitations="Recommendation only; no confirmed defect diagnosis or actuator authority.",
    )

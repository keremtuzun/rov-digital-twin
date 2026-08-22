from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DOMAIN_LABELS = {
    "structure",
    "nature_ecology",
    "contamination",
    "fishing_aquaculture",
    "general_underwater",
    "unknown",
}
CONDITION_LABELS = {
    "ok",
    "normal_surface",  # v1 compatibility
    "biofouling",
    "marine_debris",
    "poor_visibility",
    "low_visibility",  # v1 compatibility
    "possible_damage",
    "possible_weak_point",
    "ecological_stress",
    "fish_or_habitat_activity",
    "structure_ok",
    "possible_crack",
    "possible_corrosion",
    "crack",
    "corrosion",
    "biofouling_on_structure",
    "heavy_biofouling_on_structure",
    "surface_degradation",
    "possible_structural_weak_point",
    "obstruction_or_debris_on_structure",
    "unknown_structure_condition",
    "healthy_coral",
    "bleached_coral",
    "coral_bleaching",
    "damaged_coral",
    "possible_coral_stress",
    "bleaching_like_pattern",
    "algae_overgrowth",
    "healthy_seafloor",
    "degraded_habitat",
    "marine_life_present",
    "low_biodiversity_visible",
    "unknown_ecological_condition",
    "plastic_waste",
    "net_or_rope_debris",
    "oil_like_sheen",
    "high_turbidity",
    "suspicious_discoloration",
    "algae_bloom_indicator",
    "normal_water_condition",
    "unknown_contamination_status",
    "fish_present",
    "fish_school_present",
    "fish_school",
    "low_fish_activity",
    "low_activity",
    "vegetation_present",
    "suitable_habitat_indicator",
    "clear_visibility",
    "net_damage",
    "cage_damage",
    "debris_near_aquaculture",
    "poor_visibility_for_survey",
    "unknown_field_condition",
    "unknown",
}
ALLOWED_LABELS = CONDITION_LABELS
VISIBILITY_LEVELS = {"clear", "good", "moderate", "poor", "unknown"}
ANOMALY_LEVELS = {"low", "medium", "high"}
ALLOWED_ACTIONS = {
    "continue_survey",
    "inspect_closer",
    "hold_position",
    "request_human_review",
    "mark_location",
    "capture_more_data",
    "avoid_area",
    "return_to_base",
    "surface_or_recover",
    "send_alert",
}


def _probability(value: float, name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


@dataclass(frozen=True)
class BoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    def __post_init__(self) -> None:
        if min(self.x_min, self.y_min) < 0 or self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("bbox coordinates must be non-negative and have positive area")


@dataclass(frozen=True)
class Classification:
    label: str
    confidence: float
    top_k: list[dict[str, float | str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.label not in CONDITION_LABELS:
            raise ValueError(f"unsupported label: {self.label}")
        object.__setattr__(self, "confidence", _probability(self.confidence, "confidence"))
        for item in self.top_k:
            if item.get("label") not in CONDITION_LABELS:
                raise ValueError("top_k contains an unsupported label")
            _probability(float(item.get("confidence", -1)), "top_k confidence")


@dataclass(frozen=True)
class InspectionDomain:
    label: str
    confidence: float

    def __post_init__(self) -> None:
        if self.label not in DOMAIN_LABELS:
            raise ValueError(f"unsupported inspection domain: {self.label}")
        object.__setattr__(self, "confidence", _probability(self.confidence, "domain confidence"))


@dataclass(frozen=True)
class Anomaly:
    score: float
    level: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "score", _probability(self.score, "anomaly score"))
        if self.level not in ANOMALY_LEVELS:
            raise ValueError(f"unsupported anomaly level: {self.level}")


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: BoundingBox

    def __post_init__(self) -> None:
        if self.label not in {
            "possible_weak_point", "debris_object", "biofouling_region", "possible_damage_region",
            "coral_stress_region", "turbidity_region", "net_damage_region", "fish_group",
        }:
            raise ValueError(f"unsupported detection label: {self.label}")
        object.__setattr__(self, "confidence", _probability(self.confidence, "detection confidence"))


@dataclass(frozen=True)
class MissionContext:
    visibility_level: str = "unknown"
    depth_m: float | None = None
    battery_level: float | None = None
    communication_status: str = "stable"
    operator_mode: str = "semi_autonomous"
    survey_goal: str = "unknown"

    def __post_init__(self) -> None:
        if self.visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"unsupported visibility level: {self.visibility_level}")
        if self.battery_level is not None:
            object.__setattr__(self, "battery_level", _probability(self.battery_level, "battery level"))
        if self.depth_m is not None and self.depth_m < 0:
            raise ValueError("depth_m cannot be negative")
        if self.communication_status not in {"stable", "unstable", "lost", "unknown"}:
            raise ValueError("unsupported communication status")
        if self.operator_mode not in {"manual", "assisted", "semi_autonomous", "unknown"}:
            raise ValueError("unsupported operator mode")
        if self.survey_goal not in DOMAIN_LABELS:
            raise ValueError("unsupported survey goal")


@dataclass(frozen=True)
class ConditionAssessment:
    status: str
    risk_level: str
    score: float
    summary: str
    field_assessment: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ok", "needs_review", "unsafe_to_conclude", "unknown"}:
            raise ValueError("unsupported condition status")
        if self.risk_level not in ANOMALY_LEVELS:
            raise ValueError("unsupported risk level")
        object.__setattr__(self, "score", _probability(self.score, "condition score"))


@dataclass(frozen=True)
class PerceptionResult:
    frame_id: str
    classification: Classification
    anomaly: Anomaly
    detections: list[Detection] = field(default_factory=list)
    model_version: str = "perception_v1"
    inspection_domain: InspectionDomain = field(default_factory=lambda: InspectionDomain("unknown", 0.0))
    condition_assessment: ConditionAssessment | None = None

    def __post_init__(self) -> None:
        if not self.frame_id.strip():
            raise ValueError("frame_id is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionResult:
    decision_id: str
    frame_id: str
    recommended_action: str
    priority: str
    requires_human_review: bool
    reasoning_summary: str
    dashboard_message: str
    control_instruction: dict[str, Any]
    confidence: str
    safety_flags: list[str]
    explanation: dict[str, Any]
    domain: str = "unknown"

    def __post_init__(self) -> None:
        if self.recommended_action not in ALLOWED_ACTIONS:
            raise ValueError(f"forbidden or unknown action: {self.recommended_action}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

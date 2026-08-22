from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_LABELS = {
    "normal_surface",
    "biofouling",
    "marine_debris",
    "low_visibility",
    "possible_damage",
    "possible_weak_point",
    "unknown",
}
VISIBILITY_LEVELS = {"good", "moderate", "poor", "unknown"}
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

    def __post_init__(self) -> None:
        if self.label not in ALLOWED_LABELS:
            raise ValueError(f"unsupported label: {self.label}")
        object.__setattr__(self, "confidence", _probability(self.confidence, "confidence"))


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
        if self.label not in {"possible_weak_point", "debris_object", "biofouling_region", "possible_damage_region"}:
            raise ValueError(f"unsupported detection label: {self.label}")
        object.__setattr__(self, "confidence", _probability(self.confidence, "detection confidence"))


@dataclass(frozen=True)
class MissionContext:
    visibility_level: str = "unknown"
    depth_m: float | None = None
    battery_level: float | None = None
    communication_status: str = "stable"

    def __post_init__(self) -> None:
        if self.visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"unsupported visibility level: {self.visibility_level}")
        if self.battery_level is not None:
            object.__setattr__(self, "battery_level", _probability(self.battery_level, "battery level"))
        if self.depth_m is not None and self.depth_m < 0:
            raise ValueError("depth_m cannot be negative")
        if self.communication_status not in {"stable", "unstable", "lost", "unknown"}:
            raise ValueError("unsupported communication status")


@dataclass(frozen=True)
class PerceptionResult:
    frame_id: str
    classification: Classification
    anomaly: Anomaly
    detections: list[Detection] = field(default_factory=list)
    model_version: str = "perception_v1"

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

    def __post_init__(self) -> None:
        if self.recommended_action not in ALLOWED_ACTIONS:
            raise ValueError(f"forbidden or unknown action: {self.recommended_action}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

"""Replayable contracts between the navigation and inspection software tracks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


TARGET_TYPES = {"pipe", "weld", "joint", "hull", "cable", "support", "concrete", "unknown"}
MISSION_EVENTS = {
    "waypoint_reached", "target_found", "inspection_started", "frame_captured", "anomaly_flagged",
    "reinspection_requested", "inspection_completed",
}
DECISIONS = {"accept_detection", "request_reinspection", "change_viewpoint", "flag_unknown", "escalate"}


def _nonempty(value: str, name: str) -> None:
    if not str(value).strip():
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class RobotPose:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


@dataclass(frozen=True)
class RobotState:
    timestamp: float
    mission_id: str
    pose: RobotPose
    linear_velocity: tuple[float, float, float]
    angular_velocity: tuple[float, float, float]
    depth: float
    heading: float
    simulated_battery: float
    mission_status: str
    run_id: str = "unversioned"

    def __post_init__(self) -> None:
        _nonempty(self.mission_id, "mission_id")
        _nonempty(self.mission_status, "mission_status")
        if self.timestamp < 0 or self.depth < 0:
            raise ValueError("timestamp and depth cannot be negative")
        if not 0 <= self.simulated_battery <= 1:
            raise ValueError("simulated_battery must be between 0 and 1")


@dataclass(frozen=True)
class SensorFrame:
    frame_id: str
    mission_id: str
    timestamp: float
    frame_reference: str
    camera_intrinsics: dict[str, float] | None
    visibility_metadata: dict[str, Any]
    turbidity_estimate: float | None
    robot_pose_at_capture: RobotPose
    lighting_condition: str = "unknown"
    target_id: str | None = None
    scenario_id: str | None = None
    run_id: str = "unversioned"

    def __post_init__(self) -> None:
        for value, name in ((self.frame_id, "frame_id"), (self.mission_id, "mission_id"),
                            (self.frame_reference, "frame_reference")):
            _nonempty(value, name)
        if self.timestamp < 0:
            raise ValueError("timestamp cannot be negative")
        if self.turbidity_estimate is not None and not 0 <= self.turbidity_estimate <= 1:
            raise ValueError("turbidity_estimate must be between 0 and 1")


@dataclass(frozen=True)
class InspectionTarget:
    target_id: str
    type: str
    expected_geometry: dict[str, Any]
    current_viewpoint: dict[str, float]
    distance_to_target: float
    inspection_status: str
    mission_id: str = "unversioned"
    location: dict[str, float] = field(default_factory=dict)
    scenario_id: str | None = None
    run_id: str = "unversioned"

    def __post_init__(self) -> None:
        _nonempty(self.target_id, "target_id")
        if self.type not in TARGET_TYPES:
            raise ValueError(f"unsupported target type: {self.type}")
        if self.distance_to_target < 0:
            raise ValueError("distance_to_target cannot be negative")


@dataclass(frozen=True)
class MissionEvent:
    event_id: str
    mission_id: str
    timestamp: float
    event_type: str
    related_frame_id: str | None = None
    related_target_id: str | None = None
    robot_state: RobotState | None = None
    sensor_frame: SensorFrame | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    scenario_id: str | None = None
    run_id: str = "unversioned"

    def __post_init__(self) -> None:
        _nonempty(self.event_id, "event_id")
        _nonempty(self.mission_id, "mission_id")
        if self.event_type not in MISSION_EVENTS:
            raise ValueError(f"unsupported event_type: {self.event_type}")
        if self.timestamp < 0:
            raise ValueError("timestamp cannot be negative")
        if self.sensor_frame and self.sensor_frame.mission_id != self.mission_id:
            raise ValueError("sensor frame mission_id does not match event mission_id")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionFeedback:
    decision_id: str
    mission_id: str
    related_frame_id: str
    decision: str
    accepted_by_navigation: bool
    resulting_action: str
    related_target_id: str | None = None
    scenario_id: str | None = None
    run_id: str = "unversioned"

    def __post_init__(self) -> None:
        for value, name in ((self.decision_id, "decision_id"), (self.mission_id, "mission_id"),
                            (self.related_frame_id, "related_frame_id"),
                            (self.resulting_action, "resulting_action")):
            _nonempty(value, name)
        if self.decision not in DECISIONS:
            raise ValueError(f"unsupported decision: {self.decision}")


def mission_event_from_mapping(payload: dict[str, Any]) -> MissionEvent:
    """Reconstruct a typed mission event from a saved JSON-compatible mapping."""
    source = dict(payload)
    robot_state = source.get("robot_state")
    if robot_state:
        robot_state = dict(robot_state)
        robot_state["pose"] = RobotPose(**robot_state["pose"])
        robot_state["linear_velocity"] = tuple(robot_state["linear_velocity"])
        robot_state["angular_velocity"] = tuple(robot_state["angular_velocity"])
        source["robot_state"] = RobotState(**robot_state)
    sensor_frame = source.get("sensor_frame")
    if sensor_frame:
        sensor_frame = dict(sensor_frame)
        sensor_frame["robot_pose_at_capture"] = RobotPose(**sensor_frame["robot_pose_at_capture"])
        source["sensor_frame"] = SensorFrame(**sensor_frame)
    return MissionEvent(**source)


def write_mission_events(events: list[MissionEvent], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events),
                      encoding="utf-8")
    return output


def _write_records(records: list[Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(asdict(record), sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return output


def write_navigation_bundle(
    output_dir: str | Path,
    *,
    states: list[RobotState],
    frames: list[SensorFrame],
    targets: list[InspectionTarget],
    events: list[MissionEvent],
    feedback: list[DecisionFeedback] | None = None,
) -> dict[str, Path]:
    """Write separate replay logs so consumers do not need Unity or nested event payloads."""
    output = Path(output_dir)
    paths = {
        "robot_states": _write_records(states, output / "robot_states.jsonl"),
        "sensor_frames": _write_records(frames, output / "sensor_frames.jsonl"),
        "inspection_targets": _write_records(targets, output / "inspection_targets.jsonl"),
        "mission_events": write_mission_events(events, output / "mission_events.jsonl"),
    }
    if feedback is not None:
        paths["decision_feedback"] = _write_records(
            feedback, output / "decision_feedback.jsonl"
        )
    return paths


def read_mission_events(path: str | Path) -> list[MissionEvent]:
    events = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                events.append(mission_event_from_mapping(json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid mission event at line {line_number}: {exc}") from exc
    return events

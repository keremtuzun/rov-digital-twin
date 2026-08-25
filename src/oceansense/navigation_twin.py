"""Deterministic navigation-twin replay model and export bundle.

Unity remains the high-fidelity simulator. This dependency-light model provides a
replayable contract test and headless integration path; it does not replace Unity
physics or establish calibrated vehicle behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any

from .navigation_contracts import (
    InspectionTarget,
    MissionEvent,
    RobotPose,
    RobotState,
    SensorFrame,
)


@dataclass(frozen=True)
class NavigationMissionConfig:
    mission_id: str
    run_id: str
    target_id: str
    target_type: str
    duration_s: float
    timestep_s: float
    commanded_speed_mps: float
    start_xyz: tuple[float, float, float]
    target_xyz: tuple[float, float, float]
    current_xyz_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    battery_start: float = 1.0
    battery_drain_per_s: float = 0.0005
    visibility_condition: str = "moderate"
    turbidity_value: float = 0.3
    lighting_condition: str = "artificial_light"
    capture_distance_m: float = 1.2
    scenario_id: str | None = None
    frame_reference: str = "unassigned"
    camera_intrinsics: dict[str, float] | None = None
    expected_geometry: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("mission_id", "run_id", "target_id", "target_type"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.duration_s <= 0 or self.timestep_s <= 0 or self.commanded_speed_mps <= 0:
            raise ValueError("duration, timestep, and commanded speed must be positive")
        if self.timestep_s > self.duration_s:
            raise ValueError("timestep_s cannot exceed duration_s")
        if not 0 <= self.battery_start <= 1 or self.battery_drain_per_s < 0:
            raise ValueError("battery configuration is invalid")
        if not 0 <= self.turbidity_value <= 1 or self.capture_distance_m <= 0:
            raise ValueError("sensor condition configuration is invalid")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> NavigationMissionConfig:
        source = dict(payload)
        for field_name in ("start_xyz", "target_xyz", "current_xyz_mps"):
            if field_name in source:
                source[field_name] = tuple(float(value) for value in source[field_name])
        return cls(**source)


@dataclass(frozen=True)
class NavigationRun:
    states: list[RobotState]
    frames: list[SensorFrame]
    targets: list[InspectionTarget]
    events: list[MissionEvent]
    metrics: dict[str, float | int | bool]


def _distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def simulate_navigation(config: NavigationMissionConfig) -> NavigationRun:
    """Run a seeded-free deterministic kinematic mission with configured current disturbance."""
    position = config.start_xyz
    states: list[RobotState] = []
    events: list[MissionEvent] = []
    steps = int(config.duration_s / config.timestep_s) + 1
    reached = False
    frame: SensorFrame | None = None
    target = InspectionTarget(
        target_id=config.target_id,
        type=config.target_type,
        expected_geometry=config.expected_geometry,
        current_viewpoint={"angle_deg": 0.0},
        distance_to_target=_distance(position, config.target_xyz),
        inspection_status="planned",
        mission_id=config.mission_id,
        location={"x": config.target_xyz[0], "y": config.target_xyz[1], "z": config.target_xyz[2]},
        scenario_id=config.scenario_id,
        run_id=config.run_id,
    )
    events.append(MissionEvent(
        "event-target-found", config.mission_id, 0.0, "target_found",
        related_target_id=config.target_id, scenario_id=config.scenario_id, run_id=config.run_id,
        notes="Target supplied by mission configuration.",
    ))
    distance_travelled = 0.0
    for index in range(steps):
        timestamp = min(config.duration_s, index * config.timestep_s)
        delta = tuple(target_value - value for value, target_value in zip(position, config.target_xyz))
        remaining = _distance(position, config.target_xyz)
        if remaining > config.capture_distance_m:
            direction = tuple(value / remaining for value in delta)
            commanded = tuple(value * config.commanded_speed_mps for value in direction)
            velocity = tuple(command + current for command, current in
                             zip(commanded, config.current_xyz_mps))
        else:
            velocity = (0.0, 0.0, 0.0)
            reached = True
        heading = math.degrees(math.atan2(velocity[0], velocity[2])) if any(velocity) else 0.0
        pose = RobotPose(position[0], position[1], position[2], 0.0, 0.0, heading)
        status = "inspection" if reached else "en_route"
        states.append(RobotState(
            timestamp, config.mission_id, pose, velocity, (0.0, 0.0, 0.0),
            max(0.0, -position[1]), heading,
            max(0.0, config.battery_start - config.battery_drain_per_s * timestamp),
            status, config.run_id,
        ))
        if reached:
            frame = SensorFrame(
                frame_id=f"{config.mission_id}-frame-001",
                mission_id=config.mission_id,
                timestamp=timestamp,
                frame_reference=config.frame_reference,
                camera_intrinsics=config.camera_intrinsics,
                visibility_metadata={"condition": config.visibility_condition},
                turbidity_estimate=config.turbidity_value,
                robot_pose_at_capture=pose,
                lighting_condition=config.lighting_condition,
                target_id=config.target_id,
                scenario_id=config.scenario_id,
                run_id=config.run_id,
            )
            events.extend([
                MissionEvent(
                    "event-inspection-started", config.mission_id, timestamp,
                    "inspection_started", related_target_id=config.target_id,
                    scenario_id=config.scenario_id, run_id=config.run_id,
                ),
                MissionEvent(
                    "event-frame-captured", config.mission_id, timestamp,
                    "frame_captured", related_frame_id=frame.frame_id,
                    related_target_id=config.target_id, sensor_frame=frame,
                    scenario_id=config.scenario_id, run_id=config.run_id,
                ),
            ])
            break
        next_position = tuple(
            value + speed * config.timestep_s for value, speed in zip(position, velocity)
        )
        distance_travelled += _distance(position, next_position)
        position = next_position
    final_distance = _distance(position, config.target_xyz)
    if frame is not None:
        target = replace(
            target,
            current_viewpoint={"angle_deg": 0.0, "heading_deg": frame.robot_pose_at_capture.yaw},
            distance_to_target=final_distance,
            inspection_status="frame_captured",
        )
    return NavigationRun(
        states=states,
        frames=[frame] if frame else [],
        targets=[target],
        events=events,
        metrics={
            "reached_capture_distance": reached,
            "state_count": len(states),
            "frame_count": int(frame is not None),
            "distance_travelled_m": round(distance_travelled, 6),
            "final_distance_to_target_m": round(final_distance, 6),
            "minimum_battery": round(min(state.simulated_battery for state in states), 6),
        },
    )

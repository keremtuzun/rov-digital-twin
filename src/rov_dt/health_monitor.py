"""Deterministic cross-sensor health checks independent of learned models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HealthAssessment:
    status: str
    reasons: tuple[str, ...]
    recommended_action: str


def assess_health(values: Mapping[str, float | bool | None]) -> HealthAssessment:
    reasons: list[str] = []
    critical = False
    uncertain = False
    dvl_speed = values.get("dvl_speed_mps")
    imu_speed = values.get("imu_integrated_speed_mps")
    if dvl_speed is not None and imu_speed is not None and abs(float(dvl_speed) - float(imu_speed)) > 1.0:
        reasons.append("dvl_imu_velocity_inconsistency")
    depth_rate = values.get("pressure_depth_rate_mps")
    vertical_acceleration = values.get("vertical_acceleration_mps2")
    if depth_rate is not None and vertical_acceleration is not None:
        if abs(float(depth_rate)) > 1.0 and abs(float(vertical_acceleration)) < 0.08:
            reasons.append("pressure_imu_depth_inconsistency")
    command = values.get("thruster_cmd_mean")
    speed_change = values.get("speed_change_mps")
    current = values.get("current_a")
    if command is not None and speed_change is not None and current is not None:
        if float(command) > 0.65 and float(speed_change) < 0.05 and float(current) > 25.0:
            reasons.append("possible_propulsion_degradation")
    if values.get("communications_outage"):
        reasons.append("communications_outage")
        critical = True
    if values.get("stale_critical_sensor"):
        reasons.append("stale_critical_sensor")
        uncertain = True
    if values.get("leak_detected") or values.get("battery_critical"):
        reasons.append("critical_vehicle_interlock")
        critical = True
    if critical:
        return HealthAssessment("critical", tuple(reasons), "surface_or_recover")
    if uncertain:
        return HealthAssessment("uncertain", tuple(reasons), "request_human_review")
    if reasons:
        return HealthAssessment("degraded", tuple(reasons), "hold_position")
    return HealthAssessment("healthy", (), "continue_survey")

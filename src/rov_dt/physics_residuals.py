"""Physically interpretable derived residuals with validity and provenance."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PhysicsResidual:
    name: str
    value: float | None
    normalized_value: float | None
    valid: bool
    sensor_sources: tuple[str, ...]
    provenance: str = "derived"


def _residual(
    name: str,
    observed: float | None,
    expected: float | None,
    scale: float,
    sources: tuple[str, ...],
) -> PhysicsResidual:
    valid = (
        observed is not None
        and expected is not None
        and math.isfinite(observed)
        and math.isfinite(expected)
        and scale > 0
    )
    value = observed - expected if valid else None
    return PhysicsResidual(name, value, value / scale if value is not None else None, valid, sources)


def compute_physics_residuals(values: Mapping[str, float | None]) -> dict[str, PhysicsResidual]:
    """Compute residuals without substituting absent measurements."""
    command = values.get("thruster_cmd_mean")
    expected_acceleration = (
        command * values.get("thruster_acceleration_gain_mps2", 1.0)
        if command is not None
        else None
    )
    expected_velocity = (
        command * values.get("command_velocity_gain_mps", 1.2)
        if command is not None
        else None
    )
    expected_response = values.get("expected_thruster_response", 1.0) if command is not None else None
    pressure = values.get("pressure_kpa")
    water_density = values.get("water_density_kg_m3") or 1025.0
    pressure_depth = (
        max(0.0, (pressure - 101.325) * 1000.0 / (water_density * 9.80665))
        if pressure is not None
        else None
    )
    expected_current = (
        abs(command) * values.get("current_per_command_a", 35.0)
        if command is not None
        else None
    )
    return {
        "acceleration": _residual(
            "observed_minus_predicted_acceleration",
            values.get("observed_acceleration_mps2"),
            expected_acceleration,
            0.5,
            ("imu", "thruster_command", "vehicle_profile"),
        ),
        "velocity": _residual(
            "observed_minus_command_expected_velocity",
            values.get("speed_mps"),
            expected_velocity,
            0.5,
            ("dvl", "thruster_command", "vehicle_profile"),
        ),
        "thrust_response": _residual(
            "expected_minus_observed_thrust_response",
            expected_response,
            values.get("thruster_response_ratio"),
            0.2,
            ("thruster_command", "estimated_thruster_response"),
        ),
        "pressure_depth": _residual(
            "pressure_depth_minus_fused_depth",
            pressure_depth,
            values.get("depth_m"),
            0.25,
            ("pressure", "depth_fusion", "water_density"),
        ),
        "dvl_imu_velocity": _residual(
            "dvl_minus_imu_integrated_velocity",
            values.get("dvl_speed_mps"),
            values.get("imu_integrated_speed_mps"),
            0.3,
            ("dvl", "imu"),
        ),
        "electrical_load": _residual(
            "measured_minus_expected_current",
            values.get("current_a"),
            expected_current,
            5.0,
            ("power_sensor", "thruster_command", "vehicle_profile"),
        ),
    }

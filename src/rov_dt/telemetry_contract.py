"""Canonical Unity/ROS/Python telemetry validation and explicit legacy adaptation."""

from __future__ import annotations

import json
import math
from typing import Any

from .schema import FEATURE_NAMES, TelemetrySample

SCHEMA_VERSION = "1.0.0"
CANONICAL_DUTIES = {"station_keeping", "pipeline_tracking", "target_waypoint"}
ALLOWED_HIGH_LEVEL_INTENTS = {
    "continue_survey", "inspect_closer", "hold_position", "request_human_review", "mark_location",
    "capture_more_data", "avoid_area", "return_to_base", "surface_or_recover", "send_alert",
}
UNITY_DUTY_ALIASES = {
    "StationKeeping": "station_keeping",
    "PipelineTracking": "pipeline_tracking",
    "TargetWaypoint": "target_waypoint",
}
REQUIRED_FIELDS = (
    "schema_version", "timestamp_s", "mission_id", "duty", *FEATURE_NAMES,
)


class TelemetryContractError(ValueError):
    """Raised with an operator-readable reason when telemetry violates the contract."""


def _finite_number(payload: dict[str, Any], name: str) -> float:
    if name not in payload:
        raise TelemetryContractError(f"missing required telemetry field: {name}")
    value = payload[name]
    if isinstance(value, bool):
        raise TelemetryContractError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TelemetryContractError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise TelemetryContractError(f"{name} must be finite")
    return number


def validate_telemetry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TelemetryContractError("telemetry payload must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise TelemetryContractError(f"missing required telemetry fields: {', '.join(missing)}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise TelemetryContractError(f"unsupported schema_version: {payload['schema_version']!r}")
    mission_id = str(payload["mission_id"]).strip()
    if not mission_id:
        raise TelemetryContractError("mission_id cannot be empty")
    duty = UNITY_DUTY_ALIASES.get(str(payload["duty"]), str(payload["duty"]))
    if duty not in CANONICAL_DUTIES:
        raise TelemetryContractError(f"unsupported duty: {payload['duty']!r}")
    normalized = dict(payload)
    normalized["mission_id"] = mission_id
    normalized["duty"] = duty
    for name in ("timestamp_s", *FEATURE_NAMES):
        normalized[name] = _finite_number(payload, name)
    bounds = {
        "timestamp_s": (0, None), "depth_m": (0, None), "speed_mps": (0, None),
        "current_a": (0, None), "voltage_v": (0, None), "thruster_cmd_mean": (0, 1),
        "thruster_response_ratio": (0, 1.5), "imu_depth_disagreement_m": (0, None),
        "dvl_quality": (0, 1), "temperature_c": (-5, 120),
    }
    for name, (low, high) in bounds.items():
        value = normalized[name]
        if value < low or (high is not None and value > high):
            raise TelemetryContractError(f"{name} outside allowed range [{low}, {high}]: {value}")
    return normalized


def telemetry_sample_from_payload(payload: dict[str, Any]) -> TelemetrySample:
    normalized = validate_telemetry_payload(payload)
    fields = {name: normalized[name] for name in TelemetrySample.__dataclass_fields__ if name in normalized}
    return TelemetrySample(**fields)


def telemetry_envelope_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate model fields while retaining research provenance and pose extensions."""
    normalized = validate_telemetry_payload(payload)
    envelope = dict(payload)
    envelope.update(normalized)
    field_status = envelope.get("field_status", {})
    if not isinstance(field_status, dict):
        raise TelemetryContractError("field_status must be an object")
    allowed_status = {"simulated", "measured", "derived", "unavailable"}
    if any(status not in allowed_status for status in field_status.values()):
        raise TelemetryContractError("field_status contains an unsupported provenance value")
    for vector_name in ("position_m", "velocity_mps"):
        if vector_name in envelope:
            vector = envelope[vector_name]
            if not isinstance(vector, list) or len(vector) != 3:
                raise TelemetryContractError(f"{vector_name} must contain three numbers")
            envelope[vector_name] = [float(value) for value in vector]
    if "battery_level" in envelope:
        battery = float(envelope["battery_level"])
        if not 0 <= battery <= 1:
            raise TelemetryContractError("battery_level must be between 0 and 1")
        envelope["battery_level"] = battery
    return envelope


def telemetry_sample_from_json(raw: str | bytes) -> TelemetrySample:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TelemetryContractError(f"invalid telemetry JSON: {exc}") from exc
    return telemetry_sample_from_payload(payload)


def telemetry_envelope_from_json(raw: str | bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TelemetryContractError(f"invalid telemetry JSON: {exc}") from exc
    return telemetry_envelope_from_payload(payload)


def validate_high_level_intent(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TelemetryContractError(f"invalid command JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("intent") not in ALLOWED_HIGH_LEVEL_INTENTS:
        raise TelemetryContractError("command requires an allowlisted high-level intent")
    actuator_tokens = ("thruster", "motor", "pwm", "force", "voltage")
    forbidden = {key for key in payload if any(token in key.lower() for token in actuator_tokens)}
    if forbidden:
        raise TelemetryContractError(f"raw actuator fields are forbidden: {sorted(forbidden)}")
    return payload

"""Disabled-by-default diagnostic decision to simulation intent mapping."""

from __future__ import annotations

from typing import Any

from .telemetry_contract import TelemetryContractError, validate_high_level_intent

ACTION_TO_INTENT = {
    "continue_mission": "continue_survey",
    "degraded_mode_and_operator_review": "request_human_review",
    "hold_depth_and_operator_review": "hold_position",
    "sensor_cross_check_and_operator_review": "request_human_review",
    "reduce_speed_and_operator_review": "hold_position",
    "abort_and_surface": "surface_or_recover",
    "hold_position_and_request_operator_review": "hold_position",
}


def _contains_raw_actuator_field(value: Any) -> bool:
    forbidden_tokens = ("thruster", "motor", "pwm", "force", "voltage")
    if isinstance(value, dict):
        return any(
            any(token in str(key).lower() for token in forbidden_tokens)
            or _contains_raw_actuator_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_raw_actuator_field(item) for item in value)
    return False


def decision_to_simulation_intent(
    decision: dict[str, Any], *, enabled: bool = False, simulation_only: bool = True
) -> dict[str, str] | None:
    if not enabled:
        return None
    if not simulation_only:
        raise PermissionError("diagnostic intent gateway is restricted to simulation_only=true")
    if _contains_raw_actuator_field(decision):
        raise TelemetryContractError("diagnostic decision contains forbidden raw actuator fields")
    action = str(decision.get("action", ""))
    if action not in ACTION_TO_INTENT:
        raise TelemetryContractError(f"unsupported diagnostic action: {action!r}")
    output = {"intent": ACTION_TO_INTENT[action], "source": "diagnostic_simulation_gateway"}
    validate_high_level_intent(__import__("json").dumps(output))
    return output

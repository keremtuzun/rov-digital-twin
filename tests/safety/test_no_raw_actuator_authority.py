import json

import pytest

from rov_dt.intent_gateway import decision_to_simulation_intent
from rov_dt.runtime_monitor import DeploymentMode, authorize_mode


@pytest.mark.parametrize("field", ["pwm", "motor_voltage", "individual_motor_torque", "thruster_force"])
def test_diagnostic_path_rejects_raw_actuator_fields(field):
    decision = {"action": "continue_mission", "nested": {field: 1.0}}
    with pytest.raises(ValueError, match="raw actuator"):
        decision_to_simulation_intent(decision, enabled=True)


def test_shadow_is_default_safe_and_autonomous_requires_explicit_gate():
    assert authorize_mode(DeploymentMode.SHADOW) is False
    with pytest.raises(PermissionError):
        authorize_mode(DeploymentMode.AUTONOMOUS_HIGH_LEVEL)
    assert authorize_mode(
        DeploymentMode.AUTONOMOUS_HIGH_LEVEL, autonomous_high_level_enabled=True
    )
    assert "thruster" not in json.dumps({"intent": "hold_position"})

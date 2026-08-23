import json
import unittest
import tempfile
from pathlib import Path

from rov_dt.telemetry_contract import (
    TelemetryContractError,
    telemetry_sample_from_json,
    telemetry_sample_from_payload,
    validate_high_level_intent,
    telemetry_envelope_from_json,
)
from rov_dt.intent_gateway import decision_to_simulation_intent
from rov_dt.ros_support import resolve_model_path


ROOT = Path(__file__).resolve().parents[1]


class TelemetryContractTests(unittest.TestCase):
    def test_unity_payload_converts_to_typed_sample(self):
        raw = (ROOT / "data/telemetry_unity_sample.json").read_text(encoding="utf-8")
        sample = telemetry_sample_from_json(raw)
        self.assertEqual(sample.schema_version, "1.0.0")
        self.assertEqual(sample.duty, "pipeline_tracking")
        self.assertAlmostEqual(sample.depth_m, 7.25)
        self.assertEqual(len(sample.features()), 14)

    def test_envelope_retains_research_provenance_and_legacy_sample_still_works(self):
        raw = (ROOT / "data/telemetry_unity_sample.json").read_text(encoding="utf-8")
        envelope = telemetry_envelope_from_json(raw)
        self.assertEqual(envelope["field_status"]["current_a"], "simulated")
        self.assertEqual(len(envelope["position_m"]), 3)
        self.assertEqual(len(envelope["velocity_mps"]), 3)
        self.assertAlmostEqual(envelope["battery_level"], 0.84)
        self.assertEqual(telemetry_sample_from_json(raw).mission_id, envelope["mission_id"])

    def test_unity_enum_alias_is_deterministic(self):
        payload = json.loads((ROOT / "data/telemetry_unity_sample.json").read_text(encoding="utf-8"))
        payload["duty"] = "StationKeeping"
        self.assertEqual(telemetry_sample_from_payload(payload).duty, "station_keeping")

    def test_missing_field_has_explanatory_error(self):
        payload = json.loads((ROOT / "data/telemetry_unity_sample.json").read_text(encoding="utf-8"))
        del payload["voltage_v"]
        with self.assertRaisesRegex(TelemetryContractError, "voltage_v"):
            telemetry_sample_from_payload(payload)

    def test_invalid_json_is_rejected_without_process_exit(self):
        with self.assertRaisesRegex(TelemetryContractError, "invalid telemetry JSON"):
            telemetry_sample_from_json("{not-json")

    def test_ros_command_contract_forbids_raw_actuator_data(self):
        self.assertEqual(validate_high_level_intent('{"intent":"hold_position"}')["intent"], "hold_position")
        with self.assertRaisesRegex(TelemetryContractError, "raw actuator"):
            validate_high_level_intent('{"intent":"hold_position","thruster":0.8}')
        with self.assertRaisesRegex(TelemetryContractError, "allowlisted"):
            validate_high_level_intent('{"intent":"spin_propeller"}')

    def test_diagnostic_gateway_is_disabled_and_simulation_only(self):
        decision = {"action": "hold_depth_and_operator_review"}
        self.assertIsNone(decision_to_simulation_intent(decision))
        self.assertEqual(
            decision_to_simulation_intent(decision, enabled=True, simulation_only=True)["intent"],
            "hold_position",
        )
        with self.assertRaises(PermissionError):
            decision_to_simulation_intent(decision, enabled=True, simulation_only=False)
        with self.assertRaisesRegex(ValueError, "raw actuator"):
            decision_to_simulation_intent(
                {"action": "continue_mission", "thruster_pwm": 0.5}, enabled=True
            )
        with self.assertRaisesRegex(ValueError, "raw actuator"):
            decision_to_simulation_intent(
                {"action": "continue_mission", "control": {"motor_force": 0.2}}, enabled=True
            )

    def test_model_path_must_be_explicit_and_exist(self):
        with self.assertRaisesRegex(FileNotFoundError, "No diagnostic model configured"):
            resolve_model_path("", {})
        with self.assertRaisesRegex(FileNotFoundError, "does not exist"):
            resolve_model_path("missing-model.json", {})
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / "model.json"
            model.write_text("{}", encoding="utf-8")
            self.assertEqual(resolve_model_path(str(model), {"ROV_DT_MODEL_PATH": "ignored"}), model.resolve())


if __name__ == "__main__":
    unittest.main()

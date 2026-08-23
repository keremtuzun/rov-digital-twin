import json
import unittest
from pathlib import Path

from rov_dt.telemetry_contract import (
    TelemetryContractError,
    telemetry_sample_from_json,
    telemetry_sample_from_payload,
    validate_high_level_intent,
)


ROOT = Path(__file__).resolve().parents[1]


class TelemetryContractTests(unittest.TestCase):
    def test_unity_payload_converts_to_typed_sample(self):
        raw = (ROOT / "data/telemetry_unity_sample.json").read_text(encoding="utf-8")
        sample = telemetry_sample_from_json(raw)
        self.assertEqual(sample.schema_version, "1.0.0")
        self.assertEqual(sample.duty, "pipeline_tracking")
        self.assertAlmostEqual(sample.depth_m, 7.25)
        self.assertEqual(len(sample.features()), 14)

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


if __name__ == "__main__":
    unittest.main()

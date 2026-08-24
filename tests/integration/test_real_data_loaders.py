import csv
import json

import pytest

from rov_dt.real_data import RealDataError, load_csv, load_jsonl


def _record():
    return {
        "timestamp_s": 0.0,
        "mission_id": "m1",
        "vehicle_id": "rov1",
        "environment_id": "lake1",
        "data_source": "lake",
        "dvl_velocity_mps": [0.1, 0.0, 0.2],
        "sensor_provenance": {"dvl_velocity_mps": "dvl:serial-1"},
        "calibration_version": "cal-1",
    }


def test_jsonl_and_csv_loaders_align(tmp_path):
    record = _record()
    jsonl = tmp_path / "mission.jsonl"
    jsonl.write_text(json.dumps(record) + "\n", encoding="utf-8")
    csv_path = tmp_path / "mission.csv"
    csv_record = dict(record)
    csv_record["dvl_velocity_mps"] = json.dumps(csv_record["dvl_velocity_mps"])
    csv_record["sensor_provenance"] = json.dumps(csv_record["sensor_provenance"])
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_record)
        writer.writeheader()
        writer.writerow(csv_record)
    assert load_jsonl(jsonl)[0].measurements == load_csv(csv_path)[0].measurements


def test_present_measurement_requires_provenance():
    record = _record()
    record["sensor_provenance"] = {}
    with pytest.raises(RealDataError, match="provenance"):
        from rov_dt.real_data import record_from_mapping

        record_from_mapping(record)


def test_nested_canonical_record_round_trips(tmp_path):
    from dataclasses import asdict
    from rov_dt.real_data import record_from_mapping

    first = record_from_mapping(_record())
    path = tmp_path / "canonical.jsonl"
    path.write_text(json.dumps(asdict(first)) + "\n", encoding="utf-8")
    second = load_jsonl(path)[0]
    assert second == first

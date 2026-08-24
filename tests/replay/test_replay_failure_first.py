from rov_dt.model import SoftmaxWeakPointClassifier
from rov_dt.real_data import record_from_mapping
from scripts.replay_mission import replay


def test_incomplete_real_record_replays_as_review_not_nominal():
    record = record_from_mapping(
        {
            "timestamp_s": 1.0,
            "mission_id": "m1",
            "vehicle_id": "rov1",
            "environment_id": "sea1",
            "data_source": "open_sea",
            "depth_m": 8.0,
            "sensor_provenance": {"depth_m": "pressure:1"},
            "calibration_version": "cal-1",
        }
    )
    model = SoftmaxWeakPointClassifier(["nominal", "sensor_drift"], ["depth_m"])
    timeline = replay([record], model)
    assert timeline[0]["prediction"] == "unknown_or_out_of_distribution"
    assert timeline[0]["recommended_action"] == "request_human_review"
    assert timeline[0]["missing_features"]

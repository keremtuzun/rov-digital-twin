import math

from rov_dt.calibration import TemperatureScaler, calibration_report
from rov_dt.data_quality import assess_field_quality
from rov_dt.health_monitor import assess_health
from rov_dt.physics_residuals import compute_physics_residuals
from rov_dt.real_data import record_from_mapping
from rov_dt.temporal_model import CausalTemporalFeatures, TemporalPoint
from rov_dt.uncertainty import UNKNOWN_LABEL, TrainingDistribution, assess_uncertainty


def test_real_record_preserves_missing_mask_and_provenance():
    record = record_from_mapping(
        {
            "timestamp_s": 1.0,
            "mission_id": "mission-1",
            "vehicle_id": "rov-1",
            "environment_id": "pool-a",
            "data_source": "pool",
            "depth_m": 4.2,
            "sensor_provenance": {"depth_m": "pressure_sensor:serial-7"},
            "calibration_version": "depth-cal-3",
        }
    )
    assert record.measurements["depth_m"] == 4.2
    assert record.measurements["salinity_psu"] is None
    assert record.measurement_mask["depth_m"] is True
    assert record.measurement_mask["salinity_psu"] is False


def test_physics_residuals_never_claim_missing_value_is_valid():
    residuals = compute_physics_residuals(
        {"pressure_kpa": 141.565, "depth_m": 4.0, "water_density_kg_m3": 1025.0}
    )
    assert residuals["pressure_depth"].valid
    assert residuals["pressure_depth"].provenance == "derived"
    assert not residuals["acceleration"].valid
    assert residuals["acceleration"].value is None


def test_uncertain_nominal_is_rejected_and_ood_distance_is_mask_aware():
    assessment = assess_uncertainty(
        {"nominal": 0.27, "sensor_drift": 0.24, "drag": 0.21, "thruster": 0.18, "buoyancy": 0.10}
    )
    assert assessment.label == UNKNOWN_LABEL
    distribution = TrainingDistribution.fit([[0.0, 1.0], [0.1, 1.1], [-0.1, 0.9]])
    assert distribution.score([20.0, math.nan], [True, False]) > 4.0


def test_temperature_is_fit_on_validation_probabilities_and_reports_metrics():
    probabilities = [[0.99, 0.01], [0.95, 0.05], [0.8, 0.2], [0.7, 0.3]]
    targets = [0, 1, 0, 1]
    raw = calibration_report(probabilities, targets)
    scaler = TemperatureScaler.fit(probabilities, targets)
    calibrated = calibration_report(scaler.transform(probabilities), targets)
    assert scaler.temperature > 0
    assert calibrated["nll"] <= raw["nll"] + 1e-12
    assert len(calibrated["reliability_diagram"]) == 10


def test_temporal_features_are_past_only_and_include_missingness():
    extractor = CausalTemporalFeatures(["speed"], window_seconds=2.0, sampling_hz=2.0)
    points = [
        TemporalPoint(float(index), "m", (float(index),), (index != 1,), "nominal")
        for index in range(5)
    ]
    windows = extractor.windows(points)
    assert windows
    assert all(window[-1].timestamp_s == max(point.timestamp_s for point in window) for window in windows)
    features = extractor.transform(windows[0])
    assert features[4] > 0


def test_data_quality_and_health_are_failure_first():
    quality = assess_field_quality(
        "depth_m", [0.0, 0.1, 0.2], [1.0, None, 1.1], now_s=2.0,
        stale_after_s=0.5, plausible_range=(0.0, 100.0)
    )
    assert quality.stale and not quality.usable
    health = assess_health({"communications_outage": True})
    assert health.status == "critical"
    assert health.recommended_action == "surface_or_recover"

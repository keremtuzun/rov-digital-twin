"""Deterministically replay canonical telemetry through reliability and decision checks."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from rov_dt.health_monitor import assess_health
from rov_dt.model import SoftmaxWeakPointClassifier
from rov_dt.physics_residuals import compute_physics_residuals
from rov_dt.real_data import CanonicalTelemetryRecord, load_csv, load_jsonl, load_rosbag_export
from rov_dt.schema import FEATURE_NAMES
from rov_dt.uncertainty import TrainingDistribution, assess_uncertainty


def _load(path: Path) -> list[CanonicalTelemetryRecord]:
    if path.suffix.lower() == ".jsonl":
        return load_jsonl(path)
    if path.suffix.lower() == ".csv":
        return load_csv(path)
    return load_rosbag_export(path)


def _legacy_features(record: CanonicalTelemetryRecord) -> tuple[list[float], list[bool]]:
    measurements = record.measurements
    dvl = measurements.get("dvl_velocity_mps")
    current = measurements.get("motor_current_a")
    response = measurements.get("estimated_thruster_response")
    orientation = measurements.get("orientation_xyzw")
    mapped = {
        "depth_m": measurements.get("depth_m"),
        "depth_error_m": record.metadata.get("depth_error_m"),
        "speed_mps": math.sqrt(sum(value * value for value in dvl)) if dvl else None,
        "vertical_speed_mps": dvl[1] if dvl and len(dvl) >= 2 else None,
        "roll_deg": record.metadata.get("roll_deg"),
        "pitch_deg": record.metadata.get("pitch_deg"),
        "yaw_rate_dps": record.metadata.get("yaw_rate_dps"),
        "current_a": sum(abs(value) for value in current) if current else None,
        "voltage_v": measurements.get("battery_voltage_v"),
        "thruster_cmd_mean": (
            sum(abs(value) for value in measurements["thruster_commands"])
            / len(measurements["thruster_commands"])
            if measurements.get("thruster_commands")
            else None
        ),
        "thruster_response_ratio": (
            sum(response) / len(response) if isinstance(response, list) and response else response
        ),
        "imu_depth_disagreement_m": record.metadata.get("imu_depth_disagreement_m"),
        "dvl_quality": measurements.get("dvl_quality"),
        "temperature_c": measurements.get("temperature_c"),
    }
    # Orientation alone cannot be safely converted into roll/pitch without an agreed frame convention.
    _ = orientation
    mask = [mapped[name] is not None for name in FEATURE_NAMES]
    return [float(mapped[name]) if mapped[name] is not None else 0.0 for name in FEATURE_NAMES], mask


def replay(records: list[CanonicalTelemetryRecord], model: SoftmaxWeakPointClassifier) -> list[dict]:
    timeline = []
    statistics = model.training_statistics
    distribution = None
    if statistics.get("raw_feature_means") and statistics.get("raw_feature_scales"):
        distribution = TrainingDistribution(
            tuple(statistics["raw_feature_means"]), tuple(statistics["raw_feature_scales"])
        )
    ordered = sorted(records, key=lambda record: (record.mission_id, record.timestamp_s))
    for index, record in enumerate(ordered):
        row, mask = _legacy_features(record)
        complete = all(mask)
        probabilities = model.predict(row).probabilities if complete else {label: 1 / len(model.labels) for label in model.labels}
        ood_score = distribution.score(row, mask) if distribution else math.inf
        uncertainty = assess_uncertainty(probabilities, ood_score=ood_score)
        values = {
            "dvl_speed_mps": row[FEATURE_NAMES.index("speed_mps")] if mask[FEATURE_NAMES.index("speed_mps")] else None,
            "thruster_cmd_mean": row[FEATURE_NAMES.index("thruster_cmd_mean")] if mask[FEATURE_NAMES.index("thruster_cmd_mean")] else None,
            "current_a": row[FEATURE_NAMES.index("current_a")] if mask[FEATURE_NAMES.index("current_a")] else None,
            "stale_critical_sensor": not complete,
            "communications_outage": bool(record.measurements.get("dropped_packet")),
        }
        health = assess_health(values)
        residual_input = {name: (value if valid else None) for name, value, valid in zip(FEATURE_NAMES, row, mask)}
        residual_input["pressure_kpa"] = record.measurements.get("pressure_kpa")
        residuals = compute_physics_residuals(residual_input)
        final_action = health.recommended_action if health.status != "healthy" else (
            "request_human_review" if uncertainty.uncertain else "continue_survey"
        )
        timeline.append(
            {
                "index": index,
                "timestamp_s": record.timestamp_s,
                "mission_id": record.mission_id,
                "true_state": record.ground_truth_fault_label,
                "prediction": uncertainty.label,
                "confidence": uncertainty.maximum_probability,
                "ood_score": uncertainty.ood_score,
                "missing_features": [name for name, valid in zip(FEATURE_NAMES, mask) if not valid],
                "sensor_health": health.status,
                "sensor_health_reasons": list(health.reasons),
                "valid_residuals": [name for name, residual in residuals.items() if residual.valid],
                "recommended_action": final_action,
                "model_version": model.model_version,
                "dataset_version": model.dataset_version,
                "calibration_version": model.calibration_version,
            }
        )
    return timeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = _load(args.input)
    timeline = replay(records, SoftmaxWeakPointClassifier.load(args.model))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(timeline, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

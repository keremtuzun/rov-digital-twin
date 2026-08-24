"""Versioned loaders for simulated and real ROV telemetry with explicit missingness."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "2.0.0"
DATA_SOURCES = {"simulated", "pool", "lake", "sheltered_water", "open_sea"}

MEASUREMENT_FIELDS = (
    "latitude_deg",
    "longitude_deg",
    "depth_m",
    "pressure_kpa",
    "imu_acceleration_mps2",
    "imu_angular_velocity_rps",
    "orientation_xyzw",
    "dvl_velocity_mps",
    "dvl_altitude_m",
    "dvl_quality",
    "thruster_commands",
    "estimated_thruster_response",
    "motor_current_a",
    "battery_voltage_v",
    "battery_state_of_charge",
    "temperature_c",
    "sonar_ranges_m",
    "communications_latency_ms",
    "dropped_packet",
    "water_temperature_c",
    "salinity_psu",
    "estimated_water_density_kg_m3",
    "current_estimate_mps",
    "sea_state",
)

VECTOR_FIELDS = {
    "imu_acceleration_mps2",
    "imu_angular_velocity_rps",
    "orientation_xyzw",
    "dvl_velocity_mps",
    "thruster_commands",
    "estimated_thruster_response",
    "motor_current_a",
    "sonar_ranges_m",
    "current_estimate_mps",
}


class RealDataError(ValueError):
    """Raised when a source cannot be represented without inventing measurements."""


@dataclass(frozen=True)
class CanonicalTelemetryRecord:
    timestamp_s: float
    mission_id: str
    vehicle_id: str
    environment_id: str
    data_source: str
    measurements: dict[str, Any]
    measurement_mask: dict[str, bool]
    sensor_provenance: dict[str, str]
    calibration_version: str
    ground_truth_fault_label: str | None = None
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _parse_value(name: str, value: Any) -> Any:
    if _missing(value):
        return None
    if name == "dropped_packet":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
        raise RealDataError("dropped_packet must be boolean")
    if name in VECTOR_FIELDS:
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, list) or not parsed:
            raise RealDataError(f"{name} must be a non-empty JSON array")
        numbers = [float(item) for item in parsed]
        if not all(math.isfinite(item) for item in numbers):
            raise RealDataError(f"{name} contains NaN or infinite values")
        return numbers
    if name == "sea_state":
        return str(value)
    number = float(value)
    if not math.isfinite(number):
        raise RealDataError(f"{name} must be finite when present")
    return number


def record_from_mapping(row: dict[str, Any]) -> CanonicalTelemetryRecord:
    """Convert one mapping without imputing absent sensor values."""
    nested_measurements = row.get("measurements", {})
    if nested_measurements is not None and not isinstance(nested_measurements, dict):
        raise RealDataError("measurements must be an object")
    source_values = dict(row)
    source_values.update(nested_measurements or {})
    required = ("timestamp_s", "mission_id", "vehicle_id", "environment_id", "data_source")
    missing = [name for name in required if _missing(row.get(name))]
    if missing:
        raise RealDataError(f"missing required identity fields: {', '.join(missing)}")
    source = str(row["data_source"])
    if source not in DATA_SOURCES:
        raise RealDataError(f"unsupported data_source: {source!r}")
    timestamp = float(row["timestamp_s"])
    if not math.isfinite(timestamp) or timestamp < 0:
        raise RealDataError("timestamp_s must be a finite non-negative number")
    schema_version = str(row.get("schema_version") or SCHEMA_VERSION)
    if schema_version != SCHEMA_VERSION:
        raise RealDataError(f"unsupported canonical schema_version: {schema_version!r}")
    measurements = {name: _parse_value(name, source_values.get(name)) for name in MEASUREMENT_FIELDS}
    mask = {name: value is not None for name, value in measurements.items()}
    supplied_mask = row.get("measurement_mask")
    if isinstance(supplied_mask, str) and supplied_mask.strip():
        supplied_mask = json.loads(supplied_mask)
    if supplied_mask is not None:
        if not isinstance(supplied_mask, dict):
            raise RealDataError("measurement_mask must be an object")
        for name in MEASUREMENT_FIELDS:
            declared = bool(supplied_mask.get(name, False))
            if declared != mask[name]:
                raise RealDataError(f"measurement_mask conflicts with {name}")
    provenance = row.get("sensor_provenance", {})
    if isinstance(provenance, str):
        provenance = json.loads(provenance) if provenance.strip() else {}
    if not isinstance(provenance, dict):
        raise RealDataError("sensor_provenance must be an object")
    for name, present in mask.items():
        if present and not str(provenance.get(name, "")).strip():
            raise RealDataError(f"present measurement {name} requires sensor provenance")
    known = set(required) | set(MEASUREMENT_FIELDS) | {
        "schema_version",
        "measurements",
        "metadata",
        "measurement_mask",
        "sensor_provenance",
        "calibration_version",
        "ground_truth_fault_label",
    }
    metadata = dict(row.get("metadata") or {})
    metadata.update({name: value for name, value in row.items() if name not in known})
    return CanonicalTelemetryRecord(
        timestamp_s=timestamp,
        mission_id=str(row["mission_id"]),
        vehicle_id=str(row["vehicle_id"]),
        environment_id=str(row["environment_id"]),
        data_source=source,
        measurements=measurements,
        measurement_mask=mask,
        sensor_provenance={str(key): str(value) for key, value in provenance.items()},
        calibration_version=str(row.get("calibration_version") or "unversioned"),
        ground_truth_fault_label=(
            str(row["ground_truth_fault_label"])
            if not _missing(row.get("ground_truth_fault_label"))
            else None
        ),
        schema_version=schema_version,
        metadata=metadata,
    )


def load_csv(path: str | Path) -> list[CanonicalTelemetryRecord]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [record_from_mapping(dict(row)) for row in csv.DictReader(handle)]


def load_jsonl(path: str | Path) -> list[CanonicalTelemetryRecord]:
    records: list[CanonicalTelemetryRecord] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                records.append(record_from_mapping(payload))
            except (json.JSONDecodeError, RealDataError, TypeError) as exc:
                raise RealDataError(f"invalid JSONL record at line {line_number}: {exc}") from exc
    return records


def load_rosbag_export(path: str | Path) -> list[CanonicalTelemetryRecord]:
    """Load a canonical CSV/JSONL export made from ROS 1/2 bags.

    Native DB3/MCAP decoding is intentionally not guessed because topic/type mappings are vehicle
    specific. Export selected topics with provenance first, then pass that file here.
    """
    source = Path(path)
    if source.is_dir():
        candidates: Iterable[Path] = (*source.glob("*.jsonl"), *source.glob("*.csv"))
        files = sorted(candidates)
        if len(files) != 1:
            raise RealDataError("ROS export directory must contain exactly one canonical CSV or JSONL")
        source = files[0]
    if source.suffix.lower() in {".db3", ".mcap", ".bag"}:
        raise RealDataError("native ROS bags require an explicit topic-to-canonical export step")
    if source.suffix.lower() == ".jsonl":
        return load_jsonl(source)
    if source.suffix.lower() == ".csv":
        return load_csv(source)
    raise RealDataError(f"unsupported ROS export format: {source.suffix}")

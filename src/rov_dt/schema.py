from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class WeakPoint(str, Enum):
    NOMINAL = "nominal"
    THRUSTER_DEGRADATION = "thruster_degradation"
    BUOYANCY_IMBALANCE = "buoyancy_imbalance"
    SENSOR_DRIFT = "sensor_drift"
    HYDRODYNAMIC_DRAG = "hydrodynamic_drag"
    UNKNOWN = "unknown"


FEATURE_NAMES = (
    "depth_m",
    "depth_error_m",
    "speed_mps",
    "vertical_speed_mps",
    "roll_deg",
    "pitch_deg",
    "yaw_rate_dps",
    "current_a",
    "voltage_v",
    "thruster_cmd_mean",
    "thruster_response_ratio",
    "imu_depth_disagreement_m",
    "dvl_quality",
    "temperature_c",
)


@dataclass(frozen=True)
class TelemetrySample:
    timestamp_s: float
    mission_id: str
    duty: str
    depth_m: float
    depth_error_m: float
    speed_mps: float
    vertical_speed_mps: float
    roll_deg: float
    pitch_deg: float
    yaw_rate_dps: float
    current_a: float
    voltage_v: float
    thruster_cmd_mean: float
    thruster_response_ratio: float
    imu_depth_disagreement_m: float
    dvl_quality: float
    temperature_c: float
    label: str = WeakPoint.NOMINAL.value
    schema_version: str = "1.0.0"

    def features(self) -> list[float]:
        return [float(getattr(self, name)) for name in FEATURE_NAMES]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "TelemetrySample":
        values = dict(row)
        for name in ("timestamp_s", *FEATURE_NAMES):
            values[name] = float(values[name])
        values.setdefault("label", WeakPoint.NOMINAL.value)
        values.setdefault("schema_version", "1.0.0")
        return cls(**values)

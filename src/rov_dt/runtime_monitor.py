"""Structured, reconstructable runtime monitoring and deployment-mode gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class DeploymentMode(str, Enum):
    SIMULATION = "simulation"
    SHADOW = "shadow"
    ADVISORY = "advisory"
    AUTONOMOUS_HIGH_LEVEL = "autonomous_high_level"


@dataclass(frozen=True)
class RuntimeVersions:
    model_version: str
    model_hash: str
    dataset_version: str
    calibration_version: str
    feature_transform_version: str
    simulator_profile: str
    vehicle_profile: str


@dataclass(frozen=True)
class RuntimeEvent:
    timestamp: str
    mode: str
    prediction: dict[str, Any]
    monitoring: dict[str, Any]
    versions: RuntimeVersions
    affects_vehicle_behavior: bool


def authorize_mode(mode: DeploymentMode, *, autonomous_high_level_enabled: bool = False) -> bool:
    if mode is DeploymentMode.AUTONOMOUS_HIGH_LEVEL and not autonomous_high_level_enabled:
        raise PermissionError("autonomous_high_level requires explicit configuration")
    return mode in {DeploymentMode.ADVISORY, DeploymentMode.AUTONOMOUS_HIGH_LEVEL}


def build_runtime_event(
    mode: DeploymentMode,
    prediction: dict[str, Any],
    monitoring: dict[str, Any],
    versions: RuntimeVersions,
    *,
    autonomous_high_level_enabled: bool = False,
) -> RuntimeEvent:
    affects_behavior = authorize_mode(
        mode, autonomous_high_level_enabled=autonomous_high_level_enabled
    )
    return RuntimeEvent(
        datetime.now(timezone.utc).isoformat(),
        mode.value,
        prediction,
        monitoring,
        versions,
        affects_behavior,
    )


def append_jsonl(event: RuntimeEvent, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")


class RuntimeMonitor:
    """Aggregate operational rates without discarding individual structured events."""

    def __init__(self) -> None:
        self.inference_count = 0
        self.dropped_inference_requests = 0
        self.ood_count = 0
        self.uncertainty_sum = 0.0
        self.disagreement_sum = 0.0
        self.sensor_disagreement_count = 0
        self.inference_latency_ms_sum = 0.0

    def record(
        self,
        *,
        ood: bool,
        uncertainty: float,
        classifier_disagreement: float,
        sensor_disagreement: bool,
        inference_latency_ms: float,
    ) -> None:
        self.inference_count += 1
        self.ood_count += int(ood)
        self.uncertainty_sum += float(uncertainty)
        self.disagreement_sum += float(classifier_disagreement)
        self.sensor_disagreement_count += int(sensor_disagreement)
        self.inference_latency_ms_sum += float(inference_latency_ms)

    def record_drop(self) -> None:
        self.dropped_inference_requests += 1

    def snapshot(self) -> dict[str, float | int]:
        count = max(1, self.inference_count)
        return {
            "inference_count": self.inference_count,
            "dropped_inference_requests": self.dropped_inference_requests,
            "ood_rate": self.ood_count / count,
            "mean_uncertainty": self.uncertainty_sum / count,
            "mean_classifier_disagreement": self.disagreement_sum / count,
            "sensor_disagreement_rate": self.sensor_disagreement_count / count,
            "mean_inference_latency_ms": self.inference_latency_ms_sum / count,
        }

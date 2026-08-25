"""Shared, model-agnostic experiment contracts for the Conrad software tracks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


PREDICTION_TYPES = {"box", "mask", "class", "anomaly_score", "severity", "structured_state"}
TRACKS = {"model1", "model2_research", "navigation_twin", "failure_twin", "integration"}
DATA_KINDS = {"real", "synthetic", "mixed"}


def _required(value: str, name: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


@dataclass(frozen=True)
class DatasetManifestRecord:
    file_path: str
    source_name: str
    source_url: str
    license_or_access_status: str
    sha256: str
    media_type: str
    label_path: str | None
    label_format: str
    split: str
    environment: str
    infrastructure_type: str
    defect_type: str
    synthetic_or_real: str
    notes: str

    def __post_init__(self) -> None:
        for name in ("file_path", "source_name", "source_url", "license_or_access_status",
                     "media_type", "label_format", "split", "environment",
                     "infrastructure_type", "defect_type", "notes"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if len(self.sha256) != 64 or any(char not in "0123456789abcdef" for char in self.sha256.lower()):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")
        if self.synthetic_or_real not in {"real", "synthetic"}:
            raise ValueError("synthetic_or_real must be real or synthetic")
        if self.license_or_access_status.lower() in {"", "unknown"} and self.synthetic_or_real == "real":
            raise ValueError("real data with unknown access status is catalog-only, not experiment-ready")


@dataclass(frozen=True)
class PredictionRecord:
    run_id: str
    model_name: str
    model_version: str
    frame_id: str
    prediction_type: str
    class_label: str
    confidence: float
    target_id: str | None = None
    uncertainty: dict[str, float | bool] = field(default_factory=dict)
    geometry: dict[str, Any] | None = None
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("run_id", "model_name", "model_version", "frame_id", "class_label"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        if self.prediction_type not in PREDICTION_TYPES:
            raise ValueError(f"unsupported prediction_type: {self.prediction_type}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    date: str
    git_commit: str
    branch: str
    operator_or_agent: str
    track: str
    config_path: str
    dataset_manifest: str
    checkpoint_or_prototype_version: str
    inputs: list[str]
    outputs: list[str]
    metrics: dict[str, Any]
    synthetic_or_real_or_mixed: str
    limitations: list[str]
    next_actions: list[str]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in ("run_id", "date", "git_commit", "branch", "operator_or_agent",
                     "config_path", "dataset_manifest", "checkpoint_or_prototype_version"):
            object.__setattr__(self, name, _required(getattr(self, name), name))
        try:
            datetime.fromisoformat(self.date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("date must be ISO-8601") from exc
        if self.track not in TRACKS:
            raise ValueError(f"unsupported track: {self.track}")
        if self.synthetic_or_real_or_mixed not in DATA_KINDS:
            raise ValueError("synthetic_or_real_or_mixed must be real, synthetic, or mixed")
        if not self.limitations:
            raise ValueError("limitations must explicitly state the run's evidence boundary")
        if not self.inputs or not self.outputs:
            raise ValueError("inputs and outputs must be explicit and non-empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_jsonl(records: Iterable[DatasetManifestRecord | PredictionRecord], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    return output


def read_prediction_jsonl(path: str | Path) -> list[PredictionRecord]:
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(PredictionRecord(**json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid prediction record at line {line_number}: {exc}") from exc
    return records


def write_run_manifest(manifest: RunManifest, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def read_run_manifest(path: str | Path) -> RunManifest:
    try:
        return RunManifest(**json.loads(Path(path).read_text(encoding="utf-8")))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid run manifest {path}: {exc}") from exc

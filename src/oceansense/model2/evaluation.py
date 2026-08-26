"""Shared loader and evaluator for non-trained Model 2 D0 smoke baselines."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .baselines import BASELINE_CONTRACTS, BASELINE_NAMES, predict
from .release_validator import validate_release


@dataclass(frozen=True)
class D0Dataset:
    release_dir: Path
    manifest: dict[str, Any]
    metadata: dict[str, Any]
    splits: dict[str, Any]
    checksums: dict[str, Any]
    states: np.ndarray
    observations: np.ndarray
    observation_mask: np.ndarray

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return tuple(self.metadata["scenario_ids"])


def load_d0_release(release_dir: str | Path) -> D0Dataset:
    """Validate first, then load arrays with hidden truth kept in the evaluator object."""
    release = Path(release_dir)
    validation = validate_release(release, require_debug_d0=True)
    if not validation["valid"]:
        raise ValueError(f"D0 release validation failed: {validation['errors']}")
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads((release / "metadata.json").read_text(encoding="utf-8"))
    splits = json.loads((release / "splits.json").read_text(encoding="utf-8"))
    checksums = json.loads((release / "checksums.json").read_text(encoding="utf-8"))
    return D0Dataset(
        release_dir=release,
        manifest=manifest,
        metadata=metadata,
        splits=splits,
        checksums=checksums,
        states=np.load(release / "states.npy", allow_pickle=False),
        observations=np.load(release / "observations.npy", allow_pickle=False),
        observation_mask=np.load(release / "observation_mask.npy", allow_pickle=False),
    )


def _indices_for_split(dataset: D0Dataset, split: str) -> list[int]:
    split_ids = dataset.splits["splits"].get(split)
    if not split_ids:
        raise ValueError(f"split is missing or empty: {split}")
    lookup = {scenario_id: index for index, scenario_id in enumerate(dataset.scenario_ids)}
    return [lookup[scenario_id] for scenario_id in split_ids]


def _error_metrics(
    predictions: np.ndarray, targets: np.ndarray, mask: np.ndarray,
    state_fields: list[str],
) -> dict[str, Any]:
    error = predictions.astype(np.float64) - targets.astype(np.float64)
    absolute = np.abs(error)
    squared = np.square(error)

    def group_metrics(selection: np.ndarray) -> dict[str, float | int | None]:
        if not np.any(selection):
            return {"count": 0, "mae": None, "rmse": None}
        selected = error[selection]
        return {
            "count": int(selection.sum()),
            "mae": float(np.abs(selected).mean()),
            "rmse": float(np.sqrt(np.square(selected).mean())),
        }

    return {
        "mae_overall": float(absolute.mean()),
        "rmse_overall": float(np.sqrt(squared.mean())),
        "per_state_dimension_mae": {
            name: float(absolute[..., index].mean())
            for index, name in enumerate(state_fields)
        },
        "per_state_dimension_rmse": {
            name: float(np.sqrt(squared[..., index].mean()))
            for index, name in enumerate(state_fields)
        },
        "observed_node_error": group_metrics(mask.astype(bool)),
        "unobserved_node_error": group_metrics(~mask.astype(bool)),
    }


def evaluate_baseline(
    dataset: D0Dataset,
    baseline_name: str,
    split: str,
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Predict from observations/mask only; expose hidden states solely to metric computation."""
    indices = _indices_for_split(dataset, split)
    observations = dataset.observations[indices]
    mask = dataset.observation_mask[indices]
    predictions = predict(baseline_name, observations, mask)
    targets = dataset.states[indices]
    metrics = _error_metrics(
        predictions, targets, mask, list(dataset.manifest["state_fields"])
    )
    scenario_count, timesteps, nodes = mask.shape
    metrics.update({
        "schema_version": "1.0.0",
        "baseline_name": baseline_name,
        "split": split,
        "d0_release_id": dataset.manifest["release_id"],
        "d0_manifest_sha256": dataset.checksums["files"]["manifest.json"],
        "number_of_scenarios": scenario_count,
        "number_of_timesteps": timesteps,
        "number_of_nodes": nodes,
        "number_of_timestep_nodes": int(mask.size),
        "mask_coverage": float(mask.mean()),
        "generated_at_utc": generated_at_utc,
        "training_performed": False,
        "hidden_state_input": False,
        "debug_only": True,
        "classification_metrics": "not_computed_no_predeclared_weak_point_target",
    })
    return metrics


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_d0_smoke_evaluation(
    release_dir: str | Path,
    output_dir: str | Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    dataset = load_d0_release(release_dir)
    timestamp = generated_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    for baseline_name in BASELINE_NAMES:
        split_metrics = {
            split: evaluate_baseline(
                dataset, baseline_name, split, generated_at_utc=timestamp
            )
            for split in ("validation", "test")
        }
        result = {
            "schema_version": "1.0.0",
            "baseline_name": baseline_name,
            "baseline_type": "deterministic_non_trained_smoke_baseline",
            "baseline_contract": BASELINE_CONTRACTS[baseline_name],
            "d0_release_id": dataset.manifest["release_id"],
            "d0_manifest_sha256": dataset.checksums["files"]["manifest.json"],
            "input_files": list(dataset.manifest["inference_inputs"]),
            "target_file_evaluation_only": "states.npy",
            "validation": split_metrics["validation"],
            "test": split_metrics["test"],
            "training_performed": False,
            "debug_only": True,
            "limitations": [
                "D0 is a tiny synthetic data-contract release with uncalibrated dynamics.",
                "Results are pipeline smoke evidence, not Model 2 or real-world performance.",
                "No proprietary architecture or learned parameter is evaluated.",
            ],
        }
        results[baseline_name] = result
        _write_json(output / f"{baseline_name}_metrics.json", result)
    comparison = {
        "schema_version": "1.0.0",
        "d0_release_id": dataset.manifest["release_id"],
        "d0_manifest_sha256": dataset.checksums["files"]["manifest.json"],
        "baseline_names": list(BASELINE_NAMES),
        "validation_metrics": {
            name: results[name]["validation"] for name in BASELINE_NAMES
        },
        "test_metrics": {name: results[name]["test"] for name in BASELINE_NAMES},
        "metric_definitions": {
            "mae": "Mean absolute error across selected scenario/time/node/state entries.",
            "rmse": "Root mean squared error across selected entries.",
            "observed_node": "Current timestep/node has observation_mask=1.",
            "unobserved_node": "Current timestep/node has observation_mask=0.",
            "mask_coverage": "Fraction of evaluated timestep/node entries with mask=1.",
        },
        "generated_at_utc": timestamp,
        "training_performed": False,
        "debug_only": True,
        "limitations": [
            "D0 debug-only results cannot support a Model 2 superiority claim.",
            "Synthetic-only scores do not establish real structural or ocean performance.",
            "The comparison contains two smoke baselines, not the required six-baseline matrix.",
        ],
        "claim_boundary": "No Model 2 superiority claim is supported by this comparison.",
    }
    _write_json(output / "baseline_comparison.json", comparison)
    return comparison


def output_hashes(output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    names = (
        "last_observation_metrics.json", "simple_heuristic_metrics.json",
        "baseline_comparison.json",
    )
    return {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in names
    }

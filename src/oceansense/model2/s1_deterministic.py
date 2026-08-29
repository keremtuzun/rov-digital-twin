"""No-training deterministic baseline evaluation on the frozen synthetic S1 release."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .baseline_config import load_baseline_eval_config
from .baselines import BASELINE_CONTRACTS, BASELINE_NAMES, predict
from .evaluation import _error_metrics

S1_OUTPUT_NAMES = {
    "last_observation": "last_observation_s1_metrics.json",
    "simple_heuristic": "simple_heuristic_s1_metrics.json",
}
S1_COMPARISON_NAME = "s1_deterministic_baseline_comparison.json"


@dataclass(frozen=True)
class S1DeterministicDataset:
    """Validated S1 arrays; states remain target-only inside evaluation."""

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


def load_s1_deterministic_release(
    config_path: str | Path, repo_root: str | Path,
) -> S1DeterministicDataset:
    """Bind to the frozen config and strictly validate S1 before loading arrays."""
    config = load_baseline_eval_config(
        config_path, validate_s1_release=True, repo_root=repo_root
    )
    release = Path(repo_root) / config["release"]["path"]
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    checksums = json.loads((release / "checksums.json").read_text(encoding="utf-8"))
    if checksums["files"]["manifest.json"] != config["release"]["manifest_sha256"]:
        raise ValueError("S1 manifest checksum does not match the frozen config")
    if manifest["inference_inputs"] != config["feature_contract"]["allowed_input_files"]:
        raise ValueError("S1 inference inputs do not match the frozen feature contract")
    return S1DeterministicDataset(
        release_dir=release,
        manifest=manifest,
        metadata=json.loads((release / "metadata.json").read_text(encoding="utf-8")),
        splits=json.loads((release / "splits.json").read_text(encoding="utf-8")),
        checksums=checksums,
        states=np.load(release / "states.npy", allow_pickle=False),
        observations=np.load(release / "observations.npy", allow_pickle=False),
        observation_mask=np.load(release / "observation_mask.npy", allow_pickle=False),
    )


def _indices_for_split(dataset: S1DeterministicDataset, split: str) -> list[int]:
    split_ids = dataset.splits["splits"].get(split)
    if not split_ids:
        raise ValueError(f"split is missing or empty: {split}")
    lookup = {scenario_id: index for index, scenario_id in enumerate(dataset.scenario_ids)}
    return [lookup[scenario_id] for scenario_id in split_ids]


def evaluate_s1_deterministic_baseline(
    dataset: S1DeterministicDataset,
    baseline_name: str,
    split: str,
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Predict from allowed evidence first, then expose targets only to metrics."""
    if baseline_name not in BASELINE_NAMES:
        raise ValueError(f"unsupported deterministic baseline: {baseline_name}")
    if split not in {"validation", "test", "ood"}:
        raise ValueError(f"unsupported S1 evaluation split: {split}")
    indices = _indices_for_split(dataset, split)
    observations = dataset.observations[indices]
    mask = dataset.observation_mask[indices]
    predictions = predict(baseline_name, observations, mask)
    metrics = _error_metrics(
        predictions,
        dataset.states[indices],
        mask,
        list(dataset.manifest["state_fields"]),
    )
    scenario_count, timesteps, nodes = mask.shape
    metrics.update({
        "schema_version": "1.0.0",
        "baseline_name": baseline_name,
        "split": split,
        "release_id": dataset.manifest["release_id"],
        "manifest_sha256": dataset.checksums["files"]["manifest.json"],
        "number_of_scenarios": scenario_count,
        "number_of_timesteps": timesteps,
        "number_of_nodes": nodes,
        "number_of_timestep_nodes": int(mask.size),
        "mask_coverage": float(mask.mean()),
        "generated_at_utc": generated_at_utc,
        "training_performed": False,
        "hidden_state_input": False,
        "synthetic_only": True,
        "debug_only": False,
        "classification_metrics": "not_computed_no_predeclared_weak_point_target",
        "uncertainty_metrics": "not_applicable_deterministic_output",
    })
    return metrics


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_s1_deterministic_evaluation(
    config_path: str | Path,
    repo_root: str | Path,
    output_dir: str | Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Run both fixed rules on S1 validation/test/OOD with no fitting or selection."""
    dataset = load_s1_deterministic_release(config_path, repo_root)
    timestamp = generated_at_utc or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    for baseline_name in BASELINE_NAMES:
        split_metrics = {
            split: evaluate_s1_deterministic_baseline(
                dataset, baseline_name, split, generated_at_utc=timestamp
            )
            for split in ("validation", "test", "ood")
        }
        result = {
            "schema_version": "1.0.0",
            "baseline_name": baseline_name,
            "baseline_type": "deterministic_non_trained_s1_baseline",
            "baseline_contract": BASELINE_CONTRACTS[baseline_name],
            "release_id": dataset.manifest["release_id"],
            "manifest_sha256": dataset.checksums["files"]["manifest.json"],
            "input_files": list(dataset.manifest["inference_inputs"]),
            "target_file_evaluation_only": "states.npy",
            **split_metrics,
            "generated_at_utc": timestamp,
            "training_performed": False,
            "hidden_state_input": False,
            "synthetic_only": True,
            "limitations": [
                "S1 contains synthetic simulator data only.",
                "This fixed rule uses no learned parameters or model selection.",
                "Results do not establish real-world performance or Model 2 superiority.",
            ],
        }
        results[baseline_name] = result
        _write_json(output / S1_OUTPUT_NAMES[baseline_name], result)

    comparison = {
        "schema_version": "1.0.0",
        "release_id": dataset.manifest["release_id"],
        "manifest_sha256": dataset.checksums["files"]["manifest.json"],
        "baseline_names": list(BASELINE_NAMES),
        "validation_metrics": {
            name: results[name]["validation"] for name in BASELINE_NAMES
        },
        "test_metrics": {name: results[name]["test"] for name in BASELINE_NAMES},
        "ood_metrics": {name: results[name]["ood"] for name in BASELINE_NAMES},
        "metric_definitions": {
            "mae": "Mean absolute error across selected scenario/time/node/state entries.",
            "rmse": "Root mean squared error across selected entries.",
            "observed_node": "Current timestep/node has observation_mask=1.",
            "unobserved_node": "Current timestep/node has observation_mask=0.",
            "mask_coverage": "Fraction of evaluated timestep/node entries with mask=1.",
        },
        "generated_at_utc": timestamp,
        "training_performed": False,
        "hidden_state_input": False,
        "synthetic_only": True,
        "internal_comparison_evidence_only": True,
        "model1_status": "BLOCKED_NOT_FROZEN",
        "limitations": [
            "S1 results are synthetic-only internal comparison evidence.",
            "No learned or proprietary Model 2 method is evaluated by this run.",
            "No result proves real-world structural performance or superiority.",
            "D0 scores belong to a different release and are not compared here.",
        ],
        "claim_boundary": (
            "No real-world performance or Model 2 superiority claim is supported."
        ),
    }
    _write_json(output / S1_COMPARISON_NAME, comparison)
    return comparison

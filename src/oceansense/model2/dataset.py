"""Scenario-level Failure Twin v0 dataset generation and manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .schemas import OBSERVATION_FIELDS, STATE_FIELDS
from .simulator import TwinConfig, config_to_dict, generate_scenario


def scenario_split(scenario_id: str, train_ratio: int = 70, validation_ratio: int = 15) -> str:
    bucket = int(hashlib.sha256(scenario_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < train_ratio:
        return "train"
    if bucket < train_ratio + validation_ratio:
        return "validation"
    return "test"


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_scenario(result: Any, output_dir: str | Path, split: str) -> dict[str, Any]:
    """Write one self-contained scenario while keeping truth out of observations.json."""
    output = Path(output_dir) / result.scenario_id
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "structure.json", result.graph.to_dict())
    _write_json(output / "config.json", config_to_dict(result.config))
    np.save(output / "states.npy", result.states)
    np.save(output / "observations.npy", result.observation_tensor)
    np.save(output / "observation_mask.npy", result.observation_mask)
    _write_json(
        output / "observations.json",
        {
            "schema_version": "1.0.0",
            "observation_fields": list(OBSERVATION_FIELDS),
            "records": [record.to_dict() for record in result.observations],
        },
    )
    metadata = {
        "schema_version": "1.0.0",
        "scenario_id": result.scenario_id,
        "seed": result.seed,
        "split": split,
        "synthetic_or_real": "synthetic",
        "n_nodes": len(result.graph.nodes),
        "timesteps": result.config.timesteps,
        "state_dimensions": list(STATE_FIELDS),
        "observation_dimensions": list(OBSERVATION_FIELDS),
        "states_shape": list(result.states.shape),
        "observations_shape": list(result.observation_tensor.shape),
        "mask_shape": list(result.observation_mask.shape),
        "observed_fraction": float(result.observation_mask.mean()),
        "hidden_truth_location": "states.npy (debug/evaluation only; forbidden as model input)",
        "claim_boundary": (
            "Synthetic research fixture; dynamics are not calibrated corrosion or failure physics."
        ),
    }
    _write_json(output / "metadata.json", metadata)
    return metadata


def generate_dataset(config: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Generate deterministic scenarios and scenario-disjoint split manifests."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    dataset_seed = int(config.get("dataset_seed", 20260825))
    scenario_count = int(config.get("scenario_count", 100))
    if scenario_count < 3:
        raise ValueError("scenario_count must be at least three")
    twin_config = TwinConfig.from_mapping(config.get("twin", {}))
    records = []
    split_ids: dict[str, list[str]] = {"train": [], "validation": [], "test": []}
    for index in range(scenario_count):
        scenario_id = f"scenario_{index:06d}"
        split = scenario_split(scenario_id)
        result = generate_scenario(scenario_id, twin_config, dataset_seed + index * 10)
        records.append(write_scenario(result, output, split))
        split_ids[split].append(scenario_id)
    assigned = [item for values in split_ids.values() for item in values]
    if len(assigned) != len(set(assigned)) or len(assigned) != scenario_count:
        raise RuntimeError("scenario split leakage or omission detected")
    for split, ids in split_ids.items():
        _write_json(output / f"{split}_scenarios.json", {"split": split, "scenario_ids": ids})
    manifest = {
        "schema_version": "1.0.0",
        "dataset_version": str(config.get("dataset_version", "failure-twin-v0-debug-100")),
        "dataset_seed": dataset_seed,
        "scenario_count": scenario_count,
        "scenario_level_split": True,
        "split_ids": split_ids,
        "config": config,
        "records": records,
        "limitations": [
            "Hidden dynamics are synthetic and uncalibrated.",
            "Model1Simulator outputs are numerical observations, not image-model predictions.",
            "This dataset cannot support field-performance or structural-safety claims.",
        ],
    }
    _write_json(output / "dataset_manifest.json", manifest)
    return manifest

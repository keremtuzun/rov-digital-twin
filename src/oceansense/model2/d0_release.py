"""Build a small deterministic, contract-only Twin 2 D0 release."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import networkx
import numpy as np
import yaml

from .dataset import scenario_split
from .release_validator import validate_release
from .schemas import OBSERVATION_FIELDS, STATE_FIELDS
from .simulator import TwinConfig, generate_scenario

GENERATOR_VERSION = "oceansense-twin2-d0-release/1.0.0"
RELEASE_FILENAMES = {
    "manifest.json", "config.json", "metadata.json", "splits.json",
    "structure_graph.json", "states.npy", "observations.npy",
    "observation_mask.npy", "checksums.json",
}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_d0_release(
    config: dict[str, Any], output_dir: str | Path, *, force: bool = False
) -> dict[str, Any]:
    """Generate deterministic tensors and audit metadata without training any model."""
    output = Path(output_dir)
    if output.exists():
        if not force:
            raise FileExistsError(f"release directory already exists: {output}")
        manifest_path = output / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("refusing to replace a directory without a D0 manifest")
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest.get("release_id") != config.get("release_id"):
            raise ValueError("refusing to replace a different release_id")
        children = list(output.iterdir())
        if any(child.is_dir() or child.name not in RELEASE_FILENAMES for child in children):
            raise ValueError("refusing to replace a release directory with unexpected contents")
        for child in children:
            child.unlink()
    else:
        output.mkdir(parents=True)
    scenario_count = int(config["scenario_count"])
    dataset_seed = int(config["dataset_seed"])
    if scenario_count < 3:
        raise ValueError("D0 requires at least three scenarios")
    twin = TwinConfig.from_mapping(config["twin"])
    scenario_ids = [f"scenario_{index:06d}" for index in range(scenario_count)]
    results = [
        generate_scenario(scenario_id, twin, dataset_seed + index * 10)
        for index, scenario_id in enumerate(scenario_ids)
    ]
    states = np.stack([result.states for result in results]).astype(np.float32)
    observations = np.stack([result.observation_tensor for result in results]).astype(np.float32)
    masks = np.stack([result.observation_mask for result in results]).astype(np.uint8)
    np.save(output / "states.npy", states)
    np.save(output / "observations.npy", observations)
    np.save(output / "observation_mask.npy", masks)

    frozen_config = dict(config)
    frozen_config["generator_version"] = GENERATOR_VERSION
    _write_json(output / "config.json", frozen_config)
    split_map = {"train": [], "validation": [], "test": []}
    for scenario_id in scenario_ids:
        split_map[scenario_split(scenario_id)].append(scenario_id)
    splits = {
        "schema_version": "1.0.0",
        "unit": "scenario",
        "scenario_level": True,
        "split_seed": dataset_seed,
        "assignment_method": "sha256(scenario_id) fixed 70/15/15 buckets",
        "assignment_basis": ["scenario_id", "split_seed"],
        "target_independent": True,
        "splits": split_map,
    }
    _write_json(output / "splits.json", splits)

    scenario_graphs = []
    for result in results:
        scenario_graphs.append({
            "scenario_id": result.scenario_id,
            "structure_type": result.graph.structure_type,
            "nodes": [
                {
                    "component_id": node.component_id,
                    "tensor_index": index,
                    "node_type": node.node_type,
                    "criticality": node.criticality,
                }
                for index, node in enumerate(result.graph.nodes)
            ],
            "edges": [
                {"source": left, "target": right, "relation_type": "structural_neighbor"}
                for left, right in result.graph.edges
            ],
        })
    _write_json(
        output / "structure_graph.json",
        {"schema_version": "1.0.0", "scenario_graphs": scenario_graphs},
    )

    release_id = str(config["release_id"])
    metadata = {
        "schema_version": "1.0.0",
        "release_id": release_id,
        "created_at_utc": str(config["created_at_utc"]),
        "generation_seed": dataset_seed,
        "generator_name": "oceansense.model2.d0_release",
        "generator_version": GENERATOR_VERSION,
        "runtime_notes": platform.platform(),
        "dependencies": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "networkx": networkx.__version__,
            "pyyaml": yaml.__version__,
        },
        "synthetic_or_real": "synthetic",
        "debug_only": True,
        "scenario_ids": scenario_ids,
        "claim_boundary": (
            "D0 validates a synthetic data contract only; it is not Model 2 training, "
            "superiority evidence, calibrated physics, or real-world structural validation."
        ),
    }
    _write_json(output / "metadata.json", metadata)

    manifest = {
        "schema_version": "1.0.0",
        "release_id": release_id,
        "release_level": "D0",
        "dataset_type": "synthetic_debug",
        "files": {
            "config": "config.json",
            "metadata": "metadata.json",
            "splits": "splits.json",
            "structure_graph": "structure_graph.json",
            "states": "states.npy",
            "observations": "observations.npy",
            "observation_mask": "observation_mask.npy",
            "checksums": "checksums.json",
        },
        "dimensions": {
            "scenario_count": scenario_count,
            "timesteps": twin.timesteps,
            "node_count": twin.n_nodes,
            "state_dim": len(STATE_FIELDS),
            "obs_dim": len(OBSERVATION_FIELDS),
        },
        "array_layouts": {
            "states": ["scenario", "timestep", "node", "state_dim"],
            "observations": ["scenario", "timestep", "node", "obs_dim"],
            "observation_mask": ["scenario", "timestep", "node"],
        },
        "state_fields": list(STATE_FIELDS),
        "observation_fields": list(OBSERVATION_FIELDS),
        "observed_proxy_fields": list(OBSERVATION_FIELDS),
        "inference_inputs": [
            "observations.npy", "observation_mask.npy", "structure_graph.json"
        ],
        "hidden_truth_files": ["states.npy"],
        "debug_visualizations": [],
        "approved_for_model_training": False,
        "claim_boundary": metadata["claim_boundary"],
    }
    _write_json(output / "manifest.json", manifest)
    artifact_names = [
        "manifest.json", "config.json", "metadata.json", "splits.json",
        "structure_graph.json", "states.npy", "observations.npy", "observation_mask.npy",
    ]
    _write_json(
        output / "checksums.json",
        {"algorithm": "sha256", "files": {
            name: _sha256(output / name) for name in artifact_names
        }},
    )
    report = validate_release(output, require_debug_d0=True)
    if not report["valid"]:
        raise RuntimeError(f"generated D0 release failed validation: {report['errors']}")
    return report

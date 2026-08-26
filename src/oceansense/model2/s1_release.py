"""Build the deterministic, lineage-separated Twin 2 S1 comparison release."""

from __future__ import annotations

import hashlib
import json
import platform
import random
from pathlib import Path
from typing import Any

import networkx
import numpy as np
import yaml

from .release_validator import validate_release
from .schemas import OBSERVATION_FIELDS, STATE_FIELDS
from .simulator import TwinConfig, generate_scenario

GENERATOR_VERSION = "oceansense-twin2-s1-release/1.0.0"
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


def _prepare_output(output: Path, release_id: str, force: bool) -> None:
    if not output.exists():
        output.mkdir(parents=True)
        return
    if not force:
        raise FileExistsError(f"release directory already exists: {output}")
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("refusing to replace a directory without an S1 manifest")
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    if existing.get("release_id") != release_id or existing.get("release_level") != "S1":
        raise ValueError("refusing to replace a different release")
    children = list(output.iterdir())
    if any(child.is_dir() or child.name not in RELEASE_FILENAMES for child in children):
        raise ValueError("refusing to replace a release directory with unexpected contents")
    for child in children:
        child.unlink()


def _lineage_splits(config: dict[str, Any]) -> tuple[dict[str, list[str]], dict[str, str]]:
    count = int(config["lineage_count"])
    lineage_ids = [f"lineage_{index:04d}" for index in range(count)]
    random.Random(int(config["split_seed"])).shuffle(lineage_ids)
    split_lineage_counts = config["split_lineage_counts"]
    if sum(int(value) for value in split_lineage_counts.values()) != count:
        raise ValueError("split_lineage_counts must cover every lineage")
    split_lineages: dict[str, list[str]] = {}
    lineage_to_split: dict[str, str] = {}
    offset = 0
    for split in ("train", "validation", "test", "ood"):
        next_offset = offset + int(split_lineage_counts[split])
        values = lineage_ids[offset:next_offset]
        if not values:
            raise ValueError(f"S1 split has no lineages: {split}")
        split_lineages[split] = values
        lineage_to_split.update({lineage_id: split for lineage_id in values})
        offset = next_offset
    return split_lineages, lineage_to_split


def _scenario_config(
    config: dict[str, Any], lineage_index: int, replicate: int, split: str
) -> tuple[TwinConfig, dict[str, Any], list[str]]:
    if split == "ood":
        ood = config["ood"]
        graph_family = ood["graph_family"]
        regime_name = ood["degradation_regime"]
        coverage = float(ood["observation_coverage"])
        shifts = list(ood["shifted_dimensions"])
    else:
        graph_families = config["id_graph_families"]
        regimes = config["id_degradation_regimes"]
        coverage_levels = config["id_observation_coverage_levels"]
        graph_family = graph_families[(lineage_index + replicate) % len(graph_families)]
        regime_name = regimes[(lineage_index * 2 + replicate) % len(regimes)]
        coverage = float(coverage_levels[(lineage_index + replicate * 2) % len(coverage_levels)])
        shifts = []
    parameters = dict(config["twin_base"])
    parameters.update(config["degradation_regimes"][regime_name])
    parameters.update({
        "structure_types": [graph_family],
        "observation_coverage": coverage,
    })
    if split == "ood":
        parameters.update({
            "noise_std": config["ood"]["noise_std"],
            "severity_noise_std": config["ood"]["severity_noise_std"],
            "confidence_noise_std": config["ood"]["confidence_noise_std"],
            "environment_level": config["ood"]["environment_level"],
        })
    distribution = {
        "graph_family": graph_family,
        "degradation_regime": regime_name,
        "observation_coverage": coverage,
        "noise_std": float(parameters["noise_std"]),
        "environment_level": float(parameters["environment_level"]),
    }
    return TwinConfig.from_mapping(parameters), distribution, shifts


def build_s1_release(
    config: dict[str, Any], output_dir: str | Path, *, force: bool = False
) -> dict[str, Any]:
    """Generate an immutable synthetic comparison release; never train a model."""
    release_id = str(config["release_id"])
    output = Path(output_dir)
    _prepare_output(output, release_id, force)
    split_lineages, lineage_to_split = _lineage_splits(config)
    root_seeds = [int(seed) for seed in config["generation_seeds"]]
    scenarios_per_lineage = int(config["scenarios_per_lineage"])
    records: list[dict[str, Any]] = []
    results = []
    split_scenarios = {name: [] for name in ("train", "validation", "test", "ood")}
    lineage_ids = sorted(lineage_to_split)
    for lineage_index, lineage_id in enumerate(lineage_ids):
        split = lineage_to_split[lineage_id]
        for replicate in range(scenarios_per_lineage):
            scenario_index = len(results)
            scenario_id = f"s1_scenario_{scenario_index:06d}"
            root_seed = root_seeds[(lineage_index + replicate) % len(root_seeds)]
            scenario_seed = root_seed + lineage_index * 1000 + replicate * 17
            twin, distribution, shifts = _scenario_config(
                config, lineage_index, replicate, split
            )
            result = generate_scenario(scenario_id, twin, scenario_seed)
            results.append(result)
            split_scenarios[split].append(scenario_id)
            records.append({
                "scenario_id": scenario_id,
                "lineage_id": lineage_id,
                "split": split,
                "replicate": replicate,
                "root_seed": root_seed,
                "scenario_seed": scenario_seed,
                "distribution": distribution,
                "distribution_shift": shifts,
            })

    states = np.stack([result.states for result in results]).astype(np.float32)
    observations = np.stack([result.observation_tensor for result in results]).astype(np.float32)
    masks = np.stack([result.observation_mask for result in results]).astype(np.uint8)
    np.save(output / "states.npy", states)
    np.save(output / "observations.npy", observations)
    np.save(output / "observation_mask.npy", masks)
    frozen_config = dict(config)
    frozen_config["generator_version"] = GENERATOR_VERSION
    _write_json(output / "config.json", frozen_config)
    splits = {
        "schema_version": "1.1.0",
        "unit": "scenario",
        "scenario_level": True,
        "split_seed": int(config["split_seed"]),
        "assignment_method": "seeded lineage shuffle with frozen lineage counts",
        "assignment_basis": ["lineage_id", "split_seed"],
        "target_independent": True,
        "splits": split_scenarios,
        "lineages": split_lineages,
        "ood_definition": {
            "reference_split": "train",
            "reasons": list(config["ood"]["reasons"]),
            "shifted_dimensions": list(config["ood"]["shifted_dimensions"]),
        },
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
        {"schema_version": "1.1.0", "scenario_graphs": scenario_graphs},
    )
    scenario_ids = [result.scenario_id for result in results]
    metadata = {
        "schema_version": "1.1.0",
        "release_id": release_id,
        "created_at_utc": str(config["created_at_utc"]),
        "generation_seed": root_seeds[0],
        "generation_seeds": root_seeds,
        "generator_name": "oceansense.model2.s1_release",
        "generator_version": GENERATOR_VERSION,
        "runtime_notes": platform.platform(),
        "dependencies": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "networkx": networkx.__version__,
            "pyyaml": yaml.__version__,
        },
        "synthetic_or_real": "synthetic",
        "comparison_only": True,
        "scenario_ids": scenario_ids,
        "scenario_records": records,
        "claim_boundary": (
            "S1 is an internal synthetic baseline-comparison release. It does not prove "
            "real-world performance, proprietary superiority, calibrated physics, or safety."
        ),
    }
    _write_json(output / "metadata.json", metadata)
    first_twin = results[0].config
    manifest = {
        "schema_version": "1.1.0",
        "release_id": release_id,
        "release_level": "S1",
        "release_type": "synthetic_comparison",
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
            "scenario_count": len(results),
            "timesteps": first_twin.timesteps,
            "node_count": first_twin.n_nodes,
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
        "approved_for_baseline_development": True,
        "approved_for_proprietary_model_training": False,
        "real_world_validation": False,
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
    report = validate_release(output, require_synthetic_s1=True)
    if not report["valid"]:
        raise RuntimeError(f"generated S1 release failed validation: {report['errors']}")
    return report

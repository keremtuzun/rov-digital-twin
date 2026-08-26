"""Fail-closed validation for immutable Twin 2 dataset releases."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REQUIRED_FILE_KEYS = (
    "config", "metadata", "splits", "structure_graph", "states", "observations",
    "observation_mask", "checksums",
)
EXPECTED_PATHS = {
    "metadata": "metadata.json",
    "splits": "splits.json",
    "structure_graph": "structure_graph.json",
    "states": "states.npy",
    "observations": "observations.npy",
    "observation_mask": "observation_mask.npy",
    "checksums": "checksums.json",
}
INFERENCE_ALLOWED = {"observations.npy", "observation_mask.npy", "structure_graph.json"}
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        payload = _load_json(path)
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config must be a mapping")
    return payload


def _inside_release(release: Path, relative: str) -> Path | None:
    candidate = (release / relative).resolve()
    try:
        candidate.relative_to(release.resolve())
    except ValueError:
        return None
    return candidate


def _connected(node_ids: set[str], edges: list[tuple[str, str]]) -> bool:
    if not node_ids:
        return False
    neighbors = {node_id: set() for node_id in node_ids}
    for left, right in edges:
        neighbors[left].add(right)
        neighbors[right].add(left)
    visited: set[str] = set()
    pending = [next(iter(node_ids))]
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        pending.extend(neighbors[node] - visited)
    return visited == node_ids


def validate_release(
    release_dir: str | Path, *, require_debug_d0: bool = False
) -> dict[str, Any]:
    """Validate structure, tensors, splits, checksums, provenance, and leakage controls."""
    release = Path(release_dir)
    errors: list[dict[str, str]] = []

    def fail(code: str, message: str) -> None:
        errors.append({"code": code, "message": message})

    manifest_path = release / "manifest.json"
    if not manifest_path.is_file():
        return {
            "valid": False, "release_dir": str(release),
            "errors": [{"code": "missing_file", "message": "manifest.json is required"}],
        }
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "valid": False, "release_dir": str(release),
            "errors": [{"code": "invalid_manifest", "message": str(exc)}],
        }
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        files = {}
        fail("invalid_manifest", "manifest.files must be an object")
    resolved: dict[str, Path] = {"manifest": manifest_path}
    for key in REQUIRED_FILE_KEYS:
        relative = files.get(key)
        if not isinstance(relative, str) or not relative:
            fail("missing_manifest_path", f"manifest.files.{key} is required")
            continue
        expected = EXPECTED_PATHS.get(key)
        if key == "config":
            if relative not in {"config.json", "config.yaml"}:
                fail("invalid_manifest_path", "config path must be config.json or config.yaml")
        elif relative != expected:
            fail("invalid_manifest_path", f"{key} path must be {expected}")
        path = _inside_release(release, relative)
        if path is None:
            fail("unsafe_manifest_path", f"{key} path leaves the release directory")
        elif not path.is_file():
            fail("missing_file", f"required file is missing: {relative}")
        else:
            resolved[key] = path
    if any(key not in resolved for key in REQUIRED_FILE_KEYS):
        return {
            "valid": False, "release_dir": str(release),
            "release_id": manifest.get("release_id", "unknown"), "errors": errors,
        }

    try:
        config = _load_config(resolved["config"])
        metadata = _load_json(resolved["metadata"])
        splits = _load_json(resolved["splits"])
        graph_payload = _load_json(resolved["structure_graph"])
        checksum_payload = _load_json(resolved["checksums"])
        states = np.load(resolved["states"], allow_pickle=False)
        observations = np.load(resolved["observations"], allow_pickle=False)
        mask = np.load(resolved["observation_mask"], allow_pickle=False)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        fail("unreadable_artifact", str(exc))
        return {
            "valid": False, "release_dir": str(release),
            "release_id": manifest.get("release_id", "unknown"), "errors": errors,
        }

    dimensions = manifest.get("dimensions", {})
    dimension_names = ("scenario_count", "timesteps", "node_count", "state_dim", "obs_dim")
    if any(not isinstance(dimensions.get(name), int) or dimensions[name] <= 0 for name in dimension_names):
        fail("invalid_dimensions", "manifest dimensions must be positive integers")
        expected_states = expected_observations = expected_mask = None
    else:
        scenario_count = dimensions["scenario_count"]
        timesteps = dimensions["timesteps"]
        node_count = dimensions["node_count"]
        expected_states = (scenario_count, timesteps, node_count, dimensions["state_dim"])
        expected_observations = (scenario_count, timesteps, node_count, dimensions["obs_dim"])
        expected_mask = (scenario_count, timesteps, node_count)
        if tuple(states.shape) != expected_states:
            fail("states_shape_mismatch", f"expected {expected_states}, found {states.shape}")
        if tuple(observations.shape) != expected_observations:
            fail(
                "observations_shape_mismatch",
                f"expected {expected_observations}, found {observations.shape}",
            )
        if tuple(mask.shape) != expected_mask:
            fail("mask_shape_mismatch", f"expected {expected_mask}, found {mask.shape}")
        layouts = manifest.get("array_layouts", {})
        expected_layouts = {
            "states": ["scenario", "timestep", "node", "state_dim"],
            "observations": ["scenario", "timestep", "node", "obs_dim"],
            "observation_mask": ["scenario", "timestep", "node"],
        }
        if layouts != expected_layouts:
            fail("invalid_array_layout", "array_layouts do not match the D0 contract")

    unique_mask = set(np.unique(mask).tolist())
    if not unique_mask.issubset({0, 1, False, True}):
        fail("invalid_mask_values", f"mask must be boolean/0/1, found {sorted(unique_mask)}")
    if observations.ndim == 4 and mask.ndim == 3 and observations.shape[:3] == mask.shape:
        if np.any(observations[mask == 0] != 0):
            fail("masked_observation_nonzero", "masked observation vectors must be zero")

    scenario_ids = metadata.get("scenario_ids", [])
    if not isinstance(scenario_ids, list) or len(scenario_ids) != len(set(scenario_ids)):
        fail("invalid_scenario_ids", "metadata scenario_ids must be a unique list")
        scenario_ids = []
    if expected_states and len(scenario_ids) != expected_states[0]:
        fail("scenario_count_mismatch", "metadata scenario count does not match arrays")

    split_map = splits.get("splits", {})
    if not isinstance(split_map, dict):
        split_map = {}
    required_splits = ("train", "validation", "test")
    split_sets: dict[str, set[str]] = {}
    for name in required_splits:
        values = split_map.get(name)
        if not isinstance(values, list) or not values:
            fail("missing_split", f"{name} split must exist and be non-empty")
            values = []
        split_sets[name] = set(values)
        if len(values) != len(split_sets[name]):
            fail("duplicate_split_id", f"{name} contains duplicate scenario IDs")
    if any(split_sets[a] & split_sets[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        fail("split_overlap", "scenario IDs overlap across splits")
    assigned = set().union(*split_sets.values())
    if assigned != set(scenario_ids):
        fail("split_coverage", "splits must cover every metadata scenario exactly once")
    if splits.get("unit") != "scenario" or splits.get("scenario_level") is not True:
        fail("timestep_split_leakage", "split unit must be scenario-level")
    if not isinstance(splits.get("split_seed"), int):
        fail("missing_split_seed", "split_seed is required")
    if splits.get("target_independent") is not True:
        fail("target_derived_split", "split must declare target_independent=true")
    basis = splits.get("assignment_basis", [])
    forbidden_basis = ("state", "target", "label", "severity", "condition")
    if not isinstance(basis, list) or not basis or any(
        token in str(item).lower() for item in basis for token in forbidden_basis
    ):
        fail("target_derived_split", "assignment_basis is missing or target-dependent")

    graphs = graph_payload.get("scenario_graphs", [])
    if not isinstance(graphs, list) or len(graphs) != len(scenario_ids):
        fail("graph_scenario_mismatch", "one graph is required for every scenario")
        graphs = []
    graph_ids: set[str] = set()
    stable_node_order: list[str] | None = None
    require_connected = bool(config.get("require_connected_graph", True))
    for graph in graphs:
        graph_scenario = graph.get("scenario_id", "")
        graph_ids.add(graph_scenario)
        nodes = graph.get("nodes", [])
        node_ids = [node.get("component_id", "") for node in nodes]
        indices = [node.get("tensor_index") for node in nodes]
        if not all(node_ids) or len(node_ids) != len(set(node_ids)):
            fail("invalid_graph_nodes", f"{graph_scenario}: node IDs must be unique")
            continue
        if expected_states and len(nodes) != expected_states[2]:
            fail("graph_node_mismatch", f"{graph_scenario}: node count differs from arrays")
        if indices != list(range(len(nodes))):
            fail("unstable_tensor_mapping", f"{graph_scenario}: tensor_index must be 0..N-1")
        if stable_node_order is None:
            stable_node_order = node_ids
        elif node_ids != stable_node_order:
            fail("unstable_node_ids", f"{graph_scenario}: node order/IDs changed")
        edge_pairs: list[tuple[str, str]] = []
        for edge in graph.get("edges", []):
            left, right = edge.get("source", ""), edge.get("target", "")
            if left not in node_ids or right not in node_ids or left == right:
                fail("invalid_graph_edge", f"{graph_scenario}: invalid edge endpoints")
            else:
                edge_pairs.append((left, right))
        if require_connected and set(node_ids) and not _connected(set(node_ids), edge_pairs):
            fail("disconnected_graph", f"{graph_scenario}: graph must be connected")
    if graph_ids != set(scenario_ids):
        fail("graph_scenario_mismatch", "graph scenario IDs do not match metadata")

    checksums = checksum_payload.get("files", {})
    if checksum_payload.get("algorithm") != "sha256" or not isinstance(checksums, dict):
        fail("invalid_checksums", "checksums.json must use SHA-256 and contain files")
        checksums = {}
    checksum_required = {"manifest.json", *(files[key] for key in REQUIRED_FILE_KEYS if key != "checksums")}
    for relative in sorted(checksum_required):
        expected_hash = checksums.get(relative)
        artifact = _inside_release(release, relative)
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            fail("missing_checksum", f"valid SHA-256 is required for {relative}")
        elif artifact is None or not artifact.is_file() or _sha256(artifact) != expected_hash:
            fail("checksum_mismatch", f"SHA-256 mismatch for {relative}")

    inference_inputs = manifest.get("inference_inputs", [])
    if not isinstance(inference_inputs, list) or set(inference_inputs) - INFERENCE_ALLOWED:
        fail("hidden_state_leakage", "inference_inputs contain unapproved or ground-truth files")
    if "states.npy" in inference_inputs:
        fail("hidden_state_leakage", "states.npy cannot be an inference input")
    state_fields = set(manifest.get("state_fields", []))
    observation_fields = set(manifest.get("observation_fields", []))
    forbidden_observation_fields = state_fields | {"hidden_state", "true_condition", "ground_truth"}
    if observation_fields & forbidden_observation_fields:
        fail("hidden_state_leakage", "observations contain direct hidden-state field names")
    proxies = set(manifest.get("observed_proxy_fields", []))
    if not observation_fields or not observation_fields.issubset(proxies):
        fail("unmarked_observation_proxy", "all observation fields must be marked observed proxies")
    for visualization in manifest.get("debug_visualizations", []):
        if visualization.get("contains_ground_truth") and not visualization.get("debug_only"):
            fail("debug_truth_leakage", "ground-truth visualization must be debug-only")
        if visualization.get("path") in inference_inputs:
            fail("debug_truth_leakage", "debug visualization cannot be an inference input")

    required_metadata = (
        "schema_version", "release_id", "created_at_utc", "generation_seed",
        "generator_name", "generator_version", "runtime_notes", "dependencies",
    )
    for field in required_metadata:
        if metadata.get(field) in (None, "", [], {}):
            fail("missing_reproducibility_metadata", f"metadata.{field} is required")
    if not TIMESTAMP.fullmatch(str(metadata.get("created_at_utc", ""))):
        fail("invalid_creation_timestamp", "created_at_utc must be RFC3339 UTC")
    if not manifest.get("schema_version") or metadata.get("schema_version") != manifest.get("schema_version"):
        fail("schema_version_mismatch", "manifest/metadata schema versions must match")
    if metadata.get("release_id") != manifest.get("release_id"):
        fail("release_id_mismatch", "manifest/metadata release IDs must match")
    if metadata.get("generation_seed") != config.get("dataset_seed"):
        fail("seed_mismatch", "metadata generation seed must match config")

    if require_debug_d0:
        if manifest.get("release_level") != "D0":
            fail("not_debug_d0", "release_level must be D0")
        if metadata.get("synthetic_or_real") != "synthetic" or metadata.get("debug_only") is not True:
            fail("not_debug_d0", "D0 must be synthetic and debug_only")
        if unique_mask != {0, 1}:
            fail("not_debug_d0", "D0 must exercise observed and unobserved mask states")
        if not metadata.get("claim_boundary"):
            fail("not_debug_d0", "D0 claim boundary is required")

    return {
        "valid": not errors,
        "release_dir": str(release),
        "release_id": manifest.get("release_id", "unknown"),
        "release_level": manifest.get("release_level", "unknown"),
        "errors": errors,
        "summary": {
            "scenario_count": dimensions.get("scenario_count"),
            "states_shape": list(states.shape),
            "observations_shape": list(observations.shape),
            "mask_shape": list(mask.shape),
            "split_counts": {name: len(split_sets[name]) for name in required_splits},
            "checksums_verified": len(checksum_required),
            "inference_inputs": inference_inputs,
            "training_performed": False,
            "real_world_validation": False,
        },
    }

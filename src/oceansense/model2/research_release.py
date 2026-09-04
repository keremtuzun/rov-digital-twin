"""Fresh, explicitly authorized S2 research release; never edits frozen S1."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

import numpy as np

from .independent_mlp import S1Data, _sha256, _write_json
from .release_validator import validate_release
from .s1_release import build_s1_release


def validate_s2(path: Path, protocol: dict) -> dict:
    report = validate_release(path)
    if not report["valid"]:
        raise ValueError(f"invalid S2: {report['errors']}")
    manifest = json.loads((path / "manifest.json").read_text())
    stored = json.loads((path / "protocol.json").read_text())
    hashes = json.loads((path / "checksums.json").read_text())["files"]
    if stored != protocol or manifest.get("protocol_sha256") != _sha256(path / "protocol.json"):
        raise ValueError("S2 protocol differs from preregistered protocol")
    if (
        manifest["release_level"] != "S2"
        or manifest["release_id"] != protocol["release_id"]
        or manifest["approved_for_proprietary_model_training"] is not True
        or manifest["real_world_validation"] is not False
    ):
        raise ValueError("invalid S2 research authorization boundary")
    for filename, digest in hashes.items():
        if Path(filename).name != filename or _sha256(path / filename) != digest:
            raise ValueError("S2 checksum failure")
    metadata = json.loads((path / "metadata.json").read_text())
    if metadata["generation_seeds"] != protocol["generation_seeds"]:
        raise ValueError("S2 generation seeds differ from protocol")
    if (manifest["dimensions"]["timesteps"] != protocol["timesteps"]
            or manifest["dimensions"]["node_count"] != protocol["node_count"]):
        raise ValueError("S2 dimensions differ from protocol")
    splits = json.loads((path / "splits.json").read_text())["splits"]
    assignment = {sid: split for split, ids in splits.items() for sid in ids}
    if len(assignment) != sum(map(len, splits.values())):
        raise ValueError("S2 scenario split overlap")
    lineages = {}
    if len(metadata["scenario_records"]) != len(assignment):
        raise ValueError("S2 scenario records are incomplete")
    if len({r["scenario_seed"] for r in metadata["scenario_records"]}) != len(assignment):
        raise ValueError("S2 scenario seeds are not unique")
    for record in metadata["scenario_records"]:
        if assignment[record["scenario_id"]] != record["split"]:
            raise ValueError("S2 metadata split mismatch")
        previous = lineages.setdefault(record["lineage_id"], record["split"])
        if previous != record["split"]:
            raise ValueError("S2 lineage split overlap")
    return report


def build_s2(root: Path, protocol: dict) -> dict:
    output = root / protocol["release_path"]
    if output.exists():
        return validate_s2(output, protocol)
    config = json.loads((root / "configs/model2/s1_synthetic_release.json").read_text())
    for key in (
        "release_id",
        "generation_seeds",
        "split_seed",
        "lineage_count",
        "scenarios_per_lineage",
        "split_lineage_counts",
    ):
        config[key] = protocol[key]
    config["created_at_utc"] = "2026-09-04T13:05:16Z"
    config["twin_base"]["timesteps"] = protocol["timesteps"]
    config["twin_base"]["n_nodes"] = protocol["node_count"]
    old = json.loads((root / "data/model2/s1_synthetic/metadata.json").read_text())
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="s2-build-", dir=output.parent) as tmp:
        staged = Path(tmp) / "release"
        build_s1_release(config, staged)  # reused generator, unpublished staging only
        for path in staged.glob("*.json"):
            text = path.read_text().replace("s1_scenario_", "s2_scenario_")
            value = json.loads(re.sub(r'"lineage_(\d{4})"', r'"s2_lineage_\1"', text))
            _write_json(path, value)
        _write_json(staged / "protocol.json", protocol)
        manifest = json.loads((staged / "manifest.json").read_text())
        manifest.update(
            release_level="S2",
            approved_for_proprietary_model_training=True,
            protocol_sha256=_sha256(staged / "protocol.json"),
            authorization_scope=protocol["authorization"]["scope"],
            claim_boundary=protocol["claim_boundary"],
        )
        _write_json(staged / "manifest.json", manifest)
        metadata = json.loads((staged / "metadata.json").read_text())
        metadata["generator_name"] = "oceansense.model2.research_release"
        metadata["claim_boundary"] = protocol["claim_boundary"]
        if {r["scenario_seed"] for r in old["scenario_records"]} & {
            r["scenario_seed"] for r in metadata["scenario_records"]
        }:
            raise ValueError("S2 generation seeds overlap S1")
        _write_json(staged / "metadata.json", metadata)
        _write_json(
            staged / "checksums.json",
            {
                "algorithm": "sha256",
                "files": {
                    p.name: _sha256(p)
                    for p in sorted(staged.iterdir())
                    if p.name != "checksums.json"
                },
            },
        )
        validate_s2(staged, protocol)
        shutil.move(str(staged), str(output))
    return validate_s2(output, protocol)


def load_s2(root: Path, protocol: dict) -> S1Data:
    path = root / protocol["release_path"]
    validate_s2(path, protocol)
    return S1Data(
        path,
        json.loads((path / "manifest.json").read_text()),
        json.loads((path / "metadata.json").read_text()),
        json.loads((path / "splits.json").read_text()),
        np.load(path / "observations.npy", allow_pickle=False),
        np.load(path / "observation_mask.npy", allow_pickle=False),
        np.load(path / "states.npy", allow_pickle=False),
    )

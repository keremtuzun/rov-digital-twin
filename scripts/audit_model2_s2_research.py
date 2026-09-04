"""Verify S2 saved evidence without retraining or re-opening model inference."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from oceansense.model2.evaluation import _error_metrics
from oceansense.model2.independent_mlp import _sha256
from oceansense.model2.research_experiment import uncertainty_metrics
from oceansense.model2.research_release import load_s2


def audit(root: Path) -> dict:
    protocol = json.loads((root / "configs/model2/s2_research_protocol.json").read_text())
    data = load_s2(root, protocol)
    output = root / "reports/model2/s2_research_v0"
    if json.loads((output / "protocol.json").read_text()) != protocol:
        raise ValueError("experiment protocol mismatch")
    environment = json.loads((output / "environment.json").read_text())
    if environment["protocol_sha256"] != _sha256(output / "protocol.json"):
        raise ValueError("recorded protocol checksum mismatch")
    if environment["release_checksums_sha256"] != _sha256(data.release_dir / "checksums.json"):
        raise ValueError("recorded release checksum mismatch")
    for name, digest in environment["source_sha256"].items():
        if Path(name).name != name or _sha256(root / "src/oceansense/model2" / name) != digest:
            raise ValueError("training implementation differs from recorded source")
    matrix = json.loads((output / "matrix_locked.json").read_text())
    expected = {(v, s) for v in protocol["variants"] for s in protocol["training_seeds"]}
    locked = {(r["variant"], r["seed"]): r for r in matrix["checkpoints"]}
    if set(locked) != expected or len(matrix["checkpoints"]) != len(expected):
        raise ValueError("incomplete checkpoint matrix")
    summary = json.loads((output / "summary.json").read_text())
    collected = {}
    for variant, seed in sorted(expected):
        directory = output / variant / f"seed_{seed}"
        selection = json.loads((directory / "selected_checkpoint.json").read_text())
        if selection != locked[(variant, seed)]:
            raise ValueError("selection changed after matrix lock")
        if selection["test_used_for_selection"] or selection["ood_used_for_selection"]:
            raise ValueError("held-out selection leakage")
        if _sha256(directory / "checkpoint.pt") != selection["checkpoint_sha256"]:
            raise ValueError("checkpoint hash mismatch")
        if datetime.fromisoformat(selection["locked_at_utc"]) > datetime.fromisoformat(matrix["locked_at_utc"]):
            raise ValueError("checkpoint was not locked before matrix")
        logs = [json.loads(line) for line in (directory / "train_log.jsonl").read_text().splitlines()]
        if min(logs, key=lambda r: r["validation_mae"])["epoch"] != selection["epoch"]:
            raise ValueError("checkpoint is not validation minimum")
        completion = json.loads((directory / "completed.json").read_text())
        if completion["held_out_evaluations_per_split"] != 1:
            raise ValueError("unexpected held-out evaluation count")
        if datetime.fromisoformat(completion["completed_at_utc"]) < datetime.fromisoformat(matrix["locked_at_utc"]):
            raise ValueError("evaluation completed before matrix lock")
        for name, digest in completion["files"].items():
            if Path(name).name != name or _sha256(directory / name) != digest:
                raise ValueError("completion hash mismatch")
        collected[(variant, seed)] = {}
        for split in ("validation", "test", "ood"):
            ids = data.indices(split)
            mean = np.load(directory / f"{split}_mean.npy", allow_pickle=False)
            variance_path = directory / f"{split}_variance.npy"
            expects_variance = variant not in ("no_uncertainty", "temporal_gru", "temporal_gnn")
            if variance_path.exists() != expects_variance:
                raise ValueError("variance artifact does not match variant")
            variance = np.load(variance_path, allow_pickle=False) if variance_path.exists() else None
            if mean.shape != data.states[ids].shape or not np.isfinite(mean).all():
                raise ValueError("bad prediction shape or value")
            if variance is not None and (variance.shape != mean.shape or
                    not np.isfinite(variance).all() or np.any(variance <= 0)):
                raise ValueError("invalid uncertainty")
            saved = json.loads((directory / f"{split}_metrics.json").read_text())
            recomputed = _error_metrics(mean, data.states[ids], data.mask[ids], data.manifest["state_fields"])
            recomputed["uncertainty"] = uncertainty_metrics(mean, variance, data.states[ids], protocol["interval_z"])
            recomputed["scenario_ids"] = [data.metadata["scenario_ids"][i] for i in ids]
            if saved != recomputed:
                raise ValueError("saved metrics differ from predictions")
            collected[(variant, seed)][split] = saved
    for variant in protocol["variants"]:
        for split in ("validation", "test", "ood"):
            for key in ("mae_overall", "rmse_overall"):
                values = [collected[(variant, s)][split][key] for s in protocol["training_seeds"]]
                actual = {"mean": float(np.mean(values)), "std_population": float(np.std(values))}
                if summary["variants"][variant][split][key] != actual:
                    raise ValueError("aggregate summary mismatch")
    return {"valid": True, "runs_verified": len(expected), "held_out_inference_rerun": False,
            "synthetic_only": True, "deployment_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

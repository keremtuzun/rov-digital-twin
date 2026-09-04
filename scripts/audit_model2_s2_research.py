"""Verify S2 saved evidence without retraining or re-opening model inference."""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

from oceansense.model2.evaluation import _error_metrics
from oceansense.model2.independent_mlp import _sha256
from oceansense.model2.research_experiment import uncertainty_metrics
from oceansense.model2.research_release import load_s2


def metrics_equal(saved, computed) -> bool:
    """Allow float32 reduction roundoff, never schema or identity changes.

    Artifact SHA256 checks remain byte-exact. This tolerance applies only to
    derived metrics recomputed on different CPU/NumPy implementations.
    """
    if type(saved) is not type(computed):
        return False
    if isinstance(saved, dict):
        return saved.keys() == computed.keys() and all(
            metrics_equal(saved[key], computed[key]) for key in saved
        )
    if isinstance(saved, list):
        return len(saved) == len(computed) and all(
            metrics_equal(a, b) for a, b in zip(saved, computed)
        )
    if isinstance(saved, float):
        return (math.isfinite(saved) and math.isfinite(computed)
                and math.isclose(saved, computed, rel_tol=1e-6, abs_tol=1e-8))
    return saved == computed


def audit(root: Path) -> dict:
    protocol = json.loads((root / "configs/model2/s2_research_protocol.json").read_text())
    data = load_s2(root, protocol)
    output = root / "reports/model2/s2_research_v0"
    if json.loads((output / "protocol.json").read_text()) != protocol:
        raise ValueError("experiment protocol mismatch")
    environment = json.loads((output / "environment.json").read_text())
    if set(environment["source_sha256"]) != {"evidence_memory.py", "research_experiment.py"}:
        raise ValueError("incomplete training source inventory")
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
    if (summary.get("protocol_id") != protocol["protocol_id"] or
            summary.get("synthetic_only") is not True or
            set(summary["variants"]) != set(protocol["variants"])):
        raise ValueError("invalid summary identity or scope")
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
        expects_variance = variant not in ("no_uncertainty", "temporal_gru", "temporal_gnn")
        expected_files = {"checkpoint.pt", "selected_checkpoint.json", "train_log.jsonl"}
        for split in ("validation", "test", "ood"):
            expected_files.update({f"{split}_mean.npy", f"{split}_metrics.json"})
            if expects_variance:
                expected_files.add(f"{split}_variance.npy")
        if set(completion["files"]) != expected_files:
            raise ValueError("incomplete or unexpected completion inventory")
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
            if variance_path.exists() != expects_variance:
                raise ValueError("variance artifact does not match variant")
            variance = np.load(variance_path, allow_pickle=False) if variance_path.exists() else None
            if (mean.shape != data.states[ids].shape or not np.isfinite(mean).all()
                    or np.any(mean < 0) or np.any(mean > 1)):
                raise ValueError("bad prediction shape or value")
            if variance is not None and (variance.shape != mean.shape or
                    not np.isfinite(variance).all() or np.any(variance <= 0)):
                raise ValueError("invalid uncertainty")
            saved = json.loads((directory / f"{split}_metrics.json").read_text())
            recomputed = _error_metrics(mean, data.states[ids], data.mask[ids], data.manifest["state_fields"])
            recomputed["uncertainty"] = uncertainty_metrics(mean, variance, data.states[ids], protocol["interval_z"])
            recomputed["scenario_ids"] = [data.metadata["scenario_ids"][i] for i in ids]
            if not metrics_equal(saved, recomputed):
                raise ValueError(f"saved metrics differ from predictions: {variant}/{seed}/{split}")
            collected[(variant, seed)][split] = saved
    for variant in protocol["variants"]:
        if set(summary["variants"][variant]) != {"validation", "test", "ood"}:
            raise ValueError("invalid summary split inventory")
        for split in ("validation", "test", "ood"):
            values = [collected[(variant, s)][split] for s in protocol["training_seeds"]]

            def stats(numbers):
                return {"mean": float(np.mean(numbers)), "std_population": float(np.std(numbers))}

            actual = {}
            for key in ("mae_overall", "rmse_overall"):
                actual[key] = stats([v[key] for v in values])
            actual["unobserved_mae"] = stats([v["unobserved_node_error"]["mae"] for v in values])
            if values[0]["uncertainty"]["available"]:
                actual["uncertainty"] = {
                    key: stats([v["uncertainty"][key] for v in values])
                    for key in ("gaussian_nll", "empirical_coverage", "mean_interval_width")
                }
            if not metrics_equal(summary["variants"][variant][split], actual):
                raise ValueError("aggregate summary mismatch")
    return {"valid": True, "runs_verified": len(expected), "held_out_inference_rerun": False,
            "synthetic_only": True, "deployment_authorized": False,
            "audit_scope": "Saved research artifact integrity, not model qualification",
            "uncertainty_calibrated": False,
            "full_model_ood_coverage": summary["variants"]["full"]["ood"]["uncertainty"]["empirical_coverage"]["mean"],
            "usage_restriction": "Research only; do not use for structural safety or vehicle control"}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

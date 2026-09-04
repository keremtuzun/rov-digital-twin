"""Audit the extended Model 2 search without reloading checkpoints."""
import json
import math
from pathlib import Path

import numpy as np

from oceansense.local_restart import conformal_quantile, digest


def audit(root):
    protocol_path = root / "configs/model2_extended_v1.json"
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    data_path = root / "data" / protocol["experiment_id"]
    environment = json.loads((output / "environment.json").read_text())
    if environment["source_sha256"] != digest(root / "src/oceansense/model2_extended.py"):
        raise ValueError("training source changed")
    if environment["protocol_sha256"] != digest(protocol_path):
        raise ValueError("protocol changed")
    manifest = json.loads((data_path / "manifest.json").read_text())
    if not manifest["synthetic_only"] or manifest["real_world_validation"]:
        raise ValueError("invalid dataset claim boundary")
    for record in manifest["records"]:
        if record["groups"] != protocol["splits"][record["split"]] or \
                digest(data_path / f"{record['split']}.npz") != record["sha256"]:
            raise ValueError("dataset artifact mismatch")
    completion = json.loads((output / "completed.json").read_text())
    files = {p.relative_to(output).as_posix() for p in output.rglob("*")
             if p.is_file() and p.name != "completed.json"}
    if files != set(completion["files"]) or completion["heldout_evaluations"] != 1:
        raise ValueError("completion inventory mismatch")
    for name, sha in completion["files"].items():
        if digest(output / name) != sha:
            raise ValueError("artifact checksum mismatch")
    matrix = json.loads((output / "matrix_locked.json").read_text())
    runs = matrix["runs"]
    expected = {(c["name"], s) for c in protocol["candidates"] for s in protocol["training_seeds"]}
    if {(r["candidate"], r["seed"]) for r in runs} != expected or len(runs) != len(expected):
        raise ValueError("incomplete training matrix")
    for row in runs:
        directory = output / row["candidate"] / str(row["seed"])
        history = json.loads((directory / "history.json").read_text())
        best = min(history, key=lambda r: r["validation_mae"])
        if best["epoch"] != row["epoch"] or best["validation_mae"] != row["validation_mae"] or \
                digest(directory / "checkpoint.pt") != row["sha256"]:
            raise ValueError("invalid checkpoint selection")
    means = {c["name"]: float(np.mean([r["validation_mae"] for r in runs
                                       if r["candidate"] == c["name"]])) for c in protocol["candidates"]}
    rounds, best, stale = [], math.inf, 0
    for start in range(0, len(protocol["candidates"]), 2):
        value = min(means[c["name"]] for c in protocol["candidates"][start:start + 2])
        improved = best - value >= protocol["minimum_improvement"]
        stale = 0 if improved else stale + 1
        best = min(best, value)
        rounds.append({"round": start // 2 + 1, "best_mae_so_far": best,
                       "meaningful_improvement": improved})
    selection = {"selected": min(means, key=means.get), "validation_mae": means, "rounds": rounds,
                 "status": "bounded_architecture_plateau" if stale >= 2 else "budget_exhausted",
                 "global_optimum_proven": False, "physical_data_is_only_remaining_improvement": False}
    summary = json.loads((output / "summary.json").read_text())
    if matrix["selection"] != selection or summary["selection"] != selection:
        raise ValueError("selection mismatch")
    if summary["deployment_authorized"] or summary["physical_data_is_only_remaining_improvement"]:
        raise ValueError("invalid readiness claim")
    for split in ("calibration", "test", "ood"):
        data = np.load(data_path / f"{split}.npz", allow_pickle=False)
        prediction = np.load(output / f"{split}_predictions.npy", allow_pickle=False)
        if prediction.shape != data["states"].shape or not np.isfinite(prediction).all():
            raise ValueError("invalid prediction artifact")
        error = np.abs(prediction.astype(np.float64) - data["states"])
        scores = error.reshape(len(error), -1).max(1)
        if split == "calibration":
            quantile = conformal_quantile(scores)
        lower, upper = np.maximum(0, prediction - quantile), np.minimum(1, prediction + quantile)
        derived = {"mae": float(error.mean()), "rmse": float(np.sqrt((error ** 2).mean())),
            "unobserved_mae": float(error[data["masks"] == 0].mean()),
            "simultaneous_trajectory_coverage": float(np.mean(scores <= quantile)),
            "mean_interval_width": float((upper - lower).mean())}
        for key, value in derived.items():
            if not math.isclose(value, summary[split][key], rel_tol=1e-6, abs_tol=1e-8):
                raise ValueError("derived metric mismatch")
    if quantile != summary["calibration_quantile"]:
        raise ValueError("calibration quantile mismatch")
    return {"valid": True, "runs_verified": len(expected), "heldout_inference_rerun": False,
            "synthetic_only": True, "deployment_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

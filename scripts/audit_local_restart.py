"""Read-only evidence audit. Does not load checkpoints or rerun held-out inference."""
from pathlib import Path
import argparse
import json
import math

import numpy as np

from oceansense.local_restart import classification_metrics, conformal_quantile, digest, search_summary


def close(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-8)
    return a == b


def audit(root, experiment_id="local-synthetic-restart-v1"):
    output = root / "reports" / experiment_id
    data_dir = root / "data" / experiment_id
    protocol = json.loads((output / "protocol.json").read_text())
    environment = json.loads((output / "environment.json").read_text())
    if digest(root / "configs/restart_local_v1.json") != environment["protocol_sha256"]:
        raise ValueError("source protocol hash mismatch")
    if protocol != json.loads((root / "configs/restart_local_v1.json").read_text()):
        raise ValueError("protocol mismatch")
    if digest(root / "src/oceansense/local_restart.py") != environment["source_sha256"]:
        raise ValueError("training source changed")
    manifest = json.loads((data_dir / "manifest.json").read_text())
    if manifest["synthetic_only"] is not True or manifest["human_reviewed"] is not False:
        raise ValueError("invalid dataset claim boundary")
    seen = set()
    if (len(manifest["records"]) != len(protocol["splits"]) or
            {r["split"] for r in manifest["records"]} != set(protocol["splits"])):
        raise ValueError("split inventory mismatch")
    for record in manifest["records"]:
        if digest(data_dir / f"{record['split']}.npz") != record["sha256"]:
            raise ValueError("dataset hash mismatch")
        if record["groups"] != protocol["splits"][record["split"]]:
            raise ValueError("dataset group count mismatch")
        for name in ("scene_seeds", "scenario_seeds"):
            seeds = record[name]
            if len(seeds) != record["groups"] or len(set(seeds)) != len(seeds) or seen.intersection(seeds):
                raise ValueError("data group leakage")
            seen.update(seeds)
    completion = json.loads((output / "completed.json").read_text())
    expected_files = {p.relative_to(output).as_posix() for p in output.rglob("*")
                      if p.is_file() and p.name != "completed.json"}
    if set(completion["files"]) != expected_files or completion["heldout_evaluations"] != 1:
        raise ValueError("completion inventory mismatch")
    for name, sha in completion["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path) != sha:
            raise ValueError("artifact checksum mismatch")
    matrix = json.loads((output / "matrix_locked.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    if summary["synthetic_only"] is not True or summary["deployment_authorized"] is not False:
        raise ValueError("invalid experiment claim boundary")
    verified = 0
    for model_id in ("model1", "model2"):
        runs = matrix["runs"][model_id]
        expected = {(c["name"], seed) for c in protocol[model_id]["candidates"]
                    for seed in protocol["training_seeds"]}
        if {(r["candidate"], r["seed"]) for r in runs} != expected or len(runs) != len(expected):
            raise ValueError("training matrix incomplete")
        for r in runs:
            directory = output / model_id / r["candidate"] / str(r["seed"])
            if r != json.loads((directory / "selection.json").read_text()):
                raise ValueError("run selection changed after lock")
            if r["sha256"] != digest(directory / "checkpoint.pt"):
                raise ValueError("selected checkpoint hash mismatch")
            history = json.loads((directory / "history.json").read_text())
            best = max(history, key=lambda row: row["validation_score"])
            if best["epoch"] != r["epoch"] or best["validation_score"] != r["validation_score"]:
                raise ValueError("checkpoint not selected by validation")
            if r["locked_at"] > matrix["locked_at"]:
                raise ValueError("checkpoint locked after selection")
            verified += 1
        selection = search_summary(runs, protocol[model_id]["candidates"], protocol[model_id]["minimum_improvement"])
        if selection != matrix["selection"][model_id] or selection != summary["selection"][model_id]:
            raise ValueError("selection or plateau claim mismatch")
        for split in ("calibration", "test", "ood"):
            data = np.load(data_dir / f"{split}.npz", allow_pickle=False)
            prediction = np.load(output / f"{model_id}_{split}_predictions.npy", allow_pickle=False)
            if not np.isfinite(prediction).all() or np.any(prediction < 0) or np.any(prediction > 1):
                raise ValueError("invalid predictions")
            groups = protocol["splits"][split]
            if model_id == "model1":
                target = data["labels"].reshape(-1)
                if prediction.shape != (len(target), len(protocol[model_id]["classes"])):
                    raise ValueError("visual prediction shape mismatch")
                if not np.allclose(prediction.sum(-1), 1, atol=1e-6):
                    raise ValueError("invalid probabilities")
                scores = (1 - prediction[np.arange(len(target)), target]).reshape(groups, -1).max(1)
                if split == "calibration":
                    quantile = conformal_quantile(scores)
                sets = (1 - prediction) <= quantile
                metrics = classification_metrics(prediction, target)
                metrics.update(scene_set_coverage=float(np.mean(scores <= quantile)),
                               mean_set_size=float(sets.sum(1).mean()),
                               singleton_fraction=float(np.mean(sets.sum(1) == 1)))
            else:
                if prediction.shape != data["states"].shape:
                    raise ValueError("structural prediction shape mismatch")
                errors = np.abs(prediction.astype(np.float64) - data["states"])
                scores = errors.reshape(groups, -1).max(1)
                if split == "calibration":
                    quantile = conformal_quantile(scores)
                lower, upper = np.maximum(0, prediction - quantile), np.minimum(1, prediction + quantile)
                metrics = {"mae": float(errors.mean()), "rmse": float(np.sqrt((errors ** 2).mean())),
                           "unobserved_mae": float(errors[data["masks"] == 0].mean()),
                           "simultaneous_trajectory_coverage": float(np.mean(scores <= quantile)),
                           "mean_interval_width": float((upper - lower).mean())}
            if not close(metrics, summary["models"][model_id][split]):
                raise ValueError(f"derived metric mismatch: {model_id}/{split}")
        if quantile != summary["models"][model_id]["calibration_quantile"]:
            raise ValueError("calibration changed")
    return {"valid": True, "runs_verified": verified, "heldout_inference_rerun": False,
            "synthetic_only": True, "deployment_authorized": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="local-synthetic-restart-v1")
    args = parser.parse_args()
    print(json.dumps(audit(Path(__file__).resolve().parents[1], args.experiment_id), indent=2))

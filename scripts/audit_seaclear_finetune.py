"""Audit real-image adaptation evidence without rerunning inference."""
import json
import math
from pathlib import Path

import numpy as np

from oceansense.local_restart import digest
from oceansense.seaclear_native import metrics


def audit(root):
    protocol_path = root / "configs/seaclear_finetune_v1.json"
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    parent = root / "reports" / protocol["parent_experiment"]
    environment = json.loads((output / "environment.json").read_text())
    if environment["source_sha256"] != digest(root / "src/oceansense/seaclear_finetune.py"):
        raise ValueError("fine-tuning source changed")
    if environment["protocol_sha256"] != digest(protocol_path):
        raise ValueError("fine-tuning protocol changed")
    if environment["parent_completed_sha256"] != digest(parent / "completed.json"):
        raise ValueError("parent experiment changed")
    completion = json.loads((output / "completed.json").read_text())
    files = {p.relative_to(output).as_posix() for p in output.rglob("*")
             if p.is_file() and p.name != "completed.json"}
    if set(completion["files"]) != files or completion["heldout_evaluations"] != 1:
        raise ValueError("completion inventory mismatch")
    for name, sha in completion["files"].items():
        if digest(output / name) != sha:
            raise ValueError("artifact checksum mismatch")
    matrix = json.loads((output / "matrix_locked.json").read_text())
    expected = {(c["name"], s) for c in protocol["candidates"] for s in protocol["training_seeds"]}
    runs = matrix["runs"]
    if {(r["candidate"], r["seed"]) for r in runs} != expected or len(runs) != len(expected):
        raise ValueError("incomplete fine-tuning matrix")
    for row in runs:
        directory = output / row["candidate"] / str(row["seed"])
        history = json.loads((directory / "history.json").read_text())
        best = max(history, key=lambda r: r["validation_score"])
        if (row["epoch"] != best["epoch"] or row["validation_score"] != best["validation_score"]
                or row["sha256"] != digest(directory / "checkpoint.pt")):
            raise ValueError("invalid fine-tuning checkpoint selection")
    parent_scores = json.loads((parent / "summary.json").read_text())["selection"]["validation_scores"]
    previous, stale, rounds, means = max(parent_scores.values()), 0, [], {}
    for candidate in protocol["candidates"]:
        value = float(np.mean([r["validation_score"] for r in runs if r["candidate"] == candidate["name"]]))
        means[candidate["name"]] = value
        improved = value - previous >= protocol["minimum_improvement"]
        stale = 0 if improved else stale + 1
        previous = max(previous, value)
        rounds.append({"candidate": candidate["name"], "best_score_so_far": previous,
                       "meaningful_improvement": improved})
    selection = {"selected": max(means, key=means.get), "validation_scores": means, "rounds": rounds,
                 "status": "bounded_finetuning_plateau" if stale >= 2 else "budget_exhausted",
                 "global_optimum_proven": False, "physical_data_is_only_remaining_improvement": False}
    summary = json.loads((output / "summary.json").read_text())
    if summary["selection"] != selection or matrix["selection"] != selection:
        raise ValueError("fine-tuning search result mismatch")
    if summary["canonical_model1_ready"] or summary["deployment_authorized"]:
        raise ValueError("unsupported readiness claim")
    threshold = json.loads((output / "threshold_locked.json").read_text())["threshold"]
    source = json.loads((parent / "dataset.json").read_text())
    targets = np.load(parent / "features.npz", allow_pickle=False)["targets"]
    for split in ("calibration", "test"):
        ids = [i for i, row in enumerate(source["records"]) if row["split"] == split]
        prediction = np.load(output / f"{split}_predictions.npy", allow_pickle=False)
        if not np.isfinite(prediction).all() or prediction.shape != targets[ids].shape:
            raise ValueError("invalid fine-tuned predictions")
        expected_metrics = metrics(prediction, targets[ids], threshold)
        actual = summary[split]
        for key in expected_metrics:
            left, right = expected_metrics[key], actual[key]
            if isinstance(left, float):
                if not math.isclose(left, right, rel_tol=1e-6, abs_tol=1e-8):
                    raise ValueError("fine-tuned metrics mismatch")
            elif left != right:
                raise ValueError("fine-tuned metrics mismatch")
    return {"valid": True, "runs_verified": len(expected), "heldout_inference_rerun": False,
            "canonical_model1_ready": False, "deployment_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

"""Audit native-label SeaClear research without repeating test inference."""
import json
from pathlib import Path

import numpy as np

from oceansense.local_restart import digest, search_summary
from oceansense.seaclear_native import metrics


def audit(root):
    protocol_path = root / "configs/seaclear_native_v1.json"
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    completion = json.loads((output / "completed.json").read_text())
    actual_files = {p.relative_to(output).as_posix() for p in output.rglob("*")
                    if p.is_file() and p.name != "completed.json"}
    if actual_files != set(completion["files"]) or completion["heldout_evaluations"] != 1:
        raise ValueError("incomplete artifact inventory")
    for name, sha in completion["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path) != sha:
            raise ValueError("artifact hash mismatch")
    environment = json.loads((output / "environment.json").read_text())
    if environment["source_sha256"] != digest(root / "src/oceansense/seaclear_native.py"):
        raise ValueError("training source changed")
    if environment["protocol_sha256"] != digest(protocol_path):
        raise ValueError("protocol changed")
    dataset = json.loads((output / "dataset.json").read_text())
    rows = dataset["records"]
    if len({r["sha256"] for r in rows}) != len(rows):
        raise ValueError("duplicate image leakage")
    for row in rows:
        if row["site"] not in protocol["sites"][row["split"]]:
            raise ValueError("site split leakage")
        if digest(Path(row["path"])) != row["sha256"]:
            raise ValueError("raw source image changed")
    matrix = json.loads((output / "matrix_locked.json").read_text())
    expected = {(c["name"], seed) for c in protocol["candidates"] for seed in protocol["training_seeds"]}
    if {(r["candidate"], r["seed"]) for r in matrix["runs"]} != expected or len(matrix["runs"]) != len(expected):
        raise ValueError("incomplete training matrix")
    for row in matrix["runs"]:
        directory = output / row["candidate"] / str(row["seed"])
        history = json.loads((directory / "history.json").read_text())
        best = max(history, key=lambda r: r["validation_score"])
        if (best["epoch"] != row["epoch"] or best["validation_score"] != row["validation_score"]
                or digest(directory / "checkpoint.pt") != row["sha256"]):
            raise ValueError("checkpoint selection mismatch")
    summary = json.loads((output / "summary.json").read_text())
    selection = search_summary(matrix["runs"], protocol["candidates"], protocol["minimum_improvement"])
    if summary["selection"] != selection or matrix["selection"] != selection:
        raise ValueError("search result mismatch")
    if summary["canonical_model1_ready"] or summary["deployment_authorized"]:
        raise ValueError("unsupported readiness claim")
    arrays = np.load(output / "features.npz", allow_pickle=False)
    train = np.asarray([i for i, r in enumerate(rows) if r["split"] == "train"])
    full_target = np.asarray([r["target"] for r in rows], dtype=np.float32)
    supported = np.flatnonzero(full_target[train].sum(0) >= protocol["minimum_training_positives"])
    np.testing.assert_array_equal(supported, arrays["supported"])
    np.testing.assert_array_equal(full_target[:, supported], arrays["targets"])
    locked = json.loads((output / "threshold_locked.json").read_text())
    for split in ("calibration", "test"):
        ids = np.asarray([i for i, r in enumerate(rows) if r["split"] == split])
        pred = np.load(output / f"{split}_predictions.npy", allow_pickle=False)
        if pred.shape != arrays["targets"][ids].shape or not np.isfinite(pred).all():
            raise ValueError("invalid prediction matrix")
        if split == "calibration":
            threshold = max([i / 10 for i in range(1, 10)],
                            key=lambda t: metrics(pred, arrays["targets"][ids], t)["micro_f1"])
            if threshold != locked["threshold"]:
                raise ValueError("threshold not calibration-selected")
        if metrics(pred, arrays["targets"][ids], locked["threshold"]) != summary[split]:
            raise ValueError("saved metrics differ from predictions")
    return {"valid": True, "runs_verified": len(expected), "source_images_verified": len(rows),
            "heldout_inference_rerun": False, "canonical_model1_ready": False,
            "deployment_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

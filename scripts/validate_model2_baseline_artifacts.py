"""Audit saved predictions/metrics without rerunning held-out model inference."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from oceansense.model2.evaluation import _error_metrics
from oceansense.model2.independent_mlp import _sha256, load_s1_data


def audit(root: Path) -> dict:
    config, data = load_s1_data(root / "configs/model2/s1_learned_baseline_eval.json", root)
    results = []
    for baseline in config["baselines"]:
        for seed in config["training_seeds"]:
            directory = root / config["artifacts"]["root"] / baseline / f"seed_{seed}"
            for name in config["artifacts"]["required_per_seed"].values():
                if not (directory / name).is_file():
                    raise ValueError(f"missing required artifact: {directory / name}")
            selected = json.loads((directory / "selected_checkpoint.json").read_text())
            if selected["baseline_name"] != baseline or selected["seed"] != seed:
                raise ValueError(f"selection identity mismatch: {directory}")
            for name, key in (("checkpoint.pt", "checkpoint_sha256"), ("config.json", "config_sha256")):
                if _sha256(directory / name) != selected[key]:
                    raise ValueError(f"artifact hash mismatch: {directory / name}")
            if json.loads((directory / "config.json").read_text()) != config:
                raise ValueError(f"config differs from frozen protocol: {directory}")
            if selected["test_used_for_selection"] or selected["ood_used_for_selection"]:
                raise ValueError("held-out data used for selection")
            logs = [json.loads(line) for line in (directory / "train_log.jsonl").read_text().splitlines()]
            minimum = min(logs, key=lambda row: row["validation_mae_overall"])
            if minimum["epoch"] != selected["selected_epoch"]:
                raise ValueError(f"checkpoint is not validation minimum: {directory}")
            inventory = json.loads((directory / "prediction_summary.json").read_text())["predictions"]
            if set(inventory) != {"validation", "test", "ood"}:
                raise ValueError("incomplete prediction inventory")
            for split in ("validation", "test", "ood"):
                entry = inventory[split]
                if entry["file"] != f"{split}_predictions.npy":
                    raise ValueError("unexpected prediction file")
                path = directory / entry["file"]
                if _sha256(path) != entry["sha256"]:
                    raise ValueError(f"prediction hash mismatch: {path}")
                indices = data.indices(split)
                if entry["scenario_ids"] != [data.metadata["scenario_ids"][i] for i in indices]:
                    raise ValueError("prediction scenario ordering differs")
                predictions = np.load(path, allow_pickle=False)
                if predictions.shape != data.states[indices].shape or not np.isfinite(predictions).all():
                    raise ValueError("invalid predictions")
                recomputed = _error_metrics(predictions, data.states[indices], data.mask[indices],
                                            data.manifest["state_fields"])
                saved = json.loads((directory / f"{split}_metrics.json").read_text())
                if saved["selected_checkpoint_sha256"] != selected["checkpoint_sha256"]:
                    raise ValueError("metrics refer to another checkpoint")
                for key, expected in recomputed.items():
                    if saved[key] != expected:
                        raise ValueError(f"saved metric differs: {directory}, {split}, {key}")
            marker = directory / "completed.json"
            if baseline in ("static_gnn", "temporal_gnn"):
                completion = json.loads(marker.read_text())
                for name, digest in completion["files"].items():
                    if Path(name).name != name or _sha256(directory / name) != digest:
                        raise ValueError("completion inventory mismatch")
            results.append({"baseline": baseline, "seed": seed, "verified": True})
    return {"valid": True, "synthetic_only": True, "held_out_inference_rerun": False,
            "verified_runs": results}


if __name__ == "__main__":
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))

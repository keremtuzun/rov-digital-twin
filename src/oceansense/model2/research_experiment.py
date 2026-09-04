"""S2 experiment: lock the entire matrix before held-out model inference."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .evidence_memory import EvidenceMemory
from .evaluation import _error_metrics
from .graph_baselines import GraphBaseline, load_adjacency
from .independent_mlp import (
    _sha256,
    _utc_now,
    _write_json,
    fit_train_preprocessing,
    transform_inputs,
)
from .research_release import build_s2, load_s2
from .temporal_gru import TemporalGRU, _save_checkpoint_atomic, seed_temporal_gru


def make_model(variant, protocol):
    width = protocol["hidden_dimension"]
    if variant == "temporal_gru":
        return TemporalGRU(7, width, 1, 5, 0.0)
    if variant == "temporal_gnn":
        return GraphBaseline(
            7,
            5,
            {
                "aggregation": "mean",
                "hidden_dimension": width,
                "message_passing_layers": 2,
                "dropout": 0.1,
                "temporal_layers": 1,
            },
            temporal=True,
        )
    return EvidenceMemory(width, variant)


def forward(model, features, graph, mask, confidence):
    if isinstance(model, TemporalGRU):
        return model(features), None
    if isinstance(model, GraphBaseline):
        return model(features, graph), None
    return model(features, graph, mask, confidence)


def loss_value(mean, variance, targets):
    error = (targets - mean).square()
    loss = (
        error.mean()
        if variance is None
        else (0.5 * (math.log(2 * math.pi) + variance.log() + error / variance)).mean()
    )
    if not torch.isfinite(loss):
        raise ValueError("non-finite research loss")
    return loss


def predict(model, features, graph, mask, confidence):
    model.eval()
    with torch.no_grad():
        mean, variance = forward(
            model,
            *(torch.from_numpy(x) for x in (features, graph, mask.astype(np.float32), confidence)),
        )
    result = mean.numpy()
    if not np.isfinite(result).all():
        raise ValueError("non-finite prediction")
    return result, variance.numpy() if variance is not None else None


def uncertainty_metrics(mean, variance, target, z):
    if variance is None:
        return {"available": False}
    squared = (target.astype(np.float64) - mean) ** 2
    half = z * np.sqrt(variance)
    return {
        "available": True,
        "calibration_fitted": False,
        "gaussian_nll": float((0.5 * (np.log(2 * np.pi * variance) + squared / variance)).mean()),
        "nominal_coverage": 0.9,
        "empirical_coverage": float((np.abs(target - mean) <= half).mean()),
        "mean_interval_width": float((2 * half).mean()),
        "interval_clipped_to_target_range": False,
    }


def train_one(data, graph, protocol, variant, seed, directory):
    directory.mkdir(parents=True, exist_ok=False)
    seed_temporal_gru(seed)
    train, val = data.indices("train"), data.indices("validation")
    prep = fit_train_preprocessing(data.observations[train], data.mask[train])
    train_x = transform_inputs(data.observations[train], data.mask[train], prep)
    val_x = transform_inputs(data.observations[val], data.mask[val], prep)
    model = make_model(variant, protocol)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=protocol["learning_rate"], weight_decay=protocol["weight_decay"]
    )
    tensors = [
        train_x,
        graph[train],
        data.mask[train].astype(np.float32),
        data.observations[train, ..., 5],
        data.states[train],
    ]
    loader = DataLoader(
        TensorDataset(*(torch.from_numpy(x) for x in tensors)),
        batch_size=protocol["batch_size"],
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
    )
    best, best_epoch, stale = float("inf"), 0, 0
    with (directory / "train_log.jsonl").open("w") as log:
        for epoch in range(1, protocol["maximum_epochs"] + 1):
            model.train()
            losses = []
            for features, adjacency, mask, confidence, target in loader:
                optimizer.zero_grad(set_to_none=True)
                mean, variance = forward(model, features, adjacency, mask, confidence)
                loss = loss_value(mean, variance, target)
                loss.backward()
                nn.utils.clip_grad_norm_(
                    model.parameters(), protocol["gradient_clip"], error_if_nonfinite=True
                )
                optimizer.step()
                losses.append(float(loss.detach()))
            mean, _ = predict(
                model, val_x, graph[val], data.mask[val], data.observations[val, ..., 5]
            )
            mae = float(np.abs(mean.astype(np.float64) - data.states[val]).mean())
            previous = best
            if mae < best:
                best, best_epoch = mae, epoch
                _save_checkpoint_atomic(
                    {
                        "variant": variant,
                        "seed": seed,
                        "model_state_dict": model.state_dict(),
                        "preprocessing": prep,
                        "protocol": protocol,
                    },
                    directory / "checkpoint.pt",
                )
            stale = 0 if previous - mae > protocol["min_delta"] else stale + 1
            log.write(
                json.dumps({"epoch": epoch, "loss": float(np.mean(losses)), "validation_mae": mae})
                + "\n"
            )
            log.flush()
            if stale >= protocol["patience"]:
                break
    selected = {
        "variant": variant,
        "seed": seed,
        "epoch": best_epoch,
        "validation_mae": best,
        "checkpoint_sha256": _sha256(directory / "checkpoint.pt"),
        "locked_at_utc": _utc_now(),
        "test_used_for_selection": False,
        "ood_used_for_selection": False,
    }
    _write_json(directory / "selected_checkpoint.json", selected)
    return selected


def run_experiment(root: Path, protocol_path: Path):
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports/model2/s2_research_v0"
    if output.exists():
        raise FileExistsError("S2 experiment already exists; refusing overwrite or held-out rerun")
    build_s2(root, protocol)
    data = load_s2(root, protocol)
    graph = load_adjacency(data)
    output.mkdir(parents=True)
    _write_json(output / "protocol.json", protocol)
    _write_json(
        output / "environment.json",
        {
            "torch": str(torch.__version__),
            "numpy": np.__version__,
            "device": "cpu",
            "threads": torch.get_num_threads(),
            "release_checksums_sha256": _sha256(data.release_dir / "checksums.json"),
            "protocol_sha256": _sha256(output / "protocol.json"),
            "source_sha256": {
                p.name: _sha256(p)
                for p in (Path(__file__), Path(__file__).with_name("evidence_memory.py"))
            },
        },
    )
    locked = []
    for variant in protocol["variants"]:
        for seed in protocol["training_seeds"]:
            print(f"Training S2 {variant} seed {seed}", flush=True)
            directory = output / variant / f"seed_{seed}"
            locked.append(train_one(data, graph, protocol, variant, seed, directory))
    _write_json(output / "matrix_locked.json", {"locked_at_utc": _utc_now(), "checkpoints": locked})
    # Entire model matrix is now locked. Held-out inference begins here, not before.
    results = []
    for selection in locked:
        variant, seed = selection["variant"], selection["seed"]
        directory = output / variant / f"seed_{seed}"
        if _sha256(directory / "checkpoint.pt") != selection["checkpoint_sha256"]:
            raise ValueError("checkpoint changed after matrix lock")
        checkpoint = torch.load(directory / "checkpoint.pt", weights_only=True)
        model = make_model(variant, protocol)
        model.load_state_dict(checkpoint["model_state_dict"])
        split_metrics = {}
        for split in ("validation", "test", "ood"):
            ids = data.indices(split)
            features = transform_inputs(
                data.observations[ids], data.mask[ids], checkpoint["preprocessing"]
            )
            mean, variance = predict(
                model, features, graph[ids], data.mask[ids], data.observations[ids, ..., 5]
            )
            np.save(directory / f"{split}_mean.npy", mean, allow_pickle=False)
            if variance is not None:
                np.save(directory / f"{split}_variance.npy", variance, allow_pickle=False)
            metrics = _error_metrics(
                mean, data.states[ids], data.mask[ids], data.manifest["state_fields"]
            )
            metrics["uncertainty"] = uncertainty_metrics(
                mean, variance, data.states[ids], protocol["interval_z"]
            )
            metrics["scenario_ids"] = [data.metadata["scenario_ids"][i] for i in ids]
            _write_json(directory / f"{split}_metrics.json", metrics)
            split_metrics[split] = metrics
        _write_json(
            directory / "completed.json",
            {
                "held_out_evaluations_per_split": 1,
                "completed_at_utc": _utc_now(),
                "files": {p.name: _sha256(p) for p in sorted(directory.iterdir())},
            },
        )
        results.append({"variant": variant, "seed": seed, "metrics": split_metrics})
    summary = {
        "protocol_id": protocol["protocol_id"],
        "synthetic_only": True,
        "claim_boundary": protocol["claim_boundary"],
        "variants": {},
    }
    for variant in protocol["variants"]:
        runs = [r for r in results if r["variant"] == variant]
        summary["variants"][variant] = {}
        for split in ("validation", "test", "ood"):
            values = [r["metrics"][split] for r in runs]

            def stats(numbers):
                return {"mean": float(np.mean(numbers)), "std_population": float(np.std(numbers))}

            metrics = {
                key: stats([v[key] for v in values]) for key in ("mae_overall", "rmse_overall")
            }
            metrics["unobserved_mae"] = stats([v["unobserved_node_error"]["mae"] for v in values])
            if values[0]["uncertainty"]["available"]:
                metrics["uncertainty"] = {
                    key: stats([v["uncertainty"][key] for v in values])
                    for key in ("gaussian_nll", "empirical_coverage", "mean_interval_width")
                }
            summary["variants"][variant][split] = metrics
    _write_json(output / "summary.json", summary)
    return summary

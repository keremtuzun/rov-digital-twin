"""Frozen S1 graph runs with locked selection and non-overwriting evidence artifacts."""

from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from .evaluation import _error_metrics
from .graph_baselines import GraphBaseline, load_adjacency, masked_mse
from .independent_mlp import (
    _aggregate_scalar,
    _failure_cases,
    _sha256,
    _utc_now,
    _write_json,
    fit_train_preprocessing,
    load_s1_data,
    transform_inputs,
)
from .temporal_gru import _device_for, _save_checkpoint_atomic, seed_temporal_gru

GRAPH_BASELINES = ("static_gnn", "temporal_gnn")


def predict(model, features, adjacency, device):
    model.eval()
    with torch.no_grad():
        result = (
            model(torch.from_numpy(features).to(device), torch.from_numpy(adjacency).to(device))
            .cpu()
            .numpy()
        )
    if not np.isfinite(result).all():
        raise ValueError("non-finite predictions")
    return result.astype(np.float32)


def run_graph_seed(config, config_path, data, adjacency, root, seed, baseline):
    if baseline not in GRAPH_BASELINES or seed not in config["training_seeds"]:
        raise ValueError("baseline/seed is not in the frozen graph contract")
    output = root / config["artifacts"]["root"] / baseline / f"seed_{seed}"
    output.mkdir(parents=True, exist_ok=False)
    required = config["artifacts"]["required_per_seed"]
    shutil.copyfile(config_path, output / required["config_copy"])
    bounds = config["training_bounds"]
    architecture = config["baseline_architecture_bounds"][baseline]
    seed_temporal_gru(seed, bounds["deterministic_algorithms"])
    device = _device_for(config)
    train, val = data.indices("train"), data.indices("validation")
    preprocessing = fit_train_preprocessing(data.observations[train], data.mask[train])
    train_x = transform_inputs(data.observations[train], data.mask[train], preprocessing)
    val_x = transform_inputs(data.observations[val], data.mask[val], preprocessing)
    model = GraphBaseline(
        train_x.shape[-1], data.states.shape[-1], architecture, temporal=baseline == "temporal_gnn"
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=bounds["learning_rate"], weight_decay=bounds["weight_decay"]
    )
    loader = DataLoader(
        TensorDataset(
            torch.from_numpy(train_x),
            torch.from_numpy(adjacency[train]),
            torch.from_numpy(data.states[train].astype(np.float32)),
            torch.from_numpy(data.mask[train]),
        ),
        batch_size=bounds["batch_size_scenarios"],
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
        num_workers=bounds["num_workers"],
    )
    checkpoint_path = output / required["checkpoint"]
    best, best_epoch, stale = float("inf"), 0, 0
    started = _utc_now()
    with (output / required["train_log"]).open("w") as log:
        for epoch in range(1, bounds["max_epochs"] + 1):
            model.train()
            losses = []
            for features, graph, targets, mask in loader:
                optimizer.zero_grad(set_to_none=True)
                loss = masked_mse(
                    model(features.to(device), graph.to(device)),
                    targets.to(device),
                    mask.to(device),
                )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), bounds["gradient_clip_norm"], error_if_nonfinite=True
                )
                optimizer.step()
                losses.append(float(loss.detach().cpu()))
            predictions = predict(model, val_x, adjacency[val], device)
            mae = float(np.abs(predictions.astype(np.float64) - data.states[val]).mean())
            previous = best
            improved = mae < best
            if improved:
                best, best_epoch = mae, epoch
                _save_checkpoint_atomic(
                    {
                        "baseline_name": baseline,
                        "seed": seed,
                        "epoch": epoch,
                        "model_state_dict": model.state_dict(),
                        "preprocessing": preprocessing,
                        "input_dim": train_x.shape[-1],
                        "output_dim": data.states.shape[-1],
                        "architecture": architecture,
                    },
                    checkpoint_path,
                )
            stale = 0 if previous - mae > bounds["early_stopping_min_delta"] else stale + 1
            log.write(
                json.dumps(
                    {
                        "epoch": epoch,
                        "validation_mae_overall": mae,
                        "train_masked_mean_squared_error": float(np.mean(losses)),
                        "selected_as_best": improved,
                    }
                )
                + "\n"
            )
            log.flush()
            if stale >= bounds["early_stopping_patience"]:
                break
    selected = {
        "baseline_name": baseline,
        "seed": seed,
        "selected_epoch": best_epoch,
        "validation_mae_overall": best,
        "selection_split": "validation",
        "selection_metric": "validation.mae_overall",
        "selection_direction": "minimize",
        "checkpoint_sha256": _sha256(checkpoint_path),
        "config_sha256": _sha256(output / required["config_copy"]),
        "graph_sha256": _sha256(data.release_dir / "structure_graph.json"),
        "preprocessing": preprocessing,
        "resolved_architecture": architecture,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "device": str(device),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "torch_version": str(torch.__version__),
        "started_at_utc": started,
        "checkpoint_locked_at_utc": _utc_now(),
        "test_used_for_selection": False,
        "ood_used_for_selection": False,
        "hidden_state_input": False,
        "uses_graph": True,
        "uses_future_observations": False,
        "synthetic_only": True,
    }
    _write_json(output / required["selected_checkpoint_metadata"], selected)
    # Only locked checkpoints can reach held-out inference. No test/OOD access above.
    model.load_state_dict(
        torch.load(checkpoint_path, map_location=device, weights_only=True)["model_state_dict"]
    )
    split_metrics, predictions_index, failures = {}, {}, []
    for split in ("validation", "test", "ood"):
        indices = data.indices(split)
        features = transform_inputs(data.observations[indices], data.mask[indices], preprocessing)
        predictions = predict(model, features, adjacency[indices], device)
        metrics = _error_metrics(
            predictions, data.states[indices], data.mask[indices], data.manifest["state_fields"]
        )
        metrics.update(
            {
                "baseline_name": baseline,
                "seed": seed,
                "split": split,
                "release_id": data.manifest["release_id"],
                "synthetic_only": True,
                "mask_coverage": float(data.mask[indices].mean()),
                "selected_checkpoint_sha256": selected["checkpoint_sha256"],
                "hidden_state_input": False,
                "uses_future_observations": False,
                "uses_graph": True,
                "classification_metrics": "not_computed_no_predeclared_weak_point_target",
                "uncertainty_metrics": "not_applicable_deterministic_output",
            }
        )
        split_metrics[split] = metrics
        _write_json(output / required[f"{split}_metrics"], metrics)
        prediction_path = output / f"{split}_predictions.npy"
        np.save(prediction_path, predictions, allow_pickle=False)
        predictions_index[split] = {
            "file": prediction_path.name,
            "sha256": _sha256(prediction_path),
            "shape": list(predictions.shape),
            "dtype": str(predictions.dtype),
            "scenario_ids": [data.metadata["scenario_ids"][i] for i in indices],
        }
        failures.extend(_failure_cases(predictions, data.states[indices], data, indices, split))
    _write_json(
        output / required["prediction_summary"],
        {
            "baseline_name": baseline,
            "seed": seed,
            "synthetic_only": True,
            "predictions": predictions_index,
        },
    )
    _write_json(
        output / required["failure_cases"],
        {
            "baseline_name": baseline,
            "seed": seed,
            "synthetic_only": True,
            "cases": failures,
        },
    )
    # Completion marker inventories outputs and is never written for an interrupted run.
    _write_json(
        output / "completed.json",
        {
            "final_test_evaluations": 1,
            "final_ood_evaluations": 1,
            "completed_at_utc": _utc_now(),
            "files": {p.name: _sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
        },
    )
    return {"seed": seed, "selected_checkpoint": selected, "metrics": split_metrics}


def run_graph_baseline(config_path: str | Path, repo_root: str | Path, baseline: str) -> dict:
    if baseline not in GRAPH_BASELINES:
        raise ValueError("unknown graph baseline")
    root, path = Path(repo_root).resolve(), Path(config_path).resolve()
    config, data = load_s1_data(path, root)
    output = root / config["artifacts"]["root"] / baseline
    if output.exists():
        raise FileExistsError(f"refusing to overwrite completed or partial run: {output}")
    if baseline == "temporal_gnn":
        prior = output.parent / "static_gnn" / "aggregate_summary.json"
        if not prior.is_file():
            raise ValueError("complete Static GNN before Temporal GNN")
    adjacency = load_adjacency(data)
    results = []
    for seed in config["training_seeds"]:
        print(f"Training {baseline} seed {seed}", flush=True)
        results.append(run_graph_seed(config, path, data, adjacency, root, seed, baseline))
    aggregate = {
        "baseline_name": baseline,
        "release_id": data.manifest["release_id"],
        "training_seeds": config["training_seeds"],
        "seed_count": len(results),
        "synthetic_only": True,
        "internal_comparison_evidence_only": True,
        "proprietary_model_included": False,
        "model1_status": "BLOCKED_NOT_FROZEN",
        "per_seed": [
            {
                "seed": r["seed"],
                "selected_epoch": r["selected_checkpoint"]["selected_epoch"],
                "checkpoint_sha256": r["selected_checkpoint"]["checkpoint_sha256"],
            }
            for r in results
        ],
        "aggregate_metrics": {},
    }
    for split in ("validation", "test", "ood"):
        metrics = aggregate["aggregate_metrics"][split] = {}
        for key in ("mae_overall", "rmse_overall", "mask_coverage"):
            metrics[key] = _aggregate_scalar([r["metrics"][split][key] for r in results])
        for key in (
            "per_state_dimension_mae",
            "per_state_dimension_rmse",
            "observed_node_error",
            "unobserved_node_error",
        ):
            fields = (
                data.manifest["state_fields"] if key.startswith("per_state") else ("mae", "rmse")
            )
            metrics[key] = {
                field: _aggregate_scalar([r["metrics"][split][key][field] for r in results])
                for field in fields
            }
    _write_json(output / "aggregate_summary.json", aggregate)
    return aggregate

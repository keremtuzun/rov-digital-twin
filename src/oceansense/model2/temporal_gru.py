"""Frozen-protocol causal Temporal GRU training and evaluation for synthetic S1."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .evaluation import _error_metrics
from .independent_mlp import (
    S1Data,
    fit_train_preprocessing,
    load_s1_data,
    transform_inputs,
)

BASELINE_NAME = "temporal_gru"
PREDICTION_FILES = {
    "validation": "validation_predictions.npy",
    "test": "test_predictions.npy",
    "ood": "ood_predictions.npy",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _save_checkpoint_atomic(payload: dict[str, Any], checkpoint_path: Path) -> None:
    """Avoid exposing a partially rewritten checkpoint on interrupted Windows saves."""
    temporary = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, checkpoint_path)


def seed_temporal_gru(seed: int, deterministic: bool = True) -> None:
    """Seed every configured RNG and request deterministic Torch execution."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = deterministic
    torch.use_deterministic_algorithms(deterministic)


def prepare_temporal_features(
    observations: np.ndarray,
    mask: np.ndarray,
    preprocessing: dict[str, Any],
) -> np.ndarray:
    """Build [scenario,time,node,observation+mask] causal sequence features."""
    return transform_inputs(observations, mask, preprocessing)


class TemporalGRU(nn.Module):
    """Shared causal GRU applied independently to every node sequence."""

    def __init__(
        self,
        input_dim: int,
        hidden_dimension: int,
        recurrent_layers: int,
        output_dim: int,
        dropout: float,
        bidirectional: bool = False,
    ) -> None:
        super().__init__()
        if bidirectional:
            raise ValueError("Temporal GRU must remain causal and unidirectional")
        effective_dropout = dropout if recurrent_layers > 1 else 0.0
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dimension,
            num_layers=recurrent_layers,
            batch_first=True,
            dropout=effective_dropout,
            bidirectional=False,
        )
        self.output_head = nn.Sequential(nn.Linear(hidden_dimension, output_dim), nn.Sigmoid())

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError("inputs must have shape [scenario,timestep,node,feature]")
        scenarios, timesteps, nodes, features = inputs.shape
        node_sequences = inputs.permute(0, 2, 1, 3).reshape(
            scenarios * nodes, timesteps, features
        )
        temporal_states, _ = self.gru(node_sequences)
        predictions = self.output_head(temporal_states)
        return predictions.reshape(scenarios, nodes, timesteps, -1).permute(0, 2, 1, 3)


def _metrics(
    predictions: np.ndarray,
    targets: np.ndarray,
    mask: np.ndarray,
    data: S1Data,
    split: str,
    seed: int,
) -> dict[str, Any]:
    result = _error_metrics(predictions, targets, mask, data.manifest["state_fields"])
    result.update({
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "seed": seed,
        "split": split,
        "release_id": data.manifest["release_id"],
        "synthetic_only": True,
        "number_of_scenarios": int(mask.shape[0]),
        "number_of_timesteps": int(mask.shape[1]),
        "number_of_nodes": int(mask.shape[2]),
        "number_of_timestep_nodes": int(mask.size),
        "mask_coverage": float(mask.mean()),
        "hidden_state_input": False,
        "uses_future_observations": False,
        "uses_graph": False,
        "classification_metrics": "not_computed_no_predeclared_weak_point_target",
        "uncertainty_metrics": "not_applicable_deterministic_output",
    })
    return result


def _predict(model: nn.Module, features: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        tensor = torch.from_numpy(features).to(device)
        return model(tensor).cpu().numpy().astype(np.float32)


def _failure_cases(
    predictions: np.ndarray,
    targets: np.ndarray,
    data: S1Data,
    indices: list[int],
    split: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    per_scenario = np.abs(predictions.astype(np.float64) - targets).mean(axis=(1, 2, 3))
    ranked = np.argsort(-per_scenario, kind="stable")[:limit]
    return [
        {
            "split": split,
            "scenario_id": data.metadata["scenario_ids"][indices[int(local_index)]],
            "mae_overall": float(per_scenario[local_index]),
        }
        for local_index in ranked
    ]


def _device_for(config: dict[str, Any]) -> torch.device:
    if config["training_bounds"]["device_policy"] != "cuda_if_available_else_cpu":
        raise ValueError("unsupported frozen device policy")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def temporal_gru_seed_dir(config: dict[str, Any], repo_root: Path, seed: int) -> Path:
    return repo_root / config["artifacts"]["root"] / BASELINE_NAME / f"seed_{seed}"


def checkpoint_selection_contract(config: dict[str, Any]) -> dict[str, Any]:
    selection = config["checkpoint_selection"]
    return {
        "selection_split": "validation",
        "selection_metric": selection["metric"],
        "selection_direction": selection["direction"],
        "test_used_for_selection": selection["selection_uses_test"],
        "ood_used_for_selection": selection["selection_uses_ood"],
    }


def run_seed(
    config: dict[str, Any],
    config_path: Path,
    data: S1Data,
    repo_root: Path,
    seed: int,
) -> dict[str, Any]:
    if seed not in config["training_seeds"]:
        raise ValueError("seed is not in the frozen training seed list")
    output = temporal_gru_seed_dir(config, repo_root, seed)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite completed or partial run: {output}")
    output.mkdir(parents=True)
    required = config["artifacts"]["required_per_seed"]
    config_copy = output / required["config_copy"]
    shutil.copyfile(config_path, config_copy)

    bounds = config["training_bounds"]
    architecture = config["baseline_architecture_bounds"][BASELINE_NAME]
    if architecture["uses_future_context"] or architecture["bidirectional"]:
        raise ValueError("frozen Temporal GRU architecture must remain causal")
    if architecture["uses_graph"]:
        raise ValueError("frozen Temporal GRU architecture cannot use graph neighbors")
    seed_temporal_gru(seed, bounds["deterministic_algorithms"])
    device = _device_for(config)

    train_indices = data.indices("train")
    validation_indices = data.indices("validation")
    train_observations = data.observations[train_indices]
    train_mask = data.mask[train_indices]
    preprocessing = fit_train_preprocessing(train_observations, train_mask)
    train_features = prepare_temporal_features(train_observations, train_mask, preprocessing)
    validation_features = prepare_temporal_features(
        data.observations[validation_indices], data.mask[validation_indices], preprocessing
    )

    model = TemporalGRU(
        input_dim=train_features.shape[-1],
        hidden_dimension=architecture["hidden_dimension"],
        recurrent_layers=architecture["recurrent_layers"],
        output_dim=data.states.shape[-1],
        dropout=architecture["dropout"],
        bidirectional=architecture["bidirectional"],
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=bounds["learning_rate"],
        weight_decay=bounds["weight_decay"],
    )
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(
            torch.from_numpy(train_features),
            torch.from_numpy(data.states[train_indices].astype(np.float32)),
            torch.from_numpy(train_mask.astype(np.float32)),
        ),
        batch_size=bounds["batch_size_scenarios"],
        shuffle=True,
        num_workers=bounds["num_workers"],
        generator=generator,
    )

    checkpoint_path = output / required["checkpoint"]
    log_path = output / required["train_log"]
    best_mae = float("inf")
    best_epoch = 0
    stale_epochs = 0
    started_at = _utc_now()
    with log_path.open("w", encoding="utf-8") as log:
        for epoch in range(1, bounds["max_epochs"] + 1):
            model.train()
            loss_sum = 0.0
            batch_count = 0
            for features, targets, mask in loader:
                features = features.to(device)
                targets = targets.to(device)
                mask = mask.to(device)
                optimizer.zero_grad(set_to_none=True)
                predictions = model(features)
                weights = mask[..., None].expand_as(predictions)
                if not weights.any():
                    raise ValueError("batch has no observed supervision")
                loss = ((predictions - targets).square() * weights).sum() / weights.sum()
                if not torch.isfinite(loss):
                    raise ValueError("non-finite training loss")
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), bounds["gradient_clip_norm"])
                optimizer.step()
                loss_sum += float(loss.detach().cpu())
                batch_count += 1

            validation_predictions = _predict(model, validation_features, device)
            validation_metrics = _metrics(
                validation_predictions,
                data.states[validation_indices],
                data.mask[validation_indices],
                data,
                "validation",
                seed,
            )
            validation_mae = validation_metrics["mae_overall"]
            previous_best = best_mae
            if validation_mae < best_mae:
                best_mae = validation_mae
                best_epoch = epoch
                _save_checkpoint_atomic({
                    "baseline_name": BASELINE_NAME,
                    "seed": seed,
                    "epoch": epoch,
                    "validation_mae_overall": best_mae,
                    "model_state_dict": model.state_dict(),
                    "preprocessing": preprocessing,
                    "input_dim": train_features.shape[-1],
                    "output_dim": data.states.shape[-1],
                    **architecture,
                }, checkpoint_path)
            significant_improvement = (
                previous_best - validation_mae > bounds["early_stopping_min_delta"]
            )
            stale_epochs = 0 if significant_improvement else stale_epochs + 1
            record = {
                "epoch": epoch,
                "train_masked_mean_squared_error": loss_sum / batch_count,
                "validation_mae_overall": validation_mae,
                "selected_as_best": validation_mae == best_mae,
            }
            log.write(json.dumps(record, sort_keys=True) + "\n")
            log.flush()
            if stale_epochs >= bounds["early_stopping_patience"]:
                break

    checkpoint_sha256 = _sha256(checkpoint_path)
    selection = checkpoint_selection_contract(config)
    selected = {
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "seed": seed,
        **selection,
        "selected_epoch": best_epoch,
        "validation_mae_overall": best_mae,
        "checkpoint_file": checkpoint_path.name,
        "checkpoint_sha256": checkpoint_sha256,
        "config_file": config_copy.name,
        "config_sha256": _sha256(config_copy),
        "preprocessing": preprocessing,
        "resolved_architecture": {
            "input_features": list(data.manifest["observation_fields"])
            + ["observation_mask"],
            "input_dimension": int(train_features.shape[-1]),
            "output_fields": list(data.manifest["state_fields"]),
            "node_local_shared_weights": True,
            "predicts_each_timestep": True,
            **architecture,
        },
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "device": str(device),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
        "started_at_utc": started_at,
        "checkpoint_locked_at_utc": _utc_now(),
        "final_test_evaluations": 1,
        "final_ood_evaluations": 1,
        "hidden_state_input": False,
        "uses_future_observations": False,
        "uses_graph": False,
        "synthetic_only": True,
    }
    _write_json(output / required["selected_checkpoint_metadata"], selected)

    # Checkpoint selection is now complete and locked. Test/OOD are first accessed below.
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    prediction_summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "seed": seed,
        "synthetic_only": True,
        "predictions": {},
    }
    failures: list[dict[str, Any]] = []
    split_metrics: dict[str, dict[str, Any]] = {}
    for split in ("validation", "test", "ood"):
        indices = data.indices(split)
        features = prepare_temporal_features(
            data.observations[indices], data.mask[indices], preprocessing
        )
        predictions = _predict(model, features, device)
        prediction_path = output / PREDICTION_FILES[split]
        np.save(prediction_path, predictions, allow_pickle=False)
        metrics = _metrics(
            predictions, data.states[indices], data.mask[indices], data, split, seed
        )
        metrics["selected_checkpoint_sha256"] = checkpoint_sha256
        split_metrics[split] = metrics
        prediction_summary["predictions"][split] = {
            "file": prediction_path.name,
            "sha256": _sha256(prediction_path),
            "shape": list(predictions.shape),
            "dtype": str(predictions.dtype),
            "scenario_ids": [data.metadata["scenario_ids"][index] for index in indices],
        }
        failures.extend(
            _failure_cases(predictions, data.states[indices], data, indices, split)
        )

    _write_json(output / required["validation_metrics"], split_metrics["validation"])
    _write_json(output / required["test_metrics"], split_metrics["test"])
    _write_json(output / required["ood_metrics"], split_metrics["ood"])
    _write_json(output / required["prediction_summary"], prediction_summary)
    _write_json(output / required["failure_cases"], {
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "seed": seed,
        "definition": "Ten highest-MAE synthetic scenarios per evaluated split.",
        "cases": failures,
        "synthetic_only": True,
    })
    return {"seed": seed, "selected_checkpoint": selected, "metrics": split_metrics}


def _load_completed_seed(
    config: dict[str, Any], data: S1Data, repo_root: Path, seed: int
) -> dict[str, Any]:
    """Audit and reuse a completed seed without repeating final test/OOD evaluation."""
    output = temporal_gru_seed_dir(config, repo_root, seed)
    required = config["artifacts"]["required_per_seed"]
    expected = set(required.values()) | set(PREDICTION_FILES.values())
    missing = sorted(name for name in expected if not (output / name).is_file())
    if missing:
        raise RuntimeError(
            f"incomplete Temporal GRU seed directory requires manual recovery: "
            f"seed={seed}, missing={missing}"
        )
    selected = json.loads(
        (output / required["selected_checkpoint_metadata"]).read_text(encoding="utf-8")
    )
    checkpoint_path = output / required["checkpoint"]
    checkpoint_sha256 = _sha256(checkpoint_path)
    if selected.get("baseline_name") != BASELINE_NAME or selected.get("seed") != seed:
        raise ValueError(f"selected checkpoint metadata identity mismatch for seed {seed}")
    if selected.get("checkpoint_sha256") != checkpoint_sha256:
        raise ValueError(f"selected checkpoint checksum mismatch for seed {seed}")
    config_copy = output / required["config_copy"]
    if (
        selected.get("config_sha256") != _sha256(config_copy)
        or json.loads(config_copy.read_text(encoding="utf-8")) != config
    ):
        raise ValueError(f"saved config mismatch for seed {seed}")
    prediction_summary = json.loads(
        (output / required["prediction_summary"]).read_text(encoding="utf-8")
    )
    if (
        prediction_summary.get("baseline_name") != BASELINE_NAME
        or prediction_summary.get("seed") != seed
        or set(prediction_summary.get("predictions", {})) != set(PREDICTION_FILES)
    ):
        raise ValueError(f"prediction inventory mismatch for seed {seed}")
    for split, metadata in prediction_summary.get("predictions", {}).items():
        if metadata.get("file") != PREDICTION_FILES[split]:
            raise ValueError(f"unexpected prediction filename for seed {seed}, split {split}")
        prediction_path = output / metadata["file"]
        if metadata.get("sha256") != _sha256(prediction_path):
            raise ValueError(f"prediction checksum mismatch for seed {seed}, split {split}")
    split_metrics = {
        split: json.loads((output / required[f"{split}_metrics"]).read_text(encoding="utf-8"))
        for split in ("validation", "test", "ood")
    }
    for split, metrics in split_metrics.items():
        if (
            metrics.get("baseline_name") != BASELINE_NAME
            or metrics.get("seed") != seed
            or metrics.get("split") != split
            or metrics.get("selected_checkpoint_sha256") != checkpoint_sha256
        ):
            raise ValueError(f"metric identity mismatch for seed {seed}, split {split}")
    if set(data.manifest["state_fields"]) != set(
        split_metrics["validation"]["per_state_dimension_mae"]
    ):
        raise ValueError(f"state metric schema mismatch for seed {seed}")
    return {"seed": seed, "selected_checkpoint": selected, "metrics": split_metrics}


def _aggregate_scalar(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(array.mean()),
        "std_population": float(array.std()),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def run_temporal_gru(config_path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = Path(config_path).resolve()
    config, data = load_s1_data(path, root)
    if BASELINE_NAME not in config["baselines"]:
        raise ValueError("Temporal GRU is absent from the frozen baseline list")
    aggregate_path = root / config["artifacts"]["root"] / BASELINE_NAME / "aggregate_summary.json"
    if aggregate_path.exists():
        raise FileExistsError(f"refusing to overwrite aggregate results: {aggregate_path}")
    results = []
    for seed in config["training_seeds"]:
        seed_dir = temporal_gru_seed_dir(config, root, seed)
        if seed_dir.exists():
            results.append(_load_completed_seed(config, data, root, seed))
        else:
            results.append(run_seed(config, path, data, root, seed))
    aggregate: dict[str, Any] = {
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "release_id": config["release"]["release_id"],
        "training_seeds": config["training_seeds"],
        "seed_count": len(results),
        "synthetic_only": True,
        "internal_comparison_evidence_only": True,
        "proprietary_model_included": False,
        "model1_status": "BLOCKED_NOT_FROZEN",
        "per_seed": [],
        "aggregate_metrics": {},
        "limitations": [
            "S1 contains synthetic simulator data only.",
            "The Temporal GRU is node-local and uses no structural neighbors.",
            "These results do not establish real-world performance or Model 2 superiority.",
        ],
    }
    for result in results:
        aggregate["per_seed"].append({
            "seed": result["seed"],
            "selected_epoch": result["selected_checkpoint"]["selected_epoch"],
            "checkpoint_sha256": result["selected_checkpoint"]["checkpoint_sha256"],
            "validation_mae_overall": result["metrics"]["validation"]["mae_overall"],
            "validation_rmse_overall": result["metrics"]["validation"]["rmse_overall"],
            "test_mae_overall": result["metrics"]["test"]["mae_overall"],
            "test_rmse_overall": result["metrics"]["test"]["rmse_overall"],
            "ood_mae_overall": result["metrics"]["ood"]["mae_overall"],
            "ood_rmse_overall": result["metrics"]["ood"]["rmse_overall"],
        })
    for split in ("validation", "test", "ood"):
        aggregate["aggregate_metrics"][split] = {
            metric: _aggregate_scalar(
                [result["metrics"][split][metric] for result in results]
            )
            for metric in ("mae_overall", "rmse_overall", "mask_coverage")
        }
        for metric in ("per_state_dimension_mae", "per_state_dimension_rmse"):
            aggregate["aggregate_metrics"][split][metric] = {
                field: _aggregate_scalar([
                    result["metrics"][split][metric][field] for result in results
                ])
                for field in data.manifest["state_fields"]
            }
        for group in ("observed_node_error", "unobserved_node_error"):
            aggregate["aggregate_metrics"][split][group] = {
                metric: _aggregate_scalar([
                    result["metrics"][split][group][metric] for result in results
                ])
                for metric in ("mae", "rmse")
            }
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(aggregate_path, aggregate)
    return aggregate

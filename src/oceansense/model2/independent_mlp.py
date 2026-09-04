"""Frozen-protocol Independent MLP training and evaluation for synthetic S1."""

from __future__ import annotations

import hashlib
import json
import platform
import random
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .baseline_config import load_baseline_eval_config
from .evaluation import _error_metrics

BASELINE_NAME = "independent_mlp"
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


@dataclass(frozen=True)
class S1Data:
    release_dir: Path
    manifest: dict[str, Any]
    metadata: dict[str, Any]
    splits: dict[str, Any]
    observations: np.ndarray
    mask: np.ndarray
    states: np.ndarray

    def indices(self, split: str) -> list[int]:
        ids = self.splits["splits"].get(split)
        if not ids:
            raise ValueError(f"split is missing or empty: {split}")
        lookup = {value: index for index, value in enumerate(self.metadata["scenario_ids"])}
        return [lookup[value] for value in ids]


def load_s1_data(config_path: Path, repo_root: Path) -> tuple[dict[str, Any], S1Data]:
    config = load_baseline_eval_config(
        config_path, validate_s1_release=True, repo_root=repo_root
    )
    release = repo_root / config["release"]["path"]
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if manifest["inference_inputs"] != config["feature_contract"]["allowed_input_files"]:
        raise ValueError("release inference inputs do not match the frozen feature contract")
    metadata = json.loads((release / "metadata.json").read_text(encoding="utf-8"))
    splits = json.loads((release / "splits.json").read_text(encoding="utf-8"))
    return config, S1Data(
        release_dir=release,
        manifest=manifest,
        metadata=metadata,
        splits=splits,
        observations=np.load(release / "observations.npy", allow_pickle=False),
        mask=np.load(release / "observation_mask.npy", allow_pickle=False),
        states=np.load(release / "states.npy", allow_pickle=False),
    )


def fit_train_preprocessing(observations: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    """Fit mean imputation and scaling using observed train entries only."""
    observed = observations[mask.astype(bool)]
    if observed.size == 0:
        raise ValueError("train split contains no observed inputs")
    mean = observed.astype(np.float64).mean(axis=0)
    scale = observed.astype(np.float64).std(axis=0)
    scale[scale < 1e-8] = 1.0
    return {
        "fit_split": "train",
        "imputation": "train_observed_mean",
        "normalization": "train_observed_zscore",
        "observation_mean": mean.tolist(),
        "observation_scale": scale.tolist(),
        "observed_row_count": int(observed.shape[0]),
    }


def transform_inputs(
    observations: np.ndarray, mask: np.ndarray, preprocessing: dict[str, Any]
) -> np.ndarray:
    mean = np.asarray(preprocessing["observation_mean"], dtype=np.float32)
    scale = np.asarray(preprocessing["observation_scale"], dtype=np.float32)
    normalized = (observations.astype(np.float32) - mean) / scale
    observed = mask.astype(bool)[..., None]
    normalized = np.where(observed, normalized, np.zeros_like(normalized))
    return np.concatenate((normalized, mask.astype(np.float32)[..., None]), axis=-1)


class IndependentMLP(nn.Module):
    """Node-local, current-timestep MLP with no temporal or graph access."""

    def __init__(self, input_dim: int, hidden_dimensions: list[int], output_dim: int,
                 dropout: float) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        previous = input_dim
        for width in hidden_dimensions:
            layers.extend((nn.Linear(previous, width), nn.ReLU(), nn.Dropout(dropout)))
            previous = width
        layers.extend((nn.Linear(previous, output_dim), nn.Sigmoid()))
        self.network = nn.Sequential(*layers)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.network(inputs)


def _seed_everything(seed: int, deterministic: bool) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(deterministic)


def _metrics(predictions: np.ndarray, targets: np.ndarray, mask: np.ndarray,
             data: S1Data, split: str, seed: int) -> dict[str, Any]:
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
        "classification_metrics": "not_computed_no_predeclared_weak_point_target",
        "uncertainty_metrics": "not_applicable_deterministic_output",
    })
    return result


def _predict(model: nn.Module, features: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        tensor = torch.from_numpy(features).to(device)
        return model(tensor).cpu().numpy().astype(np.float32)


def _failure_cases(predictions: np.ndarray, targets: np.ndarray, data: S1Data,
                   indices: list[int], split: str, limit: int = 10) -> list[dict[str, Any]]:
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


def run_seed(config: dict[str, Any], config_path: Path, data: S1Data, repo_root: Path,
             seed: int) -> dict[str, Any]:
    if seed not in config["training_seeds"]:
        raise ValueError("seed is not in the frozen training seed list")
    output = repo_root / config["artifacts"]["root"] / BASELINE_NAME / f"seed_{seed}"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite completed or partial run: {output}")
    output.mkdir(parents=True)
    config_copy = output / config["artifacts"]["required_per_seed"]["config_copy"]
    shutil.copyfile(config_path, config_copy)

    bounds = config["training_bounds"]
    architecture = config["baseline_architecture_bounds"][BASELINE_NAME]
    _seed_everything(seed, bounds["deterministic_algorithms"])
    device = _device_for(config)

    train_indices = data.indices("train")
    validation_indices = data.indices("validation")
    train_observations = data.observations[train_indices]
    train_mask = data.mask[train_indices]
    preprocessing = fit_train_preprocessing(train_observations, train_mask)
    train_features = transform_inputs(train_observations, train_mask, preprocessing)
    validation_features = transform_inputs(
        data.observations[validation_indices], data.mask[validation_indices], preprocessing
    )

    model = IndependentMLP(
        train_features.shape[-1], architecture["hidden_dimensions"],
        data.states.shape[-1], architecture["dropout"],
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=bounds["learning_rate"], weight_decay=bounds["weight_decay"]
    )
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(
            torch.from_numpy(train_features),
            torch.from_numpy(data.states[train_indices].astype(np.float32)),
            torch.from_numpy(train_mask.astype(np.float32)),
        ),
        batch_size=bounds["batch_size_scenarios"], shuffle=True,
        num_workers=bounds["num_workers"], generator=generator,
    )

    checkpoint_path = output / config["artifacts"]["required_per_seed"]["checkpoint"]
    log_path = output / config["artifacts"]["required_per_seed"]["train_log"]
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
                features, targets, mask = features.to(device), targets.to(device), mask.to(device)
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
                validation_predictions, data.states[validation_indices],
                data.mask[validation_indices], data, "validation", seed,
            )
            record = {
                "epoch": epoch,
                "train_masked_mean_squared_error": loss_sum / batch_count,
                "validation_mae_overall": validation_metrics["mae_overall"],
            }
            log.write(json.dumps(record, sort_keys=True) + "\n")
            log.flush()
            if best_mae - validation_metrics["mae_overall"] > bounds["early_stopping_min_delta"]:
                best_mae = validation_metrics["mae_overall"]
                best_epoch = epoch
                stale_epochs = 0
                torch.save({
                    "baseline_name": BASELINE_NAME,
                    "seed": seed,
                    "epoch": epoch,
                    "validation_mae_overall": best_mae,
                    "model_state_dict": model.state_dict(),
                    "preprocessing": preprocessing,
                    "input_dim": train_features.shape[-1],
                    "output_dim": data.states.shape[-1],
                    "hidden_dimensions": architecture["hidden_dimensions"],
                    "dropout": architecture["dropout"],
                }, checkpoint_path)
            else:
                stale_epochs += 1
                if stale_epochs >= bounds["early_stopping_patience"]:
                    break

    checkpoint_sha256 = _sha256(checkpoint_path)
    selected_path = output / config["artifacts"]["required_per_seed"][
        "selected_checkpoint_metadata"
    ]
    selected = {
        "schema_version": "1.0.0",
        "baseline_name": BASELINE_NAME,
        "seed": seed,
        "selection_split": "validation",
        "selection_metric": config["checkpoint_selection"]["metric"],
        "selection_direction": "minimize",
        "selected_epoch": best_epoch,
        "validation_mae_overall": best_mae,
        "checkpoint_file": checkpoint_path.name,
        "checkpoint_sha256": checkpoint_sha256,
        "config_file": config_copy.name,
        "config_sha256": _sha256(config_copy),
        "preprocessing": preprocessing,
        "resolved_architecture": {
            "input_features": list(data.manifest["observation_fields"]) + ["observation_mask"],
            "input_dimension": int(train_features.shape[-1]),
            "output_fields": list(data.manifest["state_fields"]),
            **architecture,
        },
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "device": str(device),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
        "started_at_utc": started_at,
        "checkpoint_locked_at_utc": _utc_now(),
        "test_used_for_selection": False,
        "ood_used_for_selection": False,
        "synthetic_only": True,
    }
    _write_json(selected_path, selected)

    # The checkpoint is now locked. Final test and OOD access occurs only below.
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    prediction_summary: dict[str, Any] = {
        "schema_version": "1.0.0", "baseline_name": BASELINE_NAME, "seed": seed,
        "synthetic_only": True, "predictions": {},
    }
    failures: list[dict[str, Any]] = []
    split_metrics: dict[str, dict[str, Any]] = {}
    for split in ("validation", "test", "ood"):
        indices = data.indices(split)
        features = transform_inputs(data.observations[indices], data.mask[indices], preprocessing)
        predictions = _predict(model, features, device)
        prediction_path = output / PREDICTION_FILES[split]
        np.save(prediction_path, predictions, allow_pickle=False)
        metrics = _metrics(predictions, data.states[indices], data.mask[indices], data, split, seed)
        metrics["selected_checkpoint_sha256"] = checkpoint_sha256
        split_metrics[split] = metrics
        prediction_summary["predictions"][split] = {
            "file": prediction_path.name,
            "sha256": _sha256(prediction_path),
            "shape": list(predictions.shape),
            "dtype": str(predictions.dtype),
            "scenario_ids": [data.metadata["scenario_ids"][index] for index in indices],
        }
        failures.extend(_failure_cases(predictions, data.states[indices], data, indices, split))

    required = config["artifacts"]["required_per_seed"]
    _write_json(output / required["validation_metrics"], split_metrics["validation"])
    _write_json(output / required["test_metrics"], split_metrics["test"])
    _write_json(output / required["ood_metrics"], split_metrics["ood"])
    _write_json(output / required["prediction_summary"], prediction_summary)
    _write_json(output / required["failure_cases"], {
        "schema_version": "1.0.0", "baseline_name": BASELINE_NAME, "seed": seed,
        "definition": "Ten highest-MAE synthetic scenarios per evaluated split.",
        "cases": failures, "synthetic_only": True,
    })
    return {"seed": seed, "selected_checkpoint": selected, "metrics": split_metrics}


def _aggregate_scalar(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(array.mean()), "std_population": float(array.std()),
        "minimum": float(array.min()), "maximum": float(array.max()),
    }


def run_independent_mlp(config_path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = Path(config_path).resolve()
    config, data = load_s1_data(path, root)
    if BASELINE_NAME not in config["baselines"]:
        raise ValueError("Independent MLP is absent from the frozen baseline list")
    aggregate_path = root / config["artifacts"]["aggregate_summary"]
    if aggregate_path.exists():
        raise FileExistsError(f"refusing to overwrite aggregate results: {aggregate_path}")
    results = [run_seed(config, path, data, root, seed) for seed in config["training_seeds"]]
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
            "The Independent MLP has no temporal history or graph-neighbor information.",
            "These results do not establish real-world performance or proprietary superiority.",
        ],
    }
    for result in results:
        aggregate["per_seed"].append({
            "seed": result["seed"],
            "selected_epoch": result["selected_checkpoint"]["selected_epoch"],
            "checkpoint_sha256": result["selected_checkpoint"]["checkpoint_sha256"],
            "validation_mae_overall": result["metrics"]["validation"]["mae_overall"],
            "test_mae_overall": result["metrics"]["test"]["mae_overall"],
            "test_rmse_overall": result["metrics"]["test"]["rmse_overall"],
            "ood_mae_overall": result["metrics"]["ood"]["mae_overall"],
            "ood_rmse_overall": result["metrics"]["ood"]["rmse_overall"],
        })
    for split in ("validation", "test", "ood"):
        aggregate["aggregate_metrics"][split] = {
            metric: _aggregate_scalar([result["metrics"][split][metric] for result in results])
            for metric in ("mae_overall", "rmse_overall", "mask_coverage")
        }
        for metric in ("per_state_dimension_mae", "per_state_dimension_rmse"):
            aggregate["aggregate_metrics"][split][metric] = {
                field: _aggregate_scalar([
                    result["metrics"][split][metric][field] for result in results
                ]) for field in data.manifest["state_fields"]
            }
        for group in ("observed_node_error", "unobserved_node_error"):
            aggregate["aggregate_metrics"][split][group] = {
                metric: _aggregate_scalar([
                    result["metrics"][split][group][metric] for result in results
                ]) for metric in ("mae", "rmse")
            }
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(aggregate_path, aggregate)
    return aggregate

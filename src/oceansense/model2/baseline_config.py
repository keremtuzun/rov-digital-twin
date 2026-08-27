"""Load and fail-closed validate the frozen S1 learned-baseline evaluation contract."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .release_validator import validate_release

ALLOWED_BASELINES = {
    "independent_mlp", "temporal_gru", "static_gnn", "temporal_gnn",
}
REQUIRED_METRICS = {
    "mae_overall", "rmse_overall", "per_state_dimension_mae",
    "per_state_dimension_rmse", "observed_node_error", "unobserved_node_error",
    "mask_coverage",
}
REQUIRED_NO_LEAKAGE_RULES = {
    "hidden_states_forbidden_as_inputs", "test_forbidden_for_selection",
    "ood_forbidden_for_selection", "lineages_must_not_cross_splits",
    "target_values_forbidden_in_split_assignment", "normalization_train_only",
    "imputation_train_only", "future_evidence_forbidden",
    "test_and_ood_tuning_forbidden",
}
EXPECTED_SPLIT_USAGE = {
    "train": "training_only",
    "validation": "hyperparameter_and_checkpoint_selection_only",
    "test": "final_in_distribution_evaluation_once_after_selection",
    "ood": "final_out_of_distribution_evaluation_once_after_selection",
}
REQUIRED_ARTIFACTS = {
    "config_copy", "train_log", "validation_metrics", "checkpoint",
    "selected_checkpoint_metadata", "test_metrics", "ood_metrics",
    "prediction_summary", "failure_cases",
}


def _safe_relative(path: str, *, expected: str | None = None) -> bool:
    candidate = PurePosixPath(path)
    return (
        bool(path)
        and not candidate.is_absolute()
        and ".." not in candidate.parts
        and "\\" not in path
        and (expected is None or path == expected)
    )


def validate_baseline_eval_config(config: dict[str, Any]) -> None:
    errors: list[str] = []
    if config.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if config.get("status") != "FROZEN_NO_TRAINING_PERFORMED":
        errors.append("status must preserve the no-training freeze boundary")

    release = config.get("release", {})
    if not _safe_relative(release.get("path", ""), expected="data/model2/s1_synthetic"):
        errors.append("release path must be data/model2/s1_synthetic")
    if release.get("release_id") != "twin2-s1-synthetic-v1":
        errors.append("unexpected S1 release_id")
    if not re.fullmatch(r"[0-9a-f]{64}", str(release.get("manifest_sha256", ""))):
        errors.append("release manifest_sha256 must be a lowercase SHA-256")
    if release.get("strict_validation_required") is not True:
        errors.append("strict S1 release validation must be required")
    if release.get("validator_requirement") != "require_synthetic_s1":
        errors.append("validator_requirement must be require_synthetic_s1")

    baselines = config.get("baselines")
    if not isinstance(baselines, list) or set(baselines) != ALLOWED_BASELINES or len(baselines) != 4:
        errors.append("baselines must contain exactly the four approved conventional names")
    seeds = config.get("training_seeds")
    if (
        not isinstance(seeds, list) or len(seeds) < 3 or len(seeds) != len(set(seeds))
        or not all(isinstance(seed, int) and seed > 0 for seed in seeds)
    ):
        errors.append("at least three unique positive integer training seeds are required")

    split_usage = config.get("split_usage", {})
    for split, expected in EXPECTED_SPLIT_USAGE.items():
        if split_usage.get(split) != expected:
            errors.append(f"invalid {split} split usage")
    for rule in (
        "no_test_tuning", "no_ood_tuning", "scenario_level", "lineage_disjoint",
        "target_independent_assignment", "final_evaluation_requires_locked_checkpoints",
    ):
        if split_usage.get(rule) is not True:
            errors.append(f"split usage rule must be true: {rule}")

    metrics = config.get("metrics", {})
    required_metrics = metrics.get("required")
    if not isinstance(required_metrics, list) or not REQUIRED_METRICS.issubset(required_metrics):
        errors.append("required metric list is incomplete")
    weak_point = metrics.get("weak_point", {})
    if weak_point.get("enabled") is not False or not weak_point.get("reason"):
        errors.append("weak-point metrics must remain disabled with a reason until target freeze")
    uncertainty = metrics.get("uncertainty", {})
    if uncertainty.get("enabled_when_model_outputs_uncertainty") is not True:
        errors.append("uncertainty metrics must be conditional on uncertainty output")

    selection = config.get("checkpoint_selection", {})
    if selection.get("metric") != "validation.mae_overall":
        errors.append("checkpoint selection metric must be validation.mae_overall")
    if selection.get("direction") != "minimize":
        errors.append("checkpoint selection direction must minimize")
    if selection.get("selection_uses_test") is not False:
        errors.append("checkpoint selection cannot use test")
    if selection.get("selection_uses_ood") is not False:
        errors.append("checkpoint selection cannot use OOD")
    if selection.get("test_evaluations_per_selected_checkpoint") != 1:
        errors.append("test may be evaluated exactly once per selected checkpoint")
    if selection.get("ood_evaluations_per_selected_checkpoint") != 1:
        errors.append("OOD may be evaluated exactly once per selected checkpoint")

    training = config.get("training_bounds", {})
    positive_fields = (
        "max_epochs", "early_stopping_patience", "batch_size_scenarios",
        "learning_rate", "gradient_clip_norm",
    )
    if any(not isinstance(training.get(field), (int, float)) or training[field] <= 0 for field in positive_fields):
        errors.append("training bounds must contain positive conservative limits")
    if training.get("optimizer") != "adamw" or training.get("loss") != "masked_mean_squared_error":
        errors.append("optimizer/loss contract must be adamw/masked_mean_squared_error")
    if training.get("deterministic_algorithms") is not True:
        errors.append("deterministic algorithms must be required")
    if training.get("device_policy") != "cuda_if_available_else_cpu":
        errors.append("device policy must preserve CUDA preference and CPU fallback")
    if training.get("cpu_fallback_required") is not True:
        errors.append("CPU fallback must be required")

    architectures = config.get("baseline_architecture_bounds", {})
    if set(architectures) != ALLOWED_BASELINES:
        errors.append("architecture bounds must cover exactly the approved baselines")
    feature_contract = config.get("feature_contract", {})
    if feature_contract.get("hidden_state_as_input") is not False:
        errors.append("hidden states cannot be model inputs")
    if feature_contract.get("allowed_input_files") != [
        "observations.npy", "observation_mask.npy", "structure_graph.json"
    ]:
        errors.append("allowed input file list must match the S1 inference contract")
    if feature_contract.get("target_file") != "states.npy":
        errors.append("states.npy must remain the target file")
    for field in ("normalization_fit_split", "imputation_fit_split"):
        if feature_contract.get(field) != "train":
            errors.append(f"{field} must be train")
    if feature_contract.get("future_observations_allowed") is not False:
        errors.append("future observations must be forbidden")

    artifacts = config.get("artifacts", {})
    if not _safe_relative(
        artifacts.get("root", ""), expected="reports/model2/s1_learned_baselines"
    ):
        errors.append("bad output artifact root")
    if artifacts.get("per_seed_directory") != "{root}/{baseline}/seed_{seed}":
        errors.append("per-seed directory template is invalid")
    per_seed = artifacts.get("required_per_seed", {})
    if set(per_seed) != REQUIRED_ARTIFACTS or any(
        not _safe_relative(str(path)) for path in per_seed.values()
    ):
        errors.append("required per-seed artifact names are incomplete or unsafe")
    if not _safe_relative(
        artifacts.get("aggregate_summary", ""),
        expected="reports/model2/s1_learned_baselines/aggregate_summary.json",
    ):
        errors.append("bad aggregate summary path")
    if artifacts.get("checkpoint_sha256_required") is not True:
        errors.append("checkpoint SHA-256 must be required")
    if artifacts.get("config_sha256_required") is not True:
        errors.append("config SHA-256 must be required")

    leakage = config.get("no_leakage_rules", {})
    if any(leakage.get(rule) is not True for rule in REQUIRED_NO_LEAKAGE_RULES):
        errors.append("all no-leakage rules must be present and true")
    claims = config.get("claim_boundaries", {})
    required_true = ("s1_is_synthetic", "internal_comparison_evidence_only")
    required_false = (
        "real_world_structural_performance_proven", "proprietary_superiority_proven",
        "proprietary_model_included",
    )
    if any(claims.get(field) is not True for field in required_true) or any(
        claims.get(field) is not False for field in required_false
    ):
        errors.append("claim boundaries are missing or unsafe")
    if claims.get("model1_status") != "BLOCKED_NOT_FROZEN":
        errors.append("Model 1 must remain BLOCKED_NOT_FROZEN")
    if errors:
        raise ValueError("invalid S1 learned-baseline eval config: " + "; ".join(errors))


def load_baseline_eval_config(
    path: str | Path,
    *,
    validate_s1_release: bool = False,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline evaluation config must be a JSON object")
    validate_baseline_eval_config(payload)
    if validate_s1_release:
        root = Path(repo_root) if repo_root is not None else config_path.resolve().parents[2]
        release_dir = root / payload["release"]["path"]
        report = validate_release(release_dir, require_synthetic_s1=True)
        if not report["valid"]:
            raise ValueError(f"strict S1 release validation failed: {report['errors']}")
        checksums = json.loads(
            (release_dir / "checksums.json").read_text(encoding="utf-8")
        )
        if checksums["files"]["manifest.json"] != payload["release"]["manifest_sha256"]:
            raise ValueError("frozen config manifest checksum does not match S1 release")
    return payload

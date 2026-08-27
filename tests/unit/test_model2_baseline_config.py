from __future__ import annotations

import json
from pathlib import Path

import pytest

from oceansense.model2.baseline_config import (
    load_baseline_eval_config,
    validate_baseline_eval_config,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "model2" / "s1_learned_baseline_eval.json"


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_valid_config_loads_and_strictly_validates_s1_release() -> None:
    config = load_baseline_eval_config(
        CONFIG_PATH,
        validate_s1_release=True,
        repo_root=ROOT,
    )

    assert config["config_id"] == "model2-s1-learned-baseline-eval-v1"


def test_missing_baseline_fails() -> None:
    config = _config()
    config["baselines"].remove("temporal_gnn")

    with pytest.raises(ValueError, match="four approved conventional names"):
        validate_baseline_eval_config(config)


def test_too_few_seeds_fails() -> None:
    config = _config()
    config["training_seeds"] = [2026201, 2026202]

    with pytest.raises(ValueError, match="at least three unique"):
        validate_baseline_eval_config(config)


def test_proprietary_model_baseline_name_fails() -> None:
    config = _config()
    config["baselines"][-1] = "proprietary_model2"

    with pytest.raises(ValueError, match="four approved conventional names"):
        validate_baseline_eval_config(config)


def test_missing_no_test_tuning_rule_fails() -> None:
    config = _config()
    del config["split_usage"]["no_test_tuning"]

    with pytest.raises(ValueError, match="no_test_tuning"):
        validate_baseline_eval_config(config)


def test_missing_no_ood_tuning_rule_fails() -> None:
    config = _config()
    del config["split_usage"]["no_ood_tuning"]

    with pytest.raises(ValueError, match="no_ood_tuning"):
        validate_baseline_eval_config(config)


def test_missing_required_metric_fails() -> None:
    config = _config()
    config["metrics"]["required"].remove("unobserved_node_error")

    with pytest.raises(ValueError, match="required metric list is incomplete"):
        validate_baseline_eval_config(config)


def test_bad_output_path_fails() -> None:
    config = _config()
    config["artifacts"]["root"] = "../outside-repository"

    with pytest.raises(ValueError, match="bad output artifact root"):
        validate_baseline_eval_config(config)


def test_release_path_is_recorded() -> None:
    config = load_baseline_eval_config(CONFIG_PATH)

    assert config["release"]["path"] == "data/model2/s1_synthetic"
    assert config["release"]["release_id"] == "twin2-s1-synthetic-v1"
    assert config["release"]["manifest_sha256"] == (
        "2adba7821141d673e12487cf1e8f4767fb777de828630b4b98019d5e302cec33"
    )

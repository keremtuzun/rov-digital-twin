import copy
from pathlib import Path

import pytest

from oceansense.model1_baseline_v2 import (
    BASELINE_ID,
    dataset_preflight,
    load_baseline_config,
    validate_baseline_config,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/model1_baseline_v2.yaml"


def test_locked_v2_config_is_valid_and_uses_new_artifact_names():
    config = load_baseline_config(CONFIG)
    assert config["model_version"] == BASELINE_ID
    assert config["training"]["selection_metric"] == "validation_macro_f1"
    assert config["training"]["early_stopping_patience"] == 5
    for task in ("domain", "condition"):
        checkpoint = config["artifacts"][task]["checkpoint"]
        assert BASELINE_ID in checkpoint
        assert not checkpoint.startswith("models/oceansense_")


def test_v2_config_rejects_architecture_or_label_drift():
    config = load_baseline_config(CONFIG)
    changed = copy.deepcopy(config)
    changed["architecture"] = "resnet50"
    with pytest.raises(ValueError, match="locked"):
        validate_baseline_config(changed)
    changed = copy.deepcopy(config)
    changed["labels"]["condition"].reverse()
    with pytest.raises(ValueError, match="label order"):
        validate_baseline_config(changed)


def test_preflight_fails_closed_when_approved_dataset_package_is_absent():
    report = dataset_preflight(CONFIG)
    assert report["ready"] is False
    assert report["model_version"] == BASELINE_ID
    assert any("missing required file" in error and "manifest.csv" in error for error in report["errors"])
    assert any("missing required file" in error and "labels.csv" in error for error in report["errors"])
    assert any("missing required file" in error and "split.csv" in error for error in report["errors"])
    assert any("missing activation approval" in error for error in report["errors"])
    assert any("manifest.csv" in error for error in report["errors"])

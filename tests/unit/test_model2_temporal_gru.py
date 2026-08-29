from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import torch

from oceansense.model2.independent_mlp import fit_train_preprocessing, load_s1_data
from oceansense.model2.temporal_gru import (
    TemporalGRU,
    _save_checkpoint_atomic,
    _metrics,
    checkpoint_selection_contract,
    prepare_temporal_features,
    seed_temporal_gru,
    temporal_gru_seed_dir,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/model2/s1_learned_baseline_eval.json"


def _model() -> TemporalGRU:
    return TemporalGRU(7, 64, 1, 5, 0.0, bidirectional=False)


def test_gru_model_output_and_sequence_shapes() -> None:
    model = _model()
    inputs = torch.zeros((2, 5, 10, 7))

    output = model(inputs)

    assert output.shape == (2, 5, 10, 5)
    assert model.gru.hidden_size == 64
    assert model.gru.num_layers == 1
    assert model.gru.bidirectional is False
    assert torch.all((0 <= output) & (output <= 1))


def test_temporal_features_include_mask_and_train_only_imputation() -> None:
    train = np.asarray([[[[1.0, 2.0]], [[3.0, 4.0]]]], dtype=np.float32)
    train_mask = np.ones((1, 2, 1), dtype=np.uint8)
    preprocessing = fit_train_preprocessing(train, train_mask)
    observations = np.asarray([[[[3.0, 4.0]], [[99.0, 99.0]]]], dtype=np.float32)
    mask = np.asarray([[[1], [0]]], dtype=np.uint8)

    features = prepare_temporal_features(observations, mask, preprocessing)

    assert preprocessing["fit_split"] == "train"
    assert features.shape == (1, 2, 1, 3)
    assert features[0, 0, 0, -1] == 1.0
    assert np.array_equal(features[0, 1, 0], np.asarray([0.0, 0.0, 0.0]))


def test_gru_is_causal_and_future_observations_do_not_change_past_outputs() -> None:
    seed_temporal_gru(2026201)
    model = _model().eval()
    first = torch.randn((1, 5, 2, 7))
    changed_future = first.clone()
    changed_future[:, 3:] = torch.randn_like(changed_future[:, 3:]) * 100

    with torch.no_grad():
        first_output = model(first)
        changed_output = model(changed_future)

    assert torch.equal(first_output[:, :3], changed_output[:, :3])


def test_seed_control_reproduces_initial_parameters() -> None:
    seed_temporal_gru(2026202)
    first = _model()
    seed_temporal_gru(2026202)
    second = _model()

    assert all(
        torch.equal(first_value, second_value)
        for first_value, second_value in zip(first.state_dict().values(), second.state_dict().values())
    )


def test_checkpoint_save_is_atomic_and_loadable(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"

    _save_checkpoint_atomic({"value": torch.asarray([1.0])}, checkpoint)
    _save_checkpoint_atomic({"value": torch.asarray([2.0])}, checkpoint)

    assert torch.equal(
        torch.load(checkpoint, map_location="cpu", weights_only=True)["value"],
        torch.asarray([2.0]),
    )
    assert not (tmp_path / "checkpoint.pt.tmp").exists()


def test_model_interface_has_no_states_or_graph_argument() -> None:
    assert tuple(inspect.signature(TemporalGRU.forward).parameters) == ("self", "inputs")


def test_frozen_selection_contract_is_validation_only() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    selection = checkpoint_selection_contract(config)

    assert selection == {
        "selection_split": "validation",
        "selection_metric": "validation.mae_overall",
        "selection_direction": "minimize",
        "test_used_for_selection": False,
        "ood_used_for_selection": False,
    }


def test_metrics_schema_and_expected_artifact_directory() -> None:
    config, data = load_s1_data(CONFIG_PATH, ROOT)
    indices = data.indices("validation")
    predictions = np.zeros_like(data.states[indices])
    metrics = _metrics(
        predictions, data.states[indices], data.mask[indices], data, "validation", 2026201
    )

    assert set(metrics) >= {
        "mae_overall", "rmse_overall", "per_state_dimension_mae",
        "per_state_dimension_rmse", "observed_node_error", "unobserved_node_error",
        "mask_coverage",
    }
    assert metrics["uses_future_observations"] is False
    assert metrics["uses_graph"] is False
    expected = ROOT / "reports/model2/s1_learned_baselines/temporal_gru/seed_2026201"
    assert temporal_gru_seed_dir(config, ROOT, 2026201) == expected

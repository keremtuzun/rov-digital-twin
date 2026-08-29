from __future__ import annotations

import inspect

import numpy as np
import torch

from oceansense.model2.independent_mlp import (
    IndependentMLP,
    fit_train_preprocessing,
    transform_inputs,
)


def test_preprocessing_fits_observed_train_rows_only() -> None:
    observations = np.asarray([[[[1.0, 2.0], [100.0, 200.0]]]], dtype=np.float32)
    mask = np.asarray([[[1, 0]]], dtype=np.uint8)
    preprocessing = fit_train_preprocessing(observations, mask)

    assert preprocessing["fit_split"] == "train"
    assert preprocessing["observation_mean"] == [1.0, 2.0]
    assert preprocessing["observed_row_count"] == 1


def test_transform_uses_zero_normalized_imputation_and_explicit_mask() -> None:
    train = np.asarray([[[[1.0, 2.0], [3.0, 4.0]]]], dtype=np.float32)
    train_mask = np.ones((1, 1, 2), dtype=np.uint8)
    preprocessing = fit_train_preprocessing(train, train_mask)
    observations = np.asarray([[[[3.0, 4.0], [99.0, 99.0]]]], dtype=np.float32)
    mask = np.asarray([[[1, 0]]], dtype=np.uint8)

    transformed = transform_inputs(observations, mask, preprocessing)

    assert transformed.shape == (1, 1, 2, 3)
    assert np.array_equal(transformed[0, 0, 1], np.asarray([0.0, 0.0, 0.0]))
    assert transformed[0, 0, 0, -1] == 1.0


def test_model_interface_cannot_receive_states_history_or_graph() -> None:
    assert tuple(inspect.signature(IndependentMLP.forward).parameters) == ("self", "inputs")
    model = IndependentMLP(7, [64, 64], 5, 0.1)
    output = model(torch.zeros((2, 3, 4, 7)))
    assert output.shape == (2, 3, 4, 5)
    assert torch.all((0 <= output) & (output <= 1))


def test_model_matches_frozen_architecture_widths() -> None:
    model = IndependentMLP(7, [64, 64], 5, 0.1)
    linear = [layer for layer in model.network if isinstance(layer, torch.nn.Linear)]
    assert [(layer.in_features, layer.out_features) for layer in linear] == [
        (7, 64), (64, 64), (64, 5)
    ]

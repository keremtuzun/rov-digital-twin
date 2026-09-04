import numpy as np
import pytest
import torch

from oceansense.seaclear_native import average_precision, make_head, metrics


def test_average_precision_handles_ties_and_missing_positives():
    assert average_precision(np.array([0.9, 0.1]), np.array([1, 0])) == 1
    assert average_precision(np.array([0.1, 0.9]), np.array([1, 0])) == 0.5
    assert average_precision(np.array([0.5, 0.5]), np.array([1, 0])) == 0.5
    assert average_precision(np.array([0.5, 0.5]), np.array([0, 1])) == 0.5
    assert average_precision(np.array([0.9, 0.1]), np.array([0, 0])) is None


def test_multilabel_metrics_do_not_hide_missing_class_support():
    result = metrics(np.array([[0.9, 0.1], [0.1, 0.1]]), np.array([[1, 0], [0, 0]]))
    assert result["macro_ap_present_classes"] == 1
    assert result["ap_per_class"] == [1, None]
    assert result["positive_counts"] == [1, 0]
    assert result["classes_with_test_positives"] == 1
    assert result["micro_f1"] == 1
    assert result["macro_f1"] == 0.5


@pytest.mark.parametrize("hidden", [0, 128, 256])
def test_native_heads_use_features_not_label_metadata(hidden):
    model = make_head({"hidden": hidden}, 40)
    assert model(torch.zeros(2, 512)).shape == (2, 40)

import json
from pathlib import Path

import pytest
import torch

from oceansense.model2_extended import make_model


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = json.loads((ROOT / "configs/model2_extended_v1.json").read_text())


@pytest.mark.parametrize("candidate", PROTOCOL["candidates"])
def test_extended_graph_models_are_causal_and_bounded(candidate):
    torch.manual_seed(8)
    model = make_model(candidate).eval()
    features = torch.rand(2, 5, 12, 7)
    changed = features.clone()
    changed[:, 3:] = torch.rand_like(changed[:, 3:])
    graph = torch.eye(12).repeat(2, 1, 1)
    with torch.no_grad():
        first = model(features, graph)
        second = model(changed, graph)
    torch.testing.assert_close(first[:, :3], second[:, :3])
    assert first.shape == (2, 5, 12, 5)
    assert torch.all((first >= 0) & (first <= 1))


def test_extended_protocol_is_fresh_and_not_a_physical_claim():
    assert PROTOCOL["dataset_seed"] != 904170000
    assert not PROTOCOL["deployment_authorized"]
    assert "global optimum" in PROTOCOL["stopping_rule"]

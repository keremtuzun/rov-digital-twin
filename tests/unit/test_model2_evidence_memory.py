import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import torch

from oceansense.model2.evidence_memory import EvidenceMemory
from oceansense.model2.graph_baselines import load_adjacency
from oceansense.model2.research_experiment import loss_value, train_one, uncertainty_metrics
from oceansense.model2.research_release import build_s2, load_s2, validate_s2

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    torch.manual_seed(42)
    return (
        torch.rand(2, 5, 4, 7),
        torch.ones(2, 4, 4) - torch.eye(4),
        torch.ones(2, 5, 4),
        torch.ones(2, 5, 4) * 0.8,
    )


@pytest.mark.parametrize("variant", ["full", "no_memory", "no_graph", "no_gate", "no_uncertainty"])
def test_causal_bounded_and_scenario_isolated(variant):
    x, graph, mask, confidence = inputs()
    model = EvidenceMemory(8, variant).eval()
    mean, variance = model(x, graph, mask, confidence)
    assert mean.shape == (2, 5, 4, 5)
    assert torch.all((mean >= 0) & (mean <= 1))
    assert (variance is None) == (variant == "no_uncertainty")
    if variance is not None:
        assert torch.all((variance >= 1e-4) & (variance <= 1))
    changed = x.clone()
    changed[:, 3:] += 10
    assert torch.equal(mean[:, :3], model(changed, graph, mask, confidence)[0][:, :3])
    changed = x.clone()
    changed[1] += 10
    assert torch.equal(mean[0], model(changed, graph, mask, confidence)[0][0])
    permutation = [2, 0, 3, 1]
    permuted = model(
        x[:, :, permutation],
        graph[:, permutation][:, :, permutation],
        mask[:, :, permutation],
        confidence[:, :, permutation],
    )[0]
    assert torch.allclose(permuted, mean[:, :, permutation], atol=1e-6)


def test_missing_or_zero_confidence_cannot_update_from_measurements():
    x, graph, mask, confidence = inputs()
    model = EvidenceMemory(8).eval()
    for absent in ("mask", "confidence"):
        m = mask * 0 if absent == "mask" else mask
        c = confidence * 0 if absent == "confidence" else confidence
        assert torch.equal(model(x, graph, m, c)[0], model(x + 100, graph, m, c)[0])


def test_ablation_boundaries():
    x, graph, mask, confidence = inputs()
    model = EvidenceMemory(8, "no_graph").eval()
    assert torch.equal(
        model(x, graph, mask, confidence)[0], model(x, graph * 0, mask, confidence)[0]
    )
    model = EvidenceMemory(8, "no_gate").eval()
    assert torch.equal(
        model(x, graph, mask, confidence)[0], model(x, graph, mask, confidence * 0)[0]
    )
    model = EvidenceMemory(8, "no_memory").eval()
    expected = model(x, graph, mask, confidence)[0]
    x[:, :3] += 10
    assert torch.equal(expected[:, 3:], model(x, graph, mask, confidence)[0][:, 3:])


def test_variance_loss_and_interval_metrics():
    mean = torch.zeros(1, 1, 1, 5, requires_grad=True)
    variance = torch.ones_like(mean) * 0.25
    loss = loss_value(mean, variance, torch.ones_like(mean))
    loss.backward()
    assert torch.isfinite(mean.grad).all()
    result = uncertainty_metrics(np.zeros((1, 5)), np.ones((1, 5)), np.zeros((1, 5)), 1.64485)
    assert result["empirical_coverage"] == 1
    assert result["calibration_fitted"] is False


@pytest.fixture
def research_root(tmp_path):
    for relative in ("configs/model2", "data/model2/s1_synthetic"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    return tmp_path


def test_s2_release_and_training_fixture(research_root):
    protocol = json.loads((ROOT / "configs/model2/s2_research_protocol.json").read_text())
    report = build_s2(research_root, protocol)
    assert report["valid"]
    data = load_s2(research_root, protocol)
    assert data.states.shape == (200, 10, 10, 5)
    assert all(s.startswith("s2_") for s in data.metadata["scenario_ids"])
    original_hashes = (research_root / "data/model2/s1_synthetic/checksums.json").read_bytes()
    assert build_s2(research_root, protocol)["valid"]
    assert (
        original_hashes == (research_root / "data/model2/s1_synthetic/checksums.json").read_bytes()
    )
    fixture = dict(protocol, maximum_epochs=1)
    directory = research_root / "fixture-training"
    selected = train_one(data, load_adjacency(data), fixture, "full", 2026901, directory)
    assert selected["epoch"] == 1
    assert not selected["test_used_for_selection"]
    assert not list(directory.glob("test*"))
    path = data.release_dir / "protocol.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="protocol"):
        validate_s2(data.release_dir, protocol)

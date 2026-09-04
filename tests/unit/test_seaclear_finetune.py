import json
from pathlib import Path

import torch

from oceansense.seaclear_finetune import image_batch, make_model


def test_only_last_resnet_block_and_head_are_trainable():
    model = make_model(26)
    trainable = {name for name, value in model.named_parameters() if value.requires_grad}
    assert trainable
    assert all(name.startswith(("layer4.", "fc.")) for name in trainable)
    assert not model.conv1.weight.requires_grad
    assert model(torch.zeros(2, 3, 160, 160)).shape == (2, 26)


def test_cached_image_batch_is_normalized_without_label_inputs():
    cache = torch.zeros(2, 3, 32, 32, dtype=torch.uint8).numpy()
    pixels = image_batch(cache, [0], "cpu", False)
    assert pixels.shape == (1, 3, 32, 32)
    assert torch.isfinite(pixels).all()


def test_finetune_protocol_never_claims_physical_completion():
    root = Path(__file__).resolve().parents[2]
    protocol = json.loads((root / "configs/seaclear_finetune_v1.json").read_text())
    assert not protocol["deployment_authorized"]
    assert "global optimum" in protocol["stopping_rule"]

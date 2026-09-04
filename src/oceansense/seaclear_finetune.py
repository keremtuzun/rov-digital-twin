"""Validation-driven last-block adaptation after fixed-feature search."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn

from .local_restart import digest, now, write_json
from .seaclear_native import metrics


def build_cache(rows, size, path):
    cache = np.lib.format.open_memmap(path, mode="w+", dtype=np.uint8,
                                      shape=(len(rows), 3, size, size))
    for index, row in enumerate(rows):
        with Image.open(row["path"]) as image:
            image = image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
            cache[index] = np.asarray(image, dtype=np.uint8).transpose(2, 0, 1)
        if index % 1000 == 0:
            print(f"Fine-tune input cache: {index}/{len(rows)}", flush=True)
    cache.flush()
    return cache


def image_batch(cache, indices, device, augment=False):
    image = torch.from_numpy(np.asarray(cache[indices]).astype(np.float32) / 255).to(device)
    if augment:
        flip = torch.rand(len(indices), 1, 1, 1, device=device) < 0.5
        image = torch.where(flip, image.flip(-1), image)
        brightness = 0.75 + 0.5 * torch.rand(len(indices), 1, 1, 1, device=device)
        mean = image.mean((1, 2, 3), keepdim=True)
        contrast = 0.75 + 0.5 * torch.rand(len(indices), 1, 1, 1, device=device)
        image = ((image - mean) * contrast + mean).mul(brightness).clamp(0, 1)
    mean = image.new_tensor([0.485, 0.456, 0.406])[None, :, None, None]
    std = image.new_tensor([0.229, 0.224, 0.225])[None, :, None, None]
    return (image - mean) / std


def make_model(classes):
    from torchvision.models import ResNet18_Weights, resnet18
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, classes)
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.layer4.parameters():
        parameter.requires_grad = True
    for parameter in model.fc.parameters():
        parameter.requires_grad = True
    return model


def predict(model, cache, indices, targets_source, device):
    model.eval()
    output, targets = [], []
    with torch.no_grad():
        for ids in np.array_split(indices, max(1, math.ceil(len(indices) / 64))):
            prediction = model(image_batch(cache, ids, device)).sigmoid().cpu()
            if not torch.isfinite(prediction).all():
                raise ValueError("nonfinite adapted prediction")
            output.append(prediction.numpy())
            targets.append(targets_source[ids])
    return np.concatenate(output), np.concatenate(targets)


def run(root):
    protocol_path = root / "configs/seaclear_finetune_v1.json"
    protocol = json.loads(protocol_path.read_text())
    parent = root / "reports" / protocol["parent_experiment"]
    output = root / "reports" / protocol["experiment_id"]
    if output.exists():
        raise FileExistsError("fine-tuning experiment already exists; refusing held-out rerun")
    if not (parent / "completed.json").is_file():
        raise ValueError("parent native-label experiment is not complete")
    parent_protocol = json.loads((parent / "protocol.json").read_text())
    source = json.loads((parent / "dataset.json").read_text())
    arrays = np.load(parent / "features.npz", allow_pickle=False)
    supported = arrays["supported"].tolist()
    rows = source["records"]
    splits = {s: [i for i, row in enumerate(rows) if row["split"] == s] for s in parent_protocol["sites"]}
    output.mkdir(parents=True)
    write_json(output / "protocol.json", protocol)
    write_json(output / "environment.json", {"source_sha256": digest(Path(__file__)),
               "protocol_sha256": digest(protocol_path), "parent_completed_sha256": digest(parent / "completed.json"),
               "torch": str(torch.__version__), "started_at": now()})
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    cache = build_cache(rows, protocol["input_size"], output / "input_cache.npy")
    all_targets = np.asarray([r["target"] for r in rows], dtype=np.float32)[:, supported]
    train_targets = all_targets[splits["train"]]
    weight = torch.tensor((len(train_targets) - train_targets.sum(0)) /
                          np.maximum(train_targets.sum(0), 1),
                          dtype=torch.float32).clamp(1, 30).to(device)
    runs = []
    for candidate in protocol["candidates"]:
        for seed in protocol["training_seeds"]:
            torch.manual_seed(seed)
            model = make_model(len(supported)).to(device)
            optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                           lr=candidate["lr"], weight_decay=0.001)
            best, stale, state, history = -1.0, 0, None, []
            directory = output / candidate["name"] / str(seed)
            directory.mkdir(parents=True)
            for epoch in range(1, protocol["maximum_epochs"] + 1):
                model.train()
                for positions in torch.randperm(len(train_targets)).split(48):
                    position_array = positions.numpy()
                    source_ids = np.asarray(splits["train"])[position_array]
                    output_logits = model(image_batch(cache, source_ids, device, True))
                    loss = nn.functional.binary_cross_entropy_with_logits(
                        output_logits, torch.from_numpy(train_targets[position_array]).to(device),
                        pos_weight=weight if candidate["weighted"] else None)
                    if not torch.isfinite(loss):
                        raise ValueError("nonfinite fine-tuning loss")
                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1,
                                             error_if_nonfinite=True)
                    optimizer.step()
                probability, truth = predict(model, cache, np.asarray(splits["validation"]),
                                             all_targets, device)
                value = metrics(probability, truth)["macro_ap_present_classes"]
                gain = value - best
                if value > best:
                    best, best_epoch = value, epoch
                    state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()
                             if name.startswith("layer4.") or name.startswith("fc.")}
                stale = 0 if gain >= protocol["minimum_improvement"] else stale + 1
                history.append({"epoch": epoch, "validation_score": value})
                print(f"Fine-tune {candidate['name']}/{seed} epoch={epoch} mAP={value:.4f}", flush=True)
                if stale >= protocol["patience"]:
                    break
            torch.save({"state_dict": state, "candidate": candidate, "supported_indices": supported},
                       directory / "checkpoint.pt")
            write_json(directory / "history.json", history)
            record = {"candidate": candidate["name"], "seed": seed, "validation_score": best,
                      "epoch": best_epoch, "epochs_run": len(history), "sha256": digest(directory / "checkpoint.pt")}
            write_json(directory / "selection.json", record)
            runs.append(record)
            del model
            if device == "mps":
                torch.mps.empty_cache()
    parent_best = json.loads((parent / "summary.json").read_text())["selection"]["validation_scores"]
    previous = max(parent_best.values())
    rounds, stale = [], 0
    means = {}
    for candidate in protocol["candidates"]:
        value = float(np.mean([r["validation_score"] for r in runs if r["candidate"] == candidate["name"]]))
        means[candidate["name"]] = value
        improved = value - previous >= protocol["minimum_improvement"]
        stale = 0 if improved else stale + 1
        previous = max(previous, value)
        rounds.append({"candidate": candidate["name"], "best_score_so_far": previous,
                       "meaningful_improvement": improved})
    selected = max(means, key=means.get)
    selection = {"selected": selected, "validation_scores": means, "rounds": rounds,
                 "status": "bounded_finetuning_plateau" if stale >= 2 else "budget_exhausted",
                 "global_optimum_proven": False, "physical_data_is_only_remaining_improvement": False}
    write_json(output / "matrix_locked.json", {"locked_at": now(), "runs": runs, "selection": selection})
    candidate = next(c for c in protocol["candidates"] if c["name"] == selected)
    models = []
    for seed in protocol["training_seeds"]:
        model = make_model(len(supported))
        checkpoint = torch.load(output / selected / str(seed) / "checkpoint.pt", weights_only=True)
        model.load_state_dict(checkpoint["state_dict"], strict=False)
        models.append(model.to(device))
    results = {}
    for split in ("calibration", "test"):
        split_ids = np.asarray(splits[split])
        predictions, truth = zip(*(predict(model, cache, split_ids, all_targets, device)
                                   for model in models))
        prediction = np.mean(predictions, axis=0)
        np.save(output / f"{split}_predictions.npy", prediction)
        if split == "calibration":
            target = truth[0]
            threshold = max([i / 10 for i in range(1, 10)],
                            key=lambda t: metrics(prediction, target, t)["micro_f1"])
            write_json(output / "threshold_locked.json", {"threshold": threshold, "fit_split": split,
                       "probability_calibrated": False, "locked_at": now()})
        results[split] = metrics(prediction, truth[0], threshold)
    summary = {"selection": selection, **results, "supported_category_count": len(supported),
               "site_splits_unchanged": True, "test_evaluations": 1,
               "canonical_model1_ready": False, "deployment_authorized": False,
               "physical_data_is_only_remaining_improvement": False}
    write_json(output / "summary.json", summary)
    write_json(output / "completed.json", {"completed_at": now(), "heldout_evaluations": 1,
               "files": {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*")) if p.is_file()}})
    return summary

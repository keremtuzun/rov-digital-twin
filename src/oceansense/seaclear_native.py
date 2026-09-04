"""Native-label real-image research without fabricating canonical approvals."""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn

from .local_restart import digest, now, search_summary, write_json


def average_precision(prob, target):
    """Non-interpolated AP, aggregating tied scores at identical thresholds."""
    order = np.argsort(-prob, kind="stable")
    truth = target[order]
    if not truth.sum():
        return None
    tp = np.cumsum(truth)
    end = np.r_[np.flatnonzero(np.diff(prob[order]) != 0), len(order) - 1]
    recall = tp[end] / truth.sum()
    precision = tp[end] / (end + 1)
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def metrics(prob, target, threshold=0.5):
    ap = [average_precision(prob[:, i], target[:, i]) for i in range(target.shape[1])]
    available = [v for v in ap if v is not None]
    predicted = prob >= threshold
    tp = (predicted * target).sum(0)
    denom = predicted.sum(0) + target.sum(0)
    return {"macro_ap_present_classes": float(np.mean(available)) if available else 0.0,
            "ap_per_class": ap, "positive_counts": target.sum(0).astype(int).tolist(),
            "micro_f1": float(2 * tp.sum() / max(denom.sum(), 1)),
            "macro_f1": float(np.mean(2 * tp / np.maximum(denom, 1))),
            "threshold": float(threshold), "classes_with_test_positives": len(available)}


def build_rows(root, extracted, protocol):
    coco_paths = list(extracted.rglob("dataset.json"))
    if len(coco_paths) != 1:
        raise ValueError("expected exactly one source COCO dataset.json")
    coco = json.loads(coco_paths[0].read_text())
    paths = {p.name: p for p in extracted.rglob("*.jpg")}
    if len(paths) != len(list(extracted.rglob("*.jpg"))):
        raise ValueError("ambiguous image basenames")
    categories = sorted(coco["categories"], key=lambda c: c["id"])
    category_index = {c["id"]: i for i, c in enumerate(categories)}
    annotations = {}
    for row in coco["annotations"]:
        annotations.setdefault(row["image_id"], set()).add(category_index[row["category_id"]])
    with (root / "data/model1_baseline_v2/manifests/seaclear_source_assets.csv").open() as handle:
        source = {int(r["source_image_id"]): r for r in csv.DictReader(handle)}
    site_split = {site: split for split, sites in protocol["sites"].items() for site in sites}
    records, seen, duplicates = [], set(), []
    for image in sorted(coco["images"], key=lambda r: r["id"]):
        evidence = source[image["id"]]
        path = paths[Path(image["file_name"]).name]
        sha = digest(path)
        if sha != evidence["sha256"]:
            raise ValueError(f"image differs from inventoried source: {image['id']}")
        if sha in seen:
            duplicates.append(image["id"])
            continue
        seen.add(sha)
        target = np.zeros(len(categories), dtype=np.float32)
        target[list(annotations.get(image["id"], set()))] = 1
        records.append({"image_id": image["id"], "path": str(path), "sha256": sha,
                        "site": evidence["site"], "split": site_split[evidence["site"]],
                        "target": target.tolist()})
    return records, categories, duplicates


def extract_features(records, output):
    from torchvision.models import ResNet18_Weights, resnet18
    from torchvision.transforms import Compose, Normalize, Resize, ToTensor
    weights = ResNet18_Weights.IMAGENET1K_V1
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    encoder = resnet18(weights=weights).eval()
    torch.save(encoder.state_dict(), output / "encoder.pt")
    encoder.fc = nn.Identity()
    encoder.to(device)
    transform = Compose([Resize((224, 224)), ToTensor(),
                         Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    features = []
    with torch.no_grad():
        for start in range(0, len(records), 16):
            images = []
            for row in records[start:start + 16]:
                with Image.open(row["path"]) as image:
                    images.append(transform(image.convert("RGB")))
            features.append(encoder(torch.stack(images).to(device)).cpu().numpy())
            if start % 512 == 0:
                print(f"SeaClear feature extraction: {start}/{len(records)} on {device}", flush=True)
    result = np.concatenate(features).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("nonfinite real-image features")
    return result, device


def make_head(candidate, count):
    if not candidate["hidden"]:
        return nn.Linear(512, count)
    return nn.Sequential(nn.Linear(512, candidate["hidden"]), nn.ReLU(), nn.Dropout(0.3),
                         nn.Linear(candidate["hidden"], count))


def probabilities(model, features):
    model.eval()
    with torch.no_grad():
        return model(features).sigmoid().numpy()


def run(root, extracted):
    protocol_path = root / "configs/seaclear_native_v1.json"
    protocol = json.loads(protocol_path.read_text())
    output = root / "reports" / protocol["experiment_id"]
    if output.exists():
        raise FileExistsError("native-label experiment already exists; refusing held-out rerun")
    archive = root / "data/model1_baseline_v2/raw/seaclear/v1/SeaClear.rar"
    if digest(archive) != protocol["archive_sha256"]:
        raise ValueError("source archive checksum mismatch")
    output.mkdir(parents=True)
    write_json(output / "protocol.json", protocol)
    records, categories, duplicates = build_rows(root, extracted, protocol)
    write_json(output / "dataset.json", {"records": records, "categories": categories,
               "duplicate_image_ids_excluded": duplicates, "license": protocol["license"],
               "attribution": protocol["attribution"], "canonical_labels_approved": False})
    features, device = extract_features(records, output)
    targets = np.asarray([r["target"] for r in records], dtype=np.float32)
    splits = {s: np.asarray([i for i, r in enumerate(records) if r["split"] == s]) for s in protocol["sites"]}
    supported = np.flatnonzero(targets[splits["train"]].sum(0) >= protocol["minimum_training_positives"])
    if not len(supported) or any(not len(v) for v in splits.values()):
        raise ValueError("insufficient source data")
    targets = targets[:, supported]
    mean, std = features[splits["train"]].mean(0), features[splits["train"]].std(0).clip(0.01)
    features = (features - mean) / std
    np.savez_compressed(output / "features.npz", features=features, targets=targets,
                        mean=mean, std=std, supported=supported)
    write_json(output / "environment.json", {"device": device, "torch": str(torch.__version__),
               "source_sha256": digest(Path(__file__)), "protocol_sha256": digest(protocol_path),
               "started_at": now(), "encoder_sha256": digest(output / "encoder.pt")})
    tx, ty = torch.from_numpy(features[splits["train"]]), torch.from_numpy(targets[splits["train"]])
    vx, vy = torch.from_numpy(features[splits["validation"]]), targets[splits["validation"]]
    weight = ((len(ty) - ty.sum(0)) / ty.sum(0).clamp_min(1)).clamp(1, 30)
    runs = []
    for candidate in protocol["candidates"]:
        for seed in protocol["training_seeds"]:
            torch.manual_seed(seed)
            model = make_head(candidate, len(supported))
            optimizer = torch.optim.AdamW(model.parameters(), lr=candidate["lr"], weight_decay=0.001)
            best, stale, history, state = -1.0, 0, [], None
            directory = output / candidate["name"] / str(seed)
            directory.mkdir(parents=True)
            for epoch in range(1, protocol["maximum_epochs"] + 1):
                model.train()
                for ids in torch.randperm(len(ty)).split(128):
                    loss = nn.functional.binary_cross_entropy_with_logits(model(tx[ids]), ty[ids],
                            pos_weight=weight if candidate["weighted"] else None)
                    if not torch.isfinite(loss):
                        raise ValueError("nonfinite native-label loss")
                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1, error_if_nonfinite=True)
                    optimizer.step()
                value = metrics(probabilities(model, vx), vy)["macro_ap_present_classes"]
                gain = value - best
                if value > best:
                    best, best_epoch, state = value, epoch, copy.deepcopy(model.state_dict())
                stale = 0 if gain >= protocol["minimum_improvement"] else stale + 1
                history.append({"epoch": epoch, "validation_score": value})
                if stale >= protocol["patience"]:
                    break
            torch.save({"candidate": candidate, "state_dict": state, "supported_indices": supported.tolist()},
                       directory / "checkpoint.pt")
            write_json(directory / "history.json", history)
            record = {"candidate": candidate["name"], "seed": seed, "validation_score": best,
                      "epoch": best_epoch, "epochs_run": len(history), "sha256": digest(directory / "checkpoint.pt")}
            write_json(directory / "selection.json", record)
            runs.append(record)
            print(f"SeaClear {candidate['name']}/{seed}: validation mAP {best:.4f}", flush=True)
    selection = search_summary(runs, protocol["candidates"], protocol["minimum_improvement"])
    write_json(output / "matrix_locked.json", {"locked_at": now(), "runs": runs, "selection": selection})
    candidate = next(c for c in protocol["candidates"] if c["name"] == selection["selected"])
    models = []
    for seed in protocol["training_seeds"]:
        model = make_head(candidate, len(supported))
        checkpoint = torch.load(output / candidate["name"] / str(seed) / "checkpoint.pt", weights_only=True)
        model.load_state_dict(checkpoint["state_dict"])
        models.append(model)
    cal_ids = splits["calibration"]
    cal = np.mean([probabilities(m, torch.from_numpy(features[cal_ids])) for m in models], axis=0)
    threshold = max([i / 10 for i in range(1, 10)],
                    key=lambda t: metrics(cal, targets[cal_ids], t)["micro_f1"])
    write_json(output / "threshold_locked.json", {"locked_at": now(), "threshold": threshold,
               "fit_split": "calibration", "probability_calibrated": False})
    test_ids = splits["test"]
    test = np.mean([probabilities(m, torch.from_numpy(features[test_ids])) for m in models], axis=0)
    np.save(output / "calibration_predictions.npy", cal)
    np.save(output / "test_predictions.npy", test)
    summary = {"selection": selection, "calibration": metrics(cal, targets[cal_ids], threshold),
               "test": metrics(test, targets[test_ids], threshold),
               "supported_categories": [categories[i] for i in supported],
               "unsupported_categories": [c for i, c in enumerate(categories) if i not in supported],
               "split_counts": {s: len(ids) for s, ids in splits.items()},
               "native_annotation_research_only": True, "canonical_model1_ready": False,
               "deployment_authorized": False, "encoder_finetuned": False,
               "physical_data_is_only_remaining_improvement": False}
    write_json(output / "summary.json", summary)
    write_json(output / "completed.json", {"completed_at": now(), "heldout_evaluations": 1,
               "files": {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*")) if p.is_file()}})
    return summary

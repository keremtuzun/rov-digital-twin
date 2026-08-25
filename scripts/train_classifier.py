from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
from datetime import datetime, timezone
from pathlib import Path

from oceansense.evaluation import classification_metrics
from oceansense.model1_baseline_v2 import (
    dataset_preflight,
    load_baseline_config,
)
from oceansense.schemas import CONDITION_LABELS, DOMAIN_LABELS
from oceansense.underwater_augmentation import UnderwaterAugmentation


def _sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the documented EfficientNet-B0 baseline")
    parser.add_argument("--config", help="Locked Model 1 v2 JSON-compatible YAML config")
    parser.add_argument("--preflight-only", action="store_true", help="Check gates and exit without training")
    parser.add_argument("--task", choices=("domain", "condition"), default="condition")
    parser.add_argument("--data", help="ImageFolder root containing train/val/test")
    parser.add_argument("--output")
    parser.add_argument("--report")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--class-balance", choices=("none", "weighted_loss", "weighted_sampler"))
    parser.add_argument("--weights", choices=("none", "imagenet"))
    parser.add_argument("--data-manifest", help="Approved manifest used to create this ImageFolder")
    return parser.parse_args()


def _runtime_settings(args: argparse.Namespace) -> tuple[dict, dict | None, dict | None]:
    config = load_baseline_config(args.config) if args.config else None
    preflight = dataset_preflight(args.config) if args.config else None
    if args.preflight_only:
        if preflight is None:
            raise SystemExit("--preflight-only requires --config")
        print(json.dumps(preflight, indent=2))
        raise SystemExit(0 if preflight["ready"] else 2)
    if config and not preflight["ready"]:
        failures = "\n- ".join(preflight["errors"])
        raise SystemExit(f"Model 1 v2 training gate is blocked:\n- {failures}")

    training = config["training"] if config else {}
    artifacts = config["artifacts"].get(args.task, {}) if config else {}
    repo_root = Path(args.config).resolve().parent.parent if config else Path.cwd()
    data_root = Path(args.data) if args.data else None
    if data_root is None and config:
        data_root = repo_root / config["data"]["root"] / "imagefolders" / args.task
    if data_root is None:
        raise SystemExit("--data is required when --config is not supplied")
    output = args.output or artifacts.get("checkpoint")
    report = args.report or artifacts.get("training_report")
    if config:
        output = str(repo_root / output) if not Path(output).is_absolute() else output
        report = str(repo_root / report) if not Path(report).is_absolute() else report
    settings = {
        "task": args.task,
        "data": str(data_root),
        "output": output or f"models/oceansense_{args.task}_efficientnet_b0.pt",
        "report": report or f"outputs/evaluation_reports/{args.task}_classifier_metrics.json",
        "epochs": args.epochs or int(training.get("maximum_epochs", 10)),
        "batch_size": args.batch_size or int(training.get("batch_size", 16)),
        "seed": args.seed if args.seed is not None else int(training.get("seed", 42)),
        "class_balance": args.class_balance or training.get("class_balance", "weighted_loss"),
        "weights": args.weights or training.get("weights", "none"),
        "learning_rate": float(training.get("learning_rate", 3e-4)),
        "weight_decay": float(training.get("weight_decay", 0.01)),
        "warmup_epochs": int(training.get("warmup_epochs", 0)),
        "minimum_learning_rate": float(training.get("minimum_learning_rate", 1e-6)),
        "early_stopping_patience": int(training.get("early_stopping_patience", 0)),
        "early_stopping_min_delta": float(training.get("early_stopping_min_delta", 0.0)),
        "augmentation_probability": float(training.get("augmentation_probability", 0.75)),
        "model_version": config["model_version"] if config else f"{args.task}_efficientnet_b0_v1",
        "data_manifest": args.data_manifest or (config["data"]["manifest"] if config else None),
    }
    if config and settings["class_balance"] != "weighted_loss":
        raise SystemExit("model1_baseline_v2 requires weighted_loss and forbids sampler mixing")
    return settings, config, preflight


def main() -> None:
    args = _arguments()
    settings, config, preflight = _runtime_settings(args)

    try:
        import numpy as np
        import torch
        import torchvision
        from torch import nn
        from torch.utils.data import DataLoader, WeightedRandomSampler
        from torchvision import datasets, transforms
        from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[vision]'") from exc

    seed = settings["seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)

    root = Path(settings["data"])
    pretrained = EfficientNet_B0_Weights.DEFAULT if settings["weights"] == "imagenet" else None
    evaluation_transform = EfficientNet_B0_Weights.DEFAULT.transforms()
    training_transform = transforms.Compose([
        UnderwaterAugmentation(seed, settings["augmentation_probability"]),
        evaluation_transform,
    ])
    train_data = datasets.ImageFolder(root / "train", transform=training_transform)
    val_data = datasets.ImageFolder(root / "val", transform=evaluation_transform)
    test_data = datasets.ImageFolder(root / "test", transform=evaluation_transform)
    if train_data.classes != val_data.classes or train_data.classes != test_data.classes:
        raise ValueError("train/val/test class directories must match")
    allowed = DOMAIN_LABELS if settings["task"] == "domain" else CONDITION_LABELS
    unsupported = set(train_data.classes) - allowed
    if unsupported:
        raise ValueError(f"unsupported {settings['task']} classes: {sorted(unsupported)}")
    if config and set(train_data.classes) != set(config["labels"][settings["task"]]):
        raise ValueError(f"ImageFolder classes must exactly cover the locked v2 {settings['task']} schema")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = efficientnet_b0(weights=pretrained)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(train_data.classes))
    model.to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=settings["learning_rate"], weight_decay=settings["weight_decay"]
    )
    counts = [train_data.targets.count(index) for index in range(len(train_data.classes))]
    class_weights = torch.tensor(
        [len(train_data) / max(1, count) for count in counts], dtype=torch.float32, device=device
    )
    criterion = nn.CrossEntropyLoss(
        weight=class_weights if settings["class_balance"] == "weighted_loss" else None
    )
    sampler = None
    if settings["class_balance"] == "weighted_sampler":
        sample_weights = [1.0 / max(1, counts[target]) for target in train_data.targets]
        sampler = WeightedRandomSampler(
            sample_weights,
            len(sample_weights),
            replacement=True,
            generator=torch.Generator().manual_seed(seed),
        )
    loaders = {
        "train": DataLoader(
            train_data,
            batch_size=settings["batch_size"],
            shuffle=sampler is None,
            sampler=sampler,
            num_workers=0,
            generator=torch.Generator().manual_seed(seed),
        ),
        "val": DataLoader(val_data, batch_size=settings["batch_size"], shuffle=False, num_workers=0),
    }
    warmup = min(settings["warmup_epochs"], max(0, settings["epochs"] - 1))
    if warmup:
        warmup_scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer, start_factor=1.0 / warmup, end_factor=1.0, total_iters=warmup
        )
        cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=max(1, settings["epochs"] - warmup),
            eta_min=settings["minimum_learning_rate"],
        )
        scheduler = torch.optim.lr_scheduler.SequentialLR(
            optimizer, [warmup_scheduler, cosine_scheduler], milestones=[warmup]
        )
    else:
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=max(1, settings["epochs"]),
            eta_min=settings["minimum_learning_rate"],
        )

    history = []
    best_metric = -math.inf
    significant_best = -math.inf
    best_state = None
    best_epoch = 0
    stale_epochs = 0
    for epoch in range(settings["epochs"]):
        epoch_result = {"epoch": epoch + 1, "learning_rate": optimizer.param_groups[0]["lr"]}
        for phase in ("train", "val"):
            model.train(phase == "train")
            correct = total = 0
            loss_sum = 0.0
            actual: list[str] = []
            predicted: list[str] = []
            confidences: list[float] = []
            for images, targets in loaders[phase]:
                images, targets = images.to(device), targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                with torch.set_grad_enabled(phase == "train"):
                    logits = model(images)
                    loss = criterion(logits, targets)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()
                probabilities = logits.softmax(1).detach().cpu()
                guesses = probabilities.argmax(1)
                loss_sum += float(loss) * len(targets)
                correct += int((logits.argmax(1) == targets).sum())
                total += len(targets)
                actual.extend(train_data.classes[index] for index in targets.cpu().tolist())
                predicted.extend(train_data.classes[index] for index in guesses.tolist())
                confidences.extend(float(row.max()) for row in probabilities)
            metrics = classification_metrics(actual, predicted, confidences)
            epoch_result[phase] = {
                "loss": loss_sum / total,
                "accuracy": correct / total,
                "macro_f1": metrics["macro_f1"],
                "balanced_accuracy": metrics["balanced_accuracy"],
            }
            if phase == "val":
                score = metrics["macro_f1"]
                if score > best_metric:
                    best_metric = score
                    best_epoch = epoch + 1
                    best_state = {
                        key: value.detach().cpu().clone() for key, value in model.state_dict().items()
                    }
                if score >= significant_best + settings["early_stopping_min_delta"]:
                    significant_best = score
                    stale_epochs = 0
                else:
                    stale_epochs += 1
        history.append(epoch_result)
        scheduler.step()
        patience = settings["early_stopping_patience"]
        if patience and stale_epochs >= patience:
            break

    if best_state is None:
        raise RuntimeError("training produced no validation state")
    model.load_state_dict(best_state)
    model.eval()
    confusion = [[0 for _ in train_data.classes] for _ in train_data.classes]
    predictions = []
    with torch.inference_mode():
        test_loader = DataLoader(test_data, batch_size=settings["batch_size"], shuffle=False)
        for images, targets in test_loader:
            probs = model(images.to(device)).softmax(1).cpu()
            for truth, row in zip(targets.tolist(), probs):
                confidence, guess_tensor = row.max(0)
                guess = int(guess_tensor)
                confusion[truth][guess] += 1
                predictions.append({
                    "actual": train_data.classes[truth],
                    "predicted": train_data.classes[guess],
                    "confidence": float(confidence),
                })
    actual = [item["actual"] for item in predictions]
    predicted = [item["predicted"] for item in predictions]
    confidences = [item["confidence"] for item in predictions]
    metrics = classification_metrics(actual, predicted, confidences)
    safety_labels = {
        "possible_structural_concern",
        "marine_debris",
        "poor_visibility",
        "aquaculture_infrastructure_concern",
    }
    safety_false_negatives = [
        item for item in predictions
        if item["actual"] in safety_labels
        and item["predicted"] == "normal_or_no_visible_concern"
    ]
    manifest_hash = preflight["hashes"].get("manifest") if preflight else (
        hashlib.sha256(Path(settings["data_manifest"]).read_bytes()).hexdigest()
        if settings["data_manifest"] else None
    )
    config_snapshot = {key: value for key, value in settings.items() if key != "output"}
    metadata = {
        "run_id": datetime.now(timezone.utc).strftime("model1-v2-%Y%m%dT%H%M%SZ"),
        "config": config_snapshot,
        "config_sha256": _sha256_json(config_snapshot),
        "source_config_sha256": preflight["hashes"].get("config") if preflight else None,
        "data_manifest_sha256": manifest_hash,
        "labels_sha256": preflight["hashes"].get("labels") if preflight else None,
        "split_sha256": preflight["hashes"].get("split") if preflight else None,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "torchvision": torchvision.__version__,
            "numpy": np.__version__,
            "device": device,
            "cuda": torch.version.cuda,
        },
    }
    report = {
        "model": "EfficientNet-B0",
        "model_version": settings["model_version"],
        "task": settings["task"],
        "selection_metric": "validation_macro_f1",
        "best_epoch": best_epoch,
        "best_val_macro_f1": best_metric,
        "stopped_early": len(history) < settings["epochs"],
        "test_accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "expected_calibration_error": metrics["expected_calibration_error"],
        "per_class": metrics["per_class"],
        "confusion_matrix": metrics["confusion_matrix"],
        "confidence_thresholds": metrics["confidence_thresholds"],
        "history": history,
        "safety_false_negatives": safety_false_negatives,
        "predictions": predictions,
        "class_distribution": dict(zip(train_data.classes, counts)),
        "metadata": metadata,
        "limitations": [
            "Metrics apply only to independent approved groups in the recorded manifest.",
            "Image predictions do not confirm structural failure or autonomous safety.",
        ],
    }
    output = Path(settings["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": best_state,
        "labels": train_data.classes,
        "task": settings["task"],
        "model_version": settings["model_version"],
        "metadata": metadata,
    }, output)
    report_path = Path(settings["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown = report_path.with_suffix(".md")
    markdown.write_text(
        f"# {settings['task'].title()} classifier report\n\n"
        f"- Model version: {settings['model_version']}\n"
        f"- Best validation macro F1: {best_metric:.4f} (epoch {best_epoch})\n"
        f"- Test accuracy: {report['test_accuracy']:.4f}\n"
        f"- Macro F1: {report['macro_f1']:.4f}\n"
        f"- Balanced accuracy: {report['balanced_accuracy']:.4f}\n"
        f"- ECE: {report['expected_calibration_error']:.4f}\n\n"
        "These metrics apply only to the recorded split and do not confirm physical damage or safety.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "checkpoint": str(output),
        "report": str(report_path),
        "best_val_macro_f1": best_metric,
        "test_accuracy": report["test_accuracy"],
    }, indent=2))


if __name__ == "__main__":
    main()

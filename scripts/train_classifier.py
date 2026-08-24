from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from oceansense.evaluation import classification_metrics
from oceansense.underwater_augmentation import UnderwaterAugmentation
from oceansense.schemas import CONDITION_LABELS, DOMAIN_LABELS


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the documented EfficientNet-B0 baseline")
    parser.add_argument("--task", choices=("domain", "condition"), default="condition")
    parser.add_argument("--data", required=True, help="ImageFolder root containing train/val/test")
    parser.add_argument("--output")
    parser.add_argument("--report")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--class-balance", choices=("none", "weighted_loss", "weighted_sampler"), default="weighted_loss")
    parser.add_argument("--weights", choices=("none", "imagenet"), default="none")
    parser.add_argument("--data-manifest", help="Approved manifest used to create this ImageFolder")
    args = parser.parse_args()

    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, WeightedRandomSampler
        from torchvision import datasets, transforms
        from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[vision]'") from exc

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    root = Path(args.data)
    weights = EfficientNet_B0_Weights.DEFAULT if args.weights == "imagenet" else None
    evaluation_transform = EfficientNet_B0_Weights.DEFAULT.transforms()
    training_transform = transforms.Compose(
        [UnderwaterAugmentation(args.seed), evaluation_transform]
    )
    train_data = datasets.ImageFolder(root / "train", transform=training_transform)
    val_data = datasets.ImageFolder(root / "val", transform=evaluation_transform)
    test_data = datasets.ImageFolder(root / "test", transform=evaluation_transform)
    if train_data.classes != val_data.classes or train_data.classes != test_data.classes:
        raise ValueError("train/val/test class directories must match")
    allowed = DOMAIN_LABELS if args.task == "domain" else CONDITION_LABELS
    unsupported = set(train_data.classes) - allowed
    if unsupported:
        raise ValueError(f"unsupported {args.task} classes: {sorted(unsupported)}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(train_data.classes))
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    counts = [train_data.targets.count(index) for index in range(len(train_data.classes))]
    class_weights = torch.tensor([len(train_data) / max(1, count) for count in counts], dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights if args.class_balance == "weighted_loss" else None)
    sampler = None
    if args.class_balance == "weighted_sampler":
        sample_weights = [1.0 / max(1, counts[target]) for target in train_data.targets]
        sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True,
                                         generator=torch.Generator().manual_seed(args.seed))
    loaders = {
        "train": DataLoader(train_data, batch_size=args.batch_size, shuffle=sampler is None, sampler=sampler,
                            num_workers=0, generator=torch.Generator().manual_seed(args.seed)),
        "val": DataLoader(val_data, batch_size=args.batch_size, shuffle=False, num_workers=0),
    }
    history = []
    best_accuracy, best_state = -1.0, None
    for epoch in range(args.epochs):
        epoch_result = {"epoch": epoch + 1}
        for phase in ("train", "val"):
            model.train(phase == "train")
            correct = total = 0
            loss_sum = 0.0
            for images, targets in loaders[phase]:
                images, targets = images.to(device), targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                with torch.set_grad_enabled(phase == "train"):
                    logits = model(images)
                    loss = criterion(logits, targets)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()
                loss_sum += float(loss) * len(targets)
                correct += int((logits.argmax(1) == targets).sum())
                total += len(targets)
            epoch_result[phase] = {"loss": loss_sum / total, "accuracy": correct / total}
            if phase == "val" and correct / total > best_accuracy:
                best_accuracy = correct / total
                best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        history.append(epoch_result)

    model.load_state_dict(best_state)
    model.eval()
    confusion = [[0 for _ in train_data.classes] for _ in train_data.classes]
    predictions = []
    with torch.inference_mode():
        for images, targets in DataLoader(test_data, batch_size=args.batch_size, shuffle=False, num_workers=0):
            probs = model(images.to(device)).softmax(1).cpu()
            for truth, row in zip(targets.tolist(), probs):
                confidence, guess = row.max(0)
                guess = int(guess)
                confusion[truth][guess] += 1
                predictions.append({"actual": train_data.classes[truth], "predicted": train_data.classes[guess], "confidence": float(confidence)})
    supports = [sum(row) for row in confusion]
    per_class = {}
    for index, label in enumerate(train_data.classes):
        tp = confusion[index][index]
        fp = sum(confusion[row][index] for row in range(len(confusion)) if row != index)
        fn = sum(confusion[index][column] for column in range(len(confusion)) if column != index)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0, "support": supports[index]}
    actual = [item["actual"] for item in predictions]
    predicted = [item["predicted"] for item in predictions]
    confidences = [item["confidence"] for item in predictions]
    safety_metrics = classification_metrics(actual, predicted, confidences)
    normal_labels = {"normal_or_no_visible_concern", "ok", "normal_surface", "structure_ok"}
    safety_false_negatives = [item for item in predictions if (
        item["actual"] in {"possible_structural_concern", "marine_debris", "poor_visibility"}
        and item["predicted"] in normal_labels
    ) or (item["actual"] == "unknown" and item["predicted"] != "unknown" and item["confidence"] >= 0.8)]
    manifest_hash = hashlib.sha256(Path(args.data_manifest).read_bytes()).hexdigest() if args.data_manifest else None
    config = {"task": args.task, "epochs": args.epochs, "batch_size": args.batch_size, "seed": args.seed,
              "class_balance": args.class_balance, "weights": args.weights,
              "augmentation": UnderwaterAugmentation.version}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    report = {
        "model": "EfficientNet-B0", "task": args.task, "best_val_accuracy": best_accuracy,
        "test_accuracy": sum(confusion[i][i] for i in range(len(confusion))) / max(1, sum(supports)),
        "per_class": per_class, "confusion_matrix": confusion, "history": history,
        "macro_f1": safety_metrics["macro_f1"], "balanced_accuracy": safety_metrics["balanced_accuracy"],
        "expected_calibration_error": safety_metrics["expected_calibration_error"],
        "confidence_thresholds": safety_metrics["confidence_thresholds"],
        "safety_false_negatives": safety_false_negatives,
        "sample_predictions": predictions[:20], "class_distribution": dict(zip(train_data.classes, counts)),
        "metadata": {"config": config, "config_hash": config_hash, "data_manifest_sha256": manifest_hash},
        "limitations": ["Metrics apply only to independent mission/video groups in the recorded manifest.", "Image predictions do not confirm structural failure."],
    }
    output = Path(args.output or f"models/oceansense_{args.task}_efficientnet_b0.pt")
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": best_state, "labels": train_data.classes, "task": args.task,
                "model_version": f"{args.task}_efficientnet_b0_v1", "metadata": report["metadata"]}, output)
    report_path = Path(args.report or f"outputs/evaluation_reports/{args.task}_classifier_metrics.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown = report_path.with_suffix(".md")
    markdown.write_text(
        f"# {args.task.title()} classifier report\n\n"
        f"- Test accuracy: {report['test_accuracy']:.4f}\n- Macro F1: {report['macro_f1']:.4f}\n"
        f"- Balanced accuracy: {report['balanced_accuracy']:.4f}\n"
        f"- ECE: {report['expected_calibration_error']:.4f}\n\n"
        "These metrics apply only to the recorded split and do not confirm physical damage or safety.\n",
        encoding="utf-8",
    )
    print(json.dumps({"checkpoint": str(output), "report": str(report_path), "test_accuracy": report["test_accuracy"]}, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the documented EfficientNet-B0 baseline")
    parser.add_argument("--data", required=True, help="ImageFolder root containing train/val/test")
    parser.add_argument("--output", default="models/oceansense_efficientnet_b0.pt")
    parser.add_argument("--report", default="outputs/evaluation_reports/classifier_metrics.json")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader
        from torchvision import datasets
        from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[vision]'") from exc

    torch.manual_seed(args.seed)
    root = Path(args.data)
    weights = EfficientNet_B0_Weights.DEFAULT
    transform = weights.transforms()
    train_data = datasets.ImageFolder(root / "train", transform=transform)
    val_data = datasets.ImageFolder(root / "val", transform=transform)
    test_data = datasets.ImageFolder(root / "test", transform=transform)
    if train_data.classes != val_data.classes or train_data.classes != test_data.classes:
        raise ValueError("train/val/test class directories must match")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(train_data.classes))
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    criterion = nn.CrossEntropyLoss()
    loaders = {
        "train": DataLoader(train_data, batch_size=args.batch_size, shuffle=True, num_workers=0),
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
    report = {
        "model": "EfficientNet-B0", "best_val_accuracy": best_accuracy,
        "test_accuracy": sum(confusion[i][i] for i in range(len(confusion))) / max(1, sum(supports)),
        "per_class": per_class, "confusion_matrix": confusion, "history": history,
        "sample_predictions": predictions[:20], "limitations": ["Metrics apply only to the recorded held-out split.", "Image predictions do not confirm structural failure."],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": best_state, "labels": train_data.classes, "model_version": "efficientnet_b0_v1"}, output)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"checkpoint": str(output), "report": str(report_path), "test_accuracy": report["test_accuracy"]}, indent=2))


if __name__ == "__main__":
    main()

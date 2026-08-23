from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from .dataset import read_csv
from .model import SoftmaxWeakPointClassifier
from .schema import FEATURE_NAMES


def _stratified_split(samples, test_ratio: float, seed: int):
    """Mission-group split prevents adjacent telemetry from leaking across partitions."""
    by_mission: dict[str, list] = {}
    for sample in samples:
        by_mission.setdefault(sample.mission_id, []).append(sample)
    rng = random.Random(seed)
    missions = list(by_mission)
    rng.shuffle(missions)
    test_count = max(1, round(len(missions) * test_ratio))
    test_missions = set(missions[:test_count])
    train = [sample for sample in samples if sample.mission_id not in test_missions]
    test = [sample for sample in samples if sample.mission_id in test_missions]
    if not train or not test:
        raise ValueError("at least two mission groups are required for leakage-safe splitting")
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def _metrics(actual: list[str], predicted: list[str], labels: list[str]) -> dict:
    matrix = {label: {other: 0 for other in labels} for label in labels}
    for truth, guess in zip(actual, predicted):
        matrix[truth][guess] += 1
    per_class = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(matrix[label].values())}
    accuracy = sum(a == p for a, p in zip(actual, predicted)) / len(actual)
    return {
        "accuracy": accuracy,
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(labels),
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def train_from_csv(
    input_path: str | Path,
    model_path: str | Path,
    report_path: str | Path,
    epochs: int = 180,
    seed: int = 42,
) -> dict:
    samples = read_csv(input_path)
    train, test = _stratified_split(samples, 0.2, seed)
    labels = sorted({sample.label for sample in samples})
    model = SoftmaxWeakPointClassifier(labels, list(FEATURE_NAMES))
    losses = model.fit([sample.features() for sample in train], [sample.label for sample in train], epochs=epochs, seed=seed)
    guesses = [model.predict(sample.features()).label for sample in test]
    metrics = _metrics([sample.label for sample in test], guesses, labels)
    metrics.update(
        {
            "train_rows": len(train),
            "test_rows": len(test),
            "label_distribution": dict(Counter(sample.label for sample in samples)),
            "final_train_loss": losses[-1],
            "seed": seed,
            "split_strategy": "mission_group",
            "train_missions": sorted({sample.mission_id for sample in train}),
            "test_missions": sorted({sample.mission_id for sample in test}),
        }
    )
    model.save(model_path)
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics

"""Dependency-light safety metrics shared by image evaluation scripts."""

from __future__ import annotations

from collections import defaultdict


def classification_metrics(actual: list[str], predicted: list[str], confidences: list[float],
                           bins: int = 10, latencies_ms: list[float] | None = None) -> dict:
    if not actual or not (len(actual) == len(predicted) == len(confidences)):
        raise ValueError("actual, predicted and confidences must be non-empty and equal length")
    labels = sorted(set(actual) | set(predicted))
    if latencies_ms is not None and len(latencies_ms) != len(actual):
        raise ValueError("latencies_ms must match the number of predictions")
    matrix = {truth: {guess: 0 for guess in labels} for truth in labels}
    for truth, guess in zip(actual, predicted):
        matrix[truth][guess] += 1
    per_class = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[label] = {
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "support": sum(matrix[label].values()),
            "false_positive_count": fp,
            "false_negative_count": fn,
        }
    correct = [int(truth == guess) for truth, guess in zip(actual, predicted)]
    ece = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [i for i, confidence in enumerate(confidences)
                   if (low <= confidence <= high if index == bins - 1 else low <= confidence < high)]
        if members:
            accuracy = sum(correct[i] for i in members) / len(members)
            confidence = sum(confidences[i] for i in members) / len(members)
            ece += len(members) / len(actual) * abs(accuracy - confidence)
    report = {
        "accuracy": sum(correct) / len(correct),
        "balanced_accuracy": sum(item["recall"] for item in per_class.values()) / len(per_class),
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(per_class),
        "expected_calibration_error": ece,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "confidence_thresholds": {
            f"{threshold:.1f}": {
                "coverage": sum(value >= threshold for value in confidences) / len(confidences),
                "accuracy_when_accepted": (sum(ok for ok, value in zip(correct, confidences) if value >= threshold) /
                                           max(1, sum(value >= threshold for value in confidences))),
            }
            for threshold in (0.5, 0.6, 0.7, 0.8, 0.9)
        },
    }
    if latencies_ms is not None:
        ordered_latency = sorted(float(value) for value in latencies_ms)
        percentile_index = min(len(ordered_latency) - 1, int(0.95 * len(ordered_latency)))
        total_seconds = sum(ordered_latency) / 1000.0
        report["runtime"] = {
            "mean_latency_ms": sum(ordered_latency) / len(ordered_latency),
            "p95_latency_ms": ordered_latency[percentile_index],
            "throughput_per_second": len(ordered_latency) / total_seconds if total_seconds > 0 else None,
        }
    return report


def breakdown(records: list[dict], key: str) -> dict:
    buckets: dict[str, list[int]] = defaultdict(list)
    for record in records:
        buckets[str(record[key])].append(int(record["actual"] == record["predicted"]))
    return {name: {"rows": len(values), "accuracy": sum(values) / len(values)} for name, values in sorted(buckets.items())}

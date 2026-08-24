"""Unified reliability reporting without merging deployment conditions."""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Iterable


def _classification(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted({str(item["actual"]) for item in records} | {str(item["predicted"]) for item in records})
    matrix = {truth: {guess: 0 for guess in labels} for truth in labels}
    for item in records:
        matrix[str(item["actual"])][str(item["predicted"])] += 1
    per_class = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[truth][label] for truth in labels if truth != label)
        fn = sum(matrix[label][guess] for guess in labels if guess != label)
        tn = sum(
            matrix[truth][guess]
            for truth in labels
            for guess in labels
            if truth != label and guess != label
        )
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_negative_rate": 1.0 - recall,
            "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
            "support": sum(matrix[label].values()),
        }
    return {
        "per_class": per_class,
        "macro_f1": sum(item["f1"] for item in per_class.values()) / max(1, len(per_class)),
        "confusion_matrix": matrix,
    }


def _uncertainty_metrics(records: list[dict[str, Any]]) -> dict[str, float | None]:
    confidence_rows = [row for row in records if row.get("confidence") is not None]
    ece = None
    uncertainty_error_correlation = None
    if confidence_rows:
        bin_error = 0.0
        for lower_tenth in range(10):
            lower, upper = lower_tenth / 10.0, (lower_tenth + 1) / 10.0
            bucket = [
                row for row in confidence_rows
                if lower <= float(row["confidence"]) <= upper
                and (lower_tenth == 9 or float(row["confidence"]) < upper)
            ]
            if bucket:
                accuracy = sum(row["actual"] == row["predicted"] for row in bucket) / len(bucket)
                mean_confidence = sum(float(row["confidence"]) for row in bucket) / len(bucket)
                bin_error += len(bucket) / len(confidence_rows) * abs(accuracy - mean_confidence)
        ece = bin_error
        uncertainties = [1.0 - float(row["confidence"]) for row in confidence_rows]
        errors = [float(row["actual"] != row["predicted"]) for row in confidence_rows]
        mean_u, mean_e = sum(uncertainties) / len(uncertainties), sum(errors) / len(errors)
        covariance = sum((u - mean_u) * (error - mean_e) for u, error in zip(uncertainties, errors))
        variance_u = sum((u - mean_u) ** 2 for u in uncertainties)
        variance_e = sum((error - mean_e) ** 2 for error in errors)
        if variance_u > 0 and variance_e > 0:
            uncertainty_error_correlation = covariance / math.sqrt(variance_u * variance_e)

    probability_rows = [row for row in records if isinstance(row.get("probabilities"), dict)]
    brier = None
    if probability_rows:
        squared_errors = []
        for row in probability_rows:
            probabilities = row["probabilities"]
            squared_errors.append(sum(
                (float(probability) - float(label == row["actual"])) ** 2
                for label, probability in probabilities.items()
            ))
        brier = sum(squared_errors) / len(squared_errors)

    ood_rows = [
        row for row in records
        if row.get("ood_truth") is not None and row.get("ood_score") is not None
    ]
    ood_auroc = None
    positives = [row for row in ood_rows if bool(row["ood_truth"])]
    negatives = [row for row in ood_rows if not bool(row["ood_truth"])]
    if positives and negatives:
        comparisons = [
            1.0 if float(positive["ood_score"]) > float(negative["ood_score"])
            else 0.5 if float(positive["ood_score"]) == float(negative["ood_score"])
            else 0.0
            for positive in positives
            for negative in negatives
        ]
        ood_auroc = sum(comparisons) / len(comparisons)
    return {
        "ece": ece,
        "brier_score": brier,
        "ood_auroc": ood_auroc,
        "uncertainty_error_correlation": uncertainty_error_correlation,
    }


def reliability_report(
    records: Iterable[dict[str, Any]],
    *,
    critical_labels: set[str] | None = None,
) -> dict[str, Any]:
    """Report each source condition separately and keep unmeasured metrics explicit."""
    items = list(records)
    if not items:
        raise ValueError("reliability records cannot be empty")
    critical = critical_labels or {"thruster_degradation", "buoyancy_imbalance"}
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        buckets[str(item.get("condition", "unversioned"))].append(item)
    by_condition = {}
    for condition, rows in sorted(buckets.items()):
        report = _classification(rows)
        critical_rows = [row for row in rows if row["actual"] in critical]
        detected = [row for row in critical_rows if row["predicted"] == row["actual"]]
        unsafe = [row for row in rows if bool(row.get("unsafe_recommendation"))]
        delays = [float(row["detection_delay_s"]) for row in rows if row.get("detection_delay_s") is not None]
        report["safety"] = {
            "critical_fault_recall": len(detected) / len(critical_rows) if critical_rows else None,
            "missed_critical_event_count": len(critical_rows) - len(detected),
            "unsafe_recommendation_count": len(unsafe),
        }
        report["temporal"] = {
            "mean_detection_delay_s": sum(delays) / len(delays) if delays else None,
            "time_to_stable_classification_s": None,
            "fault_recovery_time_s": None,
        }
        report["uncertainty"] = _uncertainty_metrics(rows)
        report["control"] = {
            metric: (
                sum(float(row[metric]) for row in rows if row.get(metric) is not None)
                / len([row for row in rows if row.get(metric) is not None])
                if any(row.get(metric) is not None for row in rows)
                else None
            )
            for metric in (
                "station_keeping_error_m",
                "trajectory_error_m",
                "energy_use_wh",
                "control_smoothness",
                "collision_rate",
                "mission_completion_rate",
            )
        }
        by_condition[condition] = report
    return {
        "schema_version": "1.0.0",
        "by_condition": by_condition,
        "warning": "Conditions are intentionally not merged into one accuracy number.",
    }

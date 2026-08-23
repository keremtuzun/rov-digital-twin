from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from oceansense.data import read_labels
from oceansense.evaluation import breakdown, classification_metrics
from oceansense.perception import TorchvisionDomainClassifier, TorchvisionEfficientNetClassifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate both OceanSense classifiers on the same held-out records")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--domain-checkpoint", required=True)
    parser.add_argument("--condition-checkpoint", required=True)
    parser.add_argument("--output", default="outputs/evaluation_reports/multidomain_metrics.json")
    args = parser.parse_args()

    records = [record for record in read_labels(args.labels) if record.split == "test"]
    if not records:
        raise ValueError("labels file has no test records")
    labels_path = Path(args.labels)
    domain_model = TorchvisionDomainClassifier(args.domain_checkpoint)
    condition_model = TorchvisionEfficientNetClassifier(args.condition_checkpoint)
    domain_correct = condition_correct = 0
    by_domain: dict[str, Counter] = defaultdict(Counter)
    predictions = []
    false_negatives = []
    for record in records:
        image = Path(record.file_path)
        if not image.is_absolute():
            image = labels_path.parent / image
        domain = domain_model.classify_domain(image)
        condition = condition_model.classify(image)
        domain_correct += domain.label == record.inspection_domain
        condition_correct += condition.label == record.primary_label
        bucket = by_domain[record.inspection_domain]
        bucket["rows"] += 1
        bucket["condition_correct"] += condition.label == record.primary_label
        item = {
            "sample_id": record.sample_id,
            "actual_domain": record.inspection_domain,
            "predicted_domain": domain.label,
            "domain_confidence": domain.confidence,
            "actual_condition": record.primary_label,
            "predicted_condition": condition.label,
            "condition_confidence": condition.confidence,
            "actual": record.primary_label, "predicted": condition.label,
            "source": record.source, "visibility": record.visibility_level,
            "origin": "synthetic" if record.synthetic else "real",
        }
        predictions.append(item)
        if record.contains_anomaly and condition.label in {"ok", "normal_surface", "structure_ok", "normal_water_condition"}:
            false_negatives.append(item)
    metrics = classification_metrics(
        [item["actual_condition"] for item in predictions],
        [item["predicted_condition"] for item in predictions],
        [item["condition_confidence"] for item in predictions],
    )
    report = {
        "rows": len(records),
        "domain_accuracy": domain_correct / len(records),
        "condition_accuracy": condition_correct / len(records),
        "per_domain_condition_accuracy": {
            domain: values["condition_correct"] / values["rows"] for domain, values in sorted(by_domain.items())
        },
        "macro_f1": metrics["macro_f1"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "expected_calibration_error": metrics["expected_calibration_error"],
        "confidence_thresholds": metrics["confidence_thresholds"],
        "by_source": breakdown(predictions, "source"),
        "by_visibility": breakdown(predictions, "visibility"),
        "by_real_or_synthetic": breakdown(predictions, "origin"),
        "sample_predictions": predictions[:20],
        "false_negatives_for_manual_review": false_negatives,
        "limitations": [
            "Results apply only to the held-out snapshot identified by labels.csv.",
            "No metric validates structural integrity, chemistry, coral survival, or fish population size.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(output), "rows": len(records)}, indent=2))


if __name__ == "__main__":
    main()

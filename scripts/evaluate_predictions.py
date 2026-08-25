from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from oceansense.evaluation import breakdown, classification_metrics
from oceansense.experiment import read_prediction_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model-agnostic Conrad prediction JSONL")
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--failure-index", type=Path, required=True)
    args = parser.parse_args()
    predictions = read_prediction_jsonl(args.predictions)
    rows = []
    for prediction in predictions:
        actual = prediction.metadata.get("actual_label")
        if actual is None:
            raise ValueError(f"prediction {prediction.frame_id} metadata lacks actual_label")
        rows.append({
            "frame_id": prediction.frame_id,
            "actual": str(actual),
            "predicted": prediction.class_label,
            "confidence": prediction.confidence,
            "latency_ms": prediction.metadata.get("latency_ms"),
            "visual_condition": prediction.metadata.get("visual_condition", "unversioned"),
            "failure_cause": prediction.metadata.get("failure_cause", "unreviewed"),
        })
    latencies = [float(row["latency_ms"]) for row in rows if row["latency_ms"] is not None]
    metrics = classification_metrics(
        [row["actual"] for row in rows], [row["predicted"] for row in rows],
        [float(row["confidence"]) for row in rows],
        latencies_ms=latencies if len(latencies) == len(rows) else None,
    )
    metrics["robustness_by_visual_condition"] = breakdown(rows, "visual_condition")
    metrics["evidence_boundary"] = "Metrics apply only to the supplied, manifest-linked records."
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    failures = [row for row in rows if row["actual"] != row["predicted"]]
    args.failure_index.parent.mkdir(parents=True, exist_ok=True)
    with args.failure_index.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["frame_id"])
        writer.writeheader()
        writer.writerows(failures)
    print(f"Evaluated {len(rows)} records; exported {len(failures)} failures")


if __name__ == "__main__":
    main()

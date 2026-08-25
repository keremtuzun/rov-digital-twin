from __future__ import annotations

import argparse
import json
import platform
import time
from collections import Counter, defaultdict
from pathlib import Path

from oceansense.data import read_labels
from oceansense.evaluation import breakdown, classification_metrics
from oceansense.model1_baseline_v2 import dataset_preflight, load_baseline_config, sha256_file
from oceansense.perception import TorchvisionDomainClassifier, TorchvisionEfficientNetClassifier


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


def _latency_report(values: list[float]) -> dict:
    return {
        "samples": len(values),
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "mean_ms": sum(values) / len(values),
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_confusion_png(matrix: dict[str, dict[str, int]], output: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Install the vision dependencies to write the confusion matrix") from exc
    labels = list(matrix)
    cell = 86
    margin = 260
    width = margin + cell * len(labels)
    height = margin + cell * len(labels)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    maximum = max(1, max(value for row in matrix.values() for value in row.values()))
    for row_index, truth in enumerate(labels):
        draw.text((4, margin + row_index * cell + 8), truth[:38], fill="black", font=font)
        for col_index, guess in enumerate(labels):
            count = matrix[truth].get(guess, 0)
            shade = 255 - round(190 * count / maximum)
            box = (
                margin + col_index * cell,
                margin + row_index * cell,
                margin + (col_index + 1) * cell,
                margin + (row_index + 1) * cell,
            )
            draw.rectangle(box, fill=(shade, shade, 255), outline="gray")
            draw.text((box[0] + 8, box[1] + 8), str(count), fill="black", font=font)
    for col_index, label in enumerate(labels):
        draw.text((margin + col_index * cell + 3, 4), label[:12], fill="black", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate both OceanSense classifiers on the same held-out records"
    )
    parser.add_argument("--config", help="Locked Model 1 v2 config; enforces data preflight")
    parser.add_argument("--labels")
    parser.add_argument("--domain-checkpoint")
    parser.add_argument("--condition-checkpoint")
    parser.add_argument("--output")
    parser.add_argument("--prediction-ledger")
    parser.add_argument("--confusion-matrix")
    parser.add_argument("--failure-dir")
    parser.add_argument("--warmup-runs", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    config = load_baseline_config(args.config) if args.config else None
    preflight = dataset_preflight(args.config) if args.config else None
    if config and not preflight["ready"]:
        failures = "\n- ".join(preflight["errors"])
        raise SystemExit(f"Model 1 v2 evaluation gate is blocked:\n- {failures}")
    repo_root = Path(args.config).resolve().parent.parent if config else Path.cwd()

    def configured(value: str | None, key: str, fallback: str) -> Path:
        selected = value or (config["artifacts"].get(key) if config else None) or fallback
        path = Path(selected)
        return path if path.is_absolute() else repo_root / path

    if not config and not args.labels:
        raise SystemExit("--labels is required when --config is not supplied")
    labels_path = (
        Path(args.labels)
        if args.labels
        else configured(None, "unused", config["data"]["labels"])
    )
    if not config and (not args.domain_checkpoint or not args.condition_checkpoint):
        raise SystemExit("both checkpoint arguments are required when --config is not supplied")
    domain_checkpoint = (
        Path(args.domain_checkpoint)
        if args.domain_checkpoint
        else configured(None, "unused", config["artifacts"]["domain"]["checkpoint"])
    )
    condition_checkpoint = (
        Path(args.condition_checkpoint)
        if args.condition_checkpoint
        else configured(None, "unused", config["artifacts"]["condition"]["checkpoint"])
    )
    output = configured(args.output, "evaluation_report", "outputs/evaluation_reports/multidomain_metrics.json")
    ledger = configured(args.prediction_ledger, "prediction_ledger", "outputs/evaluation_reports/predictions.jsonl")
    confusion_png = configured(args.confusion_matrix, "confusion_matrix", "outputs/evaluation_reports/confusion.png")
    failure_dir = configured(args.failure_dir, "failure_cases", "outputs/evaluation_reports/failure_cases")

    records = [record for record in read_labels(labels_path) if record.split == "test"]
    if not records:
        raise ValueError("labels file has no test records")
    if config and any(record.synthetic for record in records):
        raise ValueError("primary Model 1 v2 evaluation cannot include synthetic test rows")
    domain_model = TorchvisionDomainClassifier(domain_checkpoint)
    condition_model = TorchvisionEfficientNetClassifier(condition_checkpoint)
    if config and (
        domain_model.version != config["model_version"]
        or condition_model.version != config["model_version"]
    ):
        raise ValueError("both checkpoints must carry model_version=model1_baseline_v2")

    first_image = Path(records[0].file_path)
    if not first_image.is_absolute():
        first_image = labels_path.parent / first_image
    for _ in range(max(0, args.warmup_runs)):
        domain_model.classify_domain(first_image)
        condition_model.classify(first_image)

    by_domain: dict[str, Counter] = defaultdict(Counter)
    predictions = []
    domain_latencies: list[float] = []
    condition_latencies: list[float] = []
    for record in records:
        image = Path(record.file_path)
        if not image.is_absolute():
            image = labels_path.parent / image
        start = time.perf_counter()
        domain = domain_model.classify_domain(image)
        domain_latencies.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        condition = condition_model.classify(image)
        condition_latencies.append((time.perf_counter() - start) * 1000)
        bucket = by_domain[record.inspection_domain]
        bucket["rows"] += 1
        bucket["condition_correct"] += condition.label == record.primary_label
        predictions.append({
            "sample_id": record.sample_id,
            "image_path": str(image),
            "mission_or_video_id": record.mission_or_video_id,
            "actual_domain": record.inspection_domain,
            "predicted_domain": domain.label,
            "domain_confidence": domain.confidence,
            "domain_latency_ms": domain_latencies[-1],
            "actual_condition": record.primary_label,
            "predicted_condition": condition.label,
            "condition_confidence": condition.confidence,
            "condition_latency_ms": condition_latencies[-1],
            "actual": record.primary_label,
            "predicted": condition.label,
            "source": record.source,
            "visibility": record.visibility_level,
            "origin": "synthetic" if record.synthetic else "real",
        })

    domain_metrics = classification_metrics(
        [item["actual_domain"] for item in predictions],
        [item["predicted_domain"] for item in predictions],
        [item["domain_confidence"] for item in predictions],
        latencies_ms=domain_latencies,
    )
    condition_metrics = classification_metrics(
        [item["actual_condition"] for item in predictions],
        [item["predicted_condition"] for item in predictions],
        [item["condition_confidence"] for item in predictions],
        latencies_ms=condition_latencies,
    )
    safety_labels = {
        "possible_structural_concern",
        "marine_debris",
        "poor_visibility",
        "aquaculture_infrastructure_concern",
    }
    failure_groups = {
        "safety_false_negatives": [
            item for item in predictions
            if item["actual_condition"] in safety_labels
            and item["predicted_condition"] == "normal_or_no_visible_concern"
        ],
        "high_confidence_errors": [
            item for item in predictions
            if item["actual_condition"] != item["predicted_condition"]
            and item["condition_confidence"] >= 0.8
        ],
        "low_confidence_correct": [
            item for item in predictions
            if item["actual_condition"] == item["predicted_condition"]
            and item["condition_confidence"] < 0.6
        ],
        "domain_errors": [
            item for item in predictions if item["actual_domain"] != item["predicted_domain"]
        ],
        "biofouling_structural_confusion": [
            item for item in predictions
            if {item["actual_condition"], item["predicted_condition"]}
            == {"biofouling", "possible_structural_concern"}
        ],
        "unknown_high_confidence_errors": [
            item for item in predictions
            if item["actual_condition"] == "unknown"
            and item["predicted_condition"] != "unknown"
            and item["condition_confidence"] >= 0.8
        ],
    }
    failure_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in failure_groups.items():
        _write_jsonl(failure_dir / f"{name}.jsonl", rows)
    _write_jsonl(ledger, predictions)
    _write_confusion_png(condition_metrics["confusion_matrix"], confusion_png)
    report = {
        "model_version": config["model_version"] if config else condition_model.version,
        "rows": len(records),
        "domain": domain_metrics,
        "condition": condition_metrics,
        "per_domain_condition_accuracy": {
            domain: values["condition_correct"] / values["rows"]
            for domain, values in sorted(by_domain.items())
        },
        "by_source": breakdown(predictions, "source"),
        "by_visibility": breakdown(predictions, "visibility"),
        "by_real_or_synthetic": breakdown(predictions, "origin"),
        "latency": {
            "domain": _latency_report(domain_latencies),
            "condition": _latency_report(condition_latencies),
            "warmup_runs": args.warmup_runs,
            "host": platform.platform(),
        },
        "failure_review_counts": {name: len(rows) for name, rows in failure_groups.items()},
        "artifacts": {
            "prediction_ledger": str(ledger),
            "prediction_ledger_sha256": sha256_file(ledger),
            "confusion_matrix": str(confusion_png),
            "confusion_matrix_sha256": sha256_file(confusion_png),
            "failure_cases": str(failure_dir),
            "domain_checkpoint_sha256": sha256_file(domain_checkpoint),
            "condition_checkpoint_sha256": sha256_file(condition_checkpoint),
            "labels_sha256": sha256_file(labels_path),
            "manifest_sha256": preflight["hashes"].get("manifest") if preflight else None,
            "split_sha256": preflight["hashes"].get("split") if preflight else None,
            "config_sha256": preflight["hashes"].get("config") if preflight else None,
        },
        "limitations": [
            "Results apply only to the held-out approved snapshot identified by labels.csv.",
            "No metric validates structural integrity, chemistry, ecology, or autonomous safety.",
            "Synthetic results, if separately produced, must never be merged into primary metrics.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(output),
        "prediction_ledger": str(ledger),
        "confusion_matrix": str(confusion_png),
        "rows": len(records),
    }, indent=2))


if __name__ == "__main__":
    main()

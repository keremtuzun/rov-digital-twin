from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train optional YOLOv8n only when box annotations are defensible")
    parser.add_argument("--data", required=True, help="Ultralytics dataset YAML")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--output", default="outputs/evaluation_reports/detector_metrics.json")
    args = parser.parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[detection]'") from exc
    model = YOLO("yolov8n.pt")
    model.train(data=args.data, epochs=args.epochs, imgsz=640, project="outputs/yolo_runs", name="weak_point_v1")
    metrics = model.val(data=args.data)
    report = {
        "model": "YOLOv8n", "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map),
        "limitations": ["A box indicates a possible visual concern, not confirmed structural damage."],
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.data import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OceanSense labels and optional boxes")
    parser.add_argument("labels")
    parser.add_argument("--boxes")
    parser.add_argument("--skip-file-check", action="store_true")
    parser.add_argument("--report", default="outputs/evaluation_reports/dataset_validation.json")
    args = parser.parse_args()
    report = validate_dataset(args.labels, args.boxes, check_files=not args.skip_file_check)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

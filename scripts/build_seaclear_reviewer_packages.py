"""Build or validate blinded SeaClear reviewer queue packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.seaclear_reviewer_packages import (
    QUEUE_NAMES,
    build_reviewer_packages,
    validate_reviewer_packages,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-queue",
        default="data/model1_baseline_v2/manifests/label_review_queue.csv",
    )
    parser.add_argument(
        "--output-dir", default="data/model1_baseline_v2/review_packages"
    )
    parser.add_argument("--reviewer-1-seed", type=int, default=1101)
    parser.add_argument("--reviewer-2-seed", type=int, default=1102)
    parser.add_argument("--expected-rows", type=int, default=8610)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace pristine package templates; never use after review begins",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    existing = [output_dir / name for name in (*QUEUE_NAMES.values(), "package_manifest.json")]
    if args.validate_only:
        report = validate_reviewer_packages(output_dir, expected_rows=args.expected_rows)
    else:
        if any(path.exists() for path in existing) and not args.force:
            raise SystemExit(
                "refusing to overwrite an existing reviewer package; use --validate-only"
            )
        report = build_reviewer_packages(
            args.source_queue,
            output_dir,
            reviewer_1_seed=args.reviewer_1_seed,
            reviewer_2_seed=args.reviewer_2_seed,
        )
        if report.get("row_counts") != {
            "reviewer_1": args.expected_rows,
            "reviewer_2": args.expected_rows,
        }:
            report["valid"] = False
            report.setdefault("errors", []).append("generated row counts do not match expectation")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["valid"] else 2)


if __name__ == "__main__":
    main()

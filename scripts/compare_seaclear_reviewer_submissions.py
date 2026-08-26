"""Validate and compare completed, independent SeaClear review submissions."""

from __future__ import annotations

import argparse
import json

from oceansense.seaclear_submission_intake import compare_submissions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reviewer-1",
        default="data/model1_baseline_v2/review_submissions/reviewer_1_completed.csv",
    )
    parser.add_argument(
        "--reviewer-2",
        default="data/model1_baseline_v2/review_submissions/reviewer_2_completed.csv",
    )
    parser.add_argument(
        "--package-dir", default="data/model1_baseline_v2/review_packages"
    )
    parser.add_argument(
        "--schema", default="data/model1_baseline_v2/manifests/label_review_schema.json"
    )
    parser.add_argument(
        "--output-dir", default="data/model1_baseline_v2/review_results"
    )
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = compare_submissions(
            args.reviewer_1, args.reviewer_2, args.package_dir, args.schema, args.output_dir
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INPUT_ERROR", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.strict and summary["status"] != "VALID":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

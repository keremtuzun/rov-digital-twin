"""Build the SeaClear staging manifest without approving data or starting training."""

from __future__ import annotations

import argparse
import json

from oceansense.seaclear import build_source_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--extracted-root",
        default="data/model1_baseline_v2/raw/seaclear/v1/extracted",
    )
    parser.add_argument(
        "--output",
        default="data/model1_baseline_v2/manifests/seaclear_source_assets.csv",
    )
    parser.add_argument(
        "--summary",
        default="data/model1_baseline_v2/manifests/seaclear_source_summary.json",
    )
    args = parser.parse_args()
    summary = build_source_manifest(args.extracted_root, args.output, args.summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

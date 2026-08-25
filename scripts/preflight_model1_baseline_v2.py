from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model1_baseline_v2 import dataset_preflight


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate every Model 1 baseline v2 data gate without training")
    parser.add_argument("--config", default="configs/model1_baseline_v2.yaml")
    parser.add_argument("--skip-image-check", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()

    report = dataset_preflight(args.config, check_images=not args.skip_image_check)
    if args.report:
        output = Path(args.report)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

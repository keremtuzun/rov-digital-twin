"""Build the immutable, synthetic-only Twin 2 S1 comparison release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2.s1_release import build_s1_release


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/model2/s1_synthetic_release.json")
    parser.add_argument("--output", default="data/model2/s1_synthetic")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    report = build_s1_release(config, args.output, force=args.force)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Build the deterministic, debug-only Twin 2 D0 dataset release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2.d0_release import build_d0_release


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/model2/d0_debug_release.json")
    parser.add_argument("--output", default="data/model2/d0_debug")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    report = build_d0_release(config, args.output, force=args.force)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

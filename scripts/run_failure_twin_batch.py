from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.failure_twin import generate_batch


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate claim-bounded 2D visual inspection fixtures"
    )
    parser.add_argument("--config", type=Path, default=Path("config/failure_twin_mvp.json"))
    parser.add_argument("--output", type=Path, default=Path("outputs/failure_twin_mvp"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    records = generate_batch(config, args.output)
    print(f"Generated {len(records)} paired synthetic scenarios in {args.output}")


if __name__ == "__main__":
    main()

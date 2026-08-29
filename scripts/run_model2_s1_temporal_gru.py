"""Run the frozen S1 Temporal GRU baseline for all predeclared seeds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2.temporal_gru import run_temporal_gru


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="configs/model2/s1_learned_baseline_eval.json"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run_temporal_gru(root / args.config, root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

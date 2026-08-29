"""Run Last Observation and Simple Heuristic on the frozen synthetic S1 release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oceansense.model2.s1_deterministic import run_s1_deterministic_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="configs/model2/s1_learned_baseline_eval.json"
    )
    parser.add_argument("--output-dir", default="reports/model2/s1_baselines")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    comparison = run_s1_deterministic_evaluation(
        root / args.config, root, root / args.output_dir
    )
    print(json.dumps(comparison, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

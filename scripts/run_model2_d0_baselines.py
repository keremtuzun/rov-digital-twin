"""Run non-trained Last Observation and Simple Heuristic D0 smoke baselines."""

from __future__ import annotations

import argparse
import json

from oceansense.model2.evaluation import output_hashes, run_d0_smoke_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", default="data/model2/d0_debug")
    parser.add_argument("--output-dir", default="reports/model2/d0_baselines")
    args = parser.parse_args()
    comparison = run_d0_smoke_evaluation(args.release_dir, args.output_dir)
    print(json.dumps({
        "status": "D0_DEBUG_SMOKE_COMPLETE",
        "training_performed": False,
        "debug_only": True,
        "comparison": comparison,
        "output_sha256": output_hashes(args.output_dir),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

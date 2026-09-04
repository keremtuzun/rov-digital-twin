"""Run one conventional graph baseline, without replacing any previous run."""

import argparse
import json
from pathlib import Path

from oceansense.model2.graph_training import GRAPH_BASELINES, run_graph_baseline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", choices=GRAPH_BASELINES)
    parser.add_argument("--config", default="configs/model2/s1_learned_baseline_eval.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(run_graph_baseline(root / args.config, root, args.baseline), indent=2))


if __name__ == "__main__":
    main()

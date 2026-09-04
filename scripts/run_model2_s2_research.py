"""Run the approved local S2 synthetic experiment, once."""

from pathlib import Path

import torch

from oceansense.model2.research_experiment import run_experiment

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    torch.set_num_threads(1)
    run_experiment(root, root / "configs/model2/s2_research_protocol.json")
    print("S2 complete: reports/model2/s2_research_v0/summary.json")

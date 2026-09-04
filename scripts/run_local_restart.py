"""Run the preregistered, local-only synthetic training restart."""
from pathlib import Path
import json
import torch

from oceansense.local_restart import run

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    torch.set_num_threads(2)
    print(json.dumps(run(root, root / "configs/restart_local_v1.json"), indent=2))

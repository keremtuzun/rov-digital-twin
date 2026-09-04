from pathlib import Path
import json
import torch
from oceansense.seaclear_finetune import run

if __name__ == "__main__":
    torch.set_num_threads(2)
    print(json.dumps(run(Path(__file__).resolve().parents[1]), indent=2))

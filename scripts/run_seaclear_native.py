from pathlib import Path
import argparse
import json
import torch

from oceansense.seaclear_native import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extracted", required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    print(json.dumps(run(Path(__file__).resolve().parents[1], Path(args.extracted)), indent=2))

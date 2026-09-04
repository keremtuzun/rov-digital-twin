"""Inspect training images only; never open held-out data during model selection."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "configs/restart_local_v1.json").read_text())
    data = np.load(root / "data/local-synthetic-restart-v1/train.npz", allow_pickle=False)
    sheet = Image.new("RGB", (640, 600), "white")
    draw = ImageDraw.Draw(sheet)
    for scene in range(4):
        for view in range(4):
            x, y = view * 160, scene * 150
            picture = Image.fromarray(data["images"][scene, view].transpose(1, 2, 0)).resize((128, 128))
            sheet.paste(picture, (x, y))
            label = protocol["model1"]["classes"][int(data["labels"][scene, view])]
            draw.text((x, y + 130), label, fill="black")
    sheet.save(args.output)

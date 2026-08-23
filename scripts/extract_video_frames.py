from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract deterministic frames from an approved local video")
    parser.add_argument("video")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--mission", required=True)
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required and was not found")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pattern = output / "frame_%08d.jpg"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", args.video,
                    "-vf", f"fps={args.fps}", "-q:v", "2", str(pattern)], check=True)
    metadata = [{"file": path.name, "mission_or_video_id": args.mission,
                 "frame_index": index, "frame_timestamp_s": index / args.fps}
                for index, path in enumerate(sorted(output.glob("frame_*.jpg")))]
    (output / "frames.metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Extracted {len(metadata)} frames")


if __name__ == "__main__":
    main()

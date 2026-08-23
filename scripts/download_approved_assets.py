"""Opt-in downloader that accepts only license-audited manifest rows."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

from oceansense.governance import license_gate, read_manifest, sha256_file


def download(row: dict[str, str], output_dir: Path, delay_s: float) -> Path:
    allowed, reason = license_gate(row)
    if not allowed:
        raise ValueError(f"asset {row['sample_id']} is not download-approved: {reason}")
    url = row["original_asset_url"]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("downloader accepts only HTTP(S) asset URLs")
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robots = urllib.robotparser.RobotFileParser(robots_url)
    try:
        robots.read()
    except (OSError, urllib.error.URLError):
        raise RuntimeError(f"could not verify robots.txt for {parsed.netloc}") from None
    if not robots.can_fetch("OceanSenseResearchBot/1.0", url):
        raise PermissionError(f"robots.txt disallows asset: {url}")
    destination = output_dir / row["source_name"].replace(" ", "_") / f"{row['sample_id']}{Path(parsed.path).suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(url, headers={"User-Agent": "OceanSenseResearchBot/1.0"})
    if offset:
        request.add_header("Range", f"bytes={offset}-")
    time.sleep(delay_s)
    with urllib.request.urlopen(request, timeout=60) as response:
        mode = "ab" if offset and response.status == 206 else "wb"
        with partial.open(mode) as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
    if sha256_file(partial) != row["sha256"]:
        raise ValueError(f"checksum mismatch for {row['sample_id']}; partial retained for inspection")
    partial.replace(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Download explicitly approved assets with resume/checksum/robots gates")
    parser.add_argument("approved_manifest")
    parser.add_argument("--output-dir", default="dataset/raw")
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--confirm", action="store_true", help="Required explicit acknowledgement")
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("Refusing network download without --confirm after reviewing size and license audit")
    rows = read_manifest(args.approved_manifest)
    for row in rows:
        print(download(row, Path(args.output_dir), max(0.5, args.delay_seconds)))


if __name__ == "__main__":
    main()

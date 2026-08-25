from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from oceansense.navigation_contracts import read_mission_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and summarize replayable navigation events")
    parser.add_argument("events", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    events = read_mission_events(args.events)
    if not events:
        raise ValueError("navigation event log is empty")
    missions = sorted({event.mission_id for event in events})
    timestamps = [event.timestamp for event in events]
    summary = {
        "schema_version": "1.0.0",
        "event_count": len(events),
        "mission_ids": missions,
        "event_types": dict(sorted(Counter(event.event_type for event in events).items())),
        "timestamp_monotonic": timestamps == sorted(timestamps),
        "sensor_frame_count": sum(event.sensor_frame is not None for event in events),
        "robot_state_count": sum(event.robot_state is not None for event in events),
        "inspection_consumable_without_unity_ui": True,
        "limitations": [
            "This validates a saved event contract; it does not measure simulator fidelity.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Validated {len(events)} navigation events from {len(missions)} mission(s)")


if __name__ == "__main__":
    main()

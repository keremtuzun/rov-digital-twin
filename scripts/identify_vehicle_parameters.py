"""Estimate identifiable simulator parameters from canonical real telemetry exports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rov_dt.real_data import CanonicalTelemetryRecord, load_csv, load_jsonl


def _solve_3x3(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-9:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [left - factor * right for left, right in zip(augmented[row], augmented[column])]
    return [augmented[index][-1] for index in range(3)]


def _speed(record: CanonicalTelemetryRecord) -> float | None:
    velocity = record.measurements.get("dvl_velocity_mps")
    return sum(value * value for value in velocity) ** 0.5 if velocity else None


def _command(record: CanonicalTelemetryRecord) -> float | None:
    commands = record.measurements.get("thruster_commands")
    return sum(abs(value) for value in commands) / len(commands) if commands else None


def identify(records: list[CanonicalTelemetryRecord], vehicle_id: str) -> dict:
    ordered = sorted((record for record in records if record.vehicle_id == vehicle_id), key=lambda item: item.timestamp_s)
    rows: list[tuple[list[float], float]] = []
    for left, right in zip(ordered, ordered[1:]):
        dt = right.timestamp_s - left.timestamp_s
        speed_left, speed_right, command = _speed(left), _speed(right), _command(left)
        if dt <= 0 or speed_left is None or speed_right is None or command is None:
            continue
        acceleration = (speed_right - speed_left) / dt
        rows.append(([command, -speed_left, -speed_left * abs(speed_left)], acceleration))
    matrix = [[sum(features[i] * features[j] for features, _ in rows) for j in range(3)] for i in range(3)]
    vector = [sum(features[i] * target for features, target in rows) for i in range(3)]
    solution = _solve_3x3(matrix, vector) if len(rows) >= 12 else None
    currents = []
    for record in ordered:
        current = record.measurements.get("motor_current_a")
        voltage = record.measurements.get("battery_voltage_v")
        if current and voltage is not None:
            currents.append((sum(abs(value) for value in current), float(voltage)))
    resistance = None
    if len(currents) >= 3:
        mean_i = sum(item[0] for item in currents) / len(currents)
        mean_v = sum(item[1] for item in currents) / len(currents)
        denominator = sum((item[0] - mean_i) ** 2 for item in currents)
        if denominator > 1e-9:
            resistance = -sum((item[0] - mean_i) * (item[1] - mean_v) for item in currents) / denominator
    fitted = {
        "thruster_gain_mps2_per_command": solution[0] if solution else None,
        "linear_drag_per_second": solution[1] if solution else None,
        "quadratic_drag_per_meter": solution[2] if solution else None,
        "battery_internal_resistance_ohm": resistance,
        "added_mass_kg": None,
        "buoyancy_newtons": None,
        "center_of_buoyancy_m": None,
        "thruster_lag_seconds": None,
    }
    return {
        "profile_schema_version": "1.0.0",
        "vehicle_id": vehicle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_missions": sorted({record.mission_id for record in ordered}),
        "fit_samples": len(rows),
        "parameters": fitted,
        "validity": {name: value is not None for name, value in fitted.items()},
        "method": "one_step_longitudinal_least_squares",
        "limitations": "Null parameters were not identifiable from the available channels and were not invented.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--vehicle-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = load_jsonl(args.input) if args.input.suffix.lower() == ".jsonl" else load_csv(args.input)
    profile = identify(records, args.vehicle_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

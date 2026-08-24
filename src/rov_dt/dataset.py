from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from .schema import TelemetrySample, WeakPoint


LABELS = tuple(item.value for item in WeakPoint if item is not WeakPoint.UNKNOWN)


def _bounded(rng: random.Random, mean: float, sigma: float, low: float, high: float) -> float:
    return min(high, max(low, rng.gauss(mean, sigma)))


def generate_dataset(rows: int = 4000, seed: int = 42) -> list[TelemetrySample]:
    """Create balanced, deterministic telemetry with physically interpretable fault signatures."""
    if rows < len(LABELS):
        raise ValueError(f"rows must be at least {len(LABELS)}")
    rng = random.Random(seed)
    duties = ("station_keeping", "pipeline_tracking", "target_waypoint")
    samples: list[TelemetrySample] = []
    for index in range(rows):
        label = LABELS[index % len(LABELS)]
        duty = duties[index % len(duties)]
        target_depth = rng.uniform(4.0, 80.0)
        depth_error = rng.gauss(0.0, 0.12)
        speed = _bounded(rng, 0.65, 0.18, 0.0, 1.8)
        vertical_speed = rng.gauss(0.0, 0.045)
        roll = rng.gauss(0.0, 1.2)
        pitch = rng.gauss(0.0, 1.2)
        yaw_rate = rng.gauss(0.0, 2.0)
        current = _bounded(rng, 18.0, 2.2, 5.0, 45.0)
        voltage = _bounded(rng, 47.5, 0.5, 40.0, 51.0)
        command = _bounded(rng, 0.48, 0.14, 0.05, 0.95)
        response = _bounded(rng, 0.97, 0.035, 0.2, 1.1)
        disagreement = abs(rng.gauss(0.05, 0.035))
        dvl_quality = _bounded(rng, 0.94, 0.04, 0.0, 1.0)
        temperature = _bounded(rng, 31.0, 3.0, 10.0, 70.0)

        if label == WeakPoint.THRUSTER_DEGRADATION.value:
            response = _bounded(rng, 0.48, 0.13, 0.1, 0.78)
            current += rng.uniform(5.0, 13.0)
            speed *= rng.uniform(0.45, 0.78)
            yaw_rate += rng.choice((-1, 1)) * rng.uniform(5.0, 14.0)
        elif label == WeakPoint.BUOYANCY_IMBALANCE.value:
            vertical_speed += rng.choice((-1, 1)) * rng.uniform(0.22, 0.65)
            depth_error += rng.choice((-1, 1)) * rng.uniform(0.8, 2.8)
            pitch += rng.choice((-1, 1)) * rng.uniform(6.0, 16.0)
        elif label == WeakPoint.SENSOR_DRIFT.value:
            disagreement = rng.uniform(0.65, 2.8)
            dvl_quality = _bounded(rng, 0.48, 0.18, 0.05, 0.82)
            depth_error += rng.gauss(0.0, 0.35)
        elif label == WeakPoint.HYDRODYNAMIC_DRAG.value:
            current += rng.uniform(5.0, 11.0)
            speed *= rng.uniform(0.35, 0.66)
            response = _bounded(rng, 0.82, 0.08, 0.55, 1.0)
            roll += rng.gauss(0.0, 3.0)

        samples.append(
            TelemetrySample(
                timestamp_s=round(index * 0.1, 3),
                mission_id=f"sim-{index // 200:04d}",
                duty=duty,
                depth_m=round(target_depth + depth_error, 5),
                depth_error_m=round(depth_error, 5),
                speed_mps=round(speed, 5),
                vertical_speed_mps=round(vertical_speed, 5),
                roll_deg=round(roll, 5),
                pitch_deg=round(pitch, 5),
                yaw_rate_dps=round(yaw_rate, 5),
                current_a=round(current, 5),
                voltage_v=round(voltage, 5),
                thruster_cmd_mean=round(command, 5),
                thruster_response_ratio=round(response, 5),
                imu_depth_disagreement_m=round(disagreement, 5),
                dvl_quality=round(dvl_quality, 5),
                temperature_c=round(temperature, 5),
                label=label,
            )
        )
    rng.shuffle(samples)
    return samples


def write_csv(samples: list[TelemetrySample], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(samples[0].to_dict()))
        writer.writeheader()
        writer.writerows(sample.to_dict() for sample in samples)
    return path


def read_csv(input_path: str | Path) -> list[TelemetrySample]:
    with Path(input_path).open(newline="", encoding="utf-8") as handle:
        return [TelemetrySample.from_dict(row) for row in csv.DictReader(handle)]


def build_llm_instructions(samples: list[TelemetrySample], limit: int = 1000) -> list[dict]:
    records: list[dict] = []
    for sample in samples[:limit]:
        key = sample.label
        response_map = {
            "nominal": "Telemetry is nominal. Continue mission and maintain routine monitoring.",
            "thruster_degradation": "Probable thruster degradation. Reduce load, inspect command-to-response ratio and request operator review.",
            "buoyancy_imbalance": "Probable buoyancy imbalance. Enter depth-hold safe mode and inspect trim or ballast state.",
            "sensor_drift": "Probable sensor drift. Cross-check IMU, pressure and DVL sources; do not trust autonomous depth estimates.",
            "hydrodynamic_drag": "Probable excess hydrodynamic drag. Reduce speed and inspect tether, fouling or external obstruction.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": "You are a safety-focused underwater-robot diagnostics specialist. Never bypass operator or vehicle safety gates."},
                    {"role": "user", "content": json.dumps(sample.to_dict(), sort_keys=True)},
                    {"role": "assistant", "content": response_map[key]},
                ],
                "weak_point": key,
            }
        )
    return records


def write_jsonl(records: list[dict], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path

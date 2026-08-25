"""Reproducible 2D visual fixture for interface and controlled-image experiments.

This module simulates inspected structures and visual evidence. It deliberately does
not implement the graph-based Model 2 Failure Twin v0, simulate robot motion, or claim
calibrated physical damage rendering.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


STRUCTURES = {"pipe", "weld", "joint", "plate", "cable", "platform_support", "concrete_pier"}
MATERIALS = {"steel", "coated_steel", "concrete", "composite", "unknown"}
DEFECTS = {
    "corrosion", "crack", "coating_loss", "deformation", "biofouling",
    "sediment_coverage", "leak_like_anomaly",
}
SEVERITIES = {"mild": 1, "moderate": 2, "severe": 3, "critical": 4}
PATTERNS = {"localized", "linear", "ring_shaped", "patchy", "spreading", "edge_adjacent", "weld_adjacent"}
INTENDED_USES = {"model2_r_and_d", "evaluation_fixture", "demo", "ablation"}


@dataclass(frozen=True)
class FailureScenario:
    scenario_id: str
    structure_type: str
    material_type: str
    defect_type: str
    severity: str
    spatial_pattern: str
    seed: int
    width: int = 512
    height: int = 320
    turbidity: float = 0.25
    low_light: float = 0.15
    blur_radius: float = 0.4
    backscatter: float = 0.15
    occlusion: float = 0.0
    viewpoint_angle_deg: float = 15.0
    distance_m: float = 1.2
    lighting_condition: str = "artificial_light"
    contrast: float = 0.8
    intended_use: str = "model2_r_and_d"

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id is required")
        for value, allowed, name in (
            (self.structure_type, STRUCTURES, "structure_type"),
            (self.material_type, MATERIALS, "material_type"),
            (self.defect_type, DEFECTS, "defect_type"),
            (self.severity, set(SEVERITIES), "severity"),
            (self.spatial_pattern, PATTERNS, "spatial_pattern"),
        ):
            if value not in allowed:
                raise ValueError(f"unsupported {name}: {value}")
        if self.width < 128 or self.height < 128:
            raise ValueError("visual fixture output must be at least 128x128")
        for name in ("turbidity", "low_light", "backscatter", "occlusion"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0 <= self.viewpoint_angle_deg <= 85 or self.distance_m <= 0:
            raise ValueError("viewpoint angle or distance is outside the supported MVP range")
        if not 0.1 <= self.contrast <= 1.5:
            raise ValueError("contrast must be between 0.1 and 1.5")
        if self.intended_use not in INTENDED_USES:
            raise ValueError(f"unsupported intended_use: {self.intended_use}")


def _split_for(scenario_id: str) -> str:
    bucket = int(hashlib.sha256(scenario_id.encode()).hexdigest()[:8], 16) % 100
    return "train" if bucket < 70 else ("validation" if bucket < 85 else "test")


def _structure_geometry(draw: Any, scenario: FailureScenario) -> tuple[int, int, int, int]:
    width, height = scenario.width, scenario.height
    top, bottom = int(height * 0.30), int(height * 0.70)
    left, right = int(width * 0.08), int(width * 0.92)
    base = (71, 91, 93)
    edge = (30, 47, 50)
    if scenario.structure_type in {"pipe", "joint", "weld", "cable"}:
        draw.rounded_rectangle((left, top, right, bottom), radius=(bottom - top) // 2,
                               fill=base, outline=edge, width=5)
        if scenario.structure_type in {"joint", "weld"}:
            center = width // 2
            draw.rectangle((center - 18, top - 4, center + 18, bottom + 4),
                           fill=(93, 105, 101), outline=edge, width=4)
    else:
        draw.rectangle((left, int(height * 0.18), right, int(height * 0.82)),
                       fill=base, outline=edge, width=5)
    return left, top, right, bottom


def _add_defect(image: Any, mask: Any, scenario: FailureScenario, rng: random.Random) -> None:
    from PIL import ImageDraw

    draw, mask_draw = ImageDraw.Draw(image), ImageDraw.Draw(mask)
    severity = SEVERITIES[scenario.severity]
    cx = int(scenario.width * (0.48 + rng.uniform(-0.12, 0.12)))
    cy = int(scenario.height * (0.50 + rng.uniform(-0.08, 0.08)))
    radius = 12 + severity * 11
    defect = scenario.defect_type
    if defect == "crack":
        points = [(cx - radius * 2, cy)]
        for step in range(1, 7):
            points.append((cx - radius * 2 + step * radius * 4 // 6,
                           cy + rng.randint(-radius // 2, radius // 2)))
        draw.line(points, fill=(31, 22, 18), width=2 + severity)
        mask_draw.line(points, fill=255, width=5 + severity * 2)
    elif defect == "coating_loss":
        box = (cx - radius * 2, cy - radius, cx + radius * 2, cy + radius)
        draw.ellipse(box, fill=(113, 78, 48), outline=(57, 43, 32), width=3)
        mask_draw.ellipse(box, fill=255)
    elif defect == "deformation":
        points = [(cx - radius * 2, cy), (cx, cy + radius), (cx + radius * 2, cy)]
        draw.line(points, fill=(24, 43, 47), width=7 + severity * 2)
        mask_draw.line(points, fill=255, width=12 + severity * 3)
    elif defect == "leak_like_anomaly":
        for index in range(5 + severity * 3):
            bubble = max(2, radius // (3 + index % 3))
            x = cx + rng.randint(-radius, radius)
            y = cy - index * 7 + rng.randint(-4, 4)
            draw.ellipse((x - bubble, y - bubble, x + bubble, y + bubble),
                         outline=(167, 207, 207), width=2)
            mask_draw.ellipse((x - bubble, y - bubble, x + bubble, y + bubble), fill=255)
    else:
        count = 8 + severity * 8
        color = {
            "corrosion": (126, 72, 38), "biofouling": (54, 103, 61),
            "sediment_coverage": (115, 101, 72),
        }[defect]
        for _ in range(count):
            x, y = cx + rng.randint(-radius * 2, radius * 2), cy + rng.randint(-radius, radius)
            blob = rng.randint(4, 8 + severity * 3)
            draw.ellipse((x - blob, y - blob, x + blob, y + blob), fill=color)
            mask_draw.ellipse((x - blob, y - blob, x + blob, y + blob), fill=255)


def _apply_water_conditions(image: Any, scenario: FailureScenario, rng: random.Random) -> Any:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    blue_green = Image.new("RGB", image.size, (18, 82, 91))
    image = Image.blend(image, blue_green, scenario.turbidity * 0.45)
    image = ImageEnhance.Brightness(image).enhance(max(0.2, 1.0 - scenario.low_light * 0.7))
    image = ImageEnhance.Contrast(image).enhance(scenario.contrast)
    if scenario.blur_radius:
        image = image.filter(ImageFilter.GaussianBlur(scenario.blur_radius))
    draw = ImageDraw.Draw(image)
    particles = int(scenario.backscatter * scenario.width * scenario.height / 650)
    for _ in range(particles):
        x, y = rng.randrange(scenario.width), rng.randrange(scenario.height)
        radius = rng.choice((1, 1, 2))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius),
                     fill=(135, 176, 177))
    if scenario.occlusion:
        occlusion_width = int(scenario.width * scenario.occlusion * 0.35)
        draw.rectangle((scenario.width - occlusion_width, 0, scenario.width, scenario.height),
                       fill=(9, 35, 38))
    return image


def generate_pair(scenario: FailureScenario, output_dir: str | Path) -> dict[str, Any]:
    """Generate a normal/degraded pair, mask, and claim-bounded metadata."""
    from PIL import Image, ImageDraw

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(scenario.seed)
    base = Image.new("RGB", (scenario.width, scenario.height), (14, 71, 83))
    _structure_geometry(ImageDraw.Draw(base), scenario)
    normal = _apply_water_conditions(base.copy(), scenario, random.Random(scenario.seed + 1))
    degraded_raw = base.copy()
    mask = Image.new("L", base.size, 0)
    _add_defect(degraded_raw, mask, scenario, rng)
    degraded = _apply_water_conditions(degraded_raw, scenario, random.Random(scenario.seed + 1))
    stem = scenario.scenario_id
    paths = {
        "normal_image": output / f"{stem}_normal.png",
        "degraded_image": output / f"{stem}_degraded.png",
        "ground_truth_mask": output / f"{stem}_mask.png",
        "metadata": output / f"{stem}.json",
    }
    normal.save(paths["normal_image"])
    degraded.save(paths["degraded_image"])
    mask.save(paths["ground_truth_mask"])
    mask_box = mask.getbbox()
    severity_score = SEVERITIES[scenario.severity] / max(SEVERITIES.values())
    visual_condition = {
        "turbidity": scenario.turbidity,
        "low_light": scenario.low_light,
        "blur_radius": scenario.blur_radius,
        "backscatter": scenario.backscatter,
        "occlusion_level": scenario.occlusion,
        "contrast": scenario.contrast,
    }
    metadata = {
        "schema_version": "1.0.0",
        "scenario_id": scenario.scenario_id,
        "random_seed": scenario.seed,
        "structure_type": scenario.structure_type,
        "material_type": scenario.material_type,
        "defect_type": scenario.defect_type,
        "severity_label": scenario.severity,
        "severity_score": severity_score,
        "spatial_pattern": scenario.spatial_pattern,
        "visual_condition": visual_condition,
        "viewpoint_angle": scenario.viewpoint_angle_deg,
        "camera_distance": scenario.distance_m,
        "turbidity": scenario.turbidity,
        "lighting": scenario.lighting_condition,
        "occlusion_level": scenario.occlusion,
        "output_image_path": str(paths["degraded_image"]),
        "mask_path": str(paths["ground_truth_mask"]),
        "box_coordinates": list(mask_box) if mask_box else None,
        "scenario": asdict(scenario),
        "split": _split_for(scenario.scenario_id),
        "synthetic_or_real": "synthetic",
        "intended_use": scenario.intended_use,
        "generator": "oceansense.failure_twin_v1",
        "ground_truth": {"mask_path": str(paths["ground_truth_mask"]),
                         "box_coordinates": list(mask_box) if mask_box else None,
                         "severity_ordinal": SEVERITIES[scenario.severity],
                         "severity_score": severity_score},
        "artifacts": {key: str(path) for key, path in paths.items() if key != "metadata"},
        "caption": (f"Synthetic {scenario.structure_type} with {scenario.severity} "
                    f"{scenario.defect_type}; uncalibrated visual scenario."),
        "claim_boundary": ("Controlled synthetic evidence for software experiments; not physical "
                           "damage truth and not real-world validation."),
        "limitations": [
            "Geometry and degradation are controlled 2D approximations.",
            "Severity is a generator parameter, not a calibrated engineering assessment.",
            "Synthetic evidence cannot establish real-world inspection accuracy.",
        ],
    }
    paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def generate_batch(config: dict[str, Any], output_dir: str | Path) -> list[dict[str, Any]]:
    count, master_seed = int(config.get("count", 100)), int(config.get("seed", 2026))
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(master_seed)
    records = []
    for index in range(count):
        severity = rng.choice(list(SEVERITIES))
        scenario = FailureScenario(
            scenario_id=f"FT-{master_seed}-{index:05d}",
            structure_type=rng.choice(sorted(STRUCTURES)),
            material_type=rng.choice(sorted(MATERIALS - {"unknown"})),
            defect_type=rng.choice(sorted(DEFECTS)),
            severity=severity,
            spatial_pattern=rng.choice(sorted(PATTERNS)),
            seed=master_seed * 100_000 + index,
            width=int(config.get("width", 512)), height=int(config.get("height", 320)),
            turbidity=rng.uniform(0.05, 0.65), low_light=rng.uniform(0.0, 0.55),
            blur_radius=rng.uniform(0.0, 1.4), backscatter=rng.uniform(0.0, 0.5),
            occlusion=rng.uniform(0.0, 0.25), viewpoint_angle_deg=rng.uniform(0.0, 60.0),
            distance_m=rng.uniform(0.5, 3.0), contrast=rng.uniform(0.55, 1.15),
            intended_use=str(config.get("intended_use", "model2_r_and_d")),
        )
        records.append(generate_pair(scenario, output_dir))
    index_path = Path(output_dir) / "index.jsonl"
    index_path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    for split in ("train", "validation", "test"):
        split_records = [record for record in records if record["split"] == split]
        (Path(output_dir) / f"{split}_manifest.jsonl").write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in split_records),
            encoding="utf-8",
        )
    split_summary = {
        split: sorted(record["scenario_id"] for record in records if record["split"] == split)
        for split in ("train", "validation", "test")
    }
    assigned_scenarios = [
        scenario_id for values in split_summary.values() for scenario_id in values
    ]
    if len(assigned_scenarios) != len(set(assigned_scenarios)):
        raise RuntimeError("scenario leakage detected across failure-twin splits")
    (Path(output_dir) / "split_manifest.json").write_text(
        json.dumps(split_summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return records

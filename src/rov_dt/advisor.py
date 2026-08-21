from __future__ import annotations

from dataclasses import dataclass

from .schema import TelemetrySample


@dataclass(frozen=True)
class Advisory:
    diagnosis: str
    evidence: list[str]
    recommended_checks: list[str]


class DomainAdvisor:
    """Deterministic baseline. Replace with a fine-tuned/RAG LLM behind the same interface."""

    CHECKS = {
        "nominal": ["Continue trend monitoring", "Keep periodic sensor cross-checks"],
        "thruster_degradation": ["Compare commanded and measured thrust", "Inspect propeller, ESC and current draw", "Run low-load thruster isolation test"],
        "buoyancy_imbalance": ["Verify ballast and payload shift", "Inspect leak indicators", "Recalibrate center of buoyancy"],
        "sensor_drift": ["Cross-check pressure, IMU and DVL", "Reject implausible source", "Recalibrate only in a controlled state"],
        "hydrodynamic_drag": ["Inspect tether and external obstruction", "Check fouling and frame damage", "Compare current draw at fixed speed"],
    }

    def advise(self, label: str, sample: TelemetrySample) -> Advisory:
        evidence = []
        if sample.thruster_response_ratio < 0.75:
            evidence.append(f"low thrust response ratio ({sample.thruster_response_ratio:.2f})")
        if sample.imu_depth_disagreement_m > 0.5:
            evidence.append(f"sensor disagreement ({sample.imu_depth_disagreement_m:.2f} m)")
        if abs(sample.depth_error_m) > 0.7:
            evidence.append(f"large depth error ({sample.depth_error_m:.2f} m)")
        if sample.current_a > 25:
            evidence.append(f"high current draw ({sample.current_a:.1f} A)")
        if not evidence:
            evidence.append("telemetry remains inside baseline operating envelope")
        return Advisory(label.replace("_", " "), evidence, self.CHECKS[label])

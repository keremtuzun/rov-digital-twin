"""Fast static acceptance check for the Unity project; never launches training."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNITY = ROOT / "unity"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


def main() -> None:
    manifest = json.loads((UNITY / "Packages/manifest.json").read_text(encoding="utf-8"))
    dependencies = manifest["dependencies"]
    require(dependencies.get("com.unity.ml-agents") == "4.0.0", "ML-Agents is pinned to 4.0.0")
    require("#v0.7.0" in dependencies.get("com.unity.robotics.ros-tcp-connector", ""), "ROS connector is pinned")
    version = (UNITY / "ProjectSettings/ProjectVersion.txt").read_text(encoding="utf-8")
    require("6000.0" in version, "Unity 6 project version is declared")

    scripts = UNITY / "Assets/ROVDigitalTwin/Scripts"
    required = {
        "ROVVehicle.cs", "Thruster.cs", "Hydrodynamics6Dof.cs", "ImuSensor.cs", "DepthSensor.cs",
        "DvlSensor.cs", "ForwardSonarSensor.cs", "DutyManager.cs", "ROVRLAgent.cs",
        "OceanSenseApiClient.cs", "TelemetryUdpBridge.cs", "OceanSenseDashboard.cs",
        "SimulatedPowerSensor.cs", "FaultInjectionController.cs", "SyntheticCaptureController.cs",
    }
    require(not (required - {path.name for path in scripts.glob("*.cs")}), "all runtime subsystems exist")
    agent = (scripts / "ROVRLAgent.cs").read_text(encoding="utf-8")
    builder = (UNITY / "Assets/ROVDigitalTwin/Editor/CompleteProjectBuilder.cs").read_text(encoding="utf-8")
    require("ActionSize = 8" in agent and "MakeContinuous(ROVRLAgent.ActionSize)" in builder,
            "eight continuous thruster actions are configured")
    require("ObservationSize = 39" in agent and "VectorObservationSize = ROVRLAgent.ObservationSize" in builder,
            "39 vector observations are configured")
    require("for (int index = 0; index < 16; index++)" in agent, "16-ray sonar enters observations")
    require("SaveAsPrefabAsset" in builder and "SaveScene" in builder, "scene and prefab generation is implemented")
    require("mlagents-learn" not in agent + builder, "runtime/editor code cannot start training")
    telemetry = (scripts / "TelemetryUdpBridge.cs").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "config/telemetry_schema_v1.json").read_text(encoding="utf-8"))
    for field in schema["required"]:
        require(f'\\"{field}\\"' in telemetry, f"Unity publishes canonical field {field}")
    print("Unity static validation complete. Editor compilation and Play Mode checks remain required.")


if __name__ == "__main__":
    main()

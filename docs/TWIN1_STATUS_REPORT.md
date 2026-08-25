# Twin 1 Status Report

## Executive Status

**Partially Stable.** Unity batch compilation, repository static validation and all current EditMode tests pass.
Automated PlayMode visual/soak output and real Model 1 integration remain unverified.

## Purpose

Twin 1 is the existing Unity robot/navigation and inspection-capture system under `unity/`. It supports ROV
simulation, sensor/environment emulation, navigation-policy inference, operator demonstration, image capture,
synthetic scenario generation and HTTP handoff to the current perception/decision workflow. It is not evidence
that Unity perfectly reproduces open-sea physics.

## Architecture / Design

- **Technology:** Unity `6000.5.9f1`, C#, ML-Agents, ROS connector, Python HTTP API integration.
- **Primary role:** robot/navigation digital twin and current inspection-workflow support.
- **Main modules:** vehicle/hydrodynamics/environment/sensors/mission scripts, `ROVCameraCapture.cs`,
  `SyntheticCaptureController.cs`, `OceanSenseApiClient.cs`, `MissionController.cs`, dashboard and tests.
- **Configuration:** Unity ProjectSettings/Packages, scene/prefab builder, behavior parameters and runtime fields.
- **Dependencies:** declared Unity packages; Python API only for perception/decision handoff.
- **Trust boundary:** captured Unity frames/metadata are synthetic/demo data. They may support development or
  separately labelled training studies, but cannot be mixed silently with real validation/test evidence.

## Files and Modules

| Area | Path / role |
|---|---|
| Project identity | `unity/ProjectSettings/ProjectVersion.txt` |
| Packages | `unity/Packages/manifest.json` |
| Runtime | `unity/Assets/ROVDigitalTwin/Scripts/` |
| Models | `unity/Assets/ROVDigitalTwin/Models/` - navigation `.onnx`, not Model 1 |
| EditMode tests | `unity/Assets/ROVDigitalTwin/Tests/EditMode/` |
| Static validation | `scripts/validate_unity_project.py` |
| API | `src/oceansense/api.py` |

## Inputs

| Name | Format | Producer | Used by Model 1? | Notes |
|---|---|---|---|---|
| Environment/scenario state | Unity serialized fields/runtime values | scene/operator | Indirect | current, waves, visibility, contamination and related parameters |
| Navigation actions | 8 continuous floats | ML-Agents policy/operator | No | drives thruster/control behavior |
| Robot/sensor observations | 39 floats plus 16 sonar rays | Unity subsystems | No | navigation/twin state, not Model 1 labels |
| Camera frame/context | PNG plus mission metadata | Unity camera/mission | Yes, via API | synthetic/demo provenance must remain explicit |
| Perception JSON | canonical API response | Model 1 API/fixture | Yes | fixture response is contract evidence only |

## Outputs

| Name | Format | Consumer | Training/eval safe? | Notes |
|---|---|---|---|---|
| ROV visualization/state | Unity scene/runtime telemetry | operator/dashboard | No | visual/demo and navigation validation |
| Camera capture | PNG | API/data-review workflow | Conditional | synthetic; never sole real test evidence |
| Scenario metadata | JSON | data-review workflow | Conditional | seed and conditions; synthetic provenance |
| API decision | JSON | dashboard/operator | No as Model 1 metric | fixture or real checkpoint must be identified |
| Navigation policy action | continuous vector | vehicle controller | No | unrelated to visual Model 1 checkpoint |

## Commands and Tests

| Command/check | Result |
|---|---|
| `python scripts/validate_unity_project.py` | PASS; package/version, subsystems, 8 actions, 39 observations, 16-ray sonar, schema and no-runtime-training checks |
| Unity `-batchmode -nographics -quit` | exit 0; Unity 6000.5.9f1 compilation/import succeeded |
| Unity `-runTests -testPlatform EditMode` | PASS: 8/8; 0 failed, 0 skipped |
| `python -m pytest -q tests/test_oceansense_api.py tests/unit/test_master_execution_guide.py -k "not model2"` | PASS: 14; 2 deselected |
| Automated PlayMode visual/capture/soak | Not run; unverified |

Machine-readable evidence: `outputs/model1_audit/twin1_verification.json`.

## Integration With Model 1

`OceanSenseApiClient.cs` posts a capture to `/api/perception/analyze`, then sends the perception response to
`/api/agent/decide`. Without `OCEANSENSE_CONDITION_CHECKPOINT` and `OCEANSENSE_DOMAIN_CHECKPOINT`, the API uses
fixture classifiers. This proves the wire contract only; no actual Model 1 quality or end-to-end latency is
validated. Twin 1 does not modify Model 1 manifests/splits automatically.

## Limitations

- Hydrodynamics/environment effects are parameterized approximations awaiting real telemetry calibration.
- EditMode/static success does not prove long-duration PlayMode numerical stability or correct rendered output.
- No frozen visual checkpoint exists for complete integration.
- Synthetic frames cannot establish open-sea generalization or safety.
- No “perfect,” “flawless,” or flip-free open-sea claim is supported.

## Separation From Twin 2

This is not the Python Twin 2/comparison implementation under `src/oceansense/model2/`. No Twin 2 code,
configuration, results or validation claim is included or modified.

## Next Step

Run a seeded PlayMode soak/capture matrix across bounded current, waves, buoyancy, contamination and visibility;
inspect rendered captures; then repeat with a frozen Model 1 checkpoint and record hashes, latency and failures.

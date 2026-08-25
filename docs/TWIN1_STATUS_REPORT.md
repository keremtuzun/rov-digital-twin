# Twin 1 Status Report

## Executive decision

**PARTIALLY STABLE.** Twin 1 compiles in the declared Unity editor, passes the repository's static checks,
and passes all current EditMode tests. It is not declared fully stable because no automated PlayMode visual
capture was reviewed and the real Model 1 checkpoint/data needed for end-to-end perception are absent.

## Purpose and boundary

Twin 1 is the existing Unity robot/navigation and inspection-capture system under `unity/`. It simulates ROV
motion, sensors, hydrodynamic/environment disturbances, navigation policy inference, camera capture, and the
HTTP handoff to the OceanSense perception/decision API. It supports operator demonstration and controlled
data generation; it is not proof that Unity perfectly reproduces open-sea physics.

Twin 2 is the separate Python comparison/twin implementation under `src/oceansense/model2/`. No Twin 2 code,
configuration, result, or claim is used in this review.

## Relevant files

| Area | Files / role |
|---|---|
| Unity project identity | `unity/ProjectSettings/ProjectVersion.txt` — Unity `6000.5.9f1` |
| Packages | `unity/Packages/manifest.json` — ML-Agents and ROS integration dependencies |
| Robot/environment | `unity/Assets/ROVDigitalTwin/Scripts/` — vehicle, sensors, hydrodynamics, mission and environment logic |
| Image capture | `ROVCameraCapture.cs` — PNG capture from the configured camera |
| API bridge | `OceanSenseApiClient.cs` — calls `/api/perception/analyze`, then `/api/agent/decide` |
| Synthetic capture | `SyntheticCaptureController.cs` — seeded PNG and JSON condition metadata; explicitly marked synthetic |
| Operator flow | `MissionController.cs` — inspection analysis and synthetic-capture controls |
| Tests | `unity/Assets/ROVDigitalTwin/Tests/EditMode/` and Python API/contract tests |

The two committed `.onnx` files in `unity/Assets/ROVDigitalTwin/Models/` are navigation policies. They are not
the Model 1 visual classifier.

## Input/output contract

| Direction | Input | Output |
|---|---|---|
| Environment → robot | water/current/wave/visibility/contamination parameters | forces, sensor observations, camera scene |
| Agent → vehicle | eight continuous thruster/control actions | ROV translation and rotation |
| Camera → API client | captured PNG plus mission/capture context | perception request to `/api/perception/analyze` |
| Perception → decision | canonical perception response | request to `/api/agent/decide` and decision JSON |
| Synthetic capture | seed and scenario conditions | PNG plus JSON metadata with synthetic provenance |

Without `OCEANSENSE_CONDITION_CHECKPOINT` and `OCEANSENSE_DOMAIN_CHECKPOINT`, the Python API uses fixture
classifiers. Fixture responses validate the wire contract only and must not be presented as Model 1 output.

## Verification evidence

Audited on commit `65cf3ba9bca486f4bc3c19ee01b7831a802cc652`:

| Check | Command / environment | Result |
|---|---|---|
| Static Unity contract | `python scripts/validate_unity_project.py` | PASS; required package/version, subsystem, action, observation, sonar, schema and no-runtime-training checks passed |
| Unity compile/import | Unity `6000.5.9f1`, `-batchmode -nographics -quit` | exit `0`; batch-mode compilation completed successfully |
| EditMode tests | Unity `-runTests -testPlatform EditMode` | PASS: 8/8, 0 failed, 0 skipped |
| API/Model 1 contract tests | `python -m pytest -q tests/test_oceansense_api.py tests/unit/test_master_execution_guide.py -k "not model2"` | PASS: 14, 2 deselected |
| PlayMode visual/capture test | not run | Unverified |
| Real Model 1 end-to-end | unavailable | Blocked by missing checkpoint and approved image data |

Machine-readable results are summarized in `outputs/model1_audit/twin1_verification.json`. Local Unity logs and
test XML are temporary evidence and are intentionally not treated as product artifacts.

## Known limitations

- Hydrodynamics and environmental effects are parameterized approximations and still require calibration
  against real vehicle telemetry and sea-trial measurements.
- Static and EditMode success do not prove numerical stability for every long-duration PlayMode scenario.
- Synthetic condition metadata helps coverage analysis but cannot replace real open-sea held-out evaluation.
- The absence of a frozen visual checkpoint prevents claims about classification quality or complete latency.
- No claim of “perfect,” “flawless,” or flip-free open-sea operation is supported by this evidence.

## Smallest path to stable

Run a deterministic PlayMode soak/capture suite across bounded current, wave, buoyancy, contamination, and
visibility cases; inspect captures; then repeat it with a frozen Model 1 checkpoint and record end-to-end
latency, failures, and hashes. Stability requires explicit pass bounds, not only a visually successful demo.

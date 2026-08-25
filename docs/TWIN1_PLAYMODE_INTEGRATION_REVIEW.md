# Twin 1 PlayMode and Model 1 Integration Review

**Review date:** 2026-08-25  
**Reviewed branch:** `codex/rov-digital-twin`  
**Unity editor:** 6000.5.9f1 (`b57deb96f08d`)  
**Scope:** Twin 1 review only; no Model 1 training/architecture change, external data acquisition, Model 2, or Twin 2 work

## 1. Executive Decision

**PARTIALLY STABLE**

Twin 1 has a compilable Unity 6 project, a committed scene/prefab, coherent static navigation/sensor/API contracts, and eight passing EditMode tests. It is not stable as a PlayMode or real Model 1 integration system:

- Unity batch import/compilation completed with exit code 0 on an exact temporary writable copy of the committed `Assets`, `Packages`, and `ProjectSettings`.
- EditMode executed **8/8 passing tests**, zero failed/skipped/inconclusive.
- The PlayMode test runner executed successfully but discovered **0 tests**. Its XML reports `testcasecount="0"`; its log says `No tests were executed`. This is not a PlayMode pass.
- `OceanSenseApiClient.cs` implements an HTTP image-path/prediction handoff, but no Unity-to-API integration test exists.
- The API defaults to deterministic fixture classifiers when Model 1 checkpoint environment variables are absent. Both required visual checkpoints are absent, so current evidence does not include real Model 1 inference.
- The two committed ONNX assets are ML-Agents navigation policies, not RGB perception models. The committed scene and prefab currently serialize `BehaviorParameters.m_Model` as null even though the procedural builder tries to assign the experimental navigation ONNX.

The stable evidence is therefore limited to static structure, compilation, EditMode unit behavior, and Python fixture-level API contracts. Rendered PlayMode behavior, long-run numerical stability, capture correctness, live networking, active navigation-policy assignment, and real Model 1 end-to-end inference remain partial or blocked.

## 2. Twin 1 Scope Definition

Twin 1 in this repository is the Unity-based robot/navigation and inspection-workflow support environment under `unity/`. It is not a trained visual Model 1 and is not a structural failure twin.

### Technology and modules

- **Framework:** Unity 6000.5.9f1, C#, Unity Test Framework 1.7.0, ML-Agents 4.1.0, and ROS-TCP-Connector v0.7.0; evidence: `unity/ProjectSettings/ProjectVersion.txt` and `unity/Packages/manifest.json`.
- **Primary scene:** `unity/Assets/ROVDigitalTwin/Scenes/OceanSenseDemo.unity`, enabled in `unity/ProjectSettings/EditorBuildSettings.asset`.
- **Robot asset:** `unity/Assets/ROVDigitalTwin/Prefabs/OceanSenseROV.prefab`.
- **Construction:** `unity/Assets/ROVDigitalTwin/Editor/CompleteProjectBuilder.cs` procedurally creates the scene, ROV, eight thrusters, environment, target/pipeline, sensors, camera, API client, UDP bridge, capture controller, and ML-Agents components.
- **Dynamics/environment:** `ROVVehicle.cs`, `Thruster.cs`, `Hydrodynamics6Dof.cs`, `WaterCurrentField.cs`, `UnderwaterEnvironment.cs`, `DomainRandomization.cs`, and `FaultInjectionController.cs`.
- **Sensors:** `DepthSensor.cs`, `DvlSensor.cs`, `ImuSensor.cs`, `ForwardSonarSensor.cs`, and `SimulatedPowerSensor.cs`.
- **Workflow glue:** `MissionController.cs`, `ROVCameraCapture.cs`, `SyntheticCaptureController.cs`, `OceanSenseApiClient.cs`, `TelemetryUdpBridge.cs`, and `OceanSenseDashboard.cs`.

### Intended purpose and support

Twin 1 supports approximate ROV dynamics, environmental disturbance and visibility variation, sensor/viewpoint simulation, station-keeping/pipeline/waypoint duties, navigation-agent observations and thruster actions, operator demonstration, rendered image capture, explicitly synthetic randomized captures, UDP telemetry/high-level intents, and an HTTP handoff to perception and decision endpoints.

It does **not** establish calibrated open-sea physics, field safety, visual Model 1 accuracy, structural integrity diagnosis, a frozen perception model, or a completed real-image evaluation. The Unity environment can produce a rendered viewpoint; it does not convert scene state into ground-truth physical damage evidence.

### System boundaries

- **Relationship to Model 1:** Twin 1 can send a locally stored camera-frame path to the separate Python API and display returned prediction/decision JSON. C# does not load EfficientNet checkpoints. The Python service owns the optional checkpoint loading.
- **Relationship to navigation/control:** navigation is integral to the Unity twin. `ROVRLAgent.cs` consumes 39 vector observations and emits 8 continuous residual actions around deterministic guidance. It is a control contract, not visual inference.
- **Model 2/Twin 2 boundary:** `src/oceansense/model2/`, Model 2 research, and any future failure/inspection Twin 2 are outside this review. The separate Python 2D visual fixture is also not evidence of Twin 2 calibration or Model 1 quality.

## 3. Test Evidence

| Test Type | Found? | Command / Evidence | Result | Notes |
|---|---:|---|---|---|
| EditMode tests | Yes | `unity/Assets/ROVDigitalTwin/Tests/Editor/HydrodynamicsTests.cs`; Unity command `-batchmode -nographics -runTests -testPlatform EditMode -testResults <temp>/editmode-real.xml` | Pass | XML: 8 total, 8 passed, 0 failed/skipped/inconclusive. Covers drag, rest state, 39/8 contract, depth-decaying wave component, contamination effects, attitude/thruster stop, advanced thrust curve, and deterministic fault reset. |
| PlayMode tests | No | Searched `unity/Assets` for `[UnityTest]`/`UnityEngine.TestTools`; only Editor test assembly exists. The PlayMode runner command produced `<test-run testcasecount="0" ...>` | Blocked | Runner exit 0 only means invocation completed. Log explicitly says `No tests were executed`; no scene/runtime assertion was evaluated. |
| Build/static validation | Yes | `python scripts/validate_unity_project.py`; Unity 6000.5.9f1 writable-copy batch import/compile | Pass | Static validator passed package/version, subsystem, 39/8, 16-ray, builder, telemetry-schema, and no-runtime-training checks. Unity compile exited 0 with no compiler-error match. Direct OneDrive project launch was rejected as read-only, so exact source directories were copied to a unique temporary test project; the repository was not altered. |
| Integration tests | Partial | `python -m pytest -q tests/test_oceansense_api.py tests/unit/test_master_execution_guide.py -k "not model2"` | Pass (fixture/API contract only) | 14 passed, 2 deselected. Tests inject `FixtureClassifier`/`FixtureDomainClassifier` and use a temporary fixture file. No Unity PlayMode HTTP call, rendered PNG inference, checkpoint load, UDP socket lifecycle, or real Model 1 prediction is exercised. |

The initial direct Unity command against the OneDrive reparse-point path is excluded as a test result: Unity logged `Project folder or disk is read only` and returned no test XML. The valid compile/EditMode/PlayMode discovery evidence came from a temporary writable copy containing the exact committed `Assets`, `Packages`, and `ProjectSettings`. The required reproducible commands are:

```powershell
python scripts/validate_unity_project.py
python -m pytest -q tests/test_oceansense_api.py tests/unit/test_master_execution_guide.py -k "not model2"

# On a writable Unity project path:
& $unityEditor -batchmode -nographics -quit -projectPath $testProject -logFile $compileLog
& $unityEditor -batchmode -nographics -projectPath $testProject `
  -runTests -testPlatform EditMode -testResults $editXml -logFile $editLog
& $unityEditor -batchmode -nographics -projectPath $testProject `
  -runTests -testPlatform PlayMode -testResults $playXml -logFile $playLog
```

Do not add `-quit` to the two test-runner calls: on this Unity/Test Framework combination it exited after import before executing tests and produced no XML. The test runner terminates batch mode after completion.

## 4. Model 1 Integration Evidence

| Integration Claim | Supported? | Evidence | Notes |
|---|---:|---|---|
| Twin 1 can call the perception endpoint | Partial | `OceanSenseApiClient.CaptureAndAnalyze()` posts to `/api/perception/analyze` | C# code and scene wiring exist; no PlayMode network test proves the live call. |
| Twin 1 can call the decision endpoint with the same frame ID | Partial | `OceanSenseApiClient.cs` creates one GUID, sends perception JSON to `/api/agent/decide`, and reuses the frame ID | Python API tests validate matching-ID rejection/acceptance, but not from Unity. |
| Twin 1 directly loads Model 1 checkpoints | No | No `.pt` loader or EfficientNet adapter exists in `unity/`; `OceanSenseApiClient.cs` only makes HTTP requests | Checkpoint ownership belongs to the Python API process. |
| The Python integration can load real Model 1 checkpoints | Architecturally yes; operationally blocked | `src/oceansense/api.py:build_services()` reads `OCEANSENSE_CONDITION_CHECKPOINT` and `OCEANSENSE_DOMAIN_CHECKPOINT`; `src/oceansense/perception.py` loads Torchvision EfficientNet-B0 payloads | Both expected `.pt` files are missing, so this path was not run end-to-end. |
| Current default API behavior is real Model 1 inference | No | `src/oceansense/api.py` constructs `FixtureClassifier()` and `FixtureDomainClassifier()` when checkpoint environment variables are absent | Fixtures return `unknown`/0.0 by default and identify versions/hashes as fixture evidence. |
| Twin 1 exchanges an image with the API | Partial | `ROVCameraCapture.cs` writes a 640×360 PNG; `OceanSenseApiClient.cs` sends its local `image_path` | This works only when Unity and API share the filesystem. There is no authenticated binary upload/object-storage contract for remote use. |
| Twin 1 receives prediction-like JSON | Partial | `LastPerceptionJson`, `LastDecisionJson`, and `OceanSenseDashboard.cs` | Interface is present; no real-checkpoint or PlayMode evidence proves model identity, latency, failure behavior, or render validity. |
| Current inspection result is fixture/demo rather than validated inference | Yes | Missing Model 1 checkpoints; fixture fallback in `api.py`; fixture-injected API tests | Any currently demonstrated prediction must be labeled fixture unless `/health` and output model hash prove otherwise. |

**Answers:** Twin 1 does not itself call an in-process Model 1 model or load its checkpoints. It has a real HTTP adapter capable of forwarding a rendered image path and receiving prediction JSON, but the current repository cannot demonstrate real Model 1 inference. The tested behavior is fixture/API-contract behavior. Scene randomization, target/pipeline visuals, and synthetic capture metadata are simulated inputs, not inferred inspection truth.

## 5. Input / Output Contract

| Category | Input | Producer / Interface | Output / Consumer | Evaluation-safe? |
|---|---|---|---|---:|
| Scene | `OceanSenseDemo.unity` serialized environment, pipeline, target, ROV, duties, lights/fog | Unity scene/builder/operator | Rendered world and component references | No; approximate simulation |
| Environment | current, shear/gusts/waves, density, turbidity, sediment, contamination, lighting/fog | `WaterCurrentField`, `UnderwaterEnvironment`, `DomainRandomization` | Forces, sensor quality, rendered appearance, telemetry/sidecar fields | Only as synthetic metadata, never primary real evaluation |
| Vehicle/sensors | Rigidbody state, 8 thrusters, battery/power, DVL, depth, IMU, 16-ray sonar | Unity physics/scripts | 39 navigation observations, dashboard values, telemetry | No Model 1 metric; simulator validation only |
| Navigation | duty target/pipeline geometry plus 39-float observation vector | `DutyManager`, `ROVRLAgent` | 8 continuous residual thruster commands around deterministic guidance | No; control output, not perception |
| Operator | keys `1/2/3`, `C`, `G`, `R`, `Esc` | `MissionController` | duty switch, API capture, synthetic capture, reset, zero-thrust request | Demo/operator interface |
| Image | 640×360 RGB PNG at `Application.persistentDataPath/OceanSenseCaptures` | `ROVCameraCapture` | local path sent to `/api/perception/analyze` | Conditional only with explicit synthetic/real provenance and frozen model evidence |
| Synthetic fixture | seed, viewpoint, fog/light/current/wave/contamination/turbidity/sediment | `SyntheticCaptureController` | PNG plus JSON sidecar with `real_or_synthetic="synthetic"` and cautious label policy | Supplemental/demo only |
| Perception API | JSON: `frame_id`, local `image_path`, mission context | `OceanSenseApiClient` → FastAPI | domain/classification/condition/anomaly/detections/model metadata JSON | Contract-safe; not evaluation-safe without real checkpoint/data identity |
| Decision API | same frame ID, perception JSON, mission context | Unity → `/api/agent/decide` | high-level recommendation JSON for dashboard/operator | Not a Model 1 metric and never raw thrust |
| UDP telemetry | simulated/derived schema-v1 vehicle/environment fields | `TelemetryUdpBridge`, UDP port 15000 | ROS/telemetry consumer | Simulation telemetry only |
| UDP intent | JSON allowlist on port 15001 | ROS/operator bridge | stored/displayed high-level intent | Does not actuate motors; live socket behavior untested in PlayMode |

Prediction-like outputs are evaluation-safe only after the output identifies a valid Model 1 checkpoint hash/version, the source frame and provenance are immutable, the same frame ID is preserved, fixture fallback is rejected, and the approved evaluation protocol is followed. A dashboard response or successful HTTP status alone is not Model 1 evidence.

## 6. Visual Fixture / Demo Boundary

Two separate synthetic/demo paths exist:

1. **Unity rendered capture:** `ROVCameraCapture.cs` captures the inspection camera. `SyntheticCaptureController.cs` randomizes viewpoint, fog, lighting, current, waves, contamination, turbidity, and sediment; it writes a PNG and JSON sidecar with `real_or_synthetic = "synthetic"` and `label_policy = "visual indicator only; not physical damage evidence"`.
2. **Python 2D fixture/demo:** `src/oceansense/failure_twin.py`, `src/oceansense/digital_twin_demo.py`, and `scripts/run_digital_twin_demo.py` generate controlled visual artifacts and a traceable interface demo. `docs/digital_twin_demo_report.md` states that the demo uses an `unknown`/zero-confidence placeholder because Model 1 is not frozen.

Both paths are useful for interface development, deterministic traceability, rendering checks, augmentation experiments, and separately labeled robustness work. They do not contain approved real-open-sea observations, do not prove class correctness, are not an immutable held-out Model 1 dataset, and may encode the generator's assumptions. They must be marked synthetic and reported separately; neither may count toward Model 1's 270-real-image minimum or support freeze/open-sea claims.

## 7. Navigation / Control Boundary

ML-Agents is present and relevant to robot movement in Twin 1:

- `ROVRLAgent.ObservationSize = 39`; observations include target offset, body linear/angular velocity, quaternion, depth error, battery, duty one-hot, DVL state/quality, and 16 normalized sonar distances.
- `ROVRLAgent.ActionSize = 8`; actions are bounded residual commands mixed with deterministic guidance and applied to the eight thrusters.
- Training/evaluation configs under `config/unity_ppo*.yaml` use behavior `OceanSenseROV` and PPO.
- `OceanSenseROV_Bootstrap.onnx` is 96,262 bytes, SHA-256 `c61f62b669593c901d3ceb68c824e077e9daf943fc83976ece650f823f949263`.
- `OceanSenseROV_OpenSea_Experimental.onnx` is 339,891 bytes, SHA-256 `7f38b839903f01442b120ce7b6758ddabaa111433cad8bedeb810c5d86af0e12`.
- Prior safe ONNX inspection in `docs/MODEL1_CHECKPOINT_RECOVERY_DECISION.md` records input `obs_0 [batch,39]` and output `continuous_actions [batch,8]` for the navigation exports.

These ONNX files do not accept 224-pixel RGB input, do not output the six domain or nine condition classes, and do not satisfy the PyTorch `state_dict`/labels/task Model 1 contract. They are never Model 1 visual checkpoints.

The current control integration is also partial. `CompleteProjectBuilder.cs` attempts to assign `OceanSenseROV_OpenSea_Experimental.onnx`, but both committed `OceanSenseDemo.unity` and `OceanSenseROV.prefab` serialize `m_Model: {fileID: 0}`. Thus the committed scene does not prove that either ONNX is active. The experimental policy is also documented in `docs/rl_policy_model_card.md` as a `legacy_dynamics_baseline`, unqualified after simulator changes and unapproved for real-vehicle actuation. This discrepancy must be resolved and tested without confusing navigation qualification with Model 1 integration.

## 8. Stability Assessment

| Component | Status | Evidence | Remaining Work |
|---|---|---|---|
| Unity project/package import and C# compilation | Stable | Unity 6000.5.9f1 writable-copy batch compile, exit 0; no compiler-error match | Add licensed Unity CI so the result is repeatable outside this workstation |
| Static project/schema contract | Stable | `scripts/validate_unity_project.py` passed all checks | Keep synchronized with scene/runtime changes |
| Hydrodynamics/safety unit behavior | Stable within tested units | EditMode 8/8 pass | Add broader parameter, non-finite, and regression coverage; unit tests do not prove trajectories |
| Committed scene/prefab wiring | Partially Stable | Scene contains API, capture, sensors, UDP, agent, 39/8 behavior; serialized ONNX model is null | Add runtime reference assertions and resolve builder-versus-serialized-model mismatch |
| PlayMode scene/runtime behavior | Blocked | PlayMode runner found 0 tests | Add and run scene load, reference, finite sensor/physics, reset/stop, capture, networking, and soak tests |
| Camera capture | Demo Only | `ROVCameraCapture.cs`, 640×360 local PNG | Verify PlayMode render, cleanup, failure handling, metadata/frame identity, and headless behavior |
| Synthetic capture/randomization | Demo Only | `SyntheticCaptureController.cs` and explicit synthetic sidecar | Add PlayMode artifact/schema test and visual review; keep outside real validation |
| Python API contract | Partially Stable | 14 fixture/API tests pass | Add real image decoding, service identity, live Unity HTTP, timeout/retry/auth, and remote-transfer design |
| Real Model 1 inference | Blocked | Both `.pt` checkpoints missing; API defaults to fixtures | Recover/validate original pair or separately train/freeze v2, then run hashed end-to-end test |
| Navigation observation/action contract | Stable | Static validation and EditMode assert 39 observations / 8 actions | Preserve versioning and add runtime observation/action finiteness tests |
| Navigation ONNX activation/qualification | Partially Stable | Assets/config/model card exist; committed scene/prefab model reference is null; model is legacy dynamics | Resolve assignment, rerun current-simulator regression, never treat as perception evidence |
| UDP telemetry/high-level intent | Partially Stable | `TelemetryUdpBridge.cs` matches required schema fields and blocks raw actuator words | PlayMode socket rebind, invalid JSON, 1,000-sample validation, loss/latency/fault tests |
| CI | Partially Stable | `.github/workflows/ci.yml` runs Python tests and static Unity validation | Add Unity licensed compile plus EditMode/PlayMode XML artifact job |
| Model 2 / Twin 2 | Out of Scope | Explicit task boundary; no related code changed | Separate future workstream |

## 9. Required Work Before Twin 1 Stable

1. Add a PlayMode test assembly and tests that load `OceanSenseDemo.unity`, assert all serialized component references, and verify exactly one ROV/agent/BehaviorParameters graph.
2. Assert the runtime 39-observation/8-action contract, finite Rigidbody/sensor/telemetry values, bounded tilt/position, and zero thruster command after reset, episode termination, safe-volume exit, low battery, and emergency stop.
3. Run a seeded bounded-current/wave/visibility/contamination/fault matrix plus a documented soak duration; fail on non-finite physics, null references, socket/thread errors, runaway motion, or unresolved flips.
4. Add PlayMode capture tests for PNG dimensions/readability, unique/stable frame ID, explicit synthetic provenance, complete randomization sidecar, write failures, and cleanup.
5. Add UDP tests for 1,000 schema-valid samples, invalid JSON rejection, high-level-only command acceptance, packet impairment, teardown, and two consecutive Play sessions without port conflicts.
6. Resolve whether the committed scene should reference the legacy navigation ONNX. Make builder, scene, prefab, documentation, and runtime health output agree. Requalify any active policy against current dynamics; otherwise explicitly run heuristic/guidance mode.
7. Add a Unity-to-local-API PlayMode integration test using an explicitly named fixture service. Verify capture → perception → decision frame-ID continuity, timeout/error behavior, and that fixture identity is visible rather than presented as Model 1.
8. After valid Model 1 checkpoints become available, add a separate gated end-to-end test that sets both checkpoint paths, verifies `/health` is non-fixture, records model/data hashes and latency, analyzes a provenance-safe RGB frame, and rejects partial/mismatched checkpoint configurations.
9. Replace shared-local-path image exchange with authenticated upload/object storage before remote deployment, or document local-only scope and validate path access/security.
10. Add a licensed Unity CI job that archives compile, EditMode, and PlayMode logs/XML and fails when PlayMode test count is zero.
11. Update operator/demo documentation so rendered captures, fixture responses, navigation ONNX, real Model 1 predictions, and future Model 2/Twin 2 evidence cannot be confused.
12. Retain hydrodynamic and field-performance limitations until parameter identification, HIL/tank, and supervised field evidence exist; software PlayMode stability alone is not physical validation.

## 10. Recommended Next Action

**add missing PlayMode tests**

Start with scene load/reference assertions, finite sensor/physics checks, emergency stop, capture-sidecar provenance, and UDP lifecycle. These tests can be implemented and run with fixture API identity while Model 1 checkpoints remain blocked. Add the real Model 1 integration test only after a valid checkpoint pair and evidence package exist.

## Integrity Statement

No Model 1 training was performed and no Model 1 architecture/checkpoint was changed. No external dataset was downloaded. No navigation ONNX was treated as perception. A zero-test PlayMode result was not reported as a pass. Fixture/demo outputs were not treated as real inference or validation data. No Model 2 or Twin 2 file was modified. The only planned repository change from this review is this evidence document.

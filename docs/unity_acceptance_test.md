# Unity 6 acceptance test

Current status: **editor verification required**. Unity was not installed automatically and no Unity
license-dependent CI workflow was added.

## Preconditions

- Unity Hub with a licensed Unity 6000.0 LTS editor.
- Repository checked out with Git LFS not required.
- Free UDP ports 15000 and 15001.
- Optional API running on `127.0.0.1:8000`; optional ROS 2 workspace sourced.

## Windows batch sequence

Set the installed editor path explicitly, then run from the repository root:

```powershell
$unityEditor = 'C:\Program Files\Unity\Hub\Editor\6000.0.XXf1\Editor\Unity.exe'
& $unityEditor -batchmode -nographics -quit -projectPath "$PWD\unity" `
  -executeMethod ROVDigitalTwin.Editor.CompleteProjectBuilder.BuildCompleteDemo `
  -logFile "$PWD\artifacts\unity-build.log"
& $unityEditor -batchmode -nographics -quit -projectPath "$PWD\unity" `
  -runTests -testPlatform EditMode -testResults "$PWD\artifacts\unity-editmode.xml" `
  -logFile "$PWD\artifacts\unity-editmode.log"
```

Do not consider a zero process exit sufficient: inspect both logs for compiler errors and confirm the
test XML reports zero failures.

## Scene and Play Mode checklist

1. Confirm `OceanSenseDemo.unity` and `OceanSenseROV.prefab` were generated and added to build settings.
2. Confirm `BehaviorParameters` shows 39 vector observations and 8 continuous actions.
3. Enter Play Mode without an ML trainer. Verify heuristic motion, all eight thrusters and reset.
4. Select duties 1/2/3 and verify target, pipeline and timeout behavior.
5. Trigger episode completion, out-of-volume, low battery and `Esc`; all thruster commands must become zero.
6. Verify DVL, IMU, depth, sonar and power references are non-null and finite for 10 minutes.
7. Press `C` with the API available; capture, perception and decision must share the same frame ID.
8. Press `G`; PNG and JSON sidecar must identify the sample as synthetic and record randomization values.
9. Start two consecutive Play sessions; UDP sockets must rebind without an address-in-use error.
10. Send invalid JSON and a valid high-level intent. Invalid input must be ignored; intent must never become thrust.

## Acceptance criteria

- Zero C# compile and Edit Mode test failures.
- No null-reference, socket/thread or non-finite physics errors.
- Observation/action sizes stay 39/8.
- Emergency stop and every episode termination zero thrusters within one physics tick.
- Generated scene/prefab reopen without automatic destructive regeneration.
- Telemetry validates against schema v1 for at least 1,000 consecutive samples.

Play Mode automation remains a follow-up after the first editor compile confirms the scene wiring API.

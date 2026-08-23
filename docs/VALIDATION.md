# Validation Record

## Automated checks

- Dataset generation is deterministic for a fixed seed.
- CSV serialization round-trips into the typed telemetry schema.
- Telemetry uses a mission-group 80/20 split; image splits keep every mission/video in one partition.
- The test suite requires at least 0.82 accuracy on a held-out synthetic set.
- Non-nominal decisions cannot enable autonomous execution.
- Static Unity project validation checks package pins, the procedural builder, eight actions, 39
  observations, every canonical telemetry field, sensor/bridge scripts, and the no-policy/no-training boundary.
- Unity editor tests verify that quadratic hydrodynamic drag is zero at rest and opposes motion.

## Current validation boundary

The Python suite includes a small deterministic synthetic telemetry smoke-training test that writes
only into a temporary directory. No image, detector, LLM or PPO training was run and no persistent
checkpoint was produced. Unity Editor is not installed in the code-authoring environment, so scene
generation, C# compilation, Play Mode behavior and Editor tests must be run on first open in Unity 6
before simulator acceptance.

Contract tests verify valid Unity JSON conversion, enum aliasing, missing-field errors and malformed
JSON rejection. Governance tests verify license allowlisting, named approval and checksum gates. Split
tests enforce mission/video disjointness.

## Acceptance criteria for real deployment

1. Replace synthetic distributions with versioned and reviewed SIL/HIL/field captures.
2. Split by mission/time, not by individual row, to prevent temporal leakage.
3. Calibrate confidence and define per-class recall requirements with operators.
4. Replay worst-case sensor dropouts and simultaneous faults.
5. Validate command gating on a hardware interlock before any wet test.
6. Record model hash, telemetry window, decision and operator override for every event.

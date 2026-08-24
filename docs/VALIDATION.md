# Validation Record

## Automated checks

- Dataset generation is deterministic for a fixed seed.
- CSV serialization round-trips into the typed telemetry schema.
- Telemetry uses a mission-group 80/20 split; image splits keep every mission/video in one partition.
- The test suite requires at least 0.82 accuracy on a held-out synthetic set.
- Non-nominal decisions cannot enable autonomous execution.
- Static Unity project validation checks package pins, the procedural builder, eight actions, 39
  observations, every canonical telemetry field and sensor/bridge scripts.
- Unity editor tests verify that quadratic hydrodynamic drag is zero at rest and opposes motion.

## Current validation boundary

The Python suite includes deterministic synthetic telemetry smoke training and reliability tests that
write only into temporary directories. A Unity PPO policy was trained and is documented separately in
`rl_policy_model_card.md`; no image, detector or LLM training was run. Unity 6 compilation, a headless
player build and eight EditMode tests were completed before the final calibrated-drag loader change.
The final headless rebuild attempt on 2026-08-24 was blocked before compilation by Unity Licensing
Client protocol/signature validation, not by a reported C# compiler failure; it remains an explicit
open verification item. Because the hydrodynamic, thruster and fault models are now more demanding,
the committed PPO artifact is a legacy-dynamics baseline and must pass the new regression matrix before
it can be described as current-simulator validated.

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

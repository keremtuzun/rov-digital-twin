# Validation Record

## Automated checks

- Dataset generation is deterministic for a fixed seed.
- CSV serialization round-trips into the typed telemetry schema.
- Training uses a stratified 80/20 split.
- The test suite requires at least 0.82 accuracy on a held-out synthetic set.
- Non-nominal decisions cannot enable autonomous execution.

## Acceptance criteria for real deployment

1. Replace synthetic distributions with versioned and reviewed SIL/HIL/field captures.
2. Split by mission/time, not by individual row, to prevent temporal leakage.
3. Calibrate confidence and define per-class recall requirements with operators.
4. Replay worst-case sensor dropouts and simultaneous faults.
5. Validate command gating on a hardware interlock before any wet test.
6. Record model hash, telemetry window, decision and operator override for every event.

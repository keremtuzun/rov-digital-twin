# ROV Operations Knowledge Base

## Safety hierarchy

1. Preserve vehicle integrity and positive control.
2. Reject or cross-check implausible sensor data.
3. Move to a stable state before diagnosis.
4. Require operator review for every non-nominal diagnosis.
5. Log the triggering telemetry, model version, confidence and chosen action.

## Diagnostic signatures

- Thruster degradation: low command-to-response ratio, rising current, reduced speed or asymmetric yaw.
- Buoyancy imbalance: persistent vertical velocity/depth error with large pitch or roll.
- Sensor drift: disagreement between pressure depth, IMU-derived state and DVL; falling DVL quality.
- Hydrodynamic drag: high current and low speed while individual thruster response remains moderately healthy.

## Decision boundaries

An LLM recommendation is advisory. The deterministic safety layer owns command eligibility. Critical limits, low confidence or contradictory sensors must result in hold, abort/surface, or operator review rather than autonomous continuation.

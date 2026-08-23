# Weak-point and Unity policy model card

## Weak-point classifier v2

- Artifact: `models/weakpoint_v2.json`
- Purpose: edge-friendly telemetry triage into nominal, buoyancy imbalance,
  hydrodynamic drag, sensor drift, or thruster degradation.
- Training basis: 4,000 deterministic synthetic telemetry rows generated with seed 42;
  800 rows per class and a mission-group 80/20 split to prevent adjacent-row leakage.
- Features: the canonical telemetry fields plus magnitudes, squared terms, propulsion/
  power ratios, response deficit, depth-vertical coupling, attitude magnitude, and an
  IMU/DVL disagreement interaction.
- Result: 0.9975 held-out accuracy and 0.9975 macro-F1; loss 0.06051 to 0.02667 across
  180 epochs. These scores measure the synthetic generator, not real-sea validity.
- Prohibited use: structural certification, unattended fault isolation, or direct
  thruster control. Validate and recalibrate on vehicle telemetry before deployment.

## Unity PPO bootstrap

- Artifact: `unity/Assets/ROVDigitalTwin/Models/OceanSenseROV_Bootstrap.onnx`
- Purpose: continue staged simulation learning for eight continuous thruster actions.
- Training basis: 25,000 Unity environment steps with mild domain randomization
  (`difficulty` 0.1-0.3), seed 42, PPO configuration in
  `config/unity_ppo_bootstrap.yaml`.
- Result: policy loss 0.036704 to 0.026339 and value loss 0.085941 to 0.050123.
  Episode reward remained variable and did not converge.
- Status: experimental/bootstrap only; not assigned to the scene's Behavior Parameters
  and not approved for real-vehicle commands.

The authoritative promotion procedure is `docs/unity_training_operations.md`; detailed
machine-readable results are under `artifacts/training/`.

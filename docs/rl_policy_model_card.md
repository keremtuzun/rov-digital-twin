# RL policy model card: OceanSense open-sea experimental v3

## Intended use

This checkpoint controls the simulated eight-thruster ROV in waypoint missions. It is a hybrid
controller: deterministic velocity/depth guidance supplies a recoverable baseline and PPO produces
bounded residual corrections with 0.25 command authority. Independent attitude authority limiting,
restoring torque, actuator response, slew limits, safe-volume checks and hard episode termination remain
outside the neural policy.

## Training

The policy was trained for 250,081 Unity environment steps across four parallel headless players. The
first 150,034 steps used difficulty 0.05–0.35 (seed 45); the following 100,047 steps fine-tuned on
difficulty 0.55–1.0 (seed 46). Randomization covers vehicle mass and drag, thruster efficiency, current,
turbulence, two-component subsurface wave motion, sensor noise, target geometry, turbidity, suspended
sediment and light-to-moderate contamination.

The exported artifact is
`unity/Assets/ROVDigitalTwin/Models/OceanSenseROV_OpenSea_Experimental.onnx`, SHA-256
`7f38b839903f01442b120ce7b6758ddabaa111433cad8bedeB810c5d86af0e12`.

## Frozen simulation evaluation

Seed 202 was not used for training. At difficulty 0.7–1.0, four deterministic headless environments ran
59,919 steps. All 24 reporting windows recorded mean success 1.0 and no flip event was recorded. Mean
tilt was 13.35 degrees, the maximum reporting-window mean was 14.35 degrees, mean roll/pitch rate was
0.298 rad/s, and mean cumulative reward was 12.31. Exact values are stored in
`artifacts/training/open_sea_navigation_v3_metrics.json`.

The 5.48 m tracking-error metric is the mean over complete trajectories, not final error. A successful
episode terminates inside the randomized 0.8–1.5 m waypoint radius.

## Compatibility status after the reliability overhaul

The metrics above are immutable historical results for the simulator revision used during that run.
The current simulator adds nonlinear forward/reverse thrust curves, dead zones, voltage and thermal
derating, actuator lag/slew, water-density effects, richer waves/currents, sensor delays/dropouts and
compound failures. The ONNX file has **not** been retrained or requalified against those changes.
Its current status is `legacy_dynamics_baseline`, with `deployment_approved: false`. Run the curriculum
in `config/unity_ppo_curriculum_v2.yaml`, then execute the condition-separated validation plan before
promoting a replacement. Historical success metrics must not be attributed to the current plant model.

## Safety and limitations

These results demonstrate the tested simulation distribution only. They do not establish perfect,
flawless or field-safe behavior. Unknown waves, tether loads, payload changes, biofouling, actuator
failures, sensor dropouts and modeling error can invalidate the result. The artifact is not approved for
real-vehicle actuation. Promotion requires parameter identification from ROS bags, Monte Carlo regression,
fault injection, HIL, tank tests, supervised sea trials, an independent leak/depth/geofence/power
watchdog, manual override and signed operator approval.

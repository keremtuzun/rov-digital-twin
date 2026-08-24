# Unity policy training and sustainable operations

## Current result

The current ONNX policy is **simulation-validated experimental**, not an autonomous real-vehicle
controller. It uses deterministic waypoint guidance plus a bounded PPO residual policy. Training ran
for 250,081 steps: 150,034 curriculum steps followed by 100,047 open-sea fine-tuning steps.

A frozen seed-202 evaluation at difficulty 0.7–1.0 ran for 59,919 steps in four parallel environments.
All 24 reporting windows recorded mean success 1.0, with no observed flip event. Mean tilt was 13.35
degrees and the maximum reporting-window mean was 14.35 degrees. Exact metrics are in
`artifacts/training/open_sea_navigation_v3_metrics.json`; scope and limitations are in
`docs/rl_policy_model_card.md`. The older bootstrap artifact remains only for traceability.

## Reproduce the trainer

Use Python 3.10.x. Check out the official Unity ML-Agents `release_23` branch and install
both Python packages from that same checkout, followed by the compatibility pins:

```powershell
python -m pip install .\ml-agents-envs
python -m pip install .\ml-agents
python -m pip install -r config\mlagents-requirements.txt
```

Start with the navigation curriculum while the Unity Editor or built training player is running:

```powershell
mlagents-learn config\unity_ppo_navigation_curriculum.yaml --run-id oceansense_navigation_v3
```

Continue only after waypoint success and safety metrics are stable. Fine-tune with
`config/unity_ppo_open_sea_finetune.yaml`, then freeze the model and evaluate with
`config/unity_ppo_open_sea_evaluation.yaml`. Keep a fixed evaluation seed
set that training never sees; compare success rate, collision rate, energy per metre,
depth error, and action jerk rather than selecting a model from training loss alone.

## Ocean realism and calibration loop

The Unity environment now randomizes mass, drag, current, turbulence, thruster
efficiency, target geometry, and sensor noise. It also models current shear/gusts,
two-component swell with depth-decaying underwater orbital velocity, depth-dependent
visibility and lighting, low-to-moderate contamination, turbidity, suspended sediment,
and realistic DVL/depth/sonar sample rates. Water quality affects optical visibility,
particle density, sonar noise, and DVL bottom-lock quality. These ranges are hypotheses
until calibrated from local ocean measurements.

The default scene represents lightly contaminated coastal water: contamination 0.08,
turbidity 1.2 NTU, suspended sediment 2.5 mg/L, significant wave height 0.45 m, and peak
wave period 6.5 s. These are scenario inputs—not universal sea constants. Field deployments
must replace them with measurements or site/season distributions.

For sustainable real-world operation:

1. Record versioned ROS 2 bags from tank and sea trials, including commands, power,
   vehicle state, DVL/IMU/depth/sonar, water conditions, payload, and maintenance state.
2. Estimate hydrodynamic and sensor parameters from those bags; store units, provenance,
   calibration date, vehicle configuration, and confidence bounds.
3. Retrain only from immutable dataset snapshots and preserve config, seed, commit, Unity
   version, metrics, and exported model hash for every run.
4. Gate promotion through simulation regression, shadow mode, hardware-in-the-loop,
   constrained tank tests, and supervised sea trials.
5. Keep the vehicle's independent depth/geofence/leak/power watchdog, command limits,
   manual override, and deterministic safe-stop path outside the learned policy.

## Promotion gates

A checkpoint must not command a real vehicle until it beats the deterministic controller
on the frozen evaluation suite, has zero safety-envelope violations, remains stable under
the full randomized envelope, passes telemetry-loss and sensor-fault tests, and receives
human sign-off after HIL and supervised field trials. Rollback means selecting the last
signed model artifact; never overwrite a promoted model in place.

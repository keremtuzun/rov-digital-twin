# Unity policy training and sustainable operations

## Current result

The committed ONNX policy is an **experimental bootstrap checkpoint**, not an autonomous
real-vehicle controller. A deterministic 25,000-step PPO run reduced policy loss from
0.036704 to 0.026339 (28.2%) and value loss from 0.085941 to 0.050123 (41.7%). Mean
episode reward remained variable (best reporting window -1.357, final -1.954), so the
run is not considered converged. Exact metrics are in
`artifacts/training/ppo_bootstrap_metrics.json`.

## Reproduce the trainer

Use Python 3.10.x. Check out the official Unity ML-Agents `release_23` branch and install
both Python packages from that same checkout, followed by the compatibility pins:

```powershell
python -m pip install .\ml-agents-envs
python -m pip install .\ml-agents
python -m pip install -r config\mlagents-requirements.txt
```

Start with the mild curriculum while the Unity Editor is open on `OceanSenseDemo`:

```powershell
mlagents-learn config\unity_ppo_bootstrap.yaml --run-id oceansense_ppo_bootstrap
```

Continue only after bootstrap reward is stable. Increase `difficulty` gradually toward
1.0 and use `config/unity_ppo.yaml` for the robust stage. Keep a fixed evaluation seed
set that training never sees; compare success rate, collision rate, energy per metre,
depth error, and action jerk rather than selecting a model from training loss alone.

## Ocean realism and calibration loop

The Unity environment now randomizes mass, drag, current, turbulence, thruster
efficiency, target geometry, and sensor noise. It also models current shear/gusts,
depth-dependent visibility and lighting, suspended particles, and realistic DVL/depth/
sonar sample rates. These ranges are hypotheses until calibrated.

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

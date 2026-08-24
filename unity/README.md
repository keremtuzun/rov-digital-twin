# OceanSense Unity digital twin

The older `OceanSenseROV_Bootstrap.onnx` has been superseded by
`OceanSenseROV_OpenSea_Experimental.onnx`, a hybrid waypoint-guidance plus bounded-residual PPO policy.
It passed a documented frozen evaluation on an earlier simulator revision. The reliability overhaul
changed actuator and environment dynamics, so this checkpoint is retained only as a
`legacy_dynamics_baseline` until it passes the new regression matrix. It remains unapproved for
real-vehicle actuation. See `../docs/rl_policy_model_card.md` for the exact compatibility boundary.

This is a complete Unity 6 project scaffold. It includes a procedural eight-thruster ROV, underwater
scene, six-degree-of-freedom hydrodynamics, current, buoyancy, DVL, IMU, depth and forward-sonar
sensors, three mission duties, ML-Agents observations/actions, an operator dashboard, OceanSense API
capture, and a safe high-level ROS 2 telemetry bridge.

The default ocean profile includes lightly contaminated coastal water, turbidity and
suspended sediment, depth-dependent optical attenuation, swell-driven underwater orbital
motion, current shear, gusts and sensor-quality degradation. Environment values are also
recorded in telemetry and synthetic-capture metadata so training runs remain auditable.

## Open and generate

1. Install Unity Hub and Unity Editor 6000.0 LTS or newer.
2. In Unity Hub, choose **Add > Add project from disk** and select this `unity` folder.
3. Wait for package restore and script compilation. The editor automatically invokes
   `CompleteProjectBuilder` and creates:
   - `Assets/ROVDigitalTwin/Scenes/OceanSenseDemo.unity`
   - `Assets/ROVDigitalTwin/Prefabs/OceanSenseROV.prefab`
   - generated materials
4. If generation was interrupted, run **OceanSense > Build Complete Demo**.
5. Open `OceanSenseDemo` and press Play.

The scene and prefab are editor-generated because Unity is not installed in the code-authoring
environment. They become normal editable Unity assets after the first successful open.

## Controls and services

- `1`: station keeping
- `2`: pipeline tracking
- `3`: target waypoint
- `C`: capture the inspection camera and call perception followed by decision
- `G`: capture one domain-randomized synthetic frame plus a JSON sidecar of scene parameters
- `R`: reset the ROV and duty
- `Esc`: immediately command all simulated thrusters to zero

Start the local intelligence service from the repository root before pressing `C`:

```powershell
python -m pip install -e ".[api]"
python scripts/run_api.py
```

The API client sends a PNG path that is valid when Unity and the API run on the same Windows machine.
For a remote API, replace path exchange with authenticated binary upload or object storage.

## ROS 2 bridge

Unity emits telemetry JSON by UDP to port `15000` and listens for high-level intent JSON on `15001`.
The ROS node publishes telemetry on `/rov/telemetry_json` and subscribes to
`/rov/high_level_command`:

```bash
cd ros2
colcon build --packages-select rov_dt_bridge
source install/setup.bash
ros2 run rov_dt_bridge unity_udp_bridge
```

Commands must be JSON objects with an `intent` field. They are displayed/recorded only; this bridge
does not translate network input into raw motor forces.

The diagnostic model path is mandatory; the repository intentionally contains no default
`models/weakpoint.json`. See `docs/integration_guide.md` for explicit model and disabled simulation-only
intent-gateway commands.

## ML-Agents status

The behavior is `OceanSenseROV`, with 39 vector observations and 8 continuous thruster residuals.
The generated scene assigns the experimental ONNX policy to `BehaviorParameters`; the deterministic
guidance and independent anti-flip safety layers remain active underneath it. Training and frozen
evaluation configs are under `../config/`. Real ocean operation still requires parameter identification,
sensor calibration, fault testing, HIL, tank trials and supervised sea trials.

`FaultInjectionController` provides explicit normal, individual/paired thruster degradation, hard
failure, saturation and lag, IMU bias/noise/spikes/clipping/dropout, depth bias/jump/stuck, DVL
intermittency, sonar blindness/false returns, buoyancy loss, added drag/biofouling, low battery,
communication impairment/outage and compound scenarios. Synthetic captures are marked synthetic and
must never be placed in the real external test set.

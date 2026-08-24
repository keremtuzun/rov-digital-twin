# Hardware-in-the-loop architecture

The HIL boundary is transport- and hardware-neutral:

```text
real flight computer -> real communications/ROS 2 -> simulated sensor topics -> Unity physics
                                                   <- high-level state/telemetry <-
```

Supported test arrangements are real controller with simulated vehicle, simulated diagnostics with
recorded real telemetry, and real sensors feeding a simulated environment adapter. ROS topic adapters
must translate into the canonical `2.0.0` envelope and preserve source timestamps, provenance, masks and
calibration versions.

The diagnostic, perception and LLM paths may emit only allowlisted high-level intents. PWM, motor
voltage, motor torque and individual thruster force remain inside the deterministic flight controller.
Network isolation, an independent kill switch, leak/depth/power watchdogs and operator control are
required for every energized HIL session.

For each run record the Unity commit/build, ROS graph, flight-controller firmware, vehicle profile,
simulator profile, model hashes, calibration versions, randomized seed, commands, sensor topics,
watchdog transitions and operator interventions. Replay the resulting canonical export before promotion.

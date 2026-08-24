# Progressive open-water validation plan

Simulation success is not evidence of open-sea readiness. Promotion proceeds one signed stage at a time;
failure returns the system to the previous accepted stage.

| Stage | Entry criteria | Exit criteria and metrics | Safety/logging requirements | Failure conditions |
| --- | --- | --- | --- | --- |
| 1. Pure simulation | Unit/static checks pass; profiles versioned | Frozen nominal/randomized/fault suites meet per-condition mission, collision, tracking, energy, OOD and critical-recall gates | Fixed seeds, model/config hashes, full telemetry | Flip, collision, unsafe recommendation, missing audit data |
| 2. Recorded replay | Approved canonical mission exports | Deterministic replay; acceptable fault recall, OOD AUROC, ECE and detection delay per source | Shadow mode; immutable logs and provenance | Any prediction affects vehicle; stale data accepted as valid |
| 3. SIL | Flight software build identified | Closed-loop stability and fault recovery within limits | Isolated network, deterministic watchdogs, traceable ROS graph | Raw authority escapes diagnostic path |
| 4. HIL | SIL accepted; bench risk review signed | Timing, packet-loss, sensor-fault and failover gates pass | Kill switch, current limiting, operator control, synchronized logging | Interlock failure or unbounded command |
| 5. Bench | HIL accepted; restrained dry setup | Thruster curves, voltage sag, temperature derating and emergency stop verified | Physical guards, fire/electrical plan, two-person rule | Unexpected motion, overheating, stop latency breach |
| 6. Pool | Bench accepted; waterproof/leak test | Depth/pose tracking, leak response and recovery meet signed limits | Tether, diver exclusion, recovery equipment, shadow diagnostics | Leak, loss of localization/control, safety-envelope breach |
| 7. Sheltered water | Pool accepted; weather/site permit | Repeatability across currents/visibility; no unsafe advice | Chase/recovery craft as required, geofence, weather log | Geofence breach, comms instability without safe response |
| 8. Near-shore | Sheltered-water dossier signed | Mission completion and fault handling meet predeclared limits | Marine operations plan, abort points, independent tracking | Forecast/sea state exceeds envelope; watchdog/telemetry failure |
| 9. Open water | Regulatory/organizational approval and prior stages signed | Site-specific acceptance only; no universal readiness claim | Full offshore risk plan, redundancy, recovery assets, human command | Any critical event, OOD rate or sea state exceeds signed limits |

Every stage reports conditions separately: nominal simulation, randomized simulation, synthetic faults,
pool, sheltered water and open water. Required records include source timestamps, missing masks, sensor
provenance, calibration/dataset/model/vehicle/simulator versions, uncertainty, decisions, overrides,
fault truth where defensible, collision/mission/energy/control metrics and all safety events.

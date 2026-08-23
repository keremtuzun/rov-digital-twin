# HIL and field validation plan

Every stage requires logs, named operator approval and an abort path. Passing a stage authorizes only
the next stage, not deployment.

| Stage | Preconditions | Scenarios and success criteria | Fail-safe / logs / abort |
|---|---|---|---|
| 1. Unit tests | Clean checkout, Python | Schema, taxonomy, decisions, metrics all pass | No external effect; preserve test report |
| 2. Contract tests | Canonical sample | Valid Unity JSON converts; invalid JSON/fields are rejected | Warn/drop only; log payload hash and reason |
| 3. Unity Edit Mode | Licensed Unity 6 | Compile, builder and physics contract tests pass | Exit batch on failure; retain editor/test XML |
| 4. Unity Play Mode | Generated demo | Reset, sensors, 39/8 contract, API/UDP, emergency stop | Zero thrust; log frame/physics/network events |
| 5. SIL | Approved controller container | Nominal plus every fault and combined fault; no unsafe intent | Supervisor stop, safe-volume bound, seed/config logs |
| 6. ROS bag replay | Versioned representative bags | Deterministic decisions, malformed/dropout tolerance | Never publish actuator command; archive bag/model hashes |
| 7. Controller bench | Isolated controller, no propellers | Timing, watchdog, saturation and command authorization | Hardware E-stop; voltage/current/network logs |
| 8. HIL | Guarded rig, trained staff | Sensor/controller/telemetry loop under injected faults | Physical interlock, two-person approval, immediate power cut |
| 9. Controlled pool | Permits, recovery line, safety team | Low speed, depth/hold/return, comms loss, recovery | Geofence, tether, surface command, visual observer logs |
| 10. Shallow water | Pool acceptance, weather/site permit | Current, visibility and range envelope without people nearby | Conservative abort thresholds and chase/recovery asset |
| 11. Mission pilot | Independent review and external test evidence | Predeclared mission success and zero safety violations | Pilot authority, continuous logging, post-mission quarantine/review |

At every physical stage, abort on lost operator link, watchdog expiry, unexpected thrust, leakage,
thermal/electrical limit, safe-volume breach, sensor disagreement beyond the approved envelope, or any
operator concern. The decision agent supplies only high-level recommendations; an independently tested
gateway and human authority own actuator feasibility.

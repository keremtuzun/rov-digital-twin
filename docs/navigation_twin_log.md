# Navigation twin fidelity log

## Selected component

The selected fidelity component is the command-to-thrust and hydrodynamic response path. The current
code separates command from actual thrust and models dead zone, nonlinear curve, reverse asymmetry,
saturation, lag/slew, voltage/temperature/water-density derating and per-thruster variation. The vehicle
profile loader maps identified linear/quadratic drag into explicit viscous and quadratic force terms.

## Evidence status

Python and static Unity contract checks pass. Eight Unity EditMode tests passed before the final
calibrated-drag loader adjustment. A later headless rebuild was blocked before compilation by the local
Unity Licensing Client protocol/signature check. Therefore no new before/after trajectory or PPO metric
is claimed for the final source revision, and the existing ONNX checkpoint remains a legacy-dynamics
baseline.

## Required next measurement

After the licensing/build issue is cleared, run fixed-seed legacy-vs-advanced thrust profiles over the
same station-keeping and waypoint missions. Export replayable RobotState, SensorFrame and MissionEvent
logs, and compare trajectory error, tilt, energy, mission success, collisions and actuator response lag.
Report every simulator profile separately and do not reuse historical PPO metrics as current evidence.

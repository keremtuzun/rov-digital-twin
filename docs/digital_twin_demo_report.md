# Digital twin demo report

## Purpose

The demo command links the navigation twin and 2D visual inspection fixture without collapsing their
responsibilities. It does not run the graph-based Model 2 Failure Twin v0. It produces artifacts, not
only a screenshot:

```powershell
python scripts/run_digital_twin_demo.py --run-id digital-twin-demo-v1
```

Inputs are `configs/navigation_twin/demo_mission.json` and
`configs/failure_twin/demo_scenario.json`. Outputs under `experiments/runs/<run_id>/` include separate
navigation logs, failure-twin image/mask/metadata, prediction JSONL, decision JSON, integration trace,
run manifest and JSON/Markdown reports.

## Evidence boundary

Because Model 1 has no approved freeze package, the demo uses an explicitly named placeholder that
returns `unknown` with zero confidence. The correct failure-first result is therefore `flag_unknown`,
not a fabricated successful detection. The demo validates shared-ID traceability and replayable software
interfaces only. Failure evidence is synthetic, navigation is an uncalibrated deterministic kinematic
replay, and neither result establishes field performance or physical accuracy.

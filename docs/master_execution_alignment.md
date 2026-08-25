# Master execution guide alignment

The Conrad Challenge Software Master Execution Guide is treated as a product and engineering reference.
It is not evidence that a checkpoint, dataset, metric or physical validation exists. Repository changes
preserve the existing OceanSense/ROV architecture while separating responsibilities that were previously
too easy to conflate.

| Guide track | Repository status before alignment | Implemented alignment | Remaining evidence gate |
| --- | --- | --- | --- |
| Model 1 conventional baseline | Training/evaluation code existed; no approved real dataset or checkpoint | Model 1 is named separately from telemetry diagnostics; freeze report and shared prediction evaluation are defined | Approved manifest, checkpoint and clean-checkout validation are absent |
| Dataset expansion | Seven catalog sources with conservative license notes | Existing governance remains authoritative; gaps are tied to Model 1 freeze/failure analysis | At least 15 researched sources and five usable sources require evidence-backed review |
| Navigation twin | Strong Unity ROV, PPO, faults and sim-to-real reliability work | Navigation is explicitly limited to robot motion/viewpoint context; separate RobotState/SensorFrame/Target/Event replay logs and a deterministic headless mission runner are defined | Current Unity before/after fidelity metrics remain open |
| Inspection/failure twin | A seeded 2D visual-pair generator existed but could not test hidden dynamic-state inference | Kept the visual fixture separate and added Failure Twin v0: connected graphs, simulator-only degradation trajectories, masked/noisy Model-1-like observations and scenario-level datasets | Dynamics remain deliberately uncalibrated; visual and graph twins must not be conflated |
| Model 2 R&D | The transparent scoring heuristic did not implement the new standalone dynamic-state formulation | Formalized `P(S_t | O_1...O_t)` and added the experimental environment, schemas, debug plots and tests without training | Four same-distribution baselines and literature review must precede Model 2 v0 training |
| Evaluation infrastructure | Several track-specific metrics and manifests existed | Shared dataset/prediction/run contracts, generic prediction evaluation and report generation added | Freeze package and integrated demonstration run manifest are not yet available |
| Decision agents | Safety-gated high-level actions existed | Exact mission-level accept/reinspect/change-viewpoint/unknown/escalate interface added | Operator thresholds require validation; recommendation remains non-authoritative |
| Two-twin demo | No single artifact-producing integration command | `run_digital_twin_demo.py` links all five shared IDs, pose, target, scenario ground truth, placeholder prediction, decision, logs and run report | Replace the placeholder only after Model 1 freeze; compare headless navigation with Unity |

## Architectural boundary

```text
Navigation twin / recorded mission
        -> SensorFrame + RobotState + InspectionTarget + MissionEvent
        -> Model 1 conventional observation
        -> Model 1 failure analysis and dataset gaps
        -> Model 2 structural-temporal research hypothesis
        -> mission decision recommendation

Failure Twin v0
        -> structural graph + hidden dynamic state
        -> partial/noisy masked Model-1-like observations
        -> Model 2 experiments and evaluation only

2D visual fixture
        -> controlled synthetic frames + masks + severity + metadata
        -> interface demonstration only
```

Failure Twin v0 never supplies robot dynamics or image evidence. The navigation twin never claims
structural-damage ground truth. Telemetry fault classification remains a vehicle-health capability and
is not renamed Model 1 or Model 2. LLM components may explain structured evidence but do not establish
metrics or technical truth.

## Immediate priorities

1. Acquire or approve a real Model 1 dataset manifest and checkpoint before attempting a freeze.
2. Run Model 1 evaluation and create a reviewed failure index; use it to drive source expansion.
3. Clear the Unity licensing/build blocker and measure the selected calibrated drag/thruster improvement.
4. Review the Failure Twin v0 debug dataset and its truth-only plots without treating it as field
   validation.
5. Implement the four same-distribution baselines before any Model 2 v0 network or architecture claim.
6. Capture every major run with a shared run manifest, limitations and exact reproduction command.

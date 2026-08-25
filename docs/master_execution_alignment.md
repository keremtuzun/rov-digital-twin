# Master execution guide alignment

The Conrad Challenge Software Master Execution Guide is treated as a product and engineering reference.
It is not evidence that a checkpoint, dataset, metric or physical validation exists. Repository changes
preserve the existing OceanSense/ROV architecture while separating responsibilities that were previously
too easy to conflate.

| Guide track | Repository status before alignment | Implemented alignment | Remaining evidence gate |
| --- | --- | --- | --- |
| Model 1 conventional baseline | Training/evaluation code existed; no approved real dataset or checkpoint | Model 1 is named separately from telemetry diagnostics; freeze report and shared prediction evaluation are defined | Approved manifest, checkpoint and clean-checkout validation are absent |
| Dataset expansion | Seven catalog sources with conservative license notes | Existing governance remains authoritative; gaps are tied to Model 1 freeze/failure analysis | At least 15 researched sources and five usable sources require evidence-backed review |
| Navigation twin | Strong Unity ROV, PPO, faults and sim-to-real reliability work | Navigation is explicitly limited to robot motion/viewpoint context; replay contracts are defined | Current Unity rebuild and before/after fidelity metrics remain open |
| Inspection/failure twin | Structural damage generation was mixed conceptually with synthetic camera capture | Separate seeded 2D generator emits normal/degraded pairs, masks, severity, split and metadata | Human sanity review and comparison with real visual distributions are required |
| Model 2 R&D | Vision, telemetry and LLM components could be mistaken for Model 2 | Structural-temporal evidence reasoner, graph support and mandatory ablations define a falsifiable hypothesis | Literature matrix, approved real evaluation data and empirical comparison are required |
| Evaluation infrastructure | Several track-specific metrics and manifests existed | Shared dataset/prediction/run contracts, generic prediction evaluation and report generation added | Freeze package and integrated demonstration run manifest are not yet available |
| Decision agents | Safety-gated high-level actions existed | Exact mission-level accept/reinspect/change-viewpoint/unknown/escalate interface added | Operator thresholds require validation; recommendation remains non-authoritative |

## Architectural boundary

```text
Navigation twin / recorded mission
        -> SensorFrame + RobotState + InspectionTarget + MissionEvent
        -> Model 1 conventional observation
        -> Model 1 failure analysis and dataset gaps
        -> Model 2 structural-temporal research hypothesis
        -> mission decision recommendation

Failure twin
        -> controlled synthetic frames + masks + severity + metadata
        -> Model 2 experiments and evaluation only
```

The failure twin never supplies robot dynamics. The navigation twin never claims structural-damage ground
truth. Telemetry fault classification remains a vehicle-health capability and is not renamed Model 1 or
Model 2. LLM components may explain structured evidence but do not establish metrics or technical truth.

## Immediate priorities

1. Acquire or approve a real Model 1 dataset manifest and checkpoint before attempting a freeze.
2. Run Model 1 evaluation and create a reviewed failure index; use it to drive source expansion.
3. Clear the Unity licensing/build blocker and measure the selected calibrated drag/thruster improvement.
4. Generate and human-review the first failure-twin batch without treating it as field validation.
5. Complete Model 2 literature research, then evaluate full vs ablated mechanisms on real and synthetic
   conditions separately.
6. Capture every major run with a shared run manifest, limitations and exact reproduction command.

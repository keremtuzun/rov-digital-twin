# Model 2 architecture boundary audit

Audit basis: commit `a5a8de0` and the authoritative three-system correction dated 2026-08-25.
No existing work was deleted during this audit.

## ARCHITECTURAL MIXUPS FOUND

1. `MODEL2_FIRST_SESSION_REPORT.md` listed a Unity static check alongside Model 2 verification. That
   check belongs to the robot/navigation track and is not Model 2 evidence.
2. The legacy 2D image-pair generator still described itself as an inspection/failure twin. It is a
   visual interface fixture, not the Python graph-based Failure Twin v0.
3. The navigation-plus-visual-fixture integration command was called a “two-twin demo”. That wording
   can imply that it executes or validates Model 2, although it does neither.
4. `model2_reasoning.py` is an earlier deterministic heuristic outside the new `oceansense.model2`
   package. It is valid historical research code but can be mistaken for Model 2 v0.

## FILES AFFECTED

- Model 2 report/research boundary: `docs/MODEL2_FIRST_SESSION_REPORT.md`,
  `docs/MODEL2_RESEARCH_SPEC.md`, `docs/model2_research_log.md`.
- Cross-track terminology: `README.md`, `docs/master_execution_alignment.md`,
  `docs/digital_twin_demo_report.md`, `docs/failure_twin_spec.md`.
- Legacy visual fixture naming: `src/oceansense/failure_twin.py`,
  `scripts/run_failure_twin_batch.py`.
- Integration-demo naming: `src/oceansense/digital_twin_demo.py`,
  `scripts/run_digital_twin_demo.py`.
- Legacy heuristic boundary: `src/oceansense/model2_reasoning.py`.

## WHAT IS STILL VALID

- `src/oceansense/model2/` is independently runnable Python infrastructure. It uses NumPy, NetworkX,
  Matplotlib and PyYAML through the optional `model2` dependency group, not Unity code.
- Connected graph generation, simulator-only hidden state, configurable degradation, `Model1Simulator`,
  masked/noisy observations, scenario-level splits, dataset regeneration and debug plots match the
  Failure Twin v0 scope.
- The 100-scenario, 20-node, 10-timestep debug config and its reproducibility/no-leakage tests remain
  valid.
- Unity navigation code, Model 1 perception code and the visual fixture may remain in the repository as
  separate systems.

## WHAT NEEDS TO BE DECOUPLED

- Unity/static/Play Mode results must never be included in Model 2 validation summaries.
- The visual image-pair fixture must not be called Failure Twin v0 or used as Model 2 v0 input.
- The navigation-plus-visual demo must not be presented as Model 2 integration or validation.
- The legacy heuristic must remain explicitly pre-v0 until same-distribution baselines and the dynamic
  Model 2 architecture are implemented.

## WHAT SHOULD REMAIN IN UNITY

Robot pose and motion, thrusters, hydrodynamics, underwater environment, sensors, mission targets,
navigation/RL policy, controller behavior, obstacles, disturbances and future trajectory planning.

## WHAT SHOULD MOVE/BELONG TO MODEL 2

Python structural graphs, latent infrastructure condition, degradation progression, observation masks,
Model-1-like structured evidence, scenario datasets, conventional baselines, dynamic state inference,
uncertainty, evaluation metrics and ablations. Current files already reside under
`src/oceansense/model2`; no physical move is required.

## PROPOSED CORRECTION

Keep the existing directory conventions and APIs. Correct misleading terminology and validation text,
label the historical heuristic as pre-v0, and add an automated dependency-boundary test that rejects
Unity/navigation/ML-Agents imports from the Model 2 package and standalone scripts. Continue to the four
baselines only after these corrections pass the standalone Python tests.

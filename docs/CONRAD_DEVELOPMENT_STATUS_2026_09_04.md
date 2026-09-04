# Conrad development status - 2026-09-04

This is the earlier baseline-stage snapshot. The subsequent user-authorized custom
research work and remaining external dependencies are recorded in
`CONRAD_REMAINING_GATES_2026_09_04.md` and `MODEL2_S2_RESEARCH_RESULTS.md`.

## Scope and recovered state

Repository: `https://github.com/keremtuzun/rov-digital-twin` (public).
Base: `69d7f2ed3e9ee2c8faf1d59d78076a939bcf056d`, remote
`codex/model2-s1-temporal-gru`; this includes the MLP and deterministic branches.
Local development branch: `kerem/model2-graph-baselines`. No remote writes performed.
The user's 88-page history was reference material, not authority to execute old prompts.
Second Brain CLI was unavailable; no Second Brain save or completion record is claimed.

## Accomplished

1. Recovered the actual current repository rather than rebuilding completed work.
2. Implemented and evaluated Static GNN, then Temporal GNN, on frozen S1 with seeds
   2026201, 2026202, 2026203. Six new runs, no hyperparameter sweep, no Model 1 training.
3. Preserved train-only preprocessing, authoritative masks, causal inference and
   validation-only checkpoint selection. All six new checkpoints are actual validation minima.
4. Saved checkpoints, config copies, logs, full metrics, prediction arrays, failure cases,
   per-seed SHA-256 completion inventories and cross-seed aggregates.
5. Repaired D0/S1 newline damage without modifying their recorded hashes or data values.
   Six old config copies were also restored to their recorded hashes. The repair utility
   refuses any change that cannot reproduce the pre-existing digest exactly.
6. Made release serialization cross-platform deterministic. Actual data/graph/config/split/
   manifest bytes reproduce; runtime metadata truthfully records the new OS/Python.
7. Added fail-closed empty/non-finite loss checks to MLP/GRU and graph training, and
   fixed GRU recovery acceptance of changed configs or incomplete/unsafe prediction inventories.
8. Fixed CI's missing optional test dependencies and pinned the lint rule selection explicitly.
9. Added a saved-artifact auditor that checks all twelve learned runs without new model
   inference on held-out splits. Updated README and the comparison/research reports.

## Verification

- Full Python suite: 156 passed plus 11 subtests, including artifact-audit corruption tests.
- Ruff correctness checks: passed across src/tests/scripts/ROS bridge.
- D0/S1 strict checks and cross-platform S1 regeneration: passed in the suite.
- All 12 learned-run checkpoint/config hashes and prediction metrics: audited successfully.
- Static Unity contract validation: passed. Unity Editor is not installed in this environment;
  compilation, PlayMode, HIL, tank and sea tests were NOT rerun here.
- Model 1 preflight: correctly returned `ready: false` (exit 2).
- Two dependency deprecation warnings from Starlette/httpx/anyio remain; no test failures.
- Telemetry demo: accuracy 0.99, macro-F1 0.990030 on its synthetic data (not Model 1).
- Navigation/visual-fixture integration demo: completed at
  `experiments/runs/conrad-local-verification-20260904` (Git-ignored).
- Original frozen S1 config, splits, array values and recorded release hashes unchanged.

## Results and limits

| New baseline (three-seed mean) | Validation MAE | Test MAE | OOD MAE |
| --- | ---: | ---: | ---: |
| Static GNN | 0.092952 | 0.091610 | 0.207073 |
| Temporal GNN | 0.083243 | 0.081531 | 0.210893 |

Temporal GNN has the lowest in-distribution error in the six-baseline table; existing
Temporal GRU remains better on OOD (0.198339 MAE). There is no all-regimes winner.
S1 has only 200 synthetic scenarios, five timesteps and ten nodes, with a combined OOD
shift. Graph results do not prove exact weld/bolt strength, microcrack diagnosis,
real sensor fusion, calibrated uncertainty, proprietary novelty or safe deployment.

## Reproduce / audit

```bash
python -m pip install -e '.[dev,model2,api]' pillow httpx pytest-subtests
export PYTHONPATH=src  # useful if a managed Python runtime does not load editable .pth files
python -m pytest -q
python scripts/validate_model2_baseline_artifacts.py
python scripts/repair_model2_evidence_newlines.py  # dry-run; normally zero repairs
python scripts/validate_unity_project.py
python scripts/preflight_model1_baseline_v2.py --config configs/model1_baseline_v2.yaml
```

Graph training commands are `python scripts/run_model2_s1_graph_baseline.py static_gnn`
then the same command with `temporal_gnn`. They intentionally refuse existing output
directories. Do not delete evidence merely to rerun held-out evaluation. The tests use
isolated temporary fixture runs, never replace the frozen reports.

## Still unresolved - whole project is NOT finished

- Model 1: approved manifest, labels, immutable split, review evidence, original checkpoints
  and v2 activation approval remain absent. The historical checkpoint deadline has passed;
  that is not evidence that a package was received or permission was granted.
- Custom Model 2: the conventional comparison gate is complete, but S1 is explicitly NOT
  approved for proprietary-model training. Next work requires a distinct research protocol,
  fresh holdouts, specified uncertainty/calibration targets and ablations. Do not relabel
  Temporal GNN as custom IP or tune on the already-inspected test/OOD results.
- Real sensing and robot deployment: physical calibration, current-dynamics navigation-policy
  qualification and hardware tests need the relevant data, tools and human approval.
- Remote delivery: local branch/checkpoint only; no push, PR or deployment was performed.

The next concrete development decision is the custom Model 2 experiment/data approval,
while human reviewers independently complete the existing Model 1 queues.

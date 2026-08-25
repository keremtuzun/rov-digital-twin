# Model 2 first-session implementation report

## Repository assessment

The repository already contained a visual 2D inspection/failure generator, a transparent
structural-temporal scoring heuristic, run-manifest contracts and a separate Unity navigation twin.
Those pieces remain useful but did not provide a dynamic graph simulator, hidden state trajectories,
masked observations or the scenario dataset layout required by the standalone Model 2 specification.

## Implemented

- Added Model 2 graph/state/observation schemas under `oceansense.model2`.
- Added connected chain, branched pipeline, lattice and mixed graph generation with NetworkX.
- Added normalized hidden corrosion, crack, material-loss, fatigue and condition trajectories.
- Added configurable intrinsic, environmental, neighboring and stochastic degradation terms.
- Added a numerical `Model1Simulator` role with coverage masks, noise, false positives/negatives and
  confidence; unobserved nodes remain present and hidden truth is excluded.
- Added scenario-level dataset export with structure/config/state/observation/mask/metadata files.
- Added four debug visualizations and automated acceptance tests.
- Added the fixed 100-scenario, 20-node, 10-timestep configuration.

## Reproduction

```powershell
python -m pip install -e ".[model2]"
python scripts/generate_model2_dataset.py --config configs/model2/twin_v0.yaml `
  --output data/simulated/model2_debug_v0
python scripts/visualize_model2_scenario.py data/simulated/model2_debug_v0/scenario_000000 `
  --output outputs/model2_debug_plots
python -m pytest -q tests/unit/test_model2_failure_twin_v0.py
```

## Dependencies and limitations

The new optional dependency group contains NumPy, NetworkX, Matplotlib and PyYAML. Dynamics are synthetic,
lightweight and uncalibrated; the observation generator does not run a real image model. Plots exposing
truth are debug artifacts only. This session deliberately did not train Model 2, connect Model 1,
implement active inspection, add photorealism or alter robot control.

The next allowed development session is the four same-distribution baselines and their reproducible
evaluation report. Model 2 v0 training remains gated on those baseline checks.

## Verified result

The fixed configuration generated 100 scenarios with 20 nodes and 10 timesteps. The deterministic hash
split contained 75 train, 9 validation and 16 test scenarios with no overlap. One inspected scenario
had state shape `[10, 20, 5]`, observation shape `[10, 20, 6]`, mask shape `[10, 20]` and 51% observed
entries. The standalone Model 2 validation completed with seven focused Python tests passing and Ruff
clean. A second full generation from the same seed produced identical SHA-256
hashes for the manifest, hidden states, observation tensor, mask and observation JSON of the inspected
scenario. Unity checks are intentionally excluded because they validate the separate robot/navigation
twin, not Model 2.

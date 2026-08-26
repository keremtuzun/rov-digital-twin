# Model 2 proprietary R&D groundwork

**Status:** specification only; no Model 2 training or validated proprietary claim

**Model 1 status:** **BLOCKED / NOT FROZEN**

## 1. Executive definition

Model 2 is a future uncertainty-aware structural-state inference system. Its job is to combine partial inspection evidence, component topology, inspection history, context, and missingness to estimate what may be happening at component and asset level beyond what any single observation directly shows.

The central technical question is:

> What does partial, noisy, multi-source inspection evidence imply about hidden structural condition, degradation, weak points, and future inspection risk?

Model 1 and Model 2 solve different problems. Model 1 is a conventional perception baseline: it reports directly visible objects or cautious condition indicators in an image or sensor observation. Model 2 consumes such observations as fallible evidence and reasons over structure and time. It is not another detector, an EfficientNet successor, “Model 1 v2,” a general LLM, the telemetry vehicle-health classifier, the Unity navigation policy, or a hand-written risk formula.

The proprietary/IP-oriented hypothesis is not that graphs, recurrent networks, uncertainty, or digital twins are individually novel. The hypothesis is that a project-specific mechanism for combining inspection evidence with structural topology, temporal memory, explicit missingness, and calibrated uncertainty may yield a defensible technical contribution. Novelty and ownership remain unclaimed until prior-art review, baseline comparison, experiment records, contribution tracing, and legal/IP review exist.

### Current repository reality

`src/oceansense/model2/` currently provides Failure Twin v0 research infrastructure: connected graph generation, synthetic hidden-state evolution, noisy/masked Model-1-like observations, scenario-level splits, and debug visualization. `configs/model2/twin_v0.yaml` defines a reproducible 100-scenario debug configuration, but no immutable generated dataset manifest is currently present in the repository. No Last Observation, MLP, GRU/LSTM, static GNN, temporal GNN, or comparable Model 2 baseline has been trained here.

`src/oceansense/model2_reasoning.py` is a transparent historical pre-v0 heuristic with ablations. It is not the dynamic Model 2 implementation and is not evidence of proprietary performance.

## 2. Model 2 problem formulation

Model 2 must:

> Estimate hidden structural state `S_t` from partial observations `O_1...O_t`, context `C`, structure graph `G`, and uncertainty `U`.

A working probabilistic formulation is:

`p(S_t, S_(t+1:t+h) | O_(1:t), M_(1:t), C_(1:t), G, U_(1:t))`

where:

- `S_t` is a latent state for each component at time `t`, potentially containing cautious degradation variables such as corrosion likelihood, crack likelihood, material-loss likelihood, fatigue proxy, and an aggregate condition state;
- `O_(1:t)` is the history of observations from available modalities;
- `M_(1:t)` is the explicit observation/missingness mask, not an implicit zero-value convention;
- `C_(1:t)` is inspection context such as pose, viewpoint, environment, mission, asset, and sensor configuration;
- `G=(V,E)` is the versioned structure graph whose nodes are components and whose typed edges represent known physical or functional relationships;
- `U_(1:t)` represents observation, model, and data uncertainty;
- `h` is an optional forecast horizon.

The state is hidden because no inspection covers every surface or directly measures every structural property. Time matters because persistent evidence and rates of change differ from isolated detections. The graph matters because welds, bolts, joints, pipes, panels, supports, and neighboring components are not independent. Sensor modality and inspection context matter because an RGB frame, sonar return, maintenance record, and viewpoint have different evidential meaning. Degradation history matters because current risk depends on previous states, interventions, and exposure, not only the latest image.

Failure Twin v0 currently uses normalized synthetic dimensions—`corrosion`, `crack`, `material_loss`, `fatigue`, and derived `condition`. These are controlled simulator variables, not calibrated physical measurements or real failure probabilities.

## 3. Target capabilities

A future Model 2 should be able to:

- infer a distribution over hidden degradation state rather than output one unsupported deterministic score;
- estimate and rank component-level weak-point likelihood;
- reason over welds, bolts, joints, pipes, panels, supports, coatings, connectors, and their typed relationships when the asset schema supports them;
- accumulate repeated observations across time, viewpoints, missions, and sensors;
- fuse RGB, sonar, pose, coverage, context, maintenance, and human evidence without assuming all modalities are present;
- handle missing components and missing timesteps explicitly;
- propagate observation uncertainty and distinguish aleatoric/data ambiguity from epistemic/model uncertainty where feasible;
- distinguish a visible defect indicator from inferred structural risk;
- estimate temporal trend and forecast a bounded future condition distribution;
- recommend the next component/viewpoint/sensor inspection based on uncertainty and expected information gain;
- produce evidence references and a mechanism trace suitable for engineering review.

Model 2 may estimate risk, likelihood, severity band, trend, or inspection priority for welds, bolts, or micro-crack-related evidence. It must not claim true remaining strength, load capacity, crack depth, or failure time from a photograph alone. Those claims require calibrated physical measurements, material/load models, and appropriate engineering validation.

## 4. Candidate inputs

| Input group | Candidate fields | Required treatment |
| --- | --- | --- |
| Model 1 evidence | class probabilities, embeddings, visible-region references, confidence, unknown/OOD score | Evidence only; preserve checkpoint/version and calibration metadata. |
| RGB | frame reference, timestamp, camera intrinsics, exposure, quality, crop/region | Do not silently treat pixels or Model 1 labels as hidden truth. |
| Acoustic sensing | sonar/side-scan references, range, bearing, quality, modality mask | Maintain modality-specific preprocessing and uncertainty. |
| Navigation | pose, covariance, trajectory, viewpoint, distance, coverage | Record coordinate frame and synchronization error. |
| Asset structure | stable component IDs, node types, typed edges, criticality, geometry references | Version and hash the topology; never infer absent edges from desired outcomes. |
| History | prior observations, prior state estimates, inspection/maintenance timestamps | Prevent future-to-past leakage and record interventions. |
| Environment | current, turbidity, salinity, temperature, contamination, wave/disturbance context | Include units, source, uncertainty, and missingness. |
| Human/engineering evidence | reviewed findings, NDT results, severity bands, maintenance/failure records | Require provenance, qualification, rights, and label definition. |
| Twin 2 | synthetic hidden states, observations, masks, graph, scenario parameters | Simulator truth is training/evaluation truth only inside synthetic experiments. |

Every input needs a stable source ID, timestamp or time index, provenance, version, uncertainty representation, and missingness indicator. Inputs unavailable at inference must not enter training features.

## 5. Candidate outputs

Model 2 may produce:

- per-component posterior condition estimate or state distribution;
- degradation, weak-point, and cautious defect-family likelihoods;
- crack/corrosion/material-loss likelihood—not a confirmed diagnosis;
- component risk or inspection-priority score with defined scope;
- uncertainty, calibration status, OOD status, and an abstain/unknown result;
- recommended next component, viewpoint, or modality to inspect;
- evidence references and contribution/explanation trace;
- temporal trend and forecast interval;
- graph-level health summary with the component-level evidence retained.

Outputs must carry model/config/data versions, timestamp, asset/component IDs, evidence window, uncertainty, limitations, and a non-safety-certified claim boundary. A decision agent may recommend inspect, reinspect, change viewpoint, collect another modality, mark unknown, or escalate. It may not directly command individual thrusters or make autonomous structural-safety certification decisions.

## 6. Model 2 boundaries

- Model 2 is not Model 1, a second visual classifier, or `model1_baseline_v2`.
- Model 2 is not Twin 1. Twin 1 simulates/navigation-tests the ROV and inspection workflow.
- Model 2 is not Twin 2. Twin 2 supplies scenarios and controlled ground truth; Model 2 performs inference.
- Model 2 is not Unity navigation, ML-Agents control, an ONNX navigation policy, or vehicle telemetry diagnosis.
- Unity PlayMode, navigation success, and visual fixtures do not validate structural inference.
- Model 2 is not proof of physical deployment, physical integrity, remaining strength, or future failure time.
- It is not a single-image strength oracle and cannot convert visible concern into engineering truth without supporting evidence.
- It may not train on unapproved human labels or consume hidden simulator truth as an inference feature.
- Synthetic-only success supports debugging and architecture comparison, not real-world performance claims.
- The legacy pre-v0 heuristic is a comparator/prototype, not the proprietary Model 2.

## 7. Research questions and falsification tests

1. Which hidden variables are identifiable from available observations, and which require direct/NDT measurements?
2. Which variables are continuous, ordinal, categorical, or survival/time-to-event targets?
3. What state-transition assumptions are defensible for each component and environment?
4. What can RGB-only sequences support beyond visible-condition persistence?
5. Which questions require sonar, pose, maintenance, loading, material, or topology data?
6. How should uncertain or erroneous Model 1 outputs enter the posterior without becoming truth?
7. Which graph edge types have physical meaning, and when should message passing be blocked or directional?
8. How should interventions, replacement, cleaning, and inspection gaps reset or alter state history?
9. Can a temporal model beat Last Observation and independent MLP on unobserved components without leakage?
10. Does graph context improve results over GRU/LSTM and static GNN when neighbor coupling is present?
11. Does the graph advantage disappear appropriately when Twin 2 `neighbor_coupling=0`?
12. How robust are conclusions to missingness mechanisms, sensor bias, class imbalance, topology errors, and domain shift?
13. Which uncertainty method gives calibrated coverage and reliable abstention under shift?
14. Which baseline is strongest, and what mechanism remains unexplained by it?
15. What real repeated-inspection evidence is required before synthetic findings can transfer?

The primary hypothesis must be rejected or narrowed if graph/temporal mechanisms do not consistently outperform simpler baselines under predeclared, leakage-free tests, or if apparent gains vanish under simulator-parameter and topology shifts.

## 8. IP hypothesis and evidence discipline

The defensible IP hypothesis is a dynamic structural-state inference mechanism that combines:

- typed structure-graph reasoning;
- temporal memory across sparse inspections;
- explicit partial-observation and coverage handling;
- uncertainty-aware evidence gating and abstention;
- degradation-state transition constraints;
- topology-aware inspection prioritization and traceable evidence.

This combination may become proprietary through a specific architecture, training objective, state-transition design, uncertainty gate, data/graph representation, or active-inspection policy that produces reproducible gains over all required baselines. The project must preserve dated hypotheses, design decisions, authorship, commits, configs, seeds, datasets, negative results, ablations, and prior-art findings. Public disclosure, licensing, contributor ownership, and patent/trade-secret strategy require qualified legal review before any novelty claim.

Current conclusion: the repository supports a well-scoped R&D hypothesis and Twin 2 groundwork. It does not yet support the claim that Model 2 is implemented, proprietary, novel, calibrated, or physically validated.

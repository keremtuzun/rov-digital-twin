# Model 2 data and Twin 2 requirements

**Status:** target contract; current Failure Twin v0 is debug infrastructure, not real-world evidence

## 1. Twin 2 purpose

Twin 2 is the inspection/failure research twin that supports Model 2. It represents a structure graph, component topology, hidden degradation state, time evolution, partial/noisy observations, sensor coverage and missingness, and known simulator ground truth for controlled experiments.

Twin 2 is not Model 2: it generates or organizes evidence and truth, while Model 2 estimates hidden state without access to truth. Twin 2 is also not Twin 1. Twin 1 covers ROV motion, hydrodynamics, sensors, viewpoints, navigation/control, and inspection workflow. Unity navigation success does not validate Twin 2 physics or Model 2 inference.

Current Failure Twin v0 creates 10–100-node connected synthetic graphs; normalized corrosion, crack, material-loss, fatigue, and aggregate-condition trajectories; noisy Model-1-like observations; binary masks; and scenario-level debug splits. Its dynamics are intentionally lightweight and uncalibrated.

## 2. Required data contract

Every immutable dataset release must have a versioned root such as:

```text
model2_<release_id>/
  dataset_manifest.json
  schema/
    structure.schema.json
    state.schema.json
    observation.schema.json
    metadata.schema.json
  config/
    twin.yaml
    observation_model.yaml
  provenance.json
  checksums.sha256
  splits/
    split.json
  scenarios/
    <scenario_id>/
      structure.json
      states.npy
      observations.npy
      observations.json
      observation_mask.npy
      metadata.json
      interventions.json
```

Failure Twin v0 currently writes analogous per-scenario files and top-level split JSON files. Moving to this release contract requires an explicit schema bundle, provenance record, checksum inventory, intervention history, and one frozen split artifact.

### Structure graph

`structure.json` must contain:

- schema/release version, asset/scenario ID, graph ID, and topology source;
- nodes with stable `component_id`, component type, criticality definition, geometry reference where available, and non-target metadata;
- edges with stable edge ID, endpoints, relation type, directionality, and source/confidence;
- coordinate frame and units for geometric fields;
- a graph hash and validation result.

Node IDs must be unique; every edge endpoint must exist; connectivity expectations must be declared. Real graphs must distinguish measured/engineered relationships from inferred ones. Target-derived edges are forbidden.

### Hidden states

`states.npy` is a tensor with declared shape `[T,N,D_state]`, dtype, dimension order, and companion `state.schema.json`. For Failure Twin v0, `D_state=5`: corrosion, crack, material loss, fatigue, and aggregate condition, all normalized synthetic variables.

The state schema must define meaning, valid range, units or “unitless synthetic,” transition assumptions, label/source method, uncertainty if applicable, and whether each target is observable in real data. Hidden state is available only to the simulator, training loss, and controlled evaluator. Feature loaders must reject it as model input.

### Observations and masks

`observations.npy` uses `[T,N,D_obs]`; `observations.json` provides traceable records and field names. Required record fields include scenario/asset/component ID, timestamp or monotonic time index, modality, source/model version, observed flag, confidence/uncertainty, quality, pose/viewpoint reference, and evidence reference.

`observation_mask.npy` uses `[T,N]` for the current single-channel v0 contract or `[T,N,D_obs/modality]` when missingness differs by field/modality. The mask—not a numeric zero—is authoritative. Unobserved values may be storage zeros only when the loader always applies the mask. Missingness mechanism/configuration must be recorded so random, coverage-driven, sensor-failure, and informative missingness are distinguishable.

For current v0, observation fields are corrosion, crack, material-loss and fatigue probabilities, severity estimate, and confidence. They are generated numerical evidence, not real Model 1 predictions.

### Scenario metadata and time

`metadata.json` must define scenario ID, asset ID/template lineage, synthetic/real status, seed, node/time counts, time base, environment regime, observation coverage, modalities, shapes, generator commit, limitations, hidden-truth location, and intervention references. Real data require UTC timestamps and synchronization uncertainty; synthetic data require deterministic time-step semantics.

### Immutable split

`splits/split.json` must map scenario and asset groups to exactly one of train, validation, or test and include split algorithm/version, seed, group keys, counts, and file hash. Separation must cover scenario ID, asset/template lineage, repeated inspection sequence, and near-duplicate derivations. OOD graph/noise/missingness regimes should be explicitly tagged rather than discovered after results.

### Config, provenance, and checksums

- `config/twin.yaml`: dynamics, topology generation, environment, intervention, clipping, and target aggregation.
- `config/observation_model.yaml`: coverage, sensor noise/bias, false positives/negatives, confidence, modality availability, and missingness.
- `provenance.json`: creator/generator, source assets, licenses/permissions, generation time, code commit, dependency/environment record, synthetic/real declaration, and known limitations.
- `checksums.sha256`: SHA-256 for every release file, generated after freeze and verified before training/evaluation.
- `dataset_manifest.json`: release ID, schema versions, scenario inventory, split hash, config hashes, checksum-file hash, counts, target/observation fields, and approval status.

No mutable “latest” dataset may support a comparison claim. Changes produce a new release ID and complete hash inventory.

## 3. Contract validation gate

Before any baseline training, automated validation must confirm:

- all required files, schemas, versions, hashes, and provenance exist;
- tensor shapes agree with metadata, node order, field order, masks, and timestamps;
- graph nodes/edges are valid and expected graphs are connected;
- values, masks, confidence, and timestamps lie within declared ranges;
- unobserved inference records contain no hidden truth;
- training features cannot load `states.npy` through the inference loader;
- splits are complete, unique, scenario/asset/lineage-disjoint, and immutable;
- generation is reproducible from config and seed;
- no raw real-world data with unclear rights are committed or used;
- synthetic/real results and primary/OOD test sets remain distinguishable.

The current 100-scenario config is suitable for debugging this validator and baseline code paths, not for a performance or IP claim.

## 4. Allowed synthetic use

Twin 2 synthetic data may be used for:

- data-loader, mask, loss, metric, and leakage tests;
- baseline implementation and reproducibility checks;
- architecture experiments and controlled mechanism ablations;
- missingness, noise, topology-error, and sensor-failure robustness tests;
- negative controls such as zero neighbor coupling and shuffled edges;
- controlled weak-point ranking and inspection-policy experiments;
- failure-mode discovery before handling restricted real data.

Synthetic data alone cannot establish real structural accuracy, real corrosion/crack detection, physical strength, remaining useful life, field calibration, safety, deployment readiness, or proprietary novelty. Simulator parameters must not be described as calibrated physics without external evidence.

## 5. Real-data requirements

Future real-world evaluation requires, where legally and practically available:

- repeated inspections of the same identified asset/components over meaningful time intervals;
- stable asset and component IDs linked to a versioned topology;
- inspection pose, viewpoint, timestamp, coverage, sensor configuration, and synchronization quality;
- rights-cleared RGB and acoustic/multi-sensor logs with immutable source hashes;
- independent human/engineering findings with definitions, qualifications, uncertainty, and adjudication;
- NDT, thickness, material-loss, maintenance, repair, replacement, or failure records when available;
- material, geometry, load/exposure, and environmental context needed for the claimed target;
- explicit records of cleaning, repair, replacement, and other state-changing interventions;
- site/asset/mission-grouped splits that prevent temporal and asset leakage;
- consent, license, privacy/security, export, retention, and redistribution controls.

Image-only labels can support visible-evidence and persistence research but generally cannot provide true physical strength or hidden-crack ground truth. Claims must be narrowed to what each reference method measures.

Real-world rollout should progress from retrospective research to prospective shadow-mode evaluation and only then to bounded decision support. Safety/certification use requires independent engineering and regulatory processes outside this R&D plan.

## 6. Interface with Model 1

Model 1 may provide timestamped component-linked observations to Model 2: class probabilities, embeddings, region/evidence references, visible-condition labels, confidence, calibration version, and unknown/OOD status. These are observations `O_t`, never hidden-state truth `S_t`.

The interface must record Model 1 checkpoint, preprocessing, class schema, calibration dataset/version, input hash, and prediction timestamp. Model 2 must consume confidence and missingness, tolerate false positives/negatives, and support abstention when Model 1 is unavailable or outside its validated domain. Training must simulate or measure Model 1 error rather than assume perfect labels.

Original Model 1 is currently blocked/not frozen, and `model1_baseline_v2` has no approved labels or split. Therefore current Twin 2 `Model1Simulator` output must remain explicitly synthetic and cannot impersonate a real Model 1 integration.

## 7. Interface with navigation and Twin 1

Navigation/Twin 1 may provide pose, covariance, trajectory, camera/sonar configuration, viewpoint, coverage, timing, and feasible next-inspection actions. Model 2 may return a high-level inspection priority or information request.

The boundary is strict:

- Twin 1 owns robot/environment simulation and navigation/control behavior.
- Twin 2 owns structural-state scenarios, observation availability, and synthetic truth.
- Model 2 owns hidden-state inference and uncertainty.
- The decision layer may translate Model 2 evidence into bounded inspect/reinspect/escalate recommendations.
- Model 2/Twin 2 may not emit PWM, motor voltage/torque, servo, or individual-thruster commands.

Twin 1 can exercise inspection coverage and viewpoint workflows, but it does not validate structural inference. Unity visual fixtures, PlayMode tests, or navigation ONNX policies are not Model 2 datasets or checkpoints.

## 8. Release and evidence levels

| Level | Evidence | Permitted statement |
| --- | --- | --- |
| D0 | Generated debug scenarios, schema/tests pass | “Pipeline/debug contract works on synthetic fixtures.” |
| S1 | Immutable synthetic release and six baselines | “Relative simulator benchmark under named assumptions.” |
| R1 | Rights-cleared retrospective repeated inspections | “Retrospective research result on named assets/data.” |
| R2 | Prospective shadow-mode study | “Prospective decision-support evidence within study scope.” |
| D3 | Independent engineering/safety validation | Only claims authorized by that external validation. |

Current status is pre-D0 for an immutable release: generator tests pass, but the generated dataset release, full schema/provenance/checksum bundle, and baseline matrix are not present. The next action is to implement and test the release validator, review the v0 state semantics, then create a checksummed debug snapshot. This does not authorize Model 2 training or a proprietary claim.

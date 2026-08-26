# Model 2 / Twin 2 S1 synthetic comparison release

**Gate result:** `S1 SYNTHETIC COMPARISON RELEASE VALID`

**Release:** `twin2-s1-synthetic-v1`

**Scope:** internal synthetic baseline comparison only; no learned baseline trained in this step

## What S1 is

S1 is an immutable, multi-seed Twin 2 release for developing and comparing conventional Model 2 baselines under controlled synthetic conditions. It expands D0 from a data-contract smoke fixture into a lineage-separated comparison dataset with multiple graph families, degradation regimes, observation coverage levels, and an explicit out-of-distribution split.

S1 still is not Model 2, a proprietary architecture, calibrated failure physics, Model 1 v2, Twin 1, Unity navigation, or a real inspection dataset. `states.npy` remains simulator-only target/evaluation truth and is excluded from declared inference inputs.

## Why S1 follows D0

D0 proved that the release format, masks, graph mappings, checksums, split loading, and two non-trained smoke baselines work end to end. Its 25 scenarios and single debug configuration were deliberately too small for learned baselines. S1 keeps the audited D0 tensor/file contract while adding scale, multiple root seeds, grouped lineages, distribution metadata, non-overlapping train/validation/test/OOD partitions, and stronger validation.

## What S1 may prove

- the S1 generator is deterministic under its frozen configuration and recorded runtime;
- related synthetic scenarios remain in one split through lineage grouping;
- learned baseline data loaders can be developed against fixed train/validation/test/OOD partitions;
- baseline behavior can be compared across named in-distribution and synthetic OOD conditions;
- checksum, provenance, graph, mask, tensor, leakage, seed, distribution, lineage, and split gates work;
- conventional baseline implementation may proceed under the predeclared comparison protocol.

## What S1 does not prove

S1 does not prove real-world Model 2 accuracy, ocean performance, physical strength, remaining life, real corrosion/crack detection, calibrated risk, safety, deployment readiness, novelty, or proprietary superiority. It does not validate Model 1, and its numerical Model-1-like evidence is synthetic. A model that performs well on S1 may only be learning this simulator’s assumptions.

Model 1 remains **BLOCKED / NOT FROZEN**. S1 creates no Model 1 labels, checkpoint, immutable Model 1 split, or freeze evidence.

## Frozen generation configuration

The source configuration is `configs/model2/s1_synthetic_release.json`. The release-local frozen copy is `data/model2/s1_synthetic/config.json`.

| Property | Value |
| --- | --- |
| Schema / generator | `1.1.0` / `oceansense-twin2-s1-release/1.0.0` |
| Scenarios | 200 |
| Timesteps / nodes | 5 / 10 |
| State / observation dimensions | 5 / 6 |
| Root seeds | `2026101`, `2026102`, `2026103`, `2026104` |
| Lineages / scenarios per lineage | 50 / 4 |
| ID graph families | `chain`, `branched_pipeline`, `small_lattice` |
| ID degradation regimes | `slow`, `moderate`, `accelerated` |
| ID observation coverage | `0.35`, `0.55`, `0.75` |
| Split seed | `1601` |

The four scenarios in a lineage are deterministic stochastic siblings derived from one lineage group and frozen root-seed schedule. The lineage, root seed, scenario seed, replicate, split, and distribution parameters are recorded for every scenario in `metadata.json`.

## Release tensors and splits

| Artifact | Shape or count |
| --- | ---: |
| `states.npy` | `[200, 5, 10, 5]` |
| `observations.npy` | `[200, 5, 10, 6]` |
| `observation_mask.npy` | `[200, 5, 10]` |
| Train | 120 scenarios / 30 lineages |
| Validation | 32 scenarios / 8 lineages |
| Test | 24 scenarios / 6 lineages |
| OOD | 24 scenarios / 6 lineages |

Every lineage is assigned wholly to exactly one split using a seeded lineage shuffle before scenario generation. Split assignment uses only `lineage_id` and the split seed; it does not use hidden state, severity, condition, labels, or timestep values. All four splits are non-empty, scenario-level, exhaustive, and pairwise disjoint in both scenario and lineage identity.

## OOD design

Train, validation, and test use the same declared in-distribution support: three graph families, three degradation regimes, coverage `0.35/0.55/0.75`, state-process noise `0.01`, and environment level `0.5`.

OOD shifts five dimensions together:

| Dimension | ID support | OOD value |
| --- | --- | --- |
| Graph family | chain, branched pipeline, small lattice | `mixed_structure` (unseen) |
| Degradation regime | slow, moderate, accelerated | `high_stress_ood` (unseen) |
| Observation coverage | 0.35, 0.55, 0.75 | `0.20` |
| State-process noise | 0.01 | `0.03` |
| Environment level | 0.50 | `0.95` |

OOD also increases severity-observation noise from `0.08` to `0.15` and confidence noise from `0.05` to `0.10`. These are synthetic stress tests, not estimates of actual sea conditions. The OOD definition and shifted dimensions are frozen in `splits.json`; every OOD scenario repeats them in its scenario record.

## Leakage controls

- Validator runs before the release is accepted.
- `states.npy` is a hidden target file, never an inference input.
- Inference inputs remain observations, observation mask, and structure graph only.
- Direct state names, `hidden_state`, `true_condition`, and `ground_truth` are forbidden observation fields.
- Observed proxy fields are declared explicitly; the mask remains authoritative.
- Every scenario appears once and every lineage appears in one split only.
- Split assignment basis is recorded and target-independent.
- OOD must have a non-empty documented reason and a value outside train support in at least one declared shifted dimension.
- Graph node IDs map to stable tensor indices; edges must be valid and graphs connected.
- Tensor shapes, mask values, masked-zero behavior, dimensions, field layouts, and scenario counts are cross-checked.
- Optional truth-bearing visualizations must be `debug_only` and cannot be inference inputs.
- No Unity, navigation policy, visual fixture, or Model 1 checkpoint is mixed into S1.

## Stronger S1 validator gate

`release_validator.py` now distinguishes D0 `debug` evidence from S1 `synthetic_comparison`. Strict S1 validation additionally requires:

- release level `S1`, type `synthetic_comparison`, and schema `1.1.0`;
- at least 200 scenarios, 5 timesteps, and 10 nodes;
- at least three recorded integer generation seeds;
- one distribution/lineage/root-seed record per scenario;
- at least three graph families, degradation regimes, and coverage levels across S1;
- non-empty train/validation/test/OOD splits;
- no scenario or lineage overlap;
- documented OOD reason/shift dimensions and an actual train-support difference;
- synthetic/comparison-only claim boundary;
- `approved_for_proprietary_model_training=false`.

The common validator continues checking required files, safe manifest paths, arrays, graphs, masks, splits, checksums, timestamps, generator/runtime metadata, and hidden-truth leakage for both D0 and S1.

## Checksum and provenance controls

`checksums.json` records SHA-256 for the manifest and every other required artifact. The current immutable hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `manifest.json` | `2adba7821141d673e12487cf1e8f4767fb777de828630b4b98019d5e302cec33` |
| `config.json` | `08b3cd9be900d905856d7be70fdff4c96253b8884388cbb88c7f4381d6d51674` |
| `metadata.json` | `8ad3f5ca2c1ffb4617ecff866bebd27167b406cf7ba224b67052462862571f41` |
| `splits.json` | `826d7063cbc9f2598a6e7c69bc3db066b599c2ee5f1497e043ddf27374eaa89d` |
| `structure_graph.json` | `d1348aaadd305185455bfcb9e4aff8ec99d414d0418c728186543e237c4b5659` |
| `states.npy` | `912d4377c1b5ddc80cf59389608eff614e88b455bfa6de8497b075f7d9b4efe4` |
| `observations.npy` | `ae1954a79ac8c7f55707050701a2706331af0e7d2cd6cd807d0abbbc21d25a8c` |
| `observation_mask.npy` | `b594cd785a2eada3eb9312ffe244032d13c25aca6633abee50f2b8743a206cac` |

Metadata records release/schema identity, UTC creation time, generator name/version, root and scenario seeds, Python/runtime platform, NumPy, NetworkX, PyYAML, scenario lineage/distribution records, synthetic status, and claim boundary. The release is approximately 1.2 MiB and contains only generated numeric/JSON artifacts, so it is committed for checkout-level reproducibility; it contains no raw images, real inspection data, personal data, labels, or checkpoints.

Any semantic change requires a new release ID. `--force` is only a controlled pre-consumption byte-regeneration check; the builder refuses unknown contents or a different release. Checksums must never be updated to conceal an unexplained mutation.

## Build and validation commands

Build a new checkout where the release path does not exist:

```powershell
python scripts/build_model2_s1_release.py
```

Validate the frozen release:

```powershell
python scripts/validate_model2_release.py `
  --release-dir data/model2/s1_synthetic `
  --strict `
  --require-synthetic-s1
```

The builder and validator do not train a model. Strict validation exits nonzero on any contract failure.

## Test evidence

Automated tests verify successful S1 validation, exact nonzero split counts, byte-identical deterministic regeneration, unseen OOD graph support, lineage-leakage rejection, scenario-overlap rejection, checksum-corruption rejection, missing-OOD-metadata rejection, and hidden-state-input rejection. Existing D0 validator tests remain active to prevent backward incompatibility.

## Next baselines allowed

With the immutable S1 gate passing, the next task may implement—not yet claim success for—Independent MLP, Temporal GRU/LSTM, Static GNN, and generic Temporal GNN baselines under the common evaluator. Training must use train only, select on validation only, open test/OOD through a frozen evaluation protocol, run repeated predeclared seeds, preserve all configs/checkpoints/predictions, and report failures and synthetic limitations.

No proprietary Model 2 mechanism should be implemented until the complete six-baseline matrix and negative controls exist. S1 results will remain internal synthetic comparison evidence and cannot support real-world or proprietary superiority claims.

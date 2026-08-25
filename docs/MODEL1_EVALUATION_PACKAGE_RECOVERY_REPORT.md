# Model 1 Evaluation Package Recovery Report

- Audit date: 2026-08-25
- Branch: `codex/rov-digital-twin`
- Audited commit: `bd273a4f6f64022e25f3e4f678813aaeaf12cb94`

## 1. Final Recovery Decision

**PARTIALLY RECOVERED.** Model 1's implementation, evaluation config/script, class schema, preprocessing code,
source-license registry, an empty approved-manifest template, and an older source-code ZIP were found. The
original evaluation package's core artifacts - visual checkpoint pair, actual `labels.csv`, approved images,
immutable split, genuine metrics, predictions, and failure examples - were not found. Evaluation remains
blocked.

“Partially recovered” describes package components, not model readiness. No new evidence supports freezing or
measuring Model 1.

## 2. Recovery Table

| Required Artifact | Found? | Path / Evidence | Usable? | Notes |
|---|---:|---|---:|---|
| Visual checkpoint pair | No | Expected `models/oceansense_{domain,condition}_efficientnet_b0.pt` absent; no matching object in all git history, local project/archive search, or remote refs | No | Local `.pt/.onnx` candidates under ignored `results/` and Unity are ML-Agents navigation policies. Unrelated LLM checkpoints in other projects were rejected by path/content context. |
| `labels.csv` | No | No actual file in repo, all git objects, OneDrive project folders, Desktop/Documents/Downloads, attachments, or reviewed ZIPs | No | Only `dataset/processed/labels.example.csv`; its referenced image does not exist. |
| Approved image dataset or manifest | Partial | `dataset/manifests/approved_assets.csv` | No | Manifest template exists but contains only its header (0 approved assets); no image snapshot found. |
| Immutable split | No | `scripts/split_image_dataset.py` and intended layout found; no split artifact/actual split rows | No | Split tooling is not an original split. |
| Evaluation config | Yes | `config/model_config.yaml`, `config/labels.yaml`, `scripts/evaluate_multidomain.py`, preprocessing source | Partial | Sufficient to understand/run the intended evaluator only after checkpoint/data recovery; does not identify an original evaluated run. |
| Metrics file | No | Intended `outputs/evaluation_reports/multidomain_metrics.json` absent | No | Telemetry/PPO metric JSONs are different components; older ZIP contains the same unrelated metrics only. |
| Prediction outputs | Partial | `data/predictions_sample.jsonl` | No | Rows explicitly identify `sample-not-a-result` and `fixture-model1`; not checkpoint output. |
| Failure-case artifacts | Partial | `outputs/model1_audit/failure_index.csv` | No | Schema header only; no reviewed rows or images. |
| License/access notes | Yes | `dataset/sources.yaml`, `dataset/licenses/README.md`, NOAA terms snapshot | Partial | Source policy exists, but there is no per-asset license/provenance package because no assets are approved. |

## 3. Files Actually Found

Times are UTC and hashes are SHA-256.

| Path | Type / size | Modified | Model 1 relationship | Enough for evaluation? |
|---|---|---|---|---:|
| `config/model_config.yaml` | YAML, 393 B | 2026-08-22 20:00:24 | EfficientNet-B0/YOLO model family and 224 input configuration; hash `8AC8A3DD...6126B9C` | No |
| `config/labels.yaml` | YAML, 1,550 B | 2026-08-23 19:21:14 | Canonical domain/condition classes and aliases; hash `E8619EFA...6680A` | No |
| `scripts/evaluate_multidomain.py` | Python, 4,260 B | 2026-08-23 19:24:46 | Intended real held-out evaluation; hash `FE6F6AF9...56482` | No; requires missing inputs |
| `src/oceansense/perception.py` | Python, 8,570 B | 2026-08-24 09:14:39 | Expected `.pt` payload/inference adapter; hash `2C74BEE1...E8445E` | No |
| `src/oceansense/underwater_augmentation.py` | Python, 2,798 B | 2026-08-24 09:07:26 | Training-only seeded preprocessing; hash `1150204D...F316` | No |
| `dataset/sources.yaml` | YAML, 2,440 B | 2026-08-23 19:21:42 | Source-level license/access policy; hash `4AC2832B...160A3C` | No |
| `dataset/licenses/README.md` | Markdown, 1,067 B | 2026-08-23 19:21:42 | License-evidence procedure; hash `F3163C03...78AF48` | No |
| `dataset/licenses/noaa_ocean_exploration_2026-08-23.txt` | text, 361 B | 2026-08-23 19:31:29 | Source-level NOAA terms only; no downloaded asset; hash `C0E841E5...4003E` | No |
| `dataset/manifests/approved_assets.csv` | CSV, 242 B | 2026-08-23 19:35:50 | Canonical manifest schema; header only; hash `B642FC72...5DFC3` | No |
| `dataset/processed/labels.example.csv` | CSV, 431 B | 2026-08-23 19:20:52 | Schema example only; hash `0AFA1587...ACDF` | No |
| `data/predictions_sample.jsonl` | JSONL, 1,709 B | 2026-08-25 08:11:02 | Explicit fixture/sample, not real result; hash `9B5C6E3A...2F7DD` | No |
| `outputs/model1_audit/failure_index.csv` | CSV, 181 B | 2026-08-25 13:01:06 | Failure-index schema header only; hash `A899D3F1...EFFC3` | No |
| `C:/Users/Kerem/Downloads/rov-digital-twin-codex-rov-digital-twin.zip` | ZIP, 461,619 B | 2026-08-23 21:18:12 | Older project export, hash `99A47231...FBE`; contains config/scripts/schema example and navigation ONNX | No; 0 visual checkpoints and 0 actual `labels.csv` |

Other candidates were explicitly rejected:

- `results/oceansense_*` and Unity `.pt/.onnx`: navigation PPO artifacts, not visual EfficientNet checkpoints.
- `models/weakpoint_v2.json` and `artifacts/*weakpoint*metrics.json`: telemetry vehicle-health classifier.
- `C:/Users/Kerem/Downloads/archive.zip`: smartphone-usage CSV only.
- `C:/Users/Kerem/Downloads/archive (1).zip`: unrelated out-of-fold/submission CSVs.
- OneDrive `golden-ai` and Kale-Forge checkpoint files: unrelated language-model projects, based on enclosing
  project/config names and optimizer/scheduler/rng checkpoint roles.

## 4. Files Still Missing

1. **Domain and condition visual checkpoints**
   - Why needed: both are mandatory constructor inputs to `evaluate_multidomain.py`.
   - Can evaluation proceed without them? No.
   - Next action: original owner searches cloud storage, external drive, training machine, release/package or
     teammate account for the two `.pt` files and associated hashes.
2. **Actual `dataset/processed/labels.csv` and approved images**
   - Why needed: supplies ground truth, file paths, source/license, domain/condition labels and test rows.
   - Can evaluation proceed without them? No.
   - Next action: recover the exact original dataset snapshot together with its manifest; do not recreate or
     download it under this task.
3. **Immutable split tied to the checkpoint**
   - Why needed: prevents leakage and makes metrics reproducible.
   - Can evaluation proceed without it? A command could be forced after inventing a split, but it would not
     recover the original evaluation and would not support freeze.
   - Next action: recover the original split/mission IDs or run manifest from the model/data owner.
4. **Original evaluation metrics and predictions**
   - Why needed: verifies prior execution and supports comparison/failure analysis.
   - Can evaluation proceed without them? A fresh evaluation could run only after checkpoints/data recovery,
     but original results cannot be verified.
   - Next action: recover `multidomain_metrics.json`, logs, prediction export, command/environment record and
     checkpoint/data hashes.
5. **Reviewed failure examples/index**
   - Why needed: documents false positives/negatives and known limitations.
   - Can evaluation proceed without it? Metrics could run after core recovery, but freeze review remains
     incomplete.
   - Next action: recover original examples or rebuild the index only from recovered held-out predictions.
6. **Per-asset legal approval package**
   - Why needed: source-level notes do not prove each image is permitted and traceable.
   - Can evaluation proceed without it? Technically possible but not project-approved or freeze-safe.
   - Next action: recover approved manifest rows, license URLs/snapshots, attribution, reviewer and image hashes.

## 5. Evaluation Readiness After Recovery

- **Can Model 1 be evaluated now?** No.
- **Exact blockers:** both visual checkpoints, actual labels/images, immutable test split, optional visual
  dependencies in the current Python environment, and provenance/license approval.
- **Is freeze possible after this step?** No. No genuine metric or failure evidence was recovered.

The intended command remains:

```powershell
python scripts/evaluate_multidomain.py `
  --labels dataset/processed/labels.csv `
  --domain-checkpoint models/oceansense_domain_efficientnet_b0.pt `
  --condition-checkpoint models/oceansense_condition_efficientnet_b0.pt `
  --output outputs/evaluation_reports/multidomain_metrics.json
```

It must not be run as evidence until the inputs are recovered, hash-verified and approved.

## 6. Commands / Search Methods Used

- Current repository: targeted recursive filename/extension scan, `rg --files`, `rg -n`, `Test-Path`, file
  metadata and SHA-256 inspection across docs/data/dataset/artifacts/results/outputs/models/config/scripts.
- Git: `git branch -a`, `git tag -l`, `git rev-list --objects --all`, full-history path searches, current/remote
  status. Only `codex/rov-digital-twin` exists remotely; no release assets were listed.
- Ignored local outputs: inspected `results/`; confirmed all checkpoints are `OceanSenseROV` ML-Agents PPO
  navigation artifacts through run names, PPO configs and `docs/rl_policy_model_card.md`.
- Local folders: recursively searched relevant file patterns in `C:/Users/Kerem/OneDrive/Documents`, OneDrive
  Desktop, regular Documents/Desktop, Downloads, ChatGPT project siblings and Codex attachments.
- Project/handoff discovery: searched folder/file names for Conrad, OceanSense, ROV, digital twin, inspection,
  handoff, archive, backup and transfer. No separate Conrad handoff directory was found.
- Archives: listed members of all three candidate ZIPs without extraction or mutation; exact core-artifact counts
  recorded for the older repo ZIP.
- Prior exported reports: searched relevant PDF/DOCX text under repo artifacts/docs and Downloads for checkpoint,
  labels, manifest and evaluation-output paths; found no embedded original package or recoverable alternate path.
- Documented references: traced all intended Model 1 paths in README/docs/config/scripts; each points to missing
  canonical locations rather than an alternate storage location.

No training was performed, no external dataset was downloaded, no placeholder was generated, no Model 1
architecture was modified, and no Model 2 or Twin 2 work was performed.

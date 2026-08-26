# Model 1 SeaClear Acquisition Report

**Date:** 2026-08-26  
**Status:** `ACQUIRED_AND_HASH_VERIFIED — NOT YET APPROVED FOR TRAINING`

## Outcome

SeaClear version 1 was acquired directly from 4TU.ResearchData after the user chose an open-license path instead of sending InspectVQA, WPI/ARL, or Structural Defects permission requests. The canonical record and DataCite metadata identify the dataset as CC BY 4.0.

## Source and integrity

- DOI: `10.4121/4f1dff25-e157-4399-a5d4-478055461689.v1`
- Canonical file: `Seaclear Marine Debris Dataset.rar`
- Size: `1,711,829,309` bytes
- Publisher/local MD5: `1cfcf0c2fa3ef0dc219a66f063c2fe99` (match)
- Local SHA-256: `2a053f748d6bdc5df8d776e87b72832f2908316f0f419f6a8d562df6df086c13`
- Extracted: 8,610 JPEGs, 31,555 annotations, 40 categories
- Integrity: no missing referenced basenames; no orphan annotation image IDs

Raw data remains local and Git-ignored. Only metadata, hashes, license evidence, and governance decisions are committed.

## Model 1 use boundary

SeaClear is a real ROV dataset suitable for marine-debris/contamination and underwater domain robustness. It does not provide the complete six-domain/nine-condition Model 1 schema and must not be used as structural crack/corrosion/biofouling truth. It cannot by itself unlock baseline training.

## Next data gate

The first gate is now complete. `scripts/build_seaclear_source_manifest.py` produced `data/model1_baseline_v2/manifests/seaclear_source_assets.csv` with 8,610 unique IDs/paths/hashes and 11 preserved site/camera groups. The manifest SHA-256 is `28efe2b996c9676b7ff100289b62ba679e98192ea7344a7624501170eee43e07`.

Remaining gates:

1. Perform independent image-level review under `data/model1_baseline_v2/annotation_instructions.md`; source-derived proposals are not approvals.
2. Acquire lawful representative coverage for the condition/domain classes SeaClear cannot establish.
3. Run duplicate and leakage checks across site/camera groups after selected rows and other sources are complete.
4. Create an immutable split only after all locked class floors can be met.
5. Obtain named internal approval before activating training.

No training was performed and no Model 1 checkpoint was created.

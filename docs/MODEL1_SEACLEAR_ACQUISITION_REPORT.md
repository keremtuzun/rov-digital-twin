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

1. Build an asset-level source manifest that preserves site/camera groups and relative paths.
2. Define a reviewed mapping for debris/contamination only; reject unsupported classes.
3. Run duplicate and leakage checks across site/camera groups.
4. Create an immutable split only after the required class/domain coverage is complete.
5. Obtain named internal approval before activating training.

No training was performed and no Model 1 checkpoint was created.

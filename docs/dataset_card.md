# Dataset card

## Intended tasks

Domain classification uses `structure`, `nature_ecology`, `contamination`, `fishing_aquaculture`,
`general_underwater`, and `unknown`. Condition classification starts with `ok`, `possible_damage`,
`possible_weak_point`, `biofouling`, `marine_debris`, `poor_visibility`, `ecological_stress`,
`fish_or_habitat_activity`, and `unknown`, with specific labels enabled only when data supports them.

## Current state

Schema and validation tooling are implemented, but no third-party image snapshot is committed. This is
intentional: dataset licenses and mappings must be reviewed before collection. Consequently, the repo
does not yet make an image-classifier accuracy claim.

## Annotation policy

Each image has one inspection domain, one primary condition, secondary labels, condition/risk metadata,
a separate anomaly flag, a synthetic flag, and an optional cautious region-of-concern box. Annotators
must use labels that describe visible indicators rather than confirmed real-world outcomes. Ambiguous
frames are `unknown`; poor-quality frames are retained because visibility is operational information.

## Split policy

`scripts/split_image_dataset.py` creates a deterministic domain-and-label-stratified 70/15/15 split. Before a
formal evaluation, group related video frames by source clip to prevent leakage; the simple script is
appropriate only when records are independent images.

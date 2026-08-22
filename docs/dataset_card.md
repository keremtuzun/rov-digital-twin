# Dataset card

## Intended task

Seven-class underwater inspection triage: `normal_surface`, `biofouling`, `marine_debris`,
`low_visibility`, `possible_damage`, `possible_weak_point`, and `unknown`.

## Current state

Schema and validation tooling are implemented, but no third-party image snapshot is committed. This is
intentional: dataset licenses and mappings must be reviewed before collection. Consequently, the repo
does not yet make an image-classifier accuracy claim.

## Annotation policy

Each image has one primary class, a separate anomaly flag, and an optional cautious region-of-concern
box. Annotators must use `possible_weak_point`, `inspection_concern`, or `possible_damage_region` rather
than labels that imply confirmed failure. Ambiguous frames are `unknown`; poor-quality frames are not
silently discarded because visibility is an operational class.

## Split policy

`scripts/split_image_dataset.py` creates a deterministic label-stratified 70/15/15 split. Before a
formal evaluation, group related video frames by source clip to prevent leakage; the simple script is
appropriate only when records are independent images.

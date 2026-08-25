# Model 1 dataset expansion log

## Current status

The current source catalog contains seven candidate source families. This is below the execution guide's
minimum of 15 and is not presented as complete. Existing entries preserve conservative access notes:
unknown or source-specific terms require manual review and are not permission to download or train.

Dataset expansion is also blocked from being fully failure-driven because Model 1 has no approved freeze
run or reviewed failure index. The current broad gaps are underwater infrastructure structures (pipes,
welds, joints, coatings, hulls, cables, bridge supports and concrete), sparse defect conditions and
difficult visual conditions such as low light, turbidity, backscatter, blur, occlusion and unusual angles.

## Next source-review workflow

1. Complete the Model 1 freeze inputs and tag its false positives/negatives.
2. Extend `dataset/sources.yaml` to at least 15 evidence-backed candidates.
3. Score usefulness specifically against reviewed Model 1 failure categories.
4. Rank the top five by usefulness and legal/access feasibility.
5. Record label conversion, frame extraction, de-duplication and annotation needs.
6. Download only assets that pass per-source/per-asset license review and checksum gates.

No new external source or license claim was invented during the execution-guide alignment.

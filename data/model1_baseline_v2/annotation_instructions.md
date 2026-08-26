# Model 1 baseline v2 annotation instructions

Status: **active instructions; no asset approvals recorded yet**.

Operational reviewer guidance and adjudication rules are in `docs/SEACLEAR_LABELING_GUIDE.md`, `docs/SEACLEAR_HUMAN_LABELING_WORKFLOW.md`, and `docs/SEACLEAR_ADJUDICATION_PROTOCOL.md`. The machine-readable row contract is `manifests/label_review_schema.json`.

## Review workflow

1. Reviewer A inspects the complete RGB frame without seeing a proposed canonical label and records domain, primary condition, visibility, exclusions, and notes.
2. Reviewer B independently repeats the review.
3. Any disagreement, `unknown`, poor visibility, ambiguous object, or unsupported source mapping goes to an adjudicator.
4. Only adjudicated rows with identifiable reviewers and no unresolved rights/provenance issue may be copied into canonical `labels.csv` and `manifest.csv`.
5. Site/camera/mission grouping must be retained. Adjacent frames and perceptual duplicates cannot cross train/validation/test boundaries.

## SeaClear boundaries

- Source annotations for manufactured waste may propose domain `contamination` and condition `marine_debris`; a reviewer must confirm that debris is visible in the full frame.
- `animal_*` annotations may propose domain `nature_ecology` and condition `fish_or_habitat_activity`; the reviewer must confirm visible animal/habitat activity rather than infer ecosystem health.
- `plant` or `branch_wood` alone cannot establish ecological stress, normal condition, or debris.
- ROV parts/cables and `unknown_instance` do not establish structural concern, aquaculture concern, or Model 1 normality.
- A frame may not be relabeled as `possible_structural_concern`, `biofouling`, `poor_visibility`, `ecological_stress_indicator`, or `aquaculture_infrastructure_concern` solely from SeaClear category metadata.
- Absence of an annotated object never automatically means `normal_or_no_visible_concern`.

## Required review fields

Each accepted row must record stable sample/asset IDs, source path/hash, source group, domain, primary and secondary conditions, visibility, real/synthetic state, Reviewer A, Reviewer B, adjudicator where applicable, decision timestamp, label provenance, approval state, and exclusion reason.

## Claim boundary

Labels describe visible indicators only. They are not diagnoses, structural-integrity findings, navigation policies, or proof of safe real-ocean operation. Synthetic Unity captures remain separate and cannot count toward real-image floors.

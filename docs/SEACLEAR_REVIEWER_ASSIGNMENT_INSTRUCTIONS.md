# SeaClear reviewer assignment instructions

## Purpose and boundary

This review converts non-binding SeaClear source-category suggestions into independent human judgments for the Model 1 **condition** taxonomy. Two reviewers are required so agreement and disagreement can be measured without one person's answer influencing the other. These packages are not an approval mechanism: Model 1 remains **BLOCKED** and **NOT FROZEN**, and no reviewed row becomes training data automatically.

The queues intentionally omit Model 1 domain-review fields. Domain labels remain outstanding and require a separate governed review before a canonical dataset can be approved.

## Assignment and blinding

The coordinator assigns `reviewer_1_queue.csv` and `reviewer_2_queue.csv` to two different identifiable people and records that mapping outside the blinded CSVs. Do not share the other queue, completed answers, summary statistics, or discuss individual images before both submissions are locked. Each reviewer must make an independent visual judgment. Source suggestions are hints only and may be wrong.

Before distribution, verify the package hashes in `data/model1_baseline_v2/review_packages/README.md`. Each reviewer works on a copy; the repository templates and `.sha256` files remain unchanged.

## Opening and completing the queue

Open the UTF-8 CSV in a spreadsheet or CSV editor without changing column names, image IDs, paths, hashes, order, or row count. Resolve `image_path_or_relative_key` beneath the authorized local SeaClear image root (`data/model1_baseline_v2/raw/seaclear/v1/extracted/`). Raw images must not be copied into Git or redistributed.

For every row, inspect the full frame at useful zoom and fill only:

- `reviewer_label`: one condition value from `docs/SEACLEAR_LABELING_GUIDE.md` when the decision requires a label.
- `reviewer_confidence`: `high`, `medium`, or `low`.
- `reviewer_notes`: short, observable evidence; do not make unsupported diagnoses.
- `reviewer_decision`: exactly one allowed decision below.
- `review_timestamp`: UTC RFC3339, for example `2026-08-26T17:30:00Z`.

Never alter a suggestion to make agreement easier. Never add columns for approval, adjudication, split assignment, or the other reviewer.

## Decision meanings

| Decision | Use it when | Required entry |
| --- | --- | --- |
| `approve_suggestion` | The visible frame supports `suggested_model1_label`. | Copy that value to `reviewer_label`; set confidence and timestamp. |
| `change_label` | A different allowed condition is better supported visually. | Enter the replacement label; explain the visible evidence in notes. |
| `reject_image` | The file is corrupt/unreadable, materially duplicated, unusably blurred/occluded, has a rights/provenance concern, or provides no reviewable evidence. | Leave `reviewer_label` blank; explain the concrete reason. |
| `mark_unknown` | The image is usable, but the condition cannot be assigned reliably from visible evidence. | Set `reviewer_label` to `unknown`; explain the ambiguity. |
| `needs_adjudication` | The reviewer sees a taxonomy/boundary problem that needs expert resolution even before comparison with the second review. | Enter the best-supported label or `unknown`, use low confidence, and explain the exact issue. |

Use only these condition labels: `normal_or_no_visible_concern`, `possible_structural_concern`, `biofouling`, `marine_debris`, `poor_visibility`, `ecological_stress_indicator`, `fish_or_habitat_activity`, `aquaculture_infrastructure_concern`, or `unknown`.

## Difficult images

- Blur, occlusion, darkness, turbidity, or backscatter do not automatically mean `poor_visibility`; apply that label only when water-column visibility is the visible condition of interest.
- Use `reject_image` when degradation prevents a defensible review of the frame at all. State whether blur, occlusion, corruption, or another concrete problem caused rejection.
- Use `mark_unknown` when the image itself is reviewable but evidence is ambiguous, out of taxonomy, or insufficient for a reliable condition. State what is unclear.
- Do not infer `normal_or_no_visible_concern` from the absence of a source annotation.
- Do not infer structural damage, corrosion, ecological stress, or aquaculture damage from object presence alone.
- Use notes for visible location and evidence, such as “plastic bottle lower-left; partly occluded.” Avoid speculation about cause, severity, or safety.

## Locking and return

Complete all rows, save as UTF-8 CSV, close and reopen it to check that columns and values remain intact, then mark the submission locked with the coordinator. Return it through the approved team channel using `reviewer_1_submission_<UTC timestamp>.csv` or `reviewer_2_submission_<UTC timestamp>.csv`. The coordinator records reviewer identity, receipt time, and SHA-256 outside the blinded file. Do not overwrite or commit the immutable queue templates with completed answers.

After both locked submissions arrive, software validation will check row identity, hashes, allowed values, completeness, and independence. The two results will then be compared by `review_id`. Agreements and disagreements are reported; disagreements and explicit escalation requests go to a separate adjudicator. No merge, agreement, or adjudication automatically approves labels. A later approval audit, domain review, immutable split, and all Model 1 baseline gates must pass before training can begin.

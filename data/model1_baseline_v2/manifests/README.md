# Model 1 source manifests

`seaclear_source_assets.csv` is a deterministic staging inventory, not the canonical approved `manifest.csv` consumed by the training gate.

- Rows: 8,610
- Unique asset IDs: 8,610
- Unique relative paths: 8,610
- Per-image SHA-256 values: 8,610
- Site groups: 5
- Site/camera groups: 11
- Approval state: every row `pending_review`
- CSV SHA-256: `28efe2b996c9676b7ff100289b62ba679e98192ea7344a7624501170eee43e07`
- Summary SHA-256: `2bed2f3c7a2fb27fe376de0817f9755821859a6f9b30eb712c9ab7d15b6fc01a`

The builder joins the COCO basename to exactly one discovered site/camera path, rejects duplicate basenames, rejects missing images and unknown category IDs, hashes every image, and marks every proposed mapping for image review. Never copy these rows into the canonical manifest merely to satisfy preflight.

## Human review queue

`label_review_queue.csv` carries all 8,610 assets into the double-review workflow and preserves 31,555 sorted source annotation IDs. Initial evidence:

- Queue SHA-256: `45ca6880fa4f5113d15d4a740167aa981a34f4d4bed3e471741bf41df1aa6a71`
- Schema SHA-256: `dbf269ab80d0e26d28fcc7bc14001634b88aecb9122614da7eadefad8a5644e7`
- `pending_review`: 8,610
- Approved labels/use flags: 0

The queue is not canonical `labels.csv`. Do not regenerate it after human review starts. Run `python scripts/build_seaclear_review_queue.py --validate-only` for a non-mutating integrity check.

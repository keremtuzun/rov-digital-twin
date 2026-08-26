# Model 1 Baseline v2 dataset workspace

Status: **source manifest complete; annotation/training gate closed**.

SeaClear v1 is the first locally acquired, hash-verified, openly licensed real underwater source. Its raw archive and extracted images are stored under ignored `raw/seaclear/v1/`. See `licenses/seaclear/README.md` and `SOURCES.md` for evidence.

`manifests/seaclear_source_assets.csv` inventories and hashes all 8,610 source images while preserving site/camera groups. Its class values are review proposals derived from source COCO annotations; every row remains `pending_review`. Rebuild it with:

```powershell
python scripts/build_seaclear_source_manifest.py
```

The human-review package is now staged at `manifests/label_review_queue.csv` with its contract in `manifests/label_review_schema.json`. All 8,610 rows remain `pending_review`; no reviewer fields or approval flags were fabricated. Validate it without mutation using:

```powershell
python scripts/build_seaclear_review_queue.py --validate-only
```

The complete approved canonical `manifest.csv`, `labels.csv`, immutable `split.csv`, completed dual-review/adjudication record, approval audit, full-class dataset validation, and activation approval do not yet exist. Do not train or evaluate `model1_baseline_v2` from this staging workspace.

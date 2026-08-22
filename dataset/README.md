# OceanSense dataset workspace

Do not commit third-party raw imagery to this repository unless redistribution is explicitly allowed.
Keep original source/license metadata for every sample and use `processed/labels.csv` as the canonical
index. The expected layout is:

```text
dataset/
  raw/{suim,trashcan,brackish,urpc,coral,structures,rov_frames,synthetic}/
  processed/images/
  processed/labels.csv
  annotations/bboxes.json
  splits/{train,val,test}.txt
  metadata/sources.csv
  metadata/class_distribution.csv
```

Validate before training:

```powershell
$env:PYTHONPATH = "src"
python scripts/validate_image_dataset.py dataset/processed/labels.csv --boxes dataset/annotations/bboxes.json
python scripts/prepare_imagefolders.py --labels dataset/processed/labels.csv
python scripts/train_domain_classifier.py --data dataset/imagefolders/domain
python scripts/train_condition_classifier.py --data dataset/imagefolders/condition
```

Every row records `inspection_domain`, condition/status/risk fields, secondary labels, and whether the
sample is synthetic. Real and synthetic samples must stay distinguishable in reports and splits.

The repository contains schema examples only. No third-party images are bundled and no dataset-derived
performance claim is made until a traceable, license-reviewed snapshot is added.

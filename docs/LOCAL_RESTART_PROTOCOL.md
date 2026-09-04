# Local training restart, 2026-09-04

The user authorized rebuilding datasets and training both models, restricted to local
compute with no spending. Old S1/S2 artifacts and Model 1 approval gates stay intact.
Second Brain is unavailable (`command not found`); this repository is the session record.

## Experiments

- `configs/restart_local_v1.json`: fresh synthetic data, 640/160/160/200/200 groups
  for training/validation/calibration/test/shifted test; four images per visual scene,
  one 12-step 10-node structural trajectory per scenario. Six configurations times
  two seeds per model, with validation early stopping. No pretrained weights.
- `configs/seaclear_native_v1.json`: publicly annotated real underwater images,
  native COCO category-presence labels. Bistrina and Marseille train; Jakljan selects;
  Slano calibrates the decision threshold; Lokrum is the untouched test site.
  Six newly trained feature-head configurations times two seeds, using an official
  fixed ImageNet ResNet18 encoder. This is transfer learning, not a from-scratch encoder.

Candidate protocols were written before each experiment. All candidate checkpoints
are locked before calibration and test prediction. Validation drives selection;
calibration drives uncertainty/decision thresholds; test results do not drive either.
Two rounds without minimum validation improvement are only a **bounded-search plateau**.
Continued improvement at the last round is **budget exhausted**, not data exhaustion.

## Data acquisition and limits

The initial scripted publisher page request returned 403; the public page opened normally
in the in-app browser and exposed the actual archive link. Its download succeeded:

- [SeaClear publisher record](https://data.4tu.nl/datasets/4f1dff25-e157-4399-a5d4-478055461689/1)
- [Official archive](https://data.4tu.nl/file/4f1dff25-e157-4399-a5d4-478055461689/e1240a2e-915e-4858-93ab-c004b26b5a5f)
- CC BY 4.0; Antun Duras, Athina Ilioudi, Ben Wolf, Ivana Palunko, Bart De Schutter (2024).
- 1,711,829,309 bytes; verified publisher MD5 `1cfcf0c2fa3ef0dc219a66f063c2fe99`;
  SHA256 `2a053f748d6bdc5df8d776e87b72832f2908316f0f419f6a8d562df6df086c13`.
- Each image is checked against the pre-existing source hash manifest. Exact duplicate
  hashes are removed globally. Site-disjoint splits prevent within-video frame leakage;
  this does not prove absence of semantically similar objects across sites.

Native source annotations are used as native research labels, not approved canonical
domain/condition labels. No reviewer identity is invented. Debris images are not labelled
as structural damage. Categories with insufficient training positives remain unsupported.
Image-level presence recognition does not provide bounding boxes or segmentation.

The synthetic renderer is deliberately simple, not photorealistic. Defect operations
are labels, not measured corrosion/crack truth. Structural dynamics remain uncalibrated.
Model 2 receives simulated observations, **not** outputs from the newly trained visual
model. Fatigue/material-loss semantics cannot be bridged from generic image labels by fiat.
High synthetic scores alone are not evidence that we have reached the physical-data limit.

## Uncertainty

Synthetic calibration uses a separate group-disjoint set with a finite-sample 90%
split-conformal quantile. Scores are the maximum label nonconformity per visual scene,
or maximum state error over an entire trajectory. Group-level uncertainty respects
within-scene/time dependence; intervals may be wide. Shifted inputs have no coverage guarantee.
The native real-image track tunes a global classification threshold, not calibrated
probabilities or guaranteed safety risk. See [Angelopoulos and Bates](https://arxiv.org/abs/2107.07511)
for the exchangeability assumptions behind split conformal prediction.

## Commands and reproducibility

Run from the repository with Python 3.12, the existing model2 dependencies and Pillow.
The real-image track additionally uses torchvision 0.29.0 with torch 2.14.0. The fixed
encoder is [official ResNet18 IMAGENET1K_V1](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html).

```sh
PYTHONPATH=src .venv/bin/python scripts/run_local_restart.py
PYTHONPATH=src .venv/bin/python scripts/audit_local_restart.py
PYTHONPATH=src .venv/bin/python scripts/run_seaclear_native.py --extracted data/model1_baseline_v2/raw/seaclear/v1/extracted
PYTHONPATH=src .venv/bin/python scripts/audit_seaclear_native.py
```

Experiment directories refuse overwrite and repeated held-out inference. Raw data,
checkpoints and full experimental records stay in ignored local directories; source code,
protocols and the final findings document are suitable for version control. Regenerating
requires a fresh experiment ID or a separate checkout, not changing recorded artifacts.
Neither experiment authorizes physical deployment, certifies strength or proves a global optimum.

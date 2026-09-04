# Local restart results - 2026-09-04

## Outcome

Research training is complete for the bounded local-compute plan. This replaces the
former **missing training resources** status for the new research tracks. It does not
replace the unavailable original Model 1 checkpoint or authorize deployment.

| Track | Search | Selected by validation | Fresh held-out result | Search status |
|---|---|---:|---:|---|
| Synthetic Model 1, eight renderer operations | 6 candidates x 2 seeds | macro-F1 0.9755 | accuracy 0.9813; shifted 0.8150 | bounded search plateau |
| Real SeaClear native multilabel, fixed encoder | 6 heads x 2 seeds | macro AP 0.2749 | site-held-out macro AP 0.2340 | budget exhausted |
| Real SeaClear last-block adaptation | 4 configs x 2 seeds | macro AP 0.2926 | site-held-out macro AP 0.2235 | bounded fine-tuning plateau |
| Synthetic Model 2 initial restart | 6 candidates x 2 seeds | MAE 0.0598 | MAE 0.0592; shifted 0.1357 | budget exhausted |
| Synthetic Model 2 extended graph search | 6 candidates x 2 seeds | MAE 0.0457 | MAE 0.0473; shifted 0.0793 | bounded architecture plateau |

All means used for selection average two training seeds. The fine-tuned visual model
improved validation but did not improve the untouched site test. It remains the selected
fine-tuning experiment because reversing the choice after seeing test metrics would leak
held-out evidence. Both real-image tracks support 26 native categories; 14 categories
with fewer than 20 training positives remain explicitly unsupported.

## Uncertainty and shift

The synthetic Model 1 ensemble reached 89.5% scene-level coverage on its 90% calibration
target, but only 37.0% on shifted renders. The synthetic images are visibly simplistic,
so nominal performance is not evidence of real defect recognition.

The extended Model 2 ensemble reached 90.5% simultaneous-trajectory coverage on
calibration and 91.6% on the fresh nominal test. Under the preregistered structural and
observation shift, coverage fell to 72.8%, even with wide clipped intervals averaging
0.816 on a [0,1] target range. This model must abstain from safety or strength claims.

## What improved

- Acquired and checksum-verified the canonical 1.7 GB CC BY 4.0 SeaClear archive.
- Used all 8,610 real underwater images with native annotations, globally removing exact
  duplicates and splitting by site before training.
- Evaluated 20 real-image configurations/seeds across fixed-feature and fine-tuning phases.
- Evaluated 36 fresh synthetic configurations/seeds across Model 1 and Model 2.
- Reduced fresh Model 2 nominal test MAE to 0.0473 and shifted MAE to 0.0793.
- Added separate calibration partitions, finite-sample conformal trajectory intervals,
  immutable checkpoint locks, saved-prediction audits and single-use held-out evaluation.

## What is now waiting on physical data

The next validation gate requires images and telemetry drawn from the actual target
vehicle, camera, structures, water conditions, missions and operating envelope. Those
observations are needed to define the real input distribution, measure cross-site shift,
connect visual outputs to Model 2 state semantics, and calibrate uncertainty. No amount
of success on the existing renderer establishes those facts.

Physical data is the next **evidence** gate, not proven to be the only possible source of
algorithmic improvement. More software experiments remain conceivable: larger encoders,
native detection/segmentation training, self-supervised underwater pretraining, richer
simulators and ensembles. On an 8 GB local machine with no spending, however, the
preregistered architecture/fine-tuning searches have reached their bounded stopping rules,
and further tuning on the same validation sets risks overfitting rather than qualification.

## Verification

- Synthetic restart audit: 24/24 runs, no held-out inference rerun.
- Native-label fixed-feature audit: 12/12 runs and 8,610/8,610 source images verified.
- Native-label adaptation audit: 8/8 runs, no held-out inference rerun.
- Extended Model 2 audit: 12/12 runs, no held-out inference rerun.
- Every audit reports `deployment_authorized: false`.

Full local artifacts and raw data are ignored by Git. The committed protocols, training
code and this result record are sufficient to understand and reproduce the experiment;
reproduction needs the publisher archive and significant local compute.

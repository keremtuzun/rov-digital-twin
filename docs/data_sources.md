# OceanSense data sources

Access review date: 2026-08-22. Image count used in this repository: **0**. The entries below are
candidates, not a claim that their images are redistributed or used in a trained artifact.

| Dataset | Primary source | License status | Intended use | Limitations / gate |
|---|---|---|---|---|
| SUIM | https://irvlab.cs.umn.edu/image-segmentation/suim | Repository code is MIT; image-license scope is not explicit on the dataset page | Underwater scene/background understanding | Do not ingest into a release until the image license is confirmed |
| TrashCan 1.0 | https://conservancy.umn.edu/items/6dd6a960-c44a-4510-a679-efb8c82ebfb7 | Academic teaching/research terms are reported; source footage rights may require JAMSTEC permission | Marine debris and anomaly examples | Not corrosion/structural-damage data; verify redistribution terms before download |
| Brackish | https://universe.roboflow.com/brad-dwyer/brackish-underwater | CC BY 4.0 on the hosted dataset page | Real underwater object/visibility examples | Marine-animal labels do not establish weak points or damage |
| URPC2020 | https://www.kaggle.com/datasets/lywang777/urpc2020 | License is not sufficiently clear from the public landing page | Robot-view object-detection research | Do not ingest into a release until license and provenance are confirmed |

For every later download, update `dataset/metadata/sources.csv` with the exact version, access date,
image count, license text/URL, transformation, label mapping, and exclusions. Never map animal/debris
labels to crack, corrosion, or confirmed structural failure.

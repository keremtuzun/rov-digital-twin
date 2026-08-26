# SeaClear Marine Debris Dataset license evidence

- Review/acquisition date: `2026-08-26` (Europe/Istanbul)
- Canonical dataset record: <https://data.4tu.nl/datasets/4f1dff25-e157-4399-a5d4-478055461689/1>
- Version DOI: `10.4121/4f1dff25-e157-4399-a5d4-478055461689.v1`
- Official project repository: <https://github.com/adjuras/seaclear-dataset>
- Publisher: 4TU.ResearchData
- Version: `1`
- Publication year: `2024`
- License: Creative Commons Attribution 4.0 International (`CC BY 4.0`)
- License URL: <https://creativecommons.org/licenses/by/4.0/>
- Data format: JPEG images with COCO JSON annotations
- Intended Model 1 role: real underwater contamination/marine-debris source; underwater domain/visibility robustness
- Structural-defect role: **not permitted by label semantics**
- Internal decision: `ACQUIRED_LICENSE_VERIFIED_ASSET_REVIEW_PENDING`

## Creators and attribution

Antun Đuraš; Athina Ilioudi; Ben Wolf; Ivana Palunko; Bart De Schutter.

Citation:

> Đuraš, A., Ilioudi, A., Wolf, B., Palunko, I., & De Schutter, B. (2024). Seaclear Marine Debris Detection & Segmentation Dataset (Version 1). 4TU.ResearchData. https://doi.org/10.4121/4f1dff25-e157-4399-a5d4-478055461689.v1

## Publisher file evidence

| File | Bytes | Publisher MD5 | Local MD5 | Local SHA-256 | Verified? |
|---|---:|---|---|---|---:|
| `Seaclear Marine Debris Dataset.rar` | 1,711,829,309 | `1cfcf0c2fa3ef0dc219a66f063c2fe99` | `1cfcf0c2fa3ef0dc219a66f063c2fe99` | `2a053f748d6bdc5df8d776e87b72832f2908316f0f419f6a8d562df6df086c13` | Yes |

The archive was downloaded from the canonical 4TU file endpoint and stored under ignored local path `data/model1_baseline_v2/raw/seaclear/v1/`.

## Extracted integrity evidence

| Check | Result |
|---|---:|
| JPEG files | 8,610 |
| COCO image records | 8,610 |
| COCO annotations | 31,555 |
| COCO categories | 40 |
| Missing referenced image basenames | 0 |
| Orphan annotation image IDs | 0 |
| Unique image IDs | 8,610 |
| Unique annotation IDs | 31,555 |

COCO `file_name` values are unique basenames while images are stored beneath site/camera folders. Future manifest tooling must preserve the discovered relative path and must not flatten files.

## Approval boundary

The license and archive integrity gates pass. The dataset is **not yet admitted to training or evaluation** because per-asset provenance, class mapping, duplicate/leakage review, immutable group-aware split, attribution rows, and named internal approval are still missing. Debris labels may support the contamination domain and a reviewed debris/concern mapping; they must not be relabeled as cracks, corrosion, biofouling, or infrastructure damage.

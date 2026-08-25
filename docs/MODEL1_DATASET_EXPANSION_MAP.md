# Model 1 Dataset Expansion Map

## Scope and decision rule

The Model 1 failure review is blocked, so this map addresses **identified coverage gaps**, not claimed observed
failures. No candidate below has been added to the approved manifest. “Review” means inspect the exact asset,
license, annotation fit, duplicates, and mission grouping before download. An unclear or per-asset license is
an acquisition blocker until resolved.

| Candidate | URL | License status | Modality / reported scale | Labels and domain | Model 1 role / coverage gap | Limitation | Action |
|---|---|---|---|---|---|---|---|
| NOAA Ocean Exploration data | https://oceanexplorer.noaa.gov/data/access/ | U.S. government material generally public domain; verify each asset | real expedition video/images; asset-dependent | mostly unlabeled open-ocean/seafloor | real backgrounds, visibility, lighting, unknown negatives | annotations must be created; asset review required | Review source assets |
| NOAA fixed-site benthic imagery | https://www.fisheries.noaa.gov/inport/item/63091 | verify record and asset terms | real benthic imagery; record-dependent | habitat/benthic context | seabed and organism negatives, site shift | not defect-labelled | Review metadata/assets |
| NOAA coral bleaching imagery | https://www.fisheries.noaa.gov/inport/item/67962 | verify record and asset terms | real coral imagery; record-dependent | coral condition | biological anomaly vs structural-defect negatives | not infrastructure inspection | Review metadata/assets |
| FathomNet | https://www.fathomnet.org/terms | per-asset CC0/CC BY/other; filter strictly | real underwater images; large portal | marine organisms and concepts | OOD wildlife/background negatives | mixed provenance and per-asset licensing | Query only approved-license assets |
| SeaClear dataset | https://data.4tu.nl/datasets/4f1dff25-e157-4399-a5d4-478055461689 | CC BY 4.0 | 8,610 real underwater debris images | boxes/segmentation for marine debris | contamination/debris detection and occlusion | geography/mission bias; not structural defects | Candidate for source review |
| TrashCan | https://irvlab.cs.umn.edu/resources/trashcan | academic/research terms; upstream JAMSTEC terms require resolution | 7,212 annotated underwater images | trash, ROV, bio classes | debris, vehicle-part confusion, negative coverage | redistribution/use terms unresolved | Hold; obtain permission clarity |
| SUIM | https://github.com/IRVLab/SUIM | dataset license not explicit enough for approval | 1,525 train/val + 110 test images | semantic underwater classes | domain segmentation, people/robot/fish negatives | small and research-oriented; unclear dataset license | Hold; request license clarification |
| DeepFish | https://github.com/alzayats/DeepFish | repository license exists; verify it covers imagery | about 39,766 frames | fish presence/count/habitat | fish and habitat negatives, video-domain shift | imagery rights and frame leakage need review | Manual rights/split review |
| CoralNet sources | https://coralnet.ucsd.edu/pages/help/api/ | source-specific permissions | real benthic images; source-dependent | point labels for benthic classes | biofouling/coral texture negatives | permissions and labels vary by source | Review source by source |
| SubPipe | https://zenodo.org/records/12666132 | license field unclear on record | RGB, side-scan sonar, inertial; full archive ~39 GB | RGB segmentation and sonar boxes for submarine pipeline | closest pipeline-inspection geometry and multimodal context | large; rights must be clarified before download | Hold; contact author/verify rights |
| Cooperamos UJI pipes | https://zenodo.org/records/15792142 | Zenodo license field unclear; derived from Roboflow | small underwater pipeline-component set | pipe, coupler, L-pipe, T-pipe segmentation | component localization and viewpoint | upstream license and dataset lineage unclear | Hold; verify upstream license |
| MIMIR-UW | https://zenodo.org/records/10406384 | license field unclear on record | synthetic RGB/depth/pose; large archives | pipeline segmentation, depth and pose | Twin 1 coverage design and synthetic pretraining research | synthetic-only; cannot be real test evidence | Hold for license; research only |
| MaVeCoDD | https://data.mendeley.com/datasets/ry392rp8cj/1 | CC BY 4.0 | real dry-dock hull images | corrosion regions of interest | corrosion representation/transfer study | dry-dock, not underwater in situ | Review as transfer-only candidate |
| Corrosion segmentation dataset | https://data.mendeley.com/datasets/kcyn4nhv2c/1 | CC BY 4.0 | 1,024 field images; 35 pixel-annotated | corrosion/coating condition | texture pretraining and annotation protocol | atmospheric rather than subsea; few dense labels | Review as transfer-only candidate |
| SMAW weld defects | https://data.mendeley.com/datasets/f7j76vz53p/1 | CC BY 4.0 | 448 processed high-resolution images | spatter, slag, undercut boxes/polygons | weld-defect morphology and label design | controlled dry imagery; domain gap | Review as transfer-only candidate |
| ConViD concrete defects | https://data.mendeley.com/datasets/fx3rthfjhy/2 | CC BY 4.0 | terrestrial concrete imagery | crack, honeycomb, spalling, void | crack/spall representation research | not underwater and not metal infrastructure | Review as transfer-only candidate |
| HU infrastructure cracks | https://zenodo.org/records/20829348 | CC BY 4.0 | 600+ high-resolution images | concrete cracks | small-crack morphology and severity review | terrestrial concrete domain | Review as transfer-only candidate |
| Institution-owned ROV captures | internal collection; no public URL | written institutional/participant approval required | real mission video and telemetry | team-defined canonical inspection labels | highest-value target-domain calibration and test set | collection cost; privacy/site/mission permissions | Draft capture and consent protocol |

## Recommended acquisition order

1. Establish the internal ROV capture/permission protocol and a mission-disjoint test design.
2. Review SeaClear and eligible NOAA/FathomNet assets for open-sea negatives, debris, visibility, and OOD cases.
3. Resolve rights for SubPipe/Cooperamos before any transfer or pipeline imagery is downloaded.
4. Use clearly licensed dry-dock/terrestrial defect sets only for transfer experiments; never mix them into the
   real underwater test claim.
5. Record every accepted asset in `approved_assets.csv`, then hash and validate the immutable snapshot.

The map must be reprioritized after the first real Model 1 failure index exists.

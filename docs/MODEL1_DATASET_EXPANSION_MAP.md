# Model 1 Dataset Expansion Map

The failure review is blocked, so “weakness addressed” means a documented coverage gap, not an observed Model 1
error. No source below has been acquired or added to `approved_assets.csv`. Verified on 2026-08-25; unclear
rights block download. Actions use the guide vocabulary exactly.

| Name | Source type | URL | License/access | Modality | Sample count | Labels | Domain | Defect types | Relevance | Weakness addressed | Limitations | Action |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|
| InspectVQA | Hugging Face dataset card | https://huggingface.co/datasets/anonymousSubmissionVqa2026/InspectVQA | CC BY-NC 4.0 **or owner-approved alternative**; commercial/project scope needs written confirmation | real RGB, masks, VQA | 8,582 rows; 3.9 GB | multi-label normal, weld seam, corrosion, fouling; optional masks/VQA | subsea pipe inspection | corrosion, fouling, weld seam | High; closest visual classes | corrosion ambiguity, marine growth, weld/component confusion, degraded vision | anonymous submission; imbalance; NC/owner-rights ambiguity; train-only split shown | Request access |
| SubPipe | Zenodo dataset record | https://zenodo.org/records/12666132 | public record with required copyright/citation text; explicit reusable license field not shown | real RGB, side-scan sonar, inertial/navigation | full ~80 GB unzipped; Mini ~12 GB; Mini2 ~16 GB | RGB segmentation, sonar pipeline boxes, pose context | submarine pipeline | pipeline presence/occlusion; not rich defect labels | High for geometry and sensor context | viewpoint/distance, occlusion, turbidity, sensor limitation | large; rights clarification required; limited structural defect labels | Request access |
| Structural Defects - Bonnín-Pascual/Ortiz | university resource page | https://xiscobonnin.github.io/resources/ | downloadable, citation supplied; explicit reuse license not displayed | real vessel/surface RGB plus B/W masks | count not stated; original/extended archives | pixel masks | vessel/structural surfaces | corrosion, cracks, coating breakdown | Medium-high transfer source | small cracks, corrosion ambiguity, coating damage | not necessarily underwater; no explicit license | Request access |
| WPI/ARL Corrosion | university dataset page | https://arl.wpi.edu/corrosion_dataset/ | download/citation instructions; explicit dataset license not displayed | RGB JPG, 512 x 512 | 600 | expert corrosion ratings | laboratory materials | corrosion severity | Medium transfer source | corrosion texture ambiguity, label severity | laboratory/non-underwater; artifacts; rights terms need confirmation | Request access |
| K-Pipelines | GitHub repository/dataset | https://github.com/leoxthomas/K-Pipelines | GPL-3.0 repository; confirm dataset/image and model-output obligations before project use | synthetic RGB PNG, 512 x 512 | 600 base, 1,080 augmented | corroded/non-corroded; provided splits | oil/gas pipeline | corrosion | Medium as synthetic sanity/augmentation only | corrosion balance and coarse classification | Stable Diffusion synthetic domain gap; must never enter real test metrics | Inspect later |
| CleanCam | Zenodo dataset record | https://zenodo.org/records/18952474 | record shows author copyright but blank license value; clarify before download | RGB JPEG: real video frames plus synthetic | 22,572 total: 18,972 real, 3,600 synthetic | 5-level viewport-fouling severity; metadata and capture-disjoint splits | aquaculture camera monitoring | viewport fouling vs turbidity/haze | High robustness source, not structural primary | turbidity, low light/contrast, fouling, sensor/camera limitation | rights unclear; fixed cameras; real/synthetic mix must stay separate | Request access |
| Dryad ship biofouling surveys | Dryad dataset | https://datadryad.org/dataset/doi%3A10.5061/dryad.hdr7sqvkb | CC0 under Dryad data policy | CSV survey data, no distributed imagery | 53 ships; 10.28 KB files | percent cover, abundance, richness, vessel/context variables | commercial ship hull surveys | biofouling context | Low for training; useful metadata/taxonomy reference | marine-growth metadata and reporting categories | tabular only; no frames/masks; non-random sampling | Use now (context only) |
| Claru Underwater Inspection | commercial provider page | https://claru.ai/datasets/underwater-inspection | commercial/request-sample; terms, cost, export and model rights require contract | real ROV/diver RGB video plus metadata | provider claims 30K+ clips/scans, 200+ hours, 15+ sites | boxes/masks/points, temporal, semantic and quality layers | subsea infrastructure | corrosion, biofouling, structural damage | Potentially high target-domain source | blur, occlusion, visibility, structural and site shift | marketing claims need sample audit; no public immutable benchmark/download | Request access |
| SeaClear | 4TU dataset record | https://data.4tu.nl/datasets/4f1dff25-e157-4399-a5d4-478055461689 | CC BY 4.0 | real underwater RGB | 8,610 images | debris boxes/segmentation | general underwater/seabed | marine debris | High for current debris class/OOD | debris confusion, occlusion, real background | not structural defects; mission/geography bias | Inspect later |
| NOAA Ocean Exploration | government data portal | https://oceanexplorer.noaa.gov/data/access/ | U.S. government material generally public domain; verify every asset | real expedition video/images | asset-dependent | mostly none | open ocean/seafloor | background/visibility | Medium for negatives/robustness | OOD, turbidity, low light, viewpoint | annotation cost; per-asset review | Inspect later |
| FathomNet | data portal/terms | https://www.fathomnet.org/terms | per-asset CC0/CC BY/other; strict filter required | real underwater RGB/video | portal-dependent | marine concepts/objects | general underwater | organisms/background | Medium for unknown negatives | marine growth/organism confusion, OOD | mixed provenance/terms; not defect-labelled | Inspect later |
| TrashCan | university resource page | https://irvlab.cs.umn.edu/resources/trashcan | academic/research conditions; upstream JAMSTEC rights unresolved | real/synthetic underwater RGB | 7,212 images | trash, ROV and biological classes | underwater debris | debris | Medium | debris/component/organism confusion | redistribution/use ambiguity | Request access |
| SUIM | GitHub dataset page | https://github.com/IRVLab/SUIM | dataset license not explicit enough for approval | real underwater RGB | 1,525 train/val, 110 test | semantic masks | general underwater | semantic scene classes | Medium robustness/background | OOD, occlusion, marine context | small; research-oriented; license unclear | Request access |
| DeepFish | GitHub dataset page | https://github.com/alzayats/DeepFish | verify repository license covers imagery | real underwater video frames | about 39,766 frames | fish presence/count/habitat | tropical marine habitat | fish/background | Medium negative/OOD source | organism confusion, temporal leakage | imagery rights and mission-disjoint regrouping need review | Request access |
| MaVeCoDD | Mendeley dataset record | https://data.mendeley.com/datasets/ry392rp8cj/1 | CC BY 4.0 | real dry-dock RGB | record-dependent | corrosion ROIs | ship hull dry dock | corrosion | Medium transfer-only | corrosion texture ambiguity | not underwater in situ | Inspect later |
| Corrosion segmentation | Mendeley dataset record | https://data.mendeley.com/datasets/kcyn4nhv2c/1 | CC BY 4.0 | terrestrial field RGB | 1,024 images; 35 pixel-annotated | corrosion/coating masks subset | atmospheric structures | corrosion/coating | Low-medium transfer-only | corrosion texture/annotation protocol | only 35 dense labels; non-subsea | Inspect later |
| SMAW weld defects | Mendeley dataset record | https://data.mendeley.com/datasets/f7j76vz53p/1 | CC BY 4.0 | controlled high-resolution RGB | 448 processed images | boxes/polygons for spatter, slag, undercut | dry welding | weld defects | Medium label-transfer study | weld/component confusion | controlled dry domain | Inspect later |
| MIMIR-UW | Zenodo synthetic dataset | https://zenodo.org/records/10406384 | explicit license not shown | synthetic RGB/depth/pose | large archives | pipeline segmentation/depth/pose | simulated pipeline | pipeline geometry | Low for current Model 1 evidence | viewpoint and synthetic scenario design | unclear rights, synthetic-only, large | Future Model 2/Twin 2 relevance only |
| Institution-owned ROV capture | internal collection | internal; no public URL | written site/owner/team approval required | real video/images/telemetry | not yet collected | canonical labels to be reviewed | target open-sea infrastructure | target conditions | Highest eventual test relevance | all real-domain gaps | cost, permissions, safety, label governance | Request access |

## Recommended Sources

- Use the Dryad table now only to design biofouling metadata/categories; it is not image training data.
- Inspect SeaClear, NOAA, FathomNet and clearly licensed transfer datasets without adding them to the manifest.
- Give target-domain priority to a permissioned internal capture set; define mission-disjoint test allocation before
  recording.

## Sources Requiring Access Request

InspectVQA, SubPipe, Structural Defects, WPI/ARL Corrosion, CleanCam, Claru, TrashCan, SUIM, DeepFish and the
internal ROV collection require license, contract, upstream-rights or permission resolution before download/use.

## Sources to Avoid

- Avoid any mirror, scrape, repost or asset whose rights cannot be traced to the source owner.
- Avoid mixing synthetic K-Pipelines/MIMIR-UW or dry transfer data into real underwater validation/test results.
- Avoid treating Claru marketing counts as an independently verified benchmark until a contract/sample audit.
- Avoid using InspectVQA for commercial/project training until CC BY-NC/owner approval is resolved in writing.

## Open Questions

1. Who owns the license-approval decision and can approve non-commercial or copyleft obligations?
2. Is the current project use commercial, educational competition use, or both?
3. Which canonical condition labels should map to corrosion, weld seam and fouling multi-label annotations?
4. What storage budget is available for SubPipe Mini variants?
5. Which named hardware and mission conditions define the eventual Model 1 benchmark?

After a real failure index exists, reprioritize this map from measured false positives/negatives rather than
coverage gaps.

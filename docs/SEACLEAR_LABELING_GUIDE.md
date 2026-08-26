# SeaClear Labeling Guide for Model 1

## 1. Reviewer context

Model 1 is a two-head EfficientNet-B0 visual baseline: one head describes the visible inspection domain and one describes a visible condition indicator. Labels are cautious observations, not confirmed structural/ecological diagnoses. SeaClear supplies real underwater RGB frames and object annotations; it does not supply approved Model 1 labels.

The review matters because source-category shortcuts can create false claims. A bottle annotation can support a marine-debris candidate, but a pipe object does not prove structural damage, an empty frame does not prove normality, and image blur does not establish water-column poor visibility without visual evidence.

## 2. Domain labels

| Domain | Use when the visible inspection context supports | Do not infer |
|---|---|---|
| `structure` | A man-made structure is the meaningful inspection subject | Damage merely because a structure exists |
| `nature_ecology` | Habitat, flora, or fauna is the meaningful scene subject | Ecosystem health from presence alone |
| `contamination` | Waste, debris, pollutant-like material, or contamination is the meaningful subject | Chemical composition or toxicity |
| `fishing_aquaculture` | Fishing/aquaculture equipment or facility context is clear | Facility damage from generic rope/net alone |
| `general_underwater` | Valid underwater scene without a more specific supported domain | “Normal” condition automatically |
| `unknown` | Domain cannot be determined reliably | A convenient replacement for careful review |

## 3. Condition labels

| Condition | Visual rule |
|---|---|
| `normal_or_no_visible_concern` | Full-frame review finds no visible concern in the relevant inspection context; absence of source annotation is insufficient |
| `possible_structural_concern` | A visible structural indicator exists; do not diagnose crack/corrosion or use object presence alone |
| `biofouling` | Visible biological growth on an inspected asset; natural habitat growth alone is not asset biofouling |
| `marine_debris` | A visible discarded/manufactured object or waste item is supported in the frame |
| `poor_visibility` | Water-column visibility materially prevents interpretation; distinguish from local blur, occlusion, compression, or bad exposure |
| `ecological_stress_indicator` | A visible stress-like indicator is present under project rules; do not infer health from species presence/absence |
| `fish_or_habitat_activity` | Fish/animal activity or habitat interaction is visibly supported |
| `aquaculture_infrastructure_concern` | A visible concern on clearly identified aquaculture infrastructure exists |
| `unknown` | The condition is genuinely indeterminate/out of schema after careful review; notes are mandatory |

## 4. SeaClear source-category mapping

Every mapping below is a review aid, never a final label. Mixed-category images require full-frame review; debris takes no automatic precedence over inspection relevance.

| SeaClear Source Category | Candidate Model 1 Label | Mapping Status | Human Review Required? | Notes |
|---|---|---|---:|---|
| `can_metal` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded can is visible |
| `tarp_plastic` | `marine_debris` | `direct_candidate` | Yes | Distinguish waste from active equipment |
| `container_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded context |
| `bottle_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm visibility and not annotation-only artifact |
| `tube_cement` | `marine_debris` | `weak_candidate` | Yes | Could be installed infrastructure |
| `plant` | none | `context_only` | Yes | Natural context; not stress or normality |
| `container_middle_size_metal` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded context |
| `animal_etc` | `fish_or_habitat_activity` | `weak_candidate` | Yes | Confirm visible animal/activity |
| `animal_sponge` | `fish_or_habitat_activity` | `weak_candidate` | Yes | Habitat evidence only; not stress/biofouling automatically |
| `bottle_glass` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded bottle |
| `wreckage_metal` | `marine_debris` | `weak_candidate` | Yes | Could be structure; never auto-map to damage |
| `unknown_instance` | `unknown` | `unknown_needs_review` | Yes | Inspect full image and explain uncertainty |
| `pipe_plastic` | `marine_debris` | `weak_candidate` | Yes | Installed pipe is not debris or structural concern by default |
| `net_plastic` | `marine_debris` | `weak_candidate` | Yes | Distinguish lost net from active fishing/aquaculture gear |
| `animal_shells` | `fish_or_habitat_activity` | `weak_candidate` | Yes | Habitat context; no health inference |
| `rope_fiber` | `marine_debris` | `weak_candidate` | Yes | Distinguish debris from active equipment |
| `animal_urchin` | `fish_or_habitat_activity` | `weak_candidate` | Yes | Visible fauna only |
| `cup_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded cup |
| `brick_clay` | `marine_debris` | `weak_candidate` | Yes | Could be structure/material in use |
| `bag_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm bag is visible |
| `sanitaries_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded item |
| `clothing_fiber` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded clothing |
| `cup_ceramic` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded cup |
| `boot_rubber` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded boot |
| `tire_rubber` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded/abandoned tire |
| `jar_glass` | `marine_debris` | `direct_candidate` | Yes | Confirm discarded jar |
| `rov_cable` | none | `context_only` | Yes | ROV equipment; not debris or infrastructure concern |
| `rov_tortuga` | none | `reject_for_model1` | Yes | Robot-only annotation; reject if no relevant scene evidence |
| `branch_wood` | none | `context_only` | Yes | Natural material; do not label debris automatically |
| `furniture_wood` | `marine_debris` | `direct_candidate` | Yes | Confirm manufactured/discarded furniture |
| `snack_wrapper_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm visible wrapper |
| `lid_plastic` | `marine_debris` | `direct_candidate` | Yes | Confirm visible discarded lid |
| `cardboard_paper` | `marine_debris` | `direct_candidate` | Yes | Confirm visible discarded material |
| `rope_plastic` | `marine_debris` | `weak_candidate` | Yes | Distinguish lost rope from active equipment |
| `cable_metal` | `marine_debris` | `weak_candidate` | Yes | Distinguish waste from installed infrastructure |
| `animal_fish` | `fish_or_habitat_activity` | `direct_candidate` | Yes | Confirm fish/activity in full frame |
| `snack_wrapper_paper` | `marine_debris` | `direct_candidate` | Yes | Confirm visible wrapper |
| `rov_vehicle_leg` | none | `reject_for_model1` | Yes | Robot self-occlusion; reject if it dominates/no relevant evidence |
| `rov_bluerov` | none | `reject_for_model1` | Yes | Robot annotation is not a scene condition |
| `animal_starfish` | `fish_or_habitat_activity` | `weak_candidate` | Yes | Visible fauna/habitat evidence only |

Allowed mapping statuses are exactly `direct_candidate`, `weak_candidate`, `context_only`, `reject_for_model1`, and `unknown_needs_review`.

## 5. Difficult images

- **Unclear or out of schema:** use `unknown`, explain what prevents a conclusion, and do not approve until the second review/adjudication resolves the case.
- **Occlusion:** label a condition only if enough evidence remains visible. Severe occlusion that prevents reliable domain/condition review is rejected as `severe_occlusion`.
- **Blur:** distinguish motion/focus blur from turbid water. Severe blur is `severe_blur`; do not automatically label `poor_visibility`.
- **Low water visibility:** use `poor_visibility` only when water-column conditions materially limit interpretation. Severe unusable frames may be rejected as `severe_visibility_loss`.
- **Multiple objects:** label the primary visible inspection concern under the project task; record other supported indicators in notes/future secondary labels. Do not use the first COCO category mechanically.
- **Marine debris vs structure:** a pipe, cable, net, rope, brick, or metal object may be active infrastructure. Require scene context before calling it debris; presence alone never means structural concern.
- **Fauna/habitat:** visible animals can support activity, not ecological health or stress. Natural growth is not automatically asset biofouling.
- **Unknown source category:** inspect the image rather than inheriting `unknown_instance`; use a supported canonical label only when visible evidence is clear.

## 6. Notes and rejection

Notes must be factual, short, and evidence-locating, for example: `plastic bottle visible lower-right; partially buried; domain contamination`. Avoid diagnoses and confidence theater. Notes are mandatory for unknown, rejection, ambiguity, disagreement, or any mapping that overrides the source suggestion.

Reject when the image is corrupt/unreadable, rights or provenance is unresolved, an exact/near duplicate is excluded, no relevant visual evidence exists, source semantics are unsupported, or blur/occlusion/visibility prevents reliable review. Use only a schema-listed rejection reason; `other_documented` requires a precise explanation.

"""Versioned cautious condition taxonomy with backward-compatible aliases."""

CANONICAL_CONDITION_LABELS = {
    "normal_or_no_visible_concern",
    "possible_structural_concern",
    "biofouling",
    "marine_debris",
    "poor_visibility",
    "ecological_stress_indicator",
    "fish_or_habitat_activity",
    "aquaculture_infrastructure_concern",
    "unknown",
}

LABEL_ALIASES = {
    "ok": "normal_or_no_visible_concern",
    "normal_surface": "normal_or_no_visible_concern",
    "structure_ok": "normal_or_no_visible_concern",
    "normal_water_condition": "normal_or_no_visible_concern",
    "clear_visibility": "normal_or_no_visible_concern",
    "possible_weak_point": "possible_structural_concern",
    "possible_structural_weak_point": "possible_structural_concern",
    "possible_damage": "possible_structural_concern",
    "possible_damage_region": "possible_structural_concern",
    "possible_crack": "possible_structural_concern",
    "crack": "possible_structural_concern",
    "possible_corrosion": "possible_structural_concern",
    "corrosion": "possible_structural_concern",
    "surface_degradation": "possible_structural_concern",
    "poor_visibility_for_survey": "poor_visibility",
    "low_visibility": "poor_visibility",
    "high_turbidity": "poor_visibility",
    "bleached_coral": "ecological_stress_indicator",
    "coral_bleaching": "ecological_stress_indicator",
    "bleaching_like_pattern": "ecological_stress_indicator",
    "possible_coral_stress": "ecological_stress_indicator",
    "ecological_stress": "ecological_stress_indicator",
    "fish_school": "fish_or_habitat_activity",
    "fish_school_present": "fish_or_habitat_activity",
    "fish_present": "fish_or_habitat_activity",
    "net_damage": "aquaculture_infrastructure_concern",
    "cage_damage": "aquaculture_infrastructure_concern",
}

DOMAIN_COMPATIBILITY = {
    "structure": {"normal_or_no_visible_concern", "possible_structural_concern", "biofouling", "marine_debris", "poor_visibility", "unknown"},
    "nature_ecology": {"normal_or_no_visible_concern", "ecological_stress_indicator", "fish_or_habitat_activity", "marine_debris", "poor_visibility", "unknown"},
    "contamination": {"normal_or_no_visible_concern", "marine_debris", "poor_visibility", "ecological_stress_indicator", "unknown"},
    "fishing_aquaculture": {"normal_or_no_visible_concern", "fish_or_habitat_activity", "aquaculture_infrastructure_concern", "marine_debris", "poor_visibility", "unknown"},
    "general_underwater": CANONICAL_CONDITION_LABELS,
    "unknown": {"unknown", "poor_visibility"},
}

DIAGNOSTIC_STRENGTH = {label: "visual_indicator_not_confirmed_diagnosis" for label in CANONICAL_CONDITION_LABELS}
DIAGNOSTIC_STRENGTH["normal_or_no_visible_concern"] = "no_visible_concern_not_proof_of_integrity"
DIAGNOSTIC_STRENGTH["unknown"] = "insufficient_evidence"


def canonicalize_label(label: str) -> str:
    return LABEL_ALIASES.get(label, label)


def is_domain_compatible(domain: str, label: str) -> bool:
    return canonicalize_label(label) in DOMAIN_COMPATIBILITY.get(domain, {"unknown"})

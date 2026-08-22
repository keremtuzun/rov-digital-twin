from __future__ import annotations

from .schemas import Classification, ConditionAssessment, InspectionDomain

OK_LABELS = {
    "ok", "normal_surface", "structure_ok", "healthy_coral", "healthy_seafloor",
    "normal_water_condition", "suitable_habitat_indicator",
}
STRUCTURE_HIGH = {
    "possible_weak_point", "possible_structural_weak_point", "possible_damage",
    "possible_corrosion", "possible_crack", "corrosion", "crack", "surface_degradation", "biofouling_on_structure", "heavy_biofouling_on_structure",
}
ECOLOGY_CONCERNS = {
    "ecological_stress", "possible_coral_stress", "bleaching_like_pattern", "bleached_coral", "coral_bleaching", "damaged_coral",
    "algae_overgrowth", "degraded_habitat", "low_biodiversity_visible",
}
CONTAMINATION_CONCERNS = {
    "marine_debris", "plastic_waste", "net_or_rope_debris", "oil_like_sheen",
    "suspicious_discoloration", "high_turbidity", "algae_bloom_indicator",
}
FISHING_CONCERNS = {"net_damage", "cage_damage", "debris_near_aquaculture", "poor_visibility_for_survey", "low_activity"}
FISHING_USEFUL = {"fish_or_habitat_activity", "fish_present", "fish_school_present", "fish_school", "vegetation_present", "suitable_habitat_indicator", "clear_visibility"}
UNKNOWN_LABELS = {"unknown", "unknown_structure_condition", "unknown_ecological_condition", "unknown_contamination_status", "unknown_field_condition"}


def assess_condition(domain: InspectionDomain, classification: Classification) -> ConditionAssessment:
    """Convert model confidence to a cautious domain-aware condition assessment."""
    label, confidence = classification.label, classification.confidence
    score = 1.0 - confidence if label in OK_LABELS else confidence
    if label in UNKNOWN_LABELS or confidence < 0.50:
        status, risk = "unsafe_to_conclude", "medium"
        summary = "Evidence is insufficient; human review or additional data is required."
    elif label in OK_LABELS:
        status = "ok"
        risk = "low" if score < 0.40 else "medium"
        summary = f"The scene appears {label.replace('_', ' ')}, without proving real-world safety."
    else:
        status = "needs_review"
        if domain.label == "structure" and label in STRUCTURE_HIGH and confidence >= 0.70 or domain.label == "contamination" and label in CONTAMINATION_CONCERNS and confidence >= 0.70:
            risk = "high"
        else:
            risk = "medium" if confidence < 0.70 else "high"
        summary = f"Visible {label.replace('_', ' ')} indicator requires cautious review."
    field_assessment = None
    if domain.label == "fishing_aquaculture":
        if label in FISHING_USEFUL and confidence >= 0.65:
            field_assessment = "promising_area"
        elif label in FISHING_CONCERNS:
            field_assessment = "operational_concern"
        else:
            field_assessment = "insufficient_evidence"
    return ConditionAssessment(status, risk, round(max(0.0, min(1.0, score)), 6), summary, field_assessment)

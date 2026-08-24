from __future__ import annotations

from itertools import count

from .rag import GroundedExplainer
from .schemas import DecisionResult, MissionContext, PerceptionResult


class DecisionAgent:
    """Rule-based safety authority; the explainer never selects or overrides actions."""

    def __init__(self, explainer: GroundedExplainer) -> None:
        self.explainer = explainer
        self._ids = count(1)

    def decide(self, perception: PerceptionResult, context: MissionContext) -> DecisionResult:
        confidence = perception.classification.confidence
        label = perception.classification.label
        domain = perception.inspection_domain.label
        flags: list[str] = []
        review = False

        if context.battery_level is not None and context.battery_level < 0.20:
            action, priority, reason = "return_to_base", "critical", "Battery is below the 20% safety threshold."
            flags.append("low_battery")
            review = True
        elif context.communication_status in {"unstable", "lost"}:
            action, priority, reason = "hold_position", "critical", "Communication is not stable."
            flags.append("communication_unstable")
            review = True
        elif context.visibility_level == "poor" or label in {"poor_visibility", "low_visibility", "poor_visibility_for_survey", "high_turbidity"}:
            action, priority, reason = "capture_more_data", "high", "Visibility is poor; collect better evidence."
            flags.append("poor_visibility")
            review = True
        elif perception.inspection_domain.confidence < 0.50 or domain == "unknown":
            action, priority, reason = "request_human_review", "high", "Inspection-domain confidence is insufficient."
            flags.append("low_domain_confidence")
            review = True
        elif confidence < 0.50 or label.startswith("unknown") or label == "unknown":
            action, priority, reason = "request_human_review", "high", "Model confidence is insufficient for an automated recommendation."
            flags.append("low_confidence")
            review = True
        elif context.survey_goal != "unknown" and context.survey_goal != domain:
            action, priority, reason = "request_human_review", "medium", "Detected domain does not match the configured survey goal."
            flags.append("survey_goal_mismatch")
            review = True
        else:
            action, priority, reason, review = self._domain_rule(domain, label, confidence)
            if review:
                flags.append("human_review_required")

        instruction = self._instruction(action)
        explanation = self.explainer.explain(perception, action)
        return DecisionResult(
            decision_id=f"DEC-{next(self._ids):05d}",
            frame_id=perception.frame_id,
            recommended_action=action,
            priority=priority,
            requires_human_review=review,
            reasoning_summary=reason,
            dashboard_message=self._dashboard(action, label),
            control_instruction=instruction,
            confidence="high" if confidence >= 0.75 else ("medium" if confidence >= 0.50 else "low"),
            safety_flags=flags,
            explanation=explanation,
            domain=domain,
            versions={
                "model_version": perception.model_version,
                "model_hash": perception.model_hash,
                "dataset_version": perception.dataset_version,
                "calibration_version": perception.calibration_version,
                "feature_transform_version": perception.feature_transform_version,
                "simulator_profile": perception.simulator_profile,
                "vehicle_profile": perception.vehicle_profile,
            },
        )

    @staticmethod
    def _domain_rule(domain: str, label: str, confidence: float) -> tuple[str, str, str, bool]:
        ok_labels = {"ok", "normal_surface", "structure_ok", "healthy_coral", "healthy_seafloor", "normal_water_condition"}
        if domain == "structure":
            if label in ok_labels and confidence > 0.75:
                return "continue_survey", "normal", "Structure appears normal at the validated confidence threshold.", False
            if label in {"possible_weak_point", "possible_structural_weak_point"} and confidence > 0.70:
                return "inspect_closer", "high", "Possible structural weak point requires closer inspection.", True
            if label in {"possible_damage", "possible_corrosion", "possible_crack", "corrosion", "crack", "surface_degradation", "biofouling_on_structure", "heavy_biofouling_on_structure"} and confidence > 0.65:
                return "mark_location", "high", "Possible structural maintenance concern should be marked for review.", True
        elif domain == "nature_ecology":
            if label in ok_labels and confidence >= 0.50:
                return "continue_survey", "normal", "No visible ecological concern exceeds the review threshold.", False
            if label in {"possible_coral_stress", "bleaching_like_pattern"}:
                return "capture_more_data", "high", "A bleaching-like or coral-stress pattern needs additional evidence.", True
            if label in {"ecological_stress", "bleached_coral", "coral_bleaching", "damaged_coral", "algae_overgrowth", "degraded_habitat", "low_biodiversity_visible"} and confidence > 0.65:
                return "mark_location", "high", "Visible ecological-stress indicator should be marked for expert review.", True
        elif domain == "contamination":
            if label == "oil_like_sheen":
                return "send_alert", "high", "An oil-like visual indicator requires an alert and human review; chemistry is unconfirmed.", True
            if label in {"suspicious_discoloration", "algae_bloom_indicator"}:
                return "capture_more_data", "high", "A visible contamination indicator needs additional evidence.", True
            if label in {"marine_debris", "plastic_waste", "net_or_rope_debris"} and confidence > 0.70:
                return "mark_location", "high", "Marine debris should be marked for review or cleanup planning.", True
            if label in ok_labels and confidence > 0.75:
                return "continue_survey", "normal", "No visible contamination indicator exceeds the review threshold.", False
        elif domain == "fishing_aquaculture":
            if label in {"net_damage", "cage_damage"}:
                return "inspect_closer", "high", "Possible aquaculture infrastructure damage requires closer inspection.", True
            if label in {"fish_or_habitat_activity", "fish_present", "fish_school_present", "fish_school", "vegetation_present"} and confidence > 0.65:
                return "mark_location", "normal", "Visible fish or habitat activity can be marked for survey follow-up.", False
            if label in {"suitable_habitat_indicator", "clear_visibility"} and confidence >= 0.50:
                return "continue_survey", "normal", "Habitat indicator supports continuing the planned survey.", False
        elif label in ok_labels and confidence > 0.75:
            return "continue_survey", "normal", "Normal visual condition exceeds the continuation threshold.", False
        return "request_human_review", "medium", "No validated domain rule covers this result confidently.", True

    @staticmethod
    def _instruction(action: str) -> dict:
        mapping = {
            "inspect_closer": {"action": "move_to_inspection_pose", "target": "detected_region", "suggested_distance_m": 0.7, "speed": "slow"},
            "continue_survey": {"action": "continue_current_survey_plan"},
            "capture_more_data": {"action": "capture_additional_frames", "speed": "slow"},
            "hold_position": {"action": "request_station_keeping"},
            "return_to_base": {"action": "request_return_to_base"},
            "request_human_review": {"action": "pause_high_level_progression"},
            "mark_location": {"action": "record_current_location", "target": "detected_region"},
            "send_alert": {"action": "notify_operator", "target": "current_frame"},
        }
        return mapping[action]

    @staticmethod
    def _dashboard(action: str, label: str) -> str:
        display_label = label.removeprefix("possible_").replace("_", " ")
        if action == "capture_more_data" and label in {"possible_coral_stress", "bleaching_like_pattern"}:
            return "Possible coral-stress indicator detected. Capture more data and request ecological review."
        if action == "capture_more_data" and label in {"suspicious_discoloration", "algae_bloom_indicator"}:
            return "Visible water-condition indicator detected. Capture more data; contamination is unconfirmed."
        messages = {
            "inspect_closer": f"Possible {display_label} detected. Recommend closer inspection.",
            "continue_survey": "No high-confidence anomaly detected. Continue survey.",
            "capture_more_data": "Poor visibility. Capture more data before proceeding.",
            "hold_position": "Communication unstable. Hold position and notify operator.",
            "return_to_base": "Low battery. Recommend return to base.",
            "request_human_review": "Result is uncertain. Human review required.",
            "mark_location": f"Visible {display_label} indicator detected. Mark location for review.",
            "send_alert": f"Possible {display_label} indicator detected. Send alert for human review.",
        }
        return messages[action]

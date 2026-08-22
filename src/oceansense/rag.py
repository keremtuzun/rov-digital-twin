from __future__ import annotations

import re
from pathlib import Path

from .schemas import PerceptionResult


class GroundedExplainer:
    """Small local retrieval layer; generation stays templated and evidence-bound."""

    def __init__(self, knowledge_dir: str | Path) -> None:
        self.documents: list[tuple[str, str]] = []
        for path in sorted(Path(knowledge_dir).glob("*.md")):
            self.documents.append((path.name, path.read_text(encoding="utf-8")))
        if not self.documents:
            raise ValueError("knowledge base is empty")

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) > 2}

    def retrieve(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        query_tokens = self._tokens(query)
        ranked = sorted(
            self.documents,
            key=lambda item: len(query_tokens & self._tokens(item[1])),
            reverse=True,
        )
        return [{"source": name, "excerpt": text[:400].strip()} for name, text in ranked[:limit]]

    def explain(self, result: PerceptionResult, action: str) -> dict:
        label = result.classification.label
        domain = result.inspection_domain.label
        risk = result.condition_assessment.risk_level if result.condition_assessment else result.anomaly.level
        sources = self.retrieve(f"{domain} {label} {risk} {action} safety uncertainty")
        concern = label not in {"ok", "normal_surface", "structure_ok", "healthy_coral", "healthy_seafloor", "normal_water_condition", "unknown"}
        summary = (
            f"The image models identified the {domain} domain and {label} condition with "
            f"{result.classification.confidence:.0%} condition confidence; the rule-based risk level is {risk}."
        )
        limitations = ["Visibility, lighting, dataset coverage, and domain shift may affect confidence."]
        if domain == "structure":
            interpretation = "This is an inspection concern, not confirmation of structural or material failure." if concern else "The image does not prove structural integrity or safety."
            limitations.append("Image-only evidence cannot determine whether a structure needs repair or rebuilding.")
        elif domain == "contamination":
            interpretation = "This is a visible pollution indicator; imagery alone cannot confirm chemical contamination."
            limitations.append("Chemical contamination requires physical sampling and qualified analysis.")
        elif domain == "nature_ecology":
            interpretation = "This is a visible ecological indicator, not confirmation of coral death or ecosystem failure."
            limitations.append("Ecological condition requires repeated observations and expert review.")
        elif domain == "fishing_aquaculture":
            interpretation = "This frame may show activity or infrastructure concern; it does not estimate a fish population."
            limitations.append("A single frame cannot establish population size or habitat suitability.")
        else:
            interpretation = "No domain-specific real-world conclusion can be established from this image alone."
        return {
            "summary": summary,
            "interpretation": interpretation,
            "recommended_action": action,
            "limitations": limitations,
            "grounding_sources": [item["source"] for item in sources],
        }

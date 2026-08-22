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
        sources = self.retrieve(f"{label} {result.anomaly.level} {action} safety uncertainty")
        concern = label not in {"normal_surface", "unknown"}
        summary = (
            f"The image model identified {label} with {result.classification.confidence:.0%} confidence; "
            f"the rule-based anomaly level is {result.anomaly.level}."
        )
        interpretation = (
            "This is an inspection concern, not confirmation of structural or material failure."
            if concern
            else "No specific damage is established by this image result."
        )
        return {
            "summary": summary,
            "interpretation": interpretation,
            "recommended_action": action,
            "limitations": [
                "Image-only evidence cannot confirm material integrity.",
                "Visibility, lighting, dataset coverage, and domain shift may affect confidence.",
            ],
            "grounding_sources": [item["source"] for item in sources],
        }

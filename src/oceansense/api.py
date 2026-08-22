from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

from .decision import DecisionAgent
from .perception import FixtureClassifier, PerceptionService, TorchvisionEfficientNetClassifier, UltralyticsDetector
from .rag import GroundedExplainer
from .schemas import (
    Anomaly, BoundingBox, Classification, Detection, MissionContext, PerceptionResult,
)


class ContextBody(BaseModel):
    visibility_level: str = "unknown"
    depth_m: float | None = None
    battery_level: float | None = Field(default=None, ge=0, le=1)
    communication_status: str = "stable"


class PerceptionBody(BaseModel):
    frame_id: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    mission_context: ContextBody = Field(default_factory=ContextBody)


class ClassificationBody(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)


class AnomalyBody(BaseModel):
    score: float = Field(ge=0, le=1)
    level: str
    reason: str = ""


class BboxBody(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class DetectionBody(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    bbox: BboxBody


class DecisionBody(BaseModel):
    frame_id: str
    classification: ClassificationBody
    anomaly: AnomalyBody
    detections: list[DetectionBody] = Field(default_factory=list)
    model_version: str = "perception_v1"
    mission_context: ContextBody = Field(default_factory=ContextBody)


def build_services() -> tuple[PerceptionService, DecisionAgent]:
    classifier_path = os.getenv("OCEANSENSE_CLASSIFIER_CHECKPOINT")
    detector_path = os.getenv("OCEANSENSE_DETECTOR_CHECKPOINT")
    classifier = TorchvisionEfficientNetClassifier(classifier_path) if classifier_path else FixtureClassifier()
    detector = UltralyticsDetector(detector_path) if detector_path else None
    knowledge = Path(__file__).parent / "knowledge_base"
    return PerceptionService(classifier, detector), DecisionAgent(GroundedExplainer(knowledge))


def create_app(perception_service: PerceptionService | None = None, decision_agent: DecisionAgent | None = None):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("Install the 'api' optional dependencies") from exc

    if perception_service is None or decision_agent is None:
        perception_service, decision_agent = build_services()

    app = FastAPI(title="OceanSense Intelligence API", version="1.0.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/perception/analyze")
    def analyze(body: PerceptionBody) -> dict:
        try:
            context = MissionContext(**body.mission_context.model_dump())
            return perception_service.analyze(body.frame_id, body.image_path, context).to_dict()
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/agent/decide")
    def decide(body: DecisionBody) -> dict:
        try:
            result = PerceptionResult(
                frame_id=body.frame_id,
                classification=Classification(**body.classification.model_dump()),
                anomaly=Anomaly(**body.anomaly.model_dump()),
                detections=[Detection(item.label, item.confidence, BoundingBox(**item.bbox.model_dump())) for item in body.detections],
                model_version=body.model_version,
            )
            return decision_agent.decide(result, MissionContext(**body.mission_context.model_dump())).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


app = create_app()

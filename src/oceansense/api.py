from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

from .decision import DecisionAgent
from .mission_decision import MissionDecisionInput, decide_mission
from .navigation_contracts import InspectionTarget, RobotPose
from .perception import (
    FixtureClassifier,
    FixtureDomainClassifier,
    PerceptionService,
    TorchvisionDomainClassifier,
    TorchvisionEfficientNetClassifier,
    UltralyticsDetector,
)
from .rag import GroundedExplainer
from .schemas import (
    Anomaly,
    BoundingBox,
    Classification,
    ConditionAssessment,
    Detection,
    InspectionDomain,
    MissionContext,
    PerceptionResult,
)


class ContextBody(BaseModel):
    visibility_level: str = "unknown"
    depth_m: float | None = None
    battery_level: float | None = Field(default=None, ge=0, le=1)
    communication_status: str = "stable"
    operator_mode: str = "semi_autonomous"
    survey_goal: str = "unknown"


class PerceptionBody(BaseModel):
    frame_id: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    mission_context: ContextBody = Field(default_factory=ContextBody)


class ClassificationBody(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    top_k: list[dict[str, float | str]] = Field(default_factory=list)
    uncertainty: dict[str, float | bool] = Field(default_factory=dict)


class InspectionDomainBody(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)


class ConditionAssessmentBody(BaseModel):
    status: str
    risk_level: str
    score: float = Field(ge=0, le=1)
    summary: str = ""
    field_assessment: str | None = None


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


class PerceptionOutputBody(BaseModel):
    frame_id: str
    inspection_domain: InspectionDomainBody
    classification: ClassificationBody
    condition_assessment: ConditionAssessmentBody
    anomaly: AnomalyBody | None = None
    detections: list[DetectionBody] = Field(default_factory=list)
    model_version: str = "perception_v1"
    model_hash: str = "unknown"
    dataset_version: str = "unversioned"
    calibration_version: str = "uncalibrated"
    feature_transform_version: str = "efficientnet_b0_default_v1"
    simulator_profile: str = "not_applicable"
    vehicle_profile: str = "unknown"


class DecisionBody(BaseModel):
    frame_id: str
    perception_output: PerceptionOutputBody | None = None
    # Flat fields preserve compatibility with the initial API contract.
    inspection_domain: InspectionDomainBody | None = None
    classification: ClassificationBody | None = None
    condition_assessment: ConditionAssessmentBody | None = None
    anomaly: AnomalyBody | None = None
    detections: list[DetectionBody] = Field(default_factory=list)
    model_version: str = "perception_v1"
    mission_context: ContextBody = Field(default_factory=ContextBody)


class RobotPoseBody(BaseModel):
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


class InspectionTargetBody(BaseModel):
    target_id: str = Field(min_length=1)
    type: str
    expected_geometry: dict = Field(default_factory=dict)
    current_viewpoint: dict[str, float] = Field(default_factory=dict)
    distance_to_target: float = Field(ge=0)
    inspection_status: str = "unknown"


class MissionDecisionBody(BaseModel):
    mission_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    robot_pose: RobotPoseBody
    inspection_target: InspectionTargetBody
    model1_outputs: list[dict] = Field(default_factory=list)
    model2_outputs: list[dict] = Field(default_factory=list)
    uncertainty: dict[str, float | bool] = Field(default_factory=dict)
    environment: dict = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list)


def build_services() -> tuple[PerceptionService, DecisionAgent]:
    classifier_path = os.getenv("OCEANSENSE_CONDITION_CHECKPOINT") or os.getenv("OCEANSENSE_CLASSIFIER_CHECKPOINT")
    domain_path = os.getenv("OCEANSENSE_DOMAIN_CHECKPOINT")
    detector_path = os.getenv("OCEANSENSE_DETECTOR_CHECKPOINT")
    classifier = TorchvisionEfficientNetClassifier(classifier_path) if classifier_path else FixtureClassifier()
    domain_classifier = TorchvisionDomainClassifier(domain_path) if domain_path else FixtureDomainClassifier()
    detector = UltralyticsDetector(detector_path) if detector_path else None
    knowledge = Path(__file__).parent / "knowledge_base"
    return PerceptionService(classifier, detector, domain_classifier), DecisionAgent(GroundedExplainer(knowledge))


def create_app(perception_service: PerceptionService | None = None, decision_agent: DecisionAgent | None = None):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("Install the 'api' optional dependencies") from exc

    if perception_service is None or decision_agent is None:
        perception_service, decision_agent = build_services()

    app = FastAPI(title="OceanSense Intelligence API", version="2.0.0")

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "domain_model": getattr(perception_service.domain_classifier, "version", "unavailable"),
            "condition_model": perception_service.classifier.version,
            "detector_enabled": perception_service.detector is not None,
        }

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
            source = body.perception_output
            if source and source.frame_id != body.frame_id:
                raise ValueError("perception_output frame_id must match frame_id")
            classification_body = source.classification if source else body.classification
            if classification_body is None:
                raise ValueError("classification is required")
            domain_body = source.inspection_domain if source else (body.inspection_domain or InspectionDomainBody(label="unknown", confidence=0.0))
            anomaly_body = source.anomaly if source else body.anomaly
            condition_body = source.condition_assessment if source else body.condition_assessment
            if anomaly_body is None:
                score = condition_body.score if condition_body else classification_body.confidence
                level = condition_body.risk_level if condition_body else ("high" if score >= 0.70 else "medium" if score >= 0.40 else "low")
                anomaly = Anomaly(score, level, "Condition assessment score")
            else:
                anomaly = Anomaly(**anomaly_body.model_dump())
            detections = source.detections if source else body.detections
            result = PerceptionResult(
                frame_id=body.frame_id,
                classification=Classification(**classification_body.model_dump()),
                anomaly=anomaly,
                detections=[Detection(item.label, item.confidence, BoundingBox(**item.bbox.model_dump())) for item in detections],
                model_version=source.model_version if source else body.model_version,
                inspection_domain=InspectionDomain(**domain_body.model_dump()),
                condition_assessment=ConditionAssessment(**condition_body.model_dump()) if condition_body else None,
                model_hash=source.model_hash if source else "unknown",
                dataset_version=source.dataset_version if source else "unversioned",
                calibration_version=source.calibration_version if source else "uncalibrated",
                feature_transform_version=(
                    source.feature_transform_version if source else "efficientnet_b0_default_v1"
                ),
                simulator_profile=source.simulator_profile if source else "not_applicable",
                vehicle_profile=source.vehicle_profile if source else "unknown",
            )
            return decision_agent.decide(result, MissionContext(**body.mission_context.model_dump())).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/mission/decide")
    def decide_from_mission_evidence(body: MissionDecisionBody) -> dict:
        """Guide-compatible evidence decision; output contains high-level intent only."""
        try:
            target = InspectionTarget(**body.inspection_target.model_dump())
            request = MissionDecisionInput(
                mission_id=body.mission_id,
                frame_id=body.frame_id,
                robot_pose=RobotPose(**body.robot_pose.model_dump()),
                inspection_target=target,
                model1_outputs=body.model1_outputs,
                model2_outputs=body.model2_outputs,
                uncertainty=body.uncertainty,
                environment=body.environment,
                history=body.history,
            )
            return decide_mission(request).__dict__
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


app = create_app()

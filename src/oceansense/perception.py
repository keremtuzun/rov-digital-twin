from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .anomaly import score_anomaly
from .schemas import (
    CONDITION_LABELS,
    DOMAIN_LABELS,
    BoundingBox,
    Classification,
    Detection,
    InspectionDomain,
    MissionContext,
    PerceptionResult,
)
from .scoring import assess_condition


class ClassifierBackend(Protocol):
    version: str

    def classify(self, image_path: Path) -> Classification: ...


class DetectorBackend(Protocol):
    def detect(self, image_path: Path) -> list[Detection]: ...


class DomainClassifierBackend(Protocol):
    version: str

    def classify_domain(self, image_path: Path) -> InspectionDomain: ...


@dataclass
class FixtureClassifier:
    """Deterministic backend for integration tests and dashboard development."""

    label: str = "unknown"
    confidence: float = 0.0
    version: str = "fixture_v1"
    model_hash: str = "fixture"
    dataset_version: str = "fixture"
    calibration_version: str = "uncalibrated"

    def classify(self, image_path: Path) -> Classification:
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        return Classification(self.label, self.confidence)


@dataclass
class FixtureDomainClassifier:
    label: str = "unknown"
    confidence: float = 0.0
    version: str = "domain_fixture_v1"

    def classify_domain(self, image_path: Path) -> InspectionDomain:
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        return InspectionDomain(self.label, self.confidence)


class TorchvisionEfficientNetClassifier:
    """EfficientNet-B0 inference adapter for checkpoints made by train_classifier.py."""

    def __init__(self, checkpoint: str | Path, device: str = "cpu") -> None:
        try:
            import torch
            from torchvision.models import efficientnet_b0
        except ImportError as exc:
            raise RuntimeError("Install the 'vision' optional dependencies for model inference") from exc
        payload = torch.load(Path(checkpoint), map_location=device, weights_only=False)
        self.model_hash = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
        self.labels = list(payload["labels"])
        self.task = str(payload.get("task", "condition"))
        if type(self) is TorchvisionEfficientNetClassifier and self.task == "domain":
            raise ValueError("A domain checkpoint cannot be used as the condition classifier")
        if type(self) is TorchvisionEfficientNetClassifier and set(self.labels) - CONDITION_LABELS:
            raise ValueError("Condition checkpoint contains unsupported labels")
        model = efficientnet_b0(weights=None)
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(self.labels))
        model.load_state_dict(payload["state_dict"])
        model.eval().to(device)
        self.model, self.device, self.torch = model, device, torch
        self.version = str(payload.get("model_version", "efficientnet_b0_v1"))
        metadata = payload.get("metadata", {})
        self.dataset_version = str(metadata.get("data_manifest_sha256") or "unversioned")
        self.calibration_version = str(metadata.get("calibration_version") or "uncalibrated")

    def _predict_distribution(self, image_path: Path):
        from PIL import Image
        from torchvision.models import EfficientNet_B0_Weights

        transform = EfficientNet_B0_Weights.DEFAULT.transforms()
        with Image.open(image_path) as image:
            tensor = transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            return self.model(tensor).softmax(dim=1)[0]

    def classify(self, image_path: Path) -> Classification:
        from .vision_uncertainty import image_quality_score, vision_uncertainty

        probabilities = self._predict_distribution(image_path)
        confidence, index = probabilities.max(dim=0)
        top_values, top_indices = probabilities.topk(min(3, len(self.labels)))
        top_k = [
            {"label": self.labels[int(item_index)], "confidence": float(item_confidence)}
            for item_confidence, item_index in zip(top_values, top_indices)
        ]
        quality = image_quality_score(image_path)
        uncertainty = vision_uncertainty(probabilities.tolist(), quality["quality"])
        uncertainty.update(quality)
        label = "unknown" if uncertainty["unknown"] else self.labels[int(index)]
        return Classification(label, float(confidence), top_k, uncertainty)


class TorchvisionDomainClassifier(TorchvisionEfficientNetClassifier):
    def __init__(self, checkpoint: str | Path, device: str = "cpu") -> None:
        super().__init__(checkpoint, device)
        if self.task != "domain":
            raise ValueError("Domain classifier requires a checkpoint trained with --task domain")
        if set(self.labels) - DOMAIN_LABELS:
            raise ValueError("Domain checkpoint contains non-domain labels")

    def classify_domain(self, image_path: Path) -> InspectionDomain:
        probabilities = self._predict_distribution(image_path)
        confidence, index = probabilities.max(dim=0)
        return InspectionDomain(self.labels[int(index)], float(confidence))


class UltralyticsDetector:
    """Optional YOLOv8 detector; omit it when defensible box annotations are unavailable."""

    def __init__(self, checkpoint: str | Path, confidence: float = 0.25) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install the 'detection' optional dependencies") from exc
        self.model = YOLO(str(checkpoint))
        self.confidence = confidence

    def detect(self, image_path: Path) -> list[Detection]:
        output: list[Detection] = []
        for result in self.model.predict(str(image_path), conf=self.confidence, verbose=False):
            for box in result.boxes:
                x1, y1, x2, y2 = (round(v) for v in box.xyxy[0].tolist())
                label = str(result.names[int(box.cls[0])])
                output.append(Detection(label, float(box.conf[0]), BoundingBox(x1, y1, x2, y2)))
        return output


class PerceptionService:
    def __init__(
        self,
        classifier: ClassifierBackend,
        detector: DetectorBackend | None = None,
        domain_classifier: DomainClassifierBackend | None = None,
    ) -> None:
        self.classifier = classifier
        self.detector = detector
        self.domain_classifier = domain_classifier

    def analyze(
        self,
        frame_id: str,
        image_path: str | Path,
        mission_context: MissionContext | None = None,
    ) -> PerceptionResult:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        context = mission_context or MissionContext()
        domain = self.domain_classifier.classify_domain(path) if self.domain_classifier else InspectionDomain("unknown", 0.0)
        classification = self.classifier.classify(path)
        # Context may lower confidence, but must never invent a new observation.
        if context.visibility_level == "poor" and classification.label != "low_visibility":
            classification = Classification(
                classification.label,
                classification.confidence * 0.8,
                classification.top_k,
                classification.uncertainty,
            )
        detections = self.detector.detect(path) if self.detector else []
        return PerceptionResult(
            frame_id=frame_id,
            classification=classification,
            anomaly=score_anomaly(classification),
            detections=detections,
            model_version=f"domain:{getattr(self.domain_classifier, 'version', 'unavailable')};condition:{self.classifier.version}",
            inspection_domain=domain,
            condition_assessment=assess_condition(domain, classification),
            model_hash=getattr(self.classifier, "model_hash", "unknown"),
            dataset_version=getattr(self.classifier, "dataset_version", "unversioned"),
            calibration_version=getattr(self.classifier, "calibration_version", "uncalibrated"),
        )


def write_result(result: PerceptionResult, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return path

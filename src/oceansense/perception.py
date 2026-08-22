from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .anomaly import score_anomaly
from .schemas import BoundingBox, Classification, Detection, MissionContext, PerceptionResult


class ClassifierBackend(Protocol):
    version: str

    def classify(self, image_path: Path) -> Classification: ...


class DetectorBackend(Protocol):
    def detect(self, image_path: Path) -> list[Detection]: ...


@dataclass
class FixtureClassifier:
    """Deterministic backend for integration tests and dashboard development."""

    label: str = "unknown"
    confidence: float = 0.0
    version: str = "fixture_v1"

    def classify(self, image_path: Path) -> Classification:
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        return Classification(self.label, self.confidence)


class TorchvisionEfficientNetClassifier:
    """EfficientNet-B0 inference adapter for checkpoints made by train_classifier.py."""

    def __init__(self, checkpoint: str | Path, device: str = "cpu") -> None:
        try:
            import torch
            from torchvision.models import efficientnet_b0
        except ImportError as exc:
            raise RuntimeError("Install the 'vision' optional dependencies for model inference") from exc
        payload = torch.load(Path(checkpoint), map_location=device, weights_only=False)
        self.labels = list(payload["labels"])
        model = efficientnet_b0(weights=None)
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(self.labels))
        model.load_state_dict(payload["state_dict"])
        model.eval().to(device)
        self.model, self.device, self.torch = model, device, torch
        self.version = str(payload.get("model_version", "efficientnet_b0_v1"))

    def classify(self, image_path: Path) -> Classification:
        from PIL import Image
        from torchvision.models import EfficientNet_B0_Weights

        transform = EfficientNet_B0_Weights.DEFAULT.transforms()
        with Image.open(image_path) as image:
            tensor = transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            probabilities = self.model(tensor).softmax(dim=1)[0]
        confidence, index = probabilities.max(dim=0)
        return Classification(self.labels[int(index)], float(confidence))


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
                x1, y1, x2, y2 = (int(round(v)) for v in box.xyxy[0].tolist())
                label = str(result.names[int(box.cls[0])])
                output.append(Detection(label, float(box.conf[0]), BoundingBox(x1, y1, x2, y2)))
        return output


class PerceptionService:
    def __init__(self, classifier: ClassifierBackend, detector: DetectorBackend | None = None) -> None:
        self.classifier = classifier
        self.detector = detector

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
        classification = self.classifier.classify(path)
        # Context may lower confidence, but must never invent a new observation.
        if context.visibility_level == "poor" and classification.label != "low_visibility":
            classification = Classification(classification.label, classification.confidence * 0.8)
        detections = self.detector.detect(path) if self.detector else []
        return PerceptionResult(
            frame_id=frame_id,
            classification=classification,
            anomaly=score_anomaly(classification),
            detections=detections,
            model_version=self.classifier.version,
        )


def write_result(result: PerceptionResult, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return path

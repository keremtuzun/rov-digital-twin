from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from oceansense.anomaly import score_anomaly
from oceansense.data import REQUIRED_COLUMNS, read_labels, stratified_split, validate_dataset, write_labels
from oceansense.decision import DecisionAgent
from oceansense.perception import FixtureClassifier, PerceptionService
from oceansense.rag import GroundedExplainer
from oceansense.schemas import Anomaly, Classification, MissionContext, PerceptionResult


KNOWLEDGE = Path(__file__).parents[1] / "src" / "oceansense" / "knowledge_base"


def perception(label: str, confidence: float, level: str | None = None) -> PerceptionResult:
    classification = Classification(label, confidence)
    anomaly = score_anomaly(classification)
    if level is not None:
        anomaly = Anomaly(anomaly.score, level, anomaly.reason)
    return PerceptionResult("frame-test", classification, anomaly)


class SchemaAndAnomalyTests(unittest.TestCase):
    def test_documented_anomaly_thresholds(self):
        self.assertEqual(score_anomaly(Classification("normal_surface", 0.80)).level, "low")
        self.assertEqual(score_anomaly(Classification("possible_damage", 0.55)).level, "medium")
        self.assertEqual(score_anomaly(Classification("possible_weak_point", 0.81)).level, "high")

    def test_invalid_values_fail_instead_of_guessing(self):
        with self.assertRaises(ValueError):
            Classification("confirmed_failure", 0.9)
        with self.assertRaises(ValueError):
            MissionContext(battery_level=1.2)


class DecisionRuleTests(unittest.TestCase):
    def setUp(self):
        self.agent = DecisionAgent(GroundedExplainer(KNOWLEDGE))

    def test_success_criteria_cases(self):
        cases = [
            (perception("normal_surface", 0.90), MissionContext(), "continue_survey"),
            (perception("possible_damage", 0.85), MissionContext(), "inspect_closer"),
            (perception("normal_surface", 0.90), MissionContext(visibility_level="poor"), "capture_more_data"),
            (perception("possible_damage", 0.40), MissionContext(), "request_human_review"),
            (perception("normal_surface", 0.90), MissionContext(battery_level=0.19), "return_to_base"),
            (perception("normal_surface", 0.90), MissionContext(communication_status="unstable"), "hold_position"),
        ]
        for result, context, expected in cases:
            with self.subTest(expected=expected):
                decision = self.agent.decide(result, context)
                self.assertEqual(decision.recommended_action, expected)

    def test_safety_precedence_and_grounded_caution(self):
        result = self.agent.decide(
            perception("possible_weak_point", 0.95),
            MissionContext(battery_level=0.10, communication_status="unstable"),
        )
        self.assertEqual(result.recommended_action, "return_to_base")
        self.assertTrue(result.requires_human_review)
        self.assertIn("not confirmation", result.explanation["interpretation"])
        self.assertTrue(result.explanation["grounding_sources"])
        serialized = json.dumps(result.to_dict())
        self.assertNotIn("thruster", serialized.lower())


class DatasetTests(unittest.TestCase):
    def test_schema_split_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            images = root / "images"
            images.mkdir()
            labels = root / "labels.csv"
            fields = sorted(REQUIRED_COLUMNS)
            rows = []
            for index in range(12):
                image = images / f"{index}.jpg"
                image.write_bytes(b"fixture")
                rows.append({
                    "sample_id": f"OS-{index:06d}", "file_path": f"images/{index}.jpg",
                    "source": "fixture", "license": "test-only", "split": "",
                    "primary_label": "normal_surface" if index < 6 else "marine_debris",
                    "contains_anomaly": "false" if index < 6 else "true", "weak_point_present": "false",
                    "visibility_level": "moderate", "confidence_label": "high", "notes": "test",
                })
            with labels.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            records = read_labels(labels)
            split = stratified_split(records, seed=7)
            output = write_labels(split, root / "split.csv")
            report = validate_dataset(output)
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(set(report["split_distribution"]), {"train", "val", "test"})


class PerceptionServiceTests(unittest.TestCase):
    def test_image_in_json_out(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "frame.jpg"
            image.write_bytes(b"fixture")
            service = PerceptionService(FixtureClassifier("possible_damage", 0.84))
            output = service.analyze("frame_00042", image, MissionContext(visibility_level="moderate"))
            self.assertEqual(output.frame_id, "frame_00042")
            self.assertEqual(output.classification.label, "possible_damage")
            self.assertEqual(output.anomaly.level, "high")
            self.assertEqual(output.detections, [])


if __name__ == "__main__":
    unittest.main()

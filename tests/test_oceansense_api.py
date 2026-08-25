from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "FastAPI optional dependency not installed")
class ApiContractTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from oceansense.api import create_app
        from oceansense.decision import DecisionAgent
        from oceansense.perception import (
            FixtureClassifier,
            FixtureDomainClassifier,
            PerceptionService,
        )
        from oceansense.rag import GroundedExplainer

        knowledge = Path(__file__).parents[1] / "src" / "oceansense" / "knowledge_base"
        self.temp = tempfile.TemporaryDirectory()
        self.image = Path(self.temp.name) / "frame.jpg"
        self.image.write_bytes(b"fixture")
        app = create_app(
            PerceptionService(
                FixtureClassifier("possible_weak_point", 0.84),
                domain_classifier=FixtureDomainClassifier("structure", 0.88),
            ),
            DecisionAgent(GroundedExplainer(knowledge)),
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.temp.cleanup()

    def test_perception_and_decision_contracts(self):
        response = self.client.post("/api/perception/analyze", json={
            "frame_id": "frame_00042", "image_path": str(self.image),
            "mission_context": {"visibility_level": "moderate", "depth_m": 4.5, "survey_goal": "structure"},
        })
        self.assertEqual(response.status_code, 200, response.text)
        perception = response.json()
        self.assertEqual(perception["inspection_domain"]["label"], "structure")
        self.assertEqual(perception["classification"]["label"], "possible_weak_point")
        decision_request = {"frame_id": perception["frame_id"], "perception_output": perception}
        decision_request["mission_context"] = {
            "visibility_level": "moderate", "depth_m": 4.5,
            "battery_level": 0.82, "communication_status": "stable",
            "operator_mode": "semi_autonomous", "survey_goal": "structure",
        }
        response = self.client.post("/api/agent/decide", json=decision_request)
        self.assertEqual(response.status_code, 200, response.text)
        decision = response.json()
        self.assertEqual(decision["recommended_action"], "inspect_closer")
        self.assertEqual(decision["domain"], "structure")
        self.assertTrue(decision["requires_human_review"])

    def test_invalid_input_returns_error(self):
        response = self.client.post("/api/perception/analyze", json={
            "frame_id": "", "image_path": "missing.jpg", "mission_context": {},
        })
        self.assertEqual(response.status_code, 422)

    def test_mismatched_nested_frame_is_rejected(self):
        response = self.client.post("/api/agent/decide", json={
            "frame_id": "frame_a",
            "perception_output": {
                "frame_id": "frame_b",
                "inspection_domain": {"label": "structure", "confidence": 0.9},
                "classification": {"label": "structure_ok", "confidence": 0.9},
                "condition_assessment": {"status": "ok", "risk_level": "low", "score": 0.1},
            },
            "mission_context": {"survey_goal": "structure"},
        })
        self.assertEqual(response.status_code, 422)

    def test_guide_compatible_mission_decision_is_high_level_only(self):
        response = self.client.post("/api/mission/decide", json={
            "mission_id": "mission-1",
            "frame_id": "frame-1",
            "robot_pose": {"x": 0, "y": 0, "z": -2, "roll": 0, "pitch": 0, "yaw": 0},
            "inspection_target": {
                "target_id": "pipe-1", "type": "pipe", "expected_geometry": {},
                "current_viewpoint": {"angle_deg": 65}, "distance_to_target": 1.0,
                "inspection_status": "started",
            },
            "model1_outputs": [{"frame_id": "frame-1", "confidence": 0.8}],
            "model2_outputs": [],
            "uncertainty": {"entropy": 0.2},
            "environment": {"visibility": "moderate"},
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["decision"], "change_viewpoint")
        self.assertNotIn("thruster", response.text.lower())


if __name__ == "__main__":
    unittest.main()

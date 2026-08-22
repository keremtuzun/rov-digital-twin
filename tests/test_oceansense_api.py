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
        from oceansense.perception import FixtureClassifier, PerceptionService
        from oceansense.rag import GroundedExplainer

        knowledge = Path(__file__).parents[1] / "src" / "oceansense" / "knowledge_base"
        self.temp = tempfile.TemporaryDirectory()
        self.image = Path(self.temp.name) / "frame.jpg"
        self.image.write_bytes(b"fixture")
        app = create_app(
            PerceptionService(FixtureClassifier("possible_damage", 0.84)),
            DecisionAgent(GroundedExplainer(knowledge)),
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.temp.cleanup()

    def test_perception_and_decision_contracts(self):
        response = self.client.post("/api/perception/analyze", json={
            "frame_id": "frame_00042", "image_path": str(self.image),
            "mission_context": {"visibility_level": "moderate", "depth_m": 4.5},
        })
        self.assertEqual(response.status_code, 200, response.text)
        perception = response.json()
        self.assertEqual(perception["classification"]["label"], "possible_damage")
        decision_request = dict(perception)
        decision_request["mission_context"] = {
            "visibility_level": "moderate", "depth_m": 4.5,
            "battery_level": 0.82, "communication_status": "stable",
        }
        response = self.client.post("/api/agent/decide", json=decision_request)
        self.assertEqual(response.status_code, 200, response.text)
        decision = response.json()
        self.assertEqual(decision["recommended_action"], "inspect_closer")
        self.assertTrue(decision["requires_human_review"])

    def test_invalid_input_returns_error(self):
        response = self.client.post("/api/perception/analyze", json={
            "frame_id": "", "image_path": "missing.jpg", "mission_context": {},
        })
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

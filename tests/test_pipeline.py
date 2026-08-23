import json
import tempfile
import unittest
from pathlib import Path

from rov_dt.dataset import generate_dataset, read_csv, write_csv
from rov_dt.decision import SafetyDecisionAgent
from rov_dt.model import SoftmaxWeakPointClassifier
from rov_dt.training import train_from_csv


class PipelineTests(unittest.TestCase):
    def test_feature_transform_v2_and_v1_model_compatibility(self):
        model = SoftmaxWeakPointClassifier(["nominal", "fault"], ["speed_mps"])
        self.assertEqual(len(model._expand([2.0])), 9)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "legacy.json"
            path.write_text(
                json.dumps(
                    {
                        "labels": ["nominal", "fault"],
                        "feature_names": ["speed_mps"],
                        "means": [0.0, 0.0],
                        "scales": [1.0, 1.0],
                        "weights": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                    }
                ),
                encoding="utf-8",
            )
            legacy = SoftmaxWeakPointClassifier.load(path)
            self.assertEqual(legacy.feature_transform, "raw_plus_absolute_v1")
            self.assertEqual(len(legacy._expand([2.0])), 2)

    def test_dataset_is_balanced_and_round_trips(self):
        samples = generate_dataset(100, seed=7)
        self.assertEqual(len(samples), 100)
        self.assertEqual(len({sample.label for sample in samples}), 5)
        with tempfile.TemporaryDirectory() as folder:
            path = write_csv(samples, Path(folder) / "data.csv")
            self.assertEqual(len(read_csv(path)), 100)

    def test_training_and_decision(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = write_csv(generate_dataset(750, seed=11), root / "data.csv")
            metrics = train_from_csv(data, root / "model.json", root / "metrics.json", epochs=90, seed=11)
            self.assertGreater(metrics["accuracy"], 0.82)
            self.assertGreater(metrics["initial_train_loss"], metrics["final_train_loss"])
            self.assertGreater(metrics["loss_reduction_fraction"], 0.0)
            self.assertFalse(set(metrics["train_missions"]) & set(metrics["test_missions"]))
            model = SoftmaxWeakPointClassifier.load(root / "model.json")
            fault = next(sample for sample in read_csv(data) if sample.label == "sensor_drift")
            decision = SafetyDecisionAgent(model).decide(fault)
            self.assertIn(decision.risk_level, {"high", "critical", "uncertain"})
            self.assertFalse(decision.autonomous_execution_allowed)
            self.assertTrue(json.dumps(decision.to_dict()))


if __name__ == "__main__":
    unittest.main()

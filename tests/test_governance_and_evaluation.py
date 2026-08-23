import csv
import tempfile
import unittest
from pathlib import Path

from oceansense.evaluation import classification_metrics
from oceansense.governance import MANIFEST_FIELDS, audit_manifest, sha256_file, write_manifest
from oceansense.taxonomy import canonicalize_label, is_domain_compatible
from scripts.convert_annotations import convert_csv


class GovernanceTests(unittest.TestCase):
    def test_license_audit_requires_allowlist_checksum_and_reviewer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset = root / "frame.jpg"
            asset.write_bytes(b"small-fixture")
            base = {field: "" for field in MANIFEST_FIELDS}
            base.update({
                "sample_id": "approved", "source_name": "fixture", "source_url": "https://example.test/source",
                "original_asset_url": "https://example.test/frame.jpg", "license": "CC-BY-4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/", "attribution": "Fixture Author",
                "downloaded_at": "2026-08-23T00:00:00Z", "sha256": sha256_file(asset),
                "inspection_domain": "structure", "primary_label": "possible_structural_concern",
                "annotation_type": "classification", "mission_or_video_id": "mission-a",
                "real_or_synthetic": "real", "approved_by": "reviewer", "approval_status": "approved",
            })
            rejected = dict(base, sample_id="rejected", license="CC-BY-NC-ND", approved_by="")
            manifest = write_manifest(root / "raw.csv", [base, rejected])
            approved, denied = audit_manifest(manifest)
            self.assertEqual([row["sample_id"] for row in approved], ["approved"])
            self.assertEqual([row["sample_id"] for row in denied], ["rejected"])

    def test_annotation_alias_conversion_is_backward_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "labels.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["sample_id", "primary_label"])
                writer.writeheader()
                writer.writerow({"sample_id": "a", "primary_label": "possible_crack"})
            migrations = convert_csv(source, root / "canonical.csv")
            self.assertEqual(migrations, {"possible_crack->possible_structural_concern": 1})
            self.assertEqual(canonicalize_label("coral_bleaching"), "ecological_stress_indicator")
            self.assertTrue(is_domain_compatible("structure", "possible_crack"))


class EvaluationTests(unittest.TestCase):
    def test_metrics_include_calibration_and_safety_relevant_aggregates(self):
        report = classification_metrics(
            ["normal", "concern", "concern", "normal"],
            ["normal", "concern", "normal", "normal"],
            [0.9, 0.8, 0.7, 0.6],
        )
        self.assertAlmostEqual(report["accuracy"], 0.75)
        self.assertIn("balanced_accuracy", report)
        self.assertIn("expected_calibration_error", report)
        self.assertIn("0.8", report["confidence_thresholds"])


if __name__ == "__main__":
    unittest.main()

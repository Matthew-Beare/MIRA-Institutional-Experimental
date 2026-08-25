from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "feature_catalog.py"
SPEC = importlib.util.spec_from_file_location("feature_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
catalog_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_tool)


class FeatureCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = catalog_tool.build(ROOT)
        self.features = [
            feature
            for category in self.catalog["categories"]
            for feature in category["features"]
        ]

    def feature(self, phrase: str):
        matches = [row for row in self.features if phrase.lower() in row["title"].lower()]
        self.assertEqual(1, len(matches), f"expected one feature containing {phrase!r}")
        return matches[0]

    def test_catalog_is_complete_unique_and_valid(self) -> None:
        self.assertEqual([], catalog_tool.validate(self.catalog, ROOT))
        self.assertGreaterEqual(len(self.features), 70)
        self.assertEqual(len(self.features), len({row["id"] for row in self.features}))

    def test_required_current_features_are_explicit_and_ci_backed(self) -> None:
        for phrase in (
            "Bidirectional receipt/order",
            "Namespaced UPC/GTIN",
            "Product/serial/barcode photo",
            "Manual discovery",
            "technical specifications",
            "Medication reminders",
            "Retired/retiree profile",
            "Parent/guardian profile",
            "Provider-neutral AI runtime",
            "Google Workspace and Microsoft 365",
            "Locked-down and regulated enterprise/VA",
            "Hierarchical machine-readable feature catalog",
        ):
            with self.subTest(phrase=phrase):
                feature = self.feature(phrase)
                self.assertEqual("ci_evidence", feature["verification"])
                self.assertTrue(feature["evidence_paths"])

    def test_catalog_does_not_lie_about_infrastructure_or_spec_only_work(self) -> None:
        self.assertEqual("not_present", self.feature("Companion/mobile app")["delivery"])
        self.assertEqual("infrastructure", self.feature("eventual PostgreSQL")["delivery"])
        self.assertEqual("specification", self.feature("Scale-based par sensing")["delivery"])
        self.assertEqual("contract", self.feature("Apple/iCloud and portable-file")["delivery"])

    def test_retired_template_is_respectful_and_does_not_infer_age_or_ability(self) -> None:
        feature = self.feature("Retired/retiree profile")
        combined = " ".join(
            (feature["title"], feature["current_status"], feature["required_disposition"])
        ).lower()
        self.assertIn("personal schedule & wellbeing", combined)
        self.assertIn("never infer age/ability", combined)
        self.assertNotIn("elderly mode", combined)
        self.assertNotIn("boomer mode", combined)

    def test_checked_in_json_matches_generated_catalog(self) -> None:
        checked_in = json.loads((ROOT / catalog_tool.JSON_PATH).read_text(encoding="utf-8"))
        self.assertEqual(self.catalog, checked_in)


if __name__ == "__main__":
    unittest.main()

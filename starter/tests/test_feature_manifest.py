#!/usr/bin/env python3
"""Tests for the portable feature-module contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_feature_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_feature_manifest", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class FeatureManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixtures" / "features" / "meal-planning.feature.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "schemas" / "feature-manifest.schema.json").read_text(encoding="utf-8"))

    def test_synthetic_portable_feature_is_valid(self):
        self.assertEqual(validator.validate_manifest(self.fixture), [])

    def test_validator_and_schema_require_the_same_top_level_fields(self):
        self.assertEqual(set(self.schema["required"]), validator.REQUIRED_FIELDS)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(self.schema["properties"]["manifest_version"]["const"], 3)

    def test_validator_and_schema_require_the_same_runtime_fields(self):
        runtime = self.schema["properties"]["runtime_contract"]
        self.assertEqual(set(runtime["required"]), validator.RUNTIME_CONTRACT_FIELDS)
        self.assertFalse(runtime["additionalProperties"])
        self.assertEqual(runtime["properties"]["on_required_failure"]["const"], "block-module-only")
        self.assertEqual(runtime["properties"]["on_optional_failure"]["const"], "degrade-capability-and-continue")

    def test_meta_schema_config_contract_is_recursive_and_closed(self):
        root = self.schema["properties"]["config_schema"]
        self.assertEqual(root["$ref"], "#/$defs/configSchemaObject")
        node = self.schema["$defs"]["configSchemaNode"]
        self.assertFalse(node["additionalProperties"])
        self.assertEqual(
            node["properties"]["items"]["$ref"],
            "#/$defs/configSchemaNode",
        )

    def test_personal_data_in_shared_source_is_rejected(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["data_boundary"]["source_contains_personal_data"] = True
        self.assertIn("source_contains_personal_data must be false", validator.validate_manifest(manifest))

    def test_unsafe_entrypoint_path_is_rejected(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["entrypoints"]["scripts"] = ["../../private/config.json"]
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("unsafe path" in error for error in errors))

    def test_unknown_fields_are_rejected(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["personal_notes"] = "must not be portable"
        self.assertIn("unknown fields: personal_notes", validator.validate_manifest(manifest))

    def test_redundant_or_ambiguous_path_segments_are_rejected(self):
        for path in ("scripts//run.py", "scripts/./run.py", "scripts/../run.py"):
            manifest = copy.deepcopy(self.fixture)
            manifest["entrypoints"]["scripts"] = [path]
            self.assertTrue(any("unsafe path" in error for error in validator.validate_manifest(manifest)))

    def test_symlink_escape_is_rejected_during_file_check(self):
        with tempfile.TemporaryDirectory() as tempdir, tempfile.TemporaryDirectory() as outside:
            root = Path(tempdir)
            target = Path(outside) / "test.py"
            target.write_text("pass\n", encoding="utf-8")
            try:
                os.symlink(target, root / "test.py")
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            manifest = copy.deepcopy(self.fixture)
            manifest["entrypoints"] = {"references": [], "scripts": [], "schemas": [], "migrations": []}
            manifest["tests"] = ["test.py"]
            errors = validator.validate_manifest(manifest, root)
            self.assertTrue(any("escapes feature root" in error for error in errors))

    def test_semver_and_ranges_are_not_accept_any_nonblank_string(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["version"] = "1.0.0-01"
        self.assertIn("version must be semantic version syntax", validator.validate_manifest(manifest))
        manifest = copy.deepcopy(self.fixture)
        manifest["compatibility"]["core"] = "whatever"
        self.assertIn(
            "compatibility.core must be a valid semantic-version range",
            validator.validate_manifest(manifest),
        )

    def test_config_schema_is_recursively_checked(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["config_schema"]["required"] = ["missing_property"]
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("required names missing properties" in error for error in errors))
        manifest = copy.deepcopy(self.fixture)
        manifest["config_schema"]["properties"]["servings"]["minimum"] = float("inf")
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("must be finite numeric" in error for error in errors))

    def test_markdown_contract_cannot_claim_implemented_delivery(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["tests"] = ["tests/contract.md"]
        errors = validator.validate_manifest(manifest)
        self.assertIn("implemented features must declare at least one executable test", errors)

        manifest = copy.deepcopy(self.fixture)
        manifest["entrypoints"]["scripts"] = []
        errors = validator.validate_manifest(manifest)
        self.assertIn("implemented features must declare at least one script entrypoint", errors)

    def test_wrong_delivery_status_type_returns_error_not_exception(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["delivery_status"] = {"implemented": True}
        self.assertIn(
            "delivery_status must be contract-only or implemented",
            validator.validate_manifest(manifest),
        )

    def test_version_range_rejects_empty_comma_terms(self):
        for value in (">=1.0.0,", ",>=1.0.0", ">=1.0.0,,<2.0.0"):
            manifest = copy.deepcopy(self.fixture)
            manifest["compatibility"]["core"] = value
            self.assertIn(
                "compatibility.core must be a valid semantic-version range",
                validator.validate_manifest(manifest),
            )

    def test_schema_rejects_wrong_typed_const_and_incompatible_keywords(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["config_schema"]["properties"]["servings"]["const"] = "two"
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("const does not match type integer" in error for error in errors))

        manifest = copy.deepcopy(self.fixture)
        manifest["config_schema"]["properties"]["servings"]["items"] = {"type": "string"}
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("valid only for array schemas" in error for error in errors))

    def test_config_schema_root_and_defaults_must_be_internally_valid(self):
        manifest = copy.deepcopy(self.fixture)
        manifest["config_schema"] = {"type": "string"}
        self.assertIn("config_schema.type must be object", validator.validate_manifest(manifest))

        manifest = copy.deepcopy(self.fixture)
        servings = manifest["config_schema"]["properties"]["servings"]
        servings["default"] = 0
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("default violates its declared constraints" in error for error in errors))

        manifest = copy.deepcopy(self.fixture)
        servings = manifest["config_schema"]["properties"]["servings"]
        servings["minimum"] = 1
        servings["enum"] = [0, 2]
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("enum contains a value outside declared constraints" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

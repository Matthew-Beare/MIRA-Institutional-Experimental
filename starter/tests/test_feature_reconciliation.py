from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "feature_reconciliation.py"
SPEC = importlib.util.spec_from_file_location("feature_reconciliation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
feature_reconciliation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feature_reconciliation)


class FeatureReconciliationTests(unittest.TestCase):
    def test_committed_dependency_map_matches_current_features(self) -> None:
        generated = feature_reconciliation.build_dependency_map(ROOT)
        committed = json.loads((ROOT / "feature-dependency-map.json").read_text(encoding="utf-8"))
        self.assertEqual(committed, generated)
        self.assertTrue(committed["policy"]["user_in_the_loop"])
        self.assertEqual("keep-current", committed["policy"]["local_behavior_default"])
        self.assertFalse(committed["policy"]["automatic_local_feature_deletion"])

    def test_register_new_user_feature_records_owner_and_refreshes_map(self) -> None:
        manifest = {
            "id": "garage-helper",
            "version": "1.0.0",
            "summary": "Garage helper",
            "dependencies": [],
            "runtime_contract": {
                "required_capabilities": ["structured-state-authority"],
                "optional_capabilities": ["drive-evidence"],
                "conditional_capabilities": {},
                "failure_domain": "garage-helper",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = root / "features" / "garage-helper"
            feature_dir.mkdir(parents=True)
            (feature_dir / "feature.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "features.lock.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "default_conflict_policy": "preserve-local-and-ask",
                        "default_rollback_policy": "checkpoint-before-change",
                        "features": {},
                    }
                ),
                encoding="utf-8",
            )
            dependency_map = feature_reconciliation.register_feature(root, "garage-helper", "user")
            lock = json.loads((root / "features.lock.json").read_text(encoding="utf-8"))
            row = lock["features"]["garage-helper"]
            self.assertEqual("user", row["owner"])
            self.assertEqual("user", row["origin"])
            self.assertIsNone(row["upstream_feature_id"])
            self.assertEqual("preserve-local-and-ask", row["conflict_policy"])
            self.assertTrue((root / "feature-dependency-map.json").is_file())
            self.assertEqual("user", dependency_map["features"]["garage-helper"]["owner"])

    def test_register_refuses_silent_ownership_transfer(self) -> None:
        manifest = {
            "id": "garage-helper",
            "version": "1.0.0",
            "summary": "Garage helper",
            "dependencies": [],
            "runtime_contract": {
                "required_capabilities": [],
                "optional_capabilities": [],
                "conditional_capabilities": {},
                "failure_domain": "garage-helper",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = root / "features" / "garage-helper"
            feature_dir.mkdir(parents=True)
            (feature_dir / "feature.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "features.lock.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "default_conflict_policy": "preserve-local-and-ask",
                        "default_rollback_policy": "checkpoint-before-change",
                        "features": {
                            "garage-helper": {
                                "owner": "user",
                                "origin": "user",
                                "installed_version": "1.0.0",
                                "upstream_feature_id": None,
                                "upstream_base_version": None,
                                "upstream_base_revision": None,
                                "local_revision": 0,
                                "owned_paths": ["starter/features/garage-helper/**"],
                                "conflict_policy": "preserve-local-and-ask",
                                "rollback_policy": "checkpoint-before-change",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                feature_reconciliation.ReconciliationError, "refusing to change.*ownership"
            ):
                feature_reconciliation.register_feature(root, "garage-helper", "mirror")

    def test_missing_required_capability_blocks_only_that_feature(self) -> None:
        dependency_map = {
            "schema_version": 1,
            "features": {
                "needs-mail": {
                    "required_capabilities": ["email-evidence"],
                    "optional_capabilities": [],
                },
                "offline": {
                    "required_capabilities": [],
                    "optional_capabilities": [],
                },
            },
        }
        result = feature_reconciliation.audit_capabilities(dependency_map, [])
        self.assertFalse(result["ready"])
        self.assertEqual(["needs-mail"], result["blocked_features"])
        self.assertEqual("blocked", result["features"]["needs-mail"]["status"])
        self.assertEqual("ready", result["features"]["offline"]["status"])

    def test_missing_optional_capability_degrades_without_blocking(self) -> None:
        dependency_map = {
            "schema_version": 1,
            "features": {
                "receipts": {
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": ["drive-evidence"],
                }
            },
        }
        result = feature_reconciliation.audit_capabilities(
            dependency_map, ["structured-state-authority"]
        )
        self.assertTrue(result["ready"])
        self.assertEqual(["receipts"], result["degraded_features"])
        self.assertEqual(["drive-evidence"], result["features"]["receipts"]["missing_optional"])

    def test_new_upstream_feature_with_missing_requirement_is_not_offered_as_installable(self) -> None:
        candidate = {
            "schema_version": 1,
            "features": {
                "mail-summary": {
                    "version": "1.0.0",
                    "summary": "Mail summary",
                    "owner": "mirror",
                    "local_revision": 0,
                    "feature_dependencies": [],
                    "required_capabilities": ["email-evidence"],
                    "optional_capabilities": [],
                }
            },
        }
        plan = feature_reconciliation.plan_upgrade(
            {"schema_version": 1, "features": {}},
            {"schema_version": 1, "features": {}},
            candidate,
            capability_sources={"email-evidence": "Gmail or Outlook email access"},
        )
        change = plan["changes"][0]
        self.assertEqual("dependency-blocked", change["kind"])
        self.assertEqual("keep-current", change["default_action"])
        self.assertEqual(["Gmail or Outlook email access"], change["missing_required_help"])

    def test_user_owned_feature_is_preserved_by_default(self) -> None:
        base = {
            "schema_version": 1,
            "features": {
                "vehicle-maintenance": {
                    "version": "1.0.0",
                    "summary": "Vehicle maintenance",
                    "owner": "mirror",
                    "local_revision": 0,
                    "feature_dependencies": [],
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": [],
                }
            },
        }
        current = {
            "schema_version": 1,
            "features": {
                "vehicle-maintenance": {
                    "version": "1.0.0-local.1",
                    "summary": "My vehicle maintenance workflow",
                    "owner": "user",
                    "local_revision": 3,
                    "feature_dependencies": [],
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": [],
                }
            },
        }
        candidate = {
            "schema_version": 1,
            "features": {
                "vehicle-maintenance": {
                    "version": "2.0.0",
                    "summary": "New upstream vehicle maintenance workflow",
                    "owner": "mirror",
                    "local_revision": 0,
                    "feature_dependencies": [],
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": [],
                }
            },
        }
        plan = feature_reconciliation.plan_upgrade(
            base,
            current,
            candidate,
            observed_capabilities=["structured-state-authority"],
        )
        self.assertEqual("proposal-only", plan["status"])
        self.assertFalse(plan["automatic_apply"])
        self.assertFalse(plan["automatic_local_feature_deletion"])
        self.assertEqual(1, len(plan["changes"]))
        change = plan["changes"][0]
        self.assertEqual("local-feature-overlap", change["kind"])
        self.assertEqual("keep-current", change["default_action"])
        self.assertTrue(change["requires_user_decision"])
        self.assertTrue(change["rollback_checkpoint_required"])

    def test_dependency_blocked_upgrade_keeps_current_behavior(self) -> None:
        base = {"schema_version": 1, "features": {}}
        current = {
            "schema_version": 1,
            "features": {
                "mail-summary": {
                    "version": "1.0.0",
                    "summary": "Mail summary",
                    "owner": "mirror",
                    "local_revision": 0,
                    "feature_dependencies": [],
                    "required_capabilities": [],
                    "optional_capabilities": [],
                }
            },
        }
        candidate = {
            "schema_version": 1,
            "features": {
                "mail-summary": {
                    "version": "2.0.0",
                    "summary": "Mail summary with inbox evidence",
                    "owner": "mirror",
                    "local_revision": 0,
                    "feature_dependencies": [],
                    "required_capabilities": ["email-evidence"],
                    "optional_capabilities": [],
                }
            },
        }
        plan = feature_reconciliation.plan_upgrade(base, current, candidate)
        change = plan["changes"][0]
        self.assertEqual("dependency-blocked", change["kind"])
        self.assertEqual("keep-current", change["default_action"])
        self.assertEqual(["email-evidence"], change["missing_required"])

    def test_boomer_copy_hides_git_mechanics_and_mentions_rollback(self) -> None:
        plan = {
            "changes": [
                {
                    "feature": "meal-planning",
                    "current_version": "1.0.0",
                    "candidate_version": "2.0.0",
                    "reason": "The planning behavior changed.",
                    "missing_required": [],
                    "missing_optional": ["drive-evidence"],
                    "missing_required_help": [],
                    "missing_optional_help": ["Google Drive, OneDrive, or another evidence store"],
                }
            ],
            "consolidation_candidates": [],
        }
        text = feature_reconciliation.render_boomer(plan)
        self.assertIn("Nothing has been changed yet", text)
        self.assertIn("rollback checkpoint", text)
        self.assertIn("keep what you have", text)
        self.assertIn("Google Drive, OneDrive", text)
        self.assertIn("Your choices: keep mine, use the new version, or show me more detail.", text)
        self.assertNotIn("git rebase", text.lower())
        self.assertNotIn("three-way merge", text.lower())

    def test_semantic_prefilter_flags_overlap_but_never_auto_consolidates(self) -> None:
        current = {
            "schema_version": 1,
            "features": {
                "my-vehicle-care": {
                    "owner": "user",
                    "summary": "vehicle maintenance receipts reminders service",
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": ["receipt-evidence"],
                }
            },
        }
        candidate = {
            "schema_version": 1,
            "features": {
                "equipment-maintenance": {
                    "owner": "mirror",
                    "summary": "equipment maintenance receipts reminders service",
                    "required_capabilities": ["structured-state-authority"],
                    "optional_capabilities": ["receipt-evidence"],
                }
            },
        }
        rows = feature_reconciliation.find_consolidation_candidates(current, candidate)
        self.assertEqual(1, len(rows))
        self.assertEqual("keep-local", rows[0]["default"])
        self.assertTrue(rows[0]["requires_user_decision"])


if __name__ == "__main__":
    unittest.main()

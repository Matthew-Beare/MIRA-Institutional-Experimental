from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / "starter"


def _module():
    path = STARTER / "tools" / "integration_dependency_router.py"
    spec = importlib.util.spec_from_file_location("integration_dependency_router", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ROUTER = _module()
CONTRACTS = json.loads((STARTER / "behavior-dependencies.json").read_text(encoding="utf-8"))
WORKFLOWS = json.loads((STARTER / "integration-workflow-catalog.json").read_text(encoding="utf-8"))
CATALOG_PATH = ROOT / "docs" / "feature-catalog.json"
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8")) if CATALOG_PATH.is_file() else None


class IntegrationDependencyRouterTests(unittest.TestCase):
    def registry(
        self,
        *,
        enabled: list[str] | None = None,
        integrations: list[dict] | None = None,
        goals: list[dict] | None = None,
        direct: list[str] | None = None,
        authorities: list[str] | None = None,
    ) -> dict:
        return {
            "schema_version": 1,
            "enabled_behaviors": enabled or [],
            "available_behaviors": sorted(CONTRACTS["assignments"]),
            "available_authorities": authorities or [],
            "direct_verified_capabilities": direct or [],
            "integrations": integrations or [],
            "goals": goals or [],
            "active_workflow_ids": [],
            "dismissed_workflow_ids": [],
        }

    def test_advertised_plugin_capability_does_not_count_as_verified(self) -> None:
        registry = self.registry(
            integrations=[
                {
                    "id": "wearable-one",
                    "display_name": "Example Watch",
                    "connection_state": "connected",
                    "verified_capabilities": [],
                    "advertised_capabilities": ["wearable_read"],
                }
            ]
        )
        environment = ROUTER.build_environment(registry, CONTRACTS)
        self.assertNotIn("wearable_read", environment["available_capabilities"])

    def test_verified_connected_wearable_and_explicit_goal_create_bounded_prompt(self) -> None:
        registry = self.registry(
            integrations=[
                {
                    "id": "garmin-example",
                    "display_name": "Garmin smartwatch",
                    "connection_state": "connected",
                    "verified_capabilities": ["wearable_read"],
                    "advertised_capabilities": ["wearable_read"],
                }
            ],
            goals=[
                {
                    "id": "fitness-goal",
                    "label": "fitness goals",
                    "active": True,
                    "tags": ["fitness"],
                }
            ],
        )
        recommendations = ROUTER.recommend_workflows(registry, CONTRACTS, WORKFLOWS)
        wearable = next(row for row in recommendations if row["id"] == "wearable-fitness-support")
        self.assertIn("Garmin smartwatch", wearable["prompt"])
        self.assertIn("fitness goals", wearable["prompt"])
        self.assertTrue(wearable["requires_confirmation"])
        self.assertFalse(wearable["automatic_enablement"])

    def test_connected_integration_does_not_trigger_goal_inference(self) -> None:
        registry = self.registry(
            integrations=[
                {
                    "id": "wearable-one",
                    "display_name": "Example Watch",
                    "connection_state": "connected",
                    "verified_capabilities": ["wearable_read"],
                    "advertised_capabilities": ["wearable_read"],
                }
            ]
        )
        self.assertEqual([], ROUTER.recommend_workflows(registry, CONTRACTS, WORKFLOWS))

    def test_disconnected_integration_capability_does_not_satisfy_dependency(self) -> None:
        registry = self.registry(
            integrations=[
                {
                    "id": "finance-one",
                    "display_name": "Example Finance",
                    "connection_state": "disconnected",
                    "verified_capabilities": ["finance_read"],
                    "advertised_capabilities": ["finance_read"],
                }
            ]
        )
        environment = ROUTER.build_environment(registry, CONTRACTS)
        self.assertNotIn("finance_read", environment["available_capabilities"])

    def test_missing_dependency_gets_boomer_safe_help_and_decline_paths(self) -> None:
        registry = self.registry(
            enabled=["c-06"],
            direct=["structured_state_read", "structured_state_write", "structured_state_readback", "source_read"],
            authorities=["purchase-receipt-archive", "source-repository"],
        )
        result = ROUTER.review(registry, CONTRACTS, WORKFLOWS, CATALOG)
        receipt = result["dependency_readiness"]["behaviors"]["c-06"]
        self.assertEqual("blocked", receipt["status"])
        self.assertTrue(receipt["remediation"])
        card = receipt["remediation"][0]
        self.assertEqual("Do you need help setting this up?", card["help_question"])
        self.assertLessEqual(len(card["guided_setup"]), 5)
        self.assertIn("will stay unavailable", card["decline_message"])
        self.assertIn("Tell me when it is ready", card["decline_message"])
        self.assertFalse(card["automatic_install"])
        self.assertFalse(card["automatic_enablement"])

    def test_verified_drive_style_capabilities_remove_required_receipt_block(self) -> None:
        registry = self.registry(
            enabled=["c-06"],
            direct=["structured_state_read", "structured_state_write", "structured_state_readback", "source_read"],
            authorities=["purchase-receipt-archive", "evidence-store", "source-repository"],
            integrations=[
                {
                    "id": "drive-example",
                    "display_name": "Google Drive",
                    "connection_state": "connected",
                    "verified_capabilities": ["evidence_read", "evidence_write", "evidence_readback"],
                    "advertised_capabilities": ["evidence_read", "evidence_write", "evidence_readback"],
                }
            ],
        )
        result = ROUTER.review(registry, CONTRACTS, WORKFLOWS, CATALOG)
        receipt = result["dependency_readiness"]["behaviors"]["c-06"]
        self.assertNotEqual("blocked", receipt["status"])
        self.assertEqual([], receipt["missing_required_capabilities"])
        self.assertEqual([], receipt["missing_required_authorities"])

    def test_finance_capability_can_propose_goal_matched_workflow_without_enabling_it(self) -> None:
        registry = self.registry(
            integrations=[
                {
                    "id": "finance-example",
                    "display_name": "Connected card accounts",
                    "connection_state": "connected",
                    "verified_capabilities": ["finance_read"],
                    "advertised_capabilities": ["finance_read"],
                }
            ],
            goals=[
                {
                    "id": "saving",
                    "label": "saving more money",
                    "active": True,
                    "tags": ["saving"],
                }
            ],
        )
        recommendations = ROUTER.recommend_workflows(registry, CONTRACTS, WORKFLOWS)
        finance = next(row for row in recommendations if row["id"] == "finance-spending-support")
        self.assertIn("Connected card accounts", finance["prompt"])
        self.assertFalse(finance["automatic_enablement"])

    def test_workflow_catalog_references_only_known_behaviors(self) -> None:
        recommendations = ROUTER.recommend_workflows(self.registry(), CONTRACTS, WORKFLOWS)
        self.assertEqual([], recommendations)
        known = set(CONTRACTS["assignments"])
        for workflow in WORKFLOWS["workflows"]:
            self.assertTrue(set(workflow["behavior_ids"]).issubset(known))

    def test_review_keeps_full_behavior_database_valid_when_catalog_is_present(self) -> None:
        registry = self.registry()
        result = ROUTER.review(registry, CONTRACTS, WORKFLOWS, CATALOG)
        self.assertEqual(123, len(CONTRACTS["assignments"]))
        if CATALOG is not None:
            audit = ROUTER.CHECKER.audit_catalog(CONTRACTS, CATALOG)
            self.assertEqual(123, audit["behavior_count"])
            self.assertTrue(audit["complete"])
        self.assertEqual(1, result["schema_version"])
        self.assertTrue(result["policy"]["verified_capabilities_only"])
        self.assertTrue(result["policy"]["explicit_user_goals_only"])


if __name__ == "__main__":
    unittest.main()

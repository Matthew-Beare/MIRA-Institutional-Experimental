from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / "starter"
CATALOG_PATH = ROOT / "docs" / "feature-catalog.json"


def _module():
    path = STARTER / "tools" / "behavior_dependency_check.py"
    spec = importlib.util.spec_from_file_location("behavior_dependency_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


CHECKER = _module()
CONTRACTS = json.loads((STARTER / "behavior-dependencies.json").read_text(encoding="utf-8"))
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8")) if CATALOG_PATH.is_file() else None


class BehaviorDependencyCheckTests(unittest.TestCase):
    def environment(
        self,
        enabled: list[str],
        *,
        missing_capabilities: set[str] | None = None,
        missing_authorities: set[str] | None = None,
        missing_behaviors: set[str] | None = None,
    ) -> dict:
        missing_capabilities = missing_capabilities or set()
        missing_authorities = missing_authorities or set()
        missing_behaviors = missing_behaviors or set()
        return {
            "schema_version": 1,
            "enabled_behaviors": enabled,
            "available_behaviors": sorted(set(CONTRACTS["assignments"]) - missing_behaviors),
            "available_capabilities": sorted(set(CONTRACTS["capability_labels"]) - missing_capabilities),
            "available_authorities": sorted(set(CONTRACTS["authority_labels"]) - missing_authorities),
        }

    @unittest.skipUnless(CATALOG is not None, "canonical forensic catalog is not shipped in generated distributions")
    def test_every_forensic_catalog_behavior_has_a_dependency_assignment(self) -> None:
        assert CATALOG is not None
        result = CHECKER.audit_catalog(CONTRACTS, CATALOG)
        self.assertTrue(result["complete"])
        self.assertEqual(123, result["behavior_count"])
        self.assertEqual(result["behavior_count"], result["dependency_assignment_count"])

    def test_receipt_intake_has_explicit_state_evidence_and_optional_ingestion_dependencies(self) -> None:
        receipt = CHECKER.resolve_behavior("c-06", CONTRACTS)
        self.assertIn("purchase-receipt-archive", receipt["required_authorities"])
        self.assertIn("evidence-store", receipt["required_authorities"])
        self.assertTrue(
            {"structured_state_read", "structured_state_write", "structured_state_readback"}.issubset(
                set(receipt["required_capabilities"])
            )
        )
        self.assertTrue(
            {"email_read", "file_import", "image_evidence_read", "ocr_candidate_extraction"}.issubset(
                set(receipt["optional_capabilities"])
            )
        )

    def test_scheduling_has_explicit_scheduler_clock_state_and_run_log_dependencies(self) -> None:
        scheduling = CHECKER.resolve_behavior("a-01", CONTRACTS)
        self.assertTrue(
            {"scheduled_dispatch", "canonical_clock_gate"}.issubset(
                set(scheduling["required_capabilities"])
            )
        )
        self.assertTrue(
            {"ops-status-register", "run-log", "scheduler", "source-repository"}.issubset(
                set(scheduling["required_authorities"])
            )
        )

    def test_missing_required_receipt_dependency_blocks_only_that_enabled_behavior(self) -> None:
        environment = self.environment(["c-06", "b-08"], missing_capabilities={"evidence_write"})
        result = CHECKER.evaluate(CONTRACTS, environment, CATALOG)
        self.assertFalse(result["ready"])
        self.assertEqual(["c-06"], result["blocked_behaviors"])
        self.assertEqual("blocked", result["behaviors"]["c-06"]["status"])
        self.assertEqual("ready", result["behaviors"]["b-08"]["status"])
        self.assertIn("unrelated workflows stay as they are", result["behaviors"]["c-06"]["prompt"])

    def test_missing_optional_email_dependency_degrades_without_blocking(self) -> None:
        environment = self.environment(
            ["c-02"],
            missing_capabilities={"email_read"},
            missing_authorities={"email"},
        )
        result = CHECKER.evaluate(CONTRACTS, environment, CATALOG)
        self.assertTrue(result["ready"])
        self.assertEqual(["c-02"], result["degraded_behaviors"])
        self.assertEqual("degraded", result["behaviors"]["c-02"]["status"])

    def test_aggregate_service_blocks_when_required_behavior_is_not_available(self) -> None:
        environment = self.environment(["f-05"], missing_behaviors={"c-06"})
        result = CHECKER.evaluate(CONTRACTS, environment, CATALOG)
        self.assertEqual(["f-05"], result["blocked_behaviors"])
        self.assertIn("c-06", result["behaviors"]["f-05"]["missing_required_behaviors"])

    @unittest.skipUnless(CATALOG is not None, "canonical forensic catalog is not shipped in generated distributions")
    def test_catalog_drift_fails_until_new_behavior_gets_dependencies(self) -> None:
        assert CATALOG is not None
        contracts = copy.deepcopy(CONTRACTS)
        contracts["assignments"].pop("c-06")
        with self.assertRaises(CHECKER.DependencyContractError):
            CHECKER.audit_catalog(contracts, CATALOG)

    def test_template_onboarding_is_dependency_checked(self) -> None:
        onboarding = CHECKER.resolve_behavior("e-21", CONTRACTS)
        self.assertIn("template_repository", onboarding["required_capabilities"])
        self.assertIn("source-repository", onboarding["required_authorities"])

    def test_dependency_engine_never_installs_or_enables_automatically(self) -> None:
        CHECKER.validate_contracts(CONTRACTS)
        policy = CONTRACTS["policy"]
        self.assertFalse(policy["automatic_dependency_install"])
        self.assertFalse(policy["automatic_behavior_enablement"])
        self.assertTrue(policy["user_in_the_loop"])


if __name__ == "__main__":
    unittest.main()

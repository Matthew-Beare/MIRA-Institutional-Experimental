from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FailureDomainArchitectureTests(unittest.TestCase):
    def text(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def manifest(self, feature_id: str) -> dict:
        return json.loads(self.text(f"starter/features/{feature_id}/feature.json"))

    def test_state_model_separates_canonical_identity_from_physical_failure_domains(self) -> None:
        state = self.text("starter/STATE_AUTHORITY_MODEL.md")
        self.assertIn("One canonical authority per data class does not mean one giant workbook", state)
        self.assertIn("Recommended production resource boundaries", state)
        self.assertIn("Core Ops authority", state)
        self.assertIn("Commerce authority", state)
        self.assertIn("Mileage/Pay authority", state)
        self.assertIn("provider-wide outage", state.lower())
        self.assertIn("Recovery snapshots", state)
        self.assertIn("never a second writable master", state)

    def test_dependency_contract_is_machine_readable_and_acyclic_by_policy(self) -> None:
        deps = self.text("starter/DEPENDENCIES.md")
        self.assertIn("manifest contract v3", deps)
        self.assertIn("failure_domain", deps)
        self.assertIn("required_capabilities", deps)
        self.assertIn("optional_capabilities", deps)
        self.assertIn("cross_module_writes", deps)
        self.assertIn("acyclic graph", deps)
        self.assertIn("block-module-only", deps)
        self.assertIn("degrade-capability-and-continue", deps)

    def test_ci_checks_declared_live_feature_files(self) -> None:
        ci = self.text(".github/workflows/ci.yml")
        self.assertIn("validate_feature_manifest.py --check-files", ci)

    def test_live_features_have_explicit_cross_module_write_contracts(self) -> None:
        meal = self.manifest("meal-planning")["runtime_contract"]
        appointment = self.manifest("appointment-reconciliation")["runtime_contract"]
        for runtime in (meal, appointment):
            self.assertFalse(set(runtime["required_capabilities"]) & set(runtime["optional_capabilities"]))
            self.assertEqual(runtime["on_required_failure"], "block-module-only")
            self.assertEqual(runtime["on_optional_failure"], "degrade-capability-and-continue")
        self.assertEqual(meal["failure_domain"], "meal-planning")
        self.assertEqual(meal["cross_module_writes"], ["shopping-procurement:upsert-meal-plan-intent"])
        self.assertEqual(appointment["failure_domain"], "appointments")
        self.assertEqual(appointment["cross_module_writes"], [])

    def test_reference_deployment_has_separate_core_commerce_and_mileage_authorities(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        brief = self.text("skill/ops-brief-policy/references/brief-run.md")
        self.assertIn("Core Ops", skill)
        self.assertIn("Mileage/Pay", skill)
        self.assertIn("Commerce", skill)
        self.assertIn("Mileage/pay is section-scoped", brief)
        self.assertIn("If the receipt workbook is unavailable", brief)
        self.assertIn("Calendar is non-authoritative evidence", brief)

    def test_receipt_core_commit_is_not_distributed_transaction(self) -> None:
        receipt = self.text("skill/ops-brief-policy/references/receipt-ingestion.md")
        self.assertIn("Failure-domain boundary", receipt)
        self.assertIn("Commit canonical purchase state first", receipt)
        self.assertIn("core receipt Audit", receipt)
        self.assertIn("does not depend on Ops Shipments", receipt)
        self.assertIn("shipment projection Degraded/Pending", receipt)
        self.assertIn("does not roll back the core receipt", receipt)

    def test_email_lifecycle_commits_commerce_before_ops_projection(self) -> None:
        email = self.text("skill/ops-brief-policy/references/email-reconciliation.md")
        self.assertIn("canonical append-only lifecycle history", email)
        self.assertIn("active fulfillment **projection/working queue**", email)
        self.assertIn("Commit/read back a supported lifecycle event", email)
        self.assertIn("mark only shipment projection `Degraded/Pending`", email)
        self.assertIn("Source-first transaction order", email)
        self.assertIn("A shipment projection failure does not roll back commerce", email)

    def test_asset_and_knowledge_links_are_source_first(self) -> None:
        asset = self.text("skill/ops-brief-policy/references/asset-acquisition.md")
        knowledge = self.text("skill/ops-brief-policy/references/knowledge-manual-ingestion.md")
        self.assertIn("Failure-domain boundary", asset)
        self.assertIn("create/enrich the canonical asset UUID and read it back before mutating another authority", asset)
        self.assertIn("Receipt/manual/warranty relationships that cross another authority are separate projection-health checks", asset)
        self.assertIn("Failure-domain boundary", knowledge)
        self.assertIn("required internal capabilities of the knowledge/manual module", knowledge)
        self.assertIn("failure to update an external asset/receipt/project relationship does not roll back", knowledge)
        self.assertIn("source-first", knowledge)

    def test_automation_contract_forbids_cross_authority_rollback(self) -> None:
        automation = self.text("docs/automation-contracts.md")
        self.assertIn("Cross-authority transaction isolation", automation)
        self.assertIn("commit the canonical source mutation first", automation)
        self.assertIn("Never roll back, clone, renumber, or delete canonical source identity", automation)
        self.assertIn("a failed Ops Brief phase does not roll back a successful receipt/order lifecycle", automation)
        self.assertIn("failed lifecycle/job phase does not block a safe brief", automation)

    def test_circuit_breaker_continues_unrelated_modules(self) -> None:
        breaker = self.text("skill/ops-brief-policy/references/module-circuit-breaker-report.md")
        self.assertIn("Stop writes for the affected module", breaker)
        self.assertIn("Continue unrelated modules", breaker)
        self.assertIn("Never create child/retry automations", breaker)


if __name__ == "__main__":
    unittest.main()

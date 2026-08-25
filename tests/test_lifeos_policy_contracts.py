from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LifeOSPolicyContractTests(unittest.TestCase):
    def text(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_public_upstream_has_license_and_external_state_boundary(self) -> None:
        readme = self.text("README.md")
        license_text = self.text("LICENSE")
        self.assertIn("intentionally public", readme)
        self.assertIn("starter/START_HERE.md", readme)
        self.assertIn("Mutable operational state", readme)
        self.assertIn("Google Sheets", readme)
        self.assertIn("Google Drive", readme)
        self.assertIn("reference deployment", readme)
        self.assertIn("public-source audit", readme)
        self.assertIn("MIT License", license_text)
        self.assertIn("Permission is hereby granted", license_text)

    def test_starter_separates_git_source_from_mutable_state(self) -> None:
        guide = self.text("starter/START_HERE.md")
        deps = self.text("starter/DEPENDENCIES.md")
        versioning = self.text("starter/VERSIONING.md")
        template = self.text("starter/INSTRUCTIONS.md.tmpl")
        state = self.text("starter/STATE_AUTHORITY_MODEL.md")
        config = json.loads(self.text("starter/config.example.json"))
        for surface in (guide, deps, versioning, template, state):
            self.assertIn("Git", surface)
            self.assertIn("state", surface.lower())
        self.assertIn("Google Sheets", state)
        self.assertIn("Google Drive", state)
        self.assertIn("Authority Registry", state)
        self.assertIn("Interview Ledger", guide)
        self.assertIn("public-source audit", guide.lower())
        self.assertIn("{{REPOSITORY_VISIBILITY}}", template)
        self.assertEqual(config["STATE_STORE"], "GOOGLE_SHEETS_DEFAULT_OR_SUPPORTED_DATABASE")
        self.assertEqual(config["AUTHORITY_REGISTRY"], "REQUIRED_IN_STRUCTURED_STATE_STORE")
        self.assertEqual(config["INTERVIEW_LEDGER"], "REQUIRED_IN_STRUCTURED_STATE_STORE")
        self.assertNotIn("PRIVATE_GIT_REPOSITORY/state", json.dumps(config))

    def test_interview_ledger_is_complete_fail_forward_and_upgradeable(self) -> None:
        ledger = self.text("starter/INTERVIEW_LEDGER.md")
        for phrase in (
            "Unresolved",
            "Asked",
            "Answered",
            "Resolved from evidence",
            "Not applicable",
            "Deferred",
            "answer the user's immediate request normally",
            "Question-bank upgrades",
        ):
            self.assertIn(phrase, ledger)
        self.assertIn("every question", ledger.lower())
        self.assertIn("not on every turn", ledger.lower())
        self.assertIn("Preferences and consent are not silently inferred", ledger)

    def test_shared_state_is_explicit_and_separate_from_feature_sharing(self) -> None:
        state = self.text("starter/STATE_AUTHORITY_MODEL.md")
        shared = self.text("starter/SHARED_FEATURE_WORKFLOW.md")
        self.assertIn("Whole-authority sharing", state)
        self.assertIn("Scoped shared authority", state)
        self.assertIn("Never infer that a family member should receive access", state)
        self.assertIn("Sharing state and sharing a feature are different operations", state)
        self.assertIn("synthetic fixtures", shared.lower())
        self.assertIn("Sheet", shared)
        self.assertIn("Drive", shared)

    def test_public_source_audit_and_ci_are_release_gates(self) -> None:
        audit = self.text("scripts/audit_public_source.py")
        ci = self.text(".github/workflows/ci.yml")
        gitignore = self.text(".gitignore")
        self.assertIn("audit_history", audit)
        self.assertIn("CARD_CANDIDATE", audit)
        self.assertIn("BLOCKED_FILENAMES", audit)
        self.assertIn("SCAN_EXEMPT_PATHS", audit)
        self.assertIn("fetch-depth: 0", ci)
        self.assertIn("scripts/audit_public_source.py . --history", ci)
        self.assertIn("scripts/audit_starter_privacy.py starter", ci)
        self.assertIn("scripts/validate_repo.py .", ci)
        self.assertIn(".env", gitignore)
        self.assertIn("*.sqlite", gitignore)

    def test_beta_audit_distinguishes_clean_and_legacy_history(self) -> None:
        audit = self.text("docs/beta-hardening-audit-2026-08-24.md")
        self.assertIn("Clean-history release: pass", audit)
        self.assertIn("Clean reachable-history privacy audit passes", audit)
        self.assertIn("no longer reachable from a named branch", audit.lower())
        self.assertIn("next real 2:45", audit.lower())

    def test_project_bootstrap_is_stable_and_git_indirected(self) -> None:
        project = self.text("project/INSTRUCTIONS.md.tmpl")
        self.assertIn("BOOTSTRAP_CONTRACT_VERSION: 4", project)
        self.assertIn("project/POLICY_FINGERPRINT.txt", project)
        self.assertNotIn("POLICY_SOURCE_FINGERPRINT:", project)

    def test_skill_agent_metadata_uses_supported_interface_contract(self) -> None:
        metadata = self.text("skill/ops-brief-policy/agents/openai.yaml")
        self.assertIn('display_name: "Ops Brief Policy"', metadata)
        self.assertIn('icon_small: "./assets/icon.svg"', metadata)
        self.assertIn('icon_large: "./assets/icon.svg"', metadata)
        self.assertIn('default_prompt: "Use $ops-brief-policy', metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)
        self.assertNotIn("products:", metadata)

    def test_scheduler_uses_evidence_chain_canonical_clock_and_entry_run_log(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        maintenance = self.text("skill/ops-brief-policy/references/state-maintenance.md")
        brief = self.text("skill/ops-brief-policy/references/brief-run.md")
        docs = self.text("docs/automation-contracts.md")
        deps = self.text("starter/DEPENDENCIES.md")
        interview = self.text("starter/LIFE_INTERVIEW.md")
        runtime = self.text("skill/ops-brief-policy/scripts/ops_policy.py")
        for surface in (skill, maintenance, docs, deps, interview):
            lower = surface.lower()
            self.assertIn("notification", lower)
            self.assertIn("duplicate", lower)
            self.assertTrue(
                any(term in lower for term in ("actual firing", "actual scheduled firing", "observed firing", "observed execution")),
                "scheduler surface lacks observed execution evidence",
            )
            self.assertTrue(
                "provider contract" in lower or "provider/tool contract" in lower,
                "scheduler surface does not condition provider metadata on documented semantics",
            )
            self.assertIn("iana", lower)
        self.assertIn("ZoneInfo", runtime)
        self.assertIn("canonical_slot_evidence", runtime)
        self.assertIn("live_slot_evidence", runtime)
        self.assertIn("runtime_system_clock", runtime)
        self.assertIn("America/New_York", runtime)
        self.assertIn("default_timezone", skill)
        self.assertIn("default_timezone", maintenance)
        self.assertIn("first external", skill.lower())
        self.assertIn("`Running`", skill)
        self.assertIn("Before Gmail", brief)
        self.assertIn("`Running`", brief)
        self.assertIn("slot-check", brief)
        self.assertIn("without `--now`", brief)
        self.assertIn("runtime_system_clock", brief)
        self.assertIn("deterministic Run ID", brief)
        self.assertIn("12:45-06:00", maintenance)

    def test_single_control_cycle_consolidates_lifecycle_jobs_and_brief(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        cycle = self.text("skill/ops-brief-policy/references/consolidated-cycle.md")
        jobs = self.text("skill/ops-brief-policy/references/qualified-job-watch.md")
        maintenance = self.text("skill/ops-brief-policy/references/state-maintenance.md")
        docs = self.text("docs/automation-contracts.md")
        project = self.text("project/INSTRUCTIONS.md.tmpl")
        for surface in (skill, maintenance, docs, project):
            self.assertIn("LyfeOS Control Cycle", surface)
        self.assertIn("Exactly one active **standalone** `LyfeOS Control Cycle`", skill)
        self.assertIn("one newly generated user-facing Ops Brief", cycle)
        self.assertIn("without `--now`", cycle)
        self.assertIn("quote old responses", cycle.lower())
        self.assertIn("PM qualified-job watch", cycle)
        self.assertIn("Job Watch", jobs)
        self.assertIn("Job Watch Settings", jobs)
        self.assertIn("candidate_qualifications", jobs)
        self.assertIn("Never hard-code", jobs)
        self.assertIn("private deployment state", jobs)
        self.assertIn("Never apply, reply, contact anyone, send email", jobs)

    def test_module_circuit_breaker_is_fail_fast_and_module_scoped(self) -> None:
        policy = self.text("skill/ops-brief-policy/references/module-circuit-breaker-report.md")
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        self.assertIn("# Module Circuit Breaker Report", policy)
        self.assertIn("Retry is **not mandatory**", policy)
        self.assertIn("same external operation fails twice", policy)
        self.assertIn("Stop writes for the affected module", policy)
        self.assertIn("Continue unrelated modules", policy)
        self.assertIn("never blind-rerun", policy)
        self.assertIn("never create hidden retry jobs", skill)

    def test_terminal_paid_miles_are_symmetric_in_reference_deployment(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        maintenance = self.text("skill/ops-brief-policy/references/state-maintenance.md")
        brief = self.text("skill/ops-brief-policy/references/brief-run.md")
        compatibility = self.text("policy/ops-brief-policy.yaml")
        platform = self.text("docs/data-platform-grafana.md")
        self.assertIn("Paid terminal mileage is symmetric", skill)
        self.assertIn("same paid-mile value", maintenance)
        self.assertIn("symmetric by canonical terminal pair", brief)
        self.assertIn("terminal_paid_miles_symmetric_by_pair: true", compatibility)
        self.assertIn("terminal_paid_miles_directional: false", compatibility)
        self.assertNotIn("never mirrors automatically", platform.lower())

    def test_carrier_retention_is_narrow_and_includes_usps(self) -> None:
        policy = self.text("skill/ops-brief-policy/references/email-reconciliation.md")
        self.assertIn("90 calendar days", policy)
        self.assertIn("FedEx, UPS, DHL and USPS", policy)
        self.assertIn("carrier-originated FedEx/UPS/DHL/USPS", policy)
        self.assertIn("merchant order confirmation", policy.lower())
        self.assertIn("open return, claim, dispute", policy)

    def test_asset_and_knowledge_identity_are_immutable_uuid_based(self) -> None:
        asset = self.text("skill/ops-brief-policy/references/asset-acquisition.md")
        manual = self.text("skill/ops-brief-policy/references/knowledge-manual-ingestion.md")
        schema = self.text("docs/household-financial-reconciliation.md")
        self.assertIn("immutable RFC 4122 UUID", asset)
        self.assertIn("collision-resistant across deployments/family members", asset)
        self.assertIn("immutable RFC 4122 UUID", manual)
        self.assertIn("Knowledge Index", manual)
        self.assertIn("Entity UUID", schema)
        self.assertIn("Friendly", schema)

    def test_receipt_inventory_uses_exact_line_and_explicit_uuid_edges(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        receipt = self.text("skill/ops-brief-policy/references/receipt-ingestion.md")
        asset = self.text("skill/ops-brief-policy/references/asset-acquisition.md")
        data_model = self.text("docs/lyfeos-data-model.md")
        runtime = self.text("skill/ops-brief-policy/scripts/inventory_reconciliation.py")
        for surface in (skill, receipt, asset, data_model):
            self.assertIn("assigned_to", surface)
            self.assertIn("installed_on", surface)
        self.assertIn("exact receipt line", asset)
        self.assertIn("Asset Relationships", data_model)
        self.assertIn("receipt_line_intents", runtime)
        self.assertIn("relationship_uuid", runtime)

    def test_calendar_projection_updates_in_place_without_task_fanout(self) -> None:
        calendar = self.text("skill/ops-brief-policy/references/calendar-projection.md")
        design = self.text("docs/automation-design.md")
        self.assertIn("Google Calendar event ID", calendar)
        self.assertIn("update the linked event in place", calendar)
        self.assertIn("order delivery dates/windows", calendar)
        self.assertIn("not a per-order automation", design.lower())
        self.assertIn("never creates per-order scheduled tasks", design.lower())

    def test_shopping_procurement_is_active_list_not_purchase_history(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        receipt = self.text("skill/ops-brief-policy/references/receipt-ingestion.md")
        catalog = self.text("starter/MODULE_CATALOG.md")
        for surface in (skill, receipt, catalog):
            self.assertIn("active shopping list", surface)
            self.assertIn("remove the fulfilled shopping row", surface)
        self.assertIn("explicit owner", receipt)
        self.assertIn("separate reconciliation task", receipt)
        self.assertIn("Purchased` tombstone", receipt)
        self.assertIn("cancellation with no supported replacement", receipt)

    def test_payment_and_reimbursement_semantics_remain_separate(self) -> None:
        payment = self.text("skill/ops-brief-policy/references/payment-reconciliation.md")
        reimbursement = self.text("skill/ops-brief-policy/references/household-reimbursement.md")
        self.assertIn("Awaiting Settlement", payment)
        self.assertIn("Overcharged", payment)
        self.assertIn("unmatched", payment.lower())
        self.assertIn("A reimbursement is not a merchant refund", reimbursement)
        self.assertIn("Net Household Cost", reimbursement)

    def test_life_planning_supports_accountability_study_and_context_variants(self) -> None:
        policy = self.text("skill/ops-brief-policy/references/life-planning-accountability.md")
        interview = self.text("starter/LIFE_INTERVIEW.md")
        catalog = self.text("starter/MODULE_CATALOG.md")
        self.assertIn("Routine accountability", policy)
        self.assertIn("Exercise / fitness organization", policy)
        self.assertIn("School / study workflow", policy)
        self.assertIn("Next-action planner", policy)
        self.assertIn("Do you regularly work away from home", interview)
        self.assertIn("minimum viable version", interview)
        self.assertIn("home versus away/on the road", interview)
        self.assertIn("Personal accountability and routines", catalog)
        self.assertIn("Education and study coach", catalog)

    def test_meal_planning_and_appointment_features_use_external_authority(self) -> None:
        meal = self.text("starter/features/meal-planning/FEATURE.md")
        appointment = self.text("starter/features/appointment-reconciliation/FEATURE.md")
        meal_manifest = json.loads(self.text("starter/features/meal-planning/feature.json"))
        appointment_manifest = json.loads(self.text("starter/features/appointment-reconciliation/feature.json"))
        self.assertIn("Google Sheets", meal)
        self.assertIn("Drive", meal)
        self.assertIn("official clinic/provider pages", appointment)
        self.assertIn("Cardiology", appointment)
        self.assertIn("morning-of", appointment)
        self.assertIn("60 minutes before", appointment)
        self.assertIn("IANA timezone", appointment)
        self.assertEqual(meal_manifest["data_boundary"]["runtime_state"], "external-authority")
        self.assertEqual(appointment_manifest["data_boundary"]["runtime_state"], "external-authority")

    def test_starter_is_bounded_nontechnical_deep_and_discovery_driven(self) -> None:
        guide = self.text("starter/START_HERE.md")
        questions = json.loads(self.text("starter/questions.json"))
        rows = [q for section in questions["sections"] for q in section["questions"]]
        ids = {q["id"] for q in rows}
        self.assertIn("non-technical user", guide)
        self.assertIn("Minimum Useful Setup", guide)
        self.assertIn("Start now by asking only the four kickoff questions", guide)
        self.assertIn("mark HOME/ROAD bypassed", guide)
        self.assertIn("driving/trucking", guide.lower())
        self.assertIn("Do you want help with meal planning?", guide)
        self.assertIn("Interview Ledger", guide)
        self.assertLess(len(guide), 12000)
        self.assertGreaterEqual(len(rows), 100)
        self.assertGreaterEqual(questions["version"], 6)
        for required in (
            "works_away_from_home",
            "accountability_domains",
            "routine_progression",
            "education_active",
            "study_home_away",
            "study_next_action_rule",
            "scheduler_timezone_integrity",
            "repository_visibility",
            "public_source_policy",
            "employment_status",
            "retired_support",
            "hiking_outdoors",
            "vacation_planning",
            "meal_planning_help",
            "existing_meal_plans",
            "fitness_wearable",
            "medical_event_tracking",
            "appointment_email_auto_update",
            "git_state_commit_policy",
            "canonical_clock_guard",
            "authority_registry",
            "interview_ledger",
            "interview_resume_policy",
            "shared_authority",
            "appointment_provider_type_research",
            "appointment_reminder_day_before",
            "appointment_reminder_morning_of",
            "appointment_reminder_relative",
        ):
            self.assertIn(required, ids)

    def test_public_blocklist_does_not_republish_private_markers(self) -> None:
        blocklist = self.text("privacy/starter-blocklist.txt")
        self.assertIn("untracked local blocklist", blocklist)
        markers = [
            line.strip()
            for line in blocklist.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        self.assertEqual([], markers)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PersonalForkLifecycleTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def manifest(self, feature_id: str) -> dict:
        return json.loads(self.text(f"features/{feature_id}/feature.json"))

    def test_first_boot_separates_git_source_from_mutable_state(self) -> None:
        guide = self.text("START_HERE.md")
        lifecycle = self.text("PERSONAL_FORK_LIFECYCLE.md")
        versioning = self.text("VERSIONING.md")
        state = self.text("STATE_AUTHORITY_MODEL.md")
        for surface in (guide, lifecycle, versioning, state):
            self.assertIn("Git", surface)
        self.assertIn("Google Sheets", state)
        self.assertIn("Google Drive", state)
        self.assertIn("Routine mutable state changes do not create Git commits", versioning)
        self.assertIn("Routine state changes happen in the canonical mutable authority, not Git", lifecycle)
        self.assertIn("Authority Registry", guide)
        self.assertIn("Interview Ledger", guide)

    def test_interview_is_fail_forward_and_complete_by_ledger(self) -> None:
        guide = self.text("START_HERE.md")
        ledger = self.text("INTERVIEW_LEDGER.md")
        interview = self.text("LIFE_INTERVIEW.md")
        for phrase in (
            "Answered",
            "Resolved from evidence",
            "Not applicable",
            "Deferred",
            "Unresolved",
        ):
            self.assertIn(phrase, ledger)
        self.assertIn("answer the user's immediate request normally", ledger)
        self.assertIn("end with", ledger)
        self.assertIn("do not silently abandon", guide.lower())
        self.assertIn("conversation detour", interview.lower())
        self.assertIn("every question", ledger.lower())

    def test_personal_feature_sharing_is_opt_in_and_excludes_state(self) -> None:
        phrase = "Do you want to make this feature available to other people?"
        guide = self.text("START_HERE.md")
        lifecycle = self.text("PERSONAL_FORK_LIFECYCLE.md")
        shared = self.text("SHARED_FEATURE_WORKFLOW.md")
        catalog = self.text("MODULE_CATALOG.md")
        for surface in (guide, lifecycle, shared, catalog):
            self.assertIn(phrase, surface)
        self.assertIn("synthetic fixtures", shared.lower())
        self.assertIn("Sheet", shared)
        self.assertIn("Drive", shared)
        self.assertIn("publication authority", shared.lower())

    def test_capability_discovery_reuses_authorities_and_connectors(self) -> None:
        discovery = self.text("CAPABILITY_DISCOVERY.md")
        deps = self.text("DEPENDENCIES.md")
        interview = self.text("LIFE_INTERVIEW.md")
        self.assertIn("Current conversation", discovery)
        self.assertIn("File Library", discovery)
        self.assertIn("Connected apps/tools/connectors", discovery)
        self.assertIn("Available plugins/apps", discovery)
        self.assertIn("Do not claim global access to arbitrary old ChatGPT conversations", discovery)
        self.assertIn("Before asking the user to connect anything", deps)
        self.assertIn("fitness/wearable", interview.lower())
        self.assertIn("one canonical structured authority per mutable data class", discovery)

    def test_meal_planning_is_first_class_and_external_authority_backed(self) -> None:
        guide = self.text("START_HERE.md")
        interview = self.text("LIFE_INTERVIEW.md")
        catalog = self.text("MODULE_CATALOG.md")
        feature = self.text("features/meal-planning/FEATURE.md")
        manifest = self.manifest("meal-planning")
        for surface in (guide, interview, catalog, feature):
            self.assertIn("meal planning", surface.lower())
        self.assertIn("Do you want help with meal planning?", guide)
        self.assertIn("shopping intent is not purchase history", feature.lower())
        self.assertIn("Google Sheets", feature)
        self.assertIn("Drive", feature)
        self.assertFalse(manifest["data_boundary"]["source_contains_personal_data"])
        self.assertEqual(manifest["data_boundary"]["runtime_state"], "external-authority")

    def test_appointment_provider_type_reminders_and_readback_are_verified(self) -> None:
        interview = self.text("LIFE_INTERVIEW.md")
        catalog = self.text("MODULE_CATALOG.md")
        feature = self.text("features/appointment-reconciliation/FEATURE.md")
        manifest = self.manifest("appointment-reconciliation")
        for phrase in (
            "provider type",
            "official clinic/provider pages",
            "day before",
            "morning-of",
            "60 minutes before",
            "read the Calendar event back",
            "canonical state back",
        ):
            self.assertIn(phrase.lower(), feature.lower())
        self.assertIn("cardiology", feature.lower())
        self.assertIn("one ChatGPT automation per appointment", catalog)
        self.assertIn("IANA timezone", feature)
        self.assertEqual(manifest["data_boundary"]["runtime_state"], "external-authority")
        self.assertFalse(manifest["data_boundary"]["source_contains_personal_data"])

    def test_optional_dependency_failures_are_module_scoped(self) -> None:
        discovery = self.text("CAPABILITY_DISCOVERY.md")
        deps = self.text("DEPENDENCIES.md")
        appointment = self.text("features/appointment-reconciliation/FEATURE.md")
        meal = self.text("features/meal-planning/FEATURE.md")
        self.assertIn("blocks only the dependent", deps)
        self.assertIn("Failure of one adapter must not disable basic meal planning", meal)
        self.assertIn("Each adapter fails independently", appointment)
        self.assertIn("one canonical structured authority per mutable data class", discovery)

    def test_interview_discovers_retirement_hobbies_meals_and_medical_event_organization(self) -> None:
        questions = json.loads(self.text("questions.json"))
        rows = [q for section in questions["sections"] for q in section["questions"]]
        ids = {q["id"] for q in rows}
        for required in (
            "employment_status",
            "retired_support",
            "hiking_outdoors",
            "vacation_planning",
            "meal_planning_help",
            "existing_meal_plans",
            "fitness_wearable",
            "medical_event_tracking",
            "appointment_email_auto_update",
            "deployment_lane",
            "ai_runtime",
            "data_classification",
            "organization_approval",
            "source_control_mode",
            "provider_capability_readback",
        ):
            self.assertIn(required, ids)
        self.assertGreaterEqual(questions["version"], 5)

    def test_portable_authorities_and_managed_source_are_explicit(self) -> None:
        questions = self.text("questions.json")
        lifecycle = self.text("PERSONAL_FORK_LIFECYCLE.md")
        state = self.text("STATE_AUTHORITY_MODEL.md")
        for phrase in ("Claude", "Microsoft Lists/Excel", "OneDrive/SharePoint", "regulated-sensitive"):
            self.assertIn(phrase, questions)
        for surface in (lifecycle, state):
            self.assertIn("managed central source", surface.lower())
            self.assertIn("organization", surface.lower())

    def test_profile_context_and_stock_service_extension_is_installed(self) -> None:
        guide = self.text("START_HERE.md")
        profile = self.text("PROFILE_AND_CONTEXT_MODES.md")
        config = json.loads(self.text("config.example.json"))
        extension = json.loads(self.text("questions.profile-and-stock-services.json"))
        extension_ids = {
            row["id"]
            for section in extension["sections"]
            for row in section["questions"]
        }
        for required in (
            "profile_roles",
            "profile_primary_role",
            "parent_guardian_support",
            "retiree_support",
            "profile_alias",
            "ai_usage_pattern",
            "briefs_enabled",
            "brief_notification_mode",
            "order_lifecycle_enabled",
            "order_update_slots",
            "order_notification_mode",
            "recipe_library_enabled",
            "recipe_sources",
            "household_routines_enabled",
            "appointment_reminders_enabled",
            "medication_reminders_enabled",
            "caregiver_reminder_sharing",
            "service_activation_states",
        ):
            self.assertIn(required, extension_ids)
        self.assertIn("private mutable profile", profile)
        self.assertIn("`retired` and `nonworking` are deliberately distinct", profile)
        self.assertIn("`parent_guardian`", profile)
        self.assertIn("first-class role", profile)
        self.assertIn("Personal Schedule & Wellbeing", profile)
        self.assertIn("Medication schedules require explicit", profile)
        self.assertIn("Driver/trucker/courier/delivery", profile)
        self.assertIn("does not mean implemented or silently enabled", profile)
        self.assertIn("how I currently use AI", guide)
        self.assertIn("stock-provisioned brief/action digest", guide)
        self.assertEqual(
            "PER_PERSON_LIFE_PROFILE_WITH_PRIVATE_USER_DEFINED_ALIAS",
            config["PROFILE_MODEL"],
        )
        for key in ("BRIEF_SERVICE", "ORDER_LIFECYCLE_SERVICE", "RECIPE_LIBRARY_SERVICE"):
            self.assertEqual("STOCK_PROVISIONED_USER_CONFIGURED_OR_DISABLED", config[key])

    def test_nontechnical_setup_precedes_interview_and_never_uses_local_git(self) -> None:
        install = self.text("INSTALL.md")
        guide = self.text("START_HERE.md")
        lifecycle = self.text("PERSONAL_FORK_LIFECYCLE.md")
        self.assertIn("browser-only", install)
        self.assertIn("ordinary ChatGPT GitHub app is read-only", install)
        self.assertIn("Codex write", install)
        self.assertIn("INSTALL.md", guide)
        self.assertIn("template copy", lifecycle)
        self.assertNotIn("fork/clone", lifecycle)

    def test_household_laundry_and_pickup_questions_are_explicit(self) -> None:
        questions = json.loads(self.text("questions.json"))
        rows = [q for section in questions["sections"] for q in section["questions"]]
        ids = {q["id"] for q in rows}
        self.assertTrue({
            "household_routine_help",
            "laundry_workflow",
            "dropoff_pickup_reminders",
        }.issubset(ids))


if __name__ == "__main__":
    unittest.main()

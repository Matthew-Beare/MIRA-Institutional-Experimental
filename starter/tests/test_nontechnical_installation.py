from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NontechnicalInstallationTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def flow(self) -> dict:
        return json.loads(self.text("install-flow.json"))

    def test_browser_only_entrypoint_is_unambiguous(self) -> None:
        install = self.text("INSTALL.md")
        self.assertIn("No Command Prompt", install)
        for forbidden in (
            "Do **not** open Command Prompt",
            "Do **not** install Git or GitHub CLI",
            "Do not substitute a fork",
            "Do not send the user to Command Prompt as a fallback",
        ):
            self.assertIn(forbidden, install)
        self.assertNotIn("git clone ", install.lower())
        self.assertNotIn("gh repo create", install.lower())

    def test_template_path_creates_private_user_owned_repository(self) -> None:
        flow = self.flow()
        self.assertEqual(5, flow["version"])
        self.assertEqual("Matthew-Beare/MIRA-Public-Experimental", flow["upstream"])
        self.assertEqual("github-template", flow["copy_method"])
        self.assertEqual("private", flow["default_personal_visibility"])
        self.assertEqual("user", flow["first_repository_creation"]["default_actor"])
        self.assertEqual("github-web", flow["first_repository_creation"]["surface"])
        self.assertIn("repository-creation action", flow["first_repository_creation"]["assistant_creation_allowed_when"])
        self.assertFalse(flow["first_repository_creation"]["include_all_branches"])
        self.assertIn("template_missing", flow["blocked_states"])
        self.assertIn("/generate", self.text("INSTALL.md"))

    def test_provider_specific_browser_onboarding_covers_non_google_lanes(self) -> None:
        flow = self.flow()
        self.assertEqual("PROVIDER_ONBOARDING.md", flow["provider_onboarding_document"])
        providers = self.text("PROVIDER_ONBOARDING.md")
        for phrase in (
            "Google Workspace lane",
            "Microsoft 365, OneDrive and SharePoint lane",
            "Apple and iCloud lane",
            "Claude and other AI runtimes",
            "Institutional and VA deployment",
            "No local OneDrive sync client",
            "read → write → readback",
        ):
            self.assertIn(phrase, providers)
        self.assertIn("PROVIDER_ONBOARDING.md", self.text("INSTALL.md"))
        self.assertIn("MIRA-Public-Experimental/generate", self.text("INSTALL.md"))

    def test_installable_skill_and_personal_google_bootstrap_are_required(self) -> None:
        flow = self.flow()
        self.assertEqual("life-planner", flow["skill_package"])
        for relative in (
            "life-planner/SKILL.md",
            flow["personal_google_blueprint"],
            flow["personal_google_verifier"],
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        gates = {row["id"]: row for row in flow["capability_gates"]}
        self.assertIn("life-planner-skill", gates)
        install = self.text("INSTALL.md")
        self.assertIn("install and validate the `life-planner` skill", install)
        self.assertIn("Do not fall back to the reference deployment", install)

    def test_read_and_write_connections_are_independent_gates(self) -> None:
        flow = self.flow()
        gates = {row["id"]: row for row in flow["capability_gates"]}
        self.assertIn("chatgpt-github-read", gates)
        self.assertIn("codex-github-write", gates)
        self.assertIn("read-only ChatGPT GitHub app", gates["codex-github-write"]["blocked_action"])
        self.assertIn("remote write and readback", " ".join(gates["codex-github-write"]["pass_evidence"]))
        self.assertIn("write_missing", flow["blocked_states"])

    def test_required_readback_prevents_fake_install_success(self) -> None:
        fields = set(self.flow()["assistant_readback_fields"])
        self.assertTrue({
            "repository",
            "visibility",
            "default_branch",
            "starter_commit",
            "chatgpt_read",
            "codex_write",
            "local_command_line_required",
            "deployment_lane",
            "ai_runtime",
            "data_classification",
            "source_mode",
            "structured_state_provider",
            "evidence_provider",
            "organization_approval",
            "organization_approval_reference",
        }.issubset(fields))

    def test_enterprise_and_alternative_ai_lanes_are_browser_only_and_capability_gated(self) -> None:
        flow = self.flow()
        self.assertTrue({"personal_browser", "enterprise_managed", "portable_manual"}.issubset(
            flow["deployment_lanes"]
        ))
        install = self.text("INSTALL.md")
        for phrase in (
            "Claude",
            "Microsoft/VA AI",
            "managed central source",
            "Do not create a personal GitHub",
            "provider_capability_router.py",
        ):
            self.assertIn(phrase, install)
        self.assertIn("claim-ai-runtime-feature-parity", flow["nontechnical_forbidden_actions"])
        self.assertIn("put-regulated-sensitive-data-in-unapproved-runtime", flow["nontechnical_forbidden_actions"])
        approval_gate = next(row for row in flow["capability_gates"] if row["id"] == "runtime-and-data-approval")
        self.assertIn("approval-evidence reference", " ".join(approval_gate["pass_evidence"]))

    def test_meals_laundry_and_pickups_are_discoverable(self) -> None:
        questions = json.loads(self.text("questions.json"))
        ids = {
            row["id"]
            for section in questions["sections"]
            for row in section["questions"]
        }
        flow = self.flow()["selected_workflow_discovery"]
        self.assertIn(flow["meal_planning_question_id"], ids)
        for question_id in flow["household_routine_question_ids"]:
            self.assertIn(question_id, ids)

    def test_weather_in_briefs_is_an_explicit_failure_isolated_opt_in(self) -> None:
        questions = json.loads(self.text("questions.json"))
        rows = {
            row["id"]: row
            for section in questions["sections"]
            for row in section["questions"]
        }
        question_id = self.flow()["selected_workflow_discovery"]["weather_brief_question_id"]
        self.assertEqual("brief_weather_enabled", question_id)
        self.assertEqual("Would you like weather included in your briefs?", rows[question_id]["prompt"])
        self.assertTrue(rows[question_id]["required"])
        for question_id in (
            "brief_weather_slots",
            "brief_weather_location_policy",
            "brief_weather_details",
            "brief_weather_units",
            "brief_severe_weather_alerts",
        ):
            self.assertIn(question_id, rows)
            self.assertIn("brief_weather_enabled is true", rows[question_id]["applies_when"])
        dependencies = self.text("DEPENDENCIES.md")
        self.assertIn("Missing or stale weather degrades only the weather section", dependencies)
        self.assertIn("official alerts are distinct evidence classes", dependencies)

    def test_public_front_door_uses_current_mira_mirror_brand(self) -> None:
        root_readme = (ROOT.parent / "README.md").read_text(encoding="utf-8")
        starter_readme = self.text("README.md")
        install = self.text("INSTALL.md")
        for surface in (root_readme, starter_readme, install):
            self.assertIn("M.I.R.R.O.R.", surface)
            self.assertIn("MIRA", surface)
            self.assertNotIn("# LyfeOS", surface)
        branding = (ROOT.parent / "docs" / "BRANDING.md").read_text(encoding="utf-8")
        self.assertIn("Life Planner", branding)
        self.assertIn("compatibility identifiers", branding)
        self.assertIn("proper trademark/domain/app-store clearance", branding)


if __name__ == "__main__":
    unittest.main()
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

    def test_git_is_explained_for_a_first_time_user(self) -> None:
        install = self.text("INSTALL.md")
        for phrase in (
            "**Git** is an undo history for files",
            "**GitHub** is a website that stores a Git project online",
            "A **repository**",
            "A **commit** is a named save point",
            "A **push** means putting a new commit onto GitHub",
            "You do **not** need to type Git commands",
        ):
            self.assertIn(phrase, install)

    def test_template_path_creates_private_user_owned_repository(self) -> None:
        flow = self.flow()
        self.assertEqual("github-template", flow["copy_method"])
        self.assertEqual("private", flow["default_personal_visibility"])
        self.assertEqual("user", flow["first_repository_creation"]["default_actor"])
        self.assertEqual("github-web", flow["first_repository_creation"]["surface"])
        self.assertIn("repository-creation action", flow["first_repository_creation"]["assistant_creation_allowed_when"])
        self.assertFalse(flow["first_repository_creation"]["include_all_branches"])
        self.assertIn("template_missing", flow["blocked_states"])
        self.assertIn("/generate", self.text("INSTALL.md"))

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

    def test_public_front_door_uses_mira_mirror_branding(self) -> None:
        surfaces = (
            (ROOT.parent / "README.md").read_text(encoding="utf-8"),
            self.text("README.md"),
            self.text("INSTALL.md"),
        )
        for surface in surfaces:
            self.assertIn("MIRROR", surface)
            self.assertIn("MIRA", surface)
            self.assertNotIn("# LyfeOS", surface)

        branding = (ROOT.parent / "docs" / "BRANDING.md").read_text(encoding="utf-8")
        self.assertIn("MIRROR Layer", branding)
        self.assertIn("MIRA Layer", branding)
        self.assertIn("MIRA, mirror on the wall", branding)
        self.assertIn("default user-facing assistant", branding)
        self.assertIn("proper trademark", branding)


if __name__ == "__main__":
    unittest.main()

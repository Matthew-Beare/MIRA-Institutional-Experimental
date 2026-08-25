from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


class MiraMirrorBrandingTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_brand_contract_is_explicit(self) -> None:
        branding = (REPO / "docs/BRANDING.md").read_text(encoding="utf-8")
        self.assertIn("Memory, Integration, Reality, Reconciliation, Observation, and Record", branding)
        self.assertIn("MIRROR Intelligence and Reasoning Assistant", branding)
        self.assertIn("Dennis E. Taylor", branding)
        self.assertIn("Bobiverse", branding)
        self.assertIn("forced acronym", branding)
        self.assertIn("holds the durable reflection of reality", branding)
        self.assertIn("Magic MIRA on the wall", branding)
        self.assertNotIn("Signature line:", branding)

    def test_public_readme_explains_brand_and_scope_up_front(self) -> None:
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("Memory, Integration, Reality, Reconciliation, Observation, and Record", readme)
        self.assertIn("MIRROR Intelligence and Reasoning Assistant", readme)
        self.assertIn("Dennis E. Taylor", readme)
        self.assertIn("Bobiverse", readme)
        self.assertIn("forced acronym", readme)
        self.assertIn("holds the durable reflection of reality", readme)
        self.assertIn("Magic MIRA on the wall", readme)
        self.assertNotIn("Signature line:", readme)
        for term in ("assets", "finances", "calendars", "email", "orders", "appointments", "medications"):
            self.assertIn(term, readme.lower())

    def test_skill_creation_and_sharing_are_explicit(self) -> None:
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        workflow = self.text("SHARED_FEATURE_WORKFLOW.md")
        for text in (
            "feature branch",
            "synthetic fixtures",
            "Do you want to make this feature available to other people?",
            "upstream pull request",
        ):
            self.assertIn(text, readme)
            self.assertIn(text, workflow)
        self.assertIn("private by default", readme.lower())
        self.assertIn("explicit publication approval", workflow)

    def test_default_front_door_is_boomer_safe(self) -> None:
        flow = json.loads(self.text("install-flow.json"))
        self.assertEqual("MIRROR", flow["brand_product_name"])
        self.assertEqual("MIRA", flow["assistant_default_name"])
        self.assertEqual("QUICK_START.md", flow["entry_document"])
        self.assertEqual("MIRROR", flow["first_boot_defaults"]["system_name"])
        self.assertEqual("MIRA", flow["first_boot_defaults"]["assistant_name"])
        self.assertFalse(flow["first_boot_defaults"]["ask_system_name_on_first_boot"])
        guide = self.text("QUICK_START.md")
        self.assertIn("Git is version history.", guide)
        self.assertIn("GitHub is the website", guide)
        self.assertIn("No Command Prompt", guide)
        self.assertIn("Make M.I.R.R.O.R. do something new", guide)
        self.assertIn("Bobiverse", guide)
        self.assertNotIn("git clone ", guide.lower())
        self.assertNotIn("gh repo create", guide.lower())

    def test_portable_skill_keeps_compatibility_id_but_uses_mira(self) -> None:
        skill = self.text("life-planner/SKILL.md")
        agent = self.text("life-planner/agents/openai.yaml")
        self.assertIn("name: life-planner", skill)
        self.assertIn("Memory, Integration, Reality, Reconciliation, Observation, and Record", skill)
        self.assertIn("ask the user to invent a system name: **false**", skill)
        self.assertIn('display_name: "MIRA | M.I.R.R.O.R."', agent)

    def test_release_channels_share_one_code_line_and_are_public(self) -> None:
        canonical_config = REPO / "distribution/channels.json"
        generated_manifest = REPO / "DEPLOYMENT_CHANNEL.json"

        if canonical_config.is_file():
            config = json.loads(canonical_config.read_text(encoding="utf-8"))
            self.assertEqual("MIRROR", config["brand_product_name"])
            self.assertEqual("MIRA", config["assistant_default_name"])
            self.assertEqual("Matthew-Beare/MIRA-Personal-Production", config["canonical_source"]["repository"])
            self.assertEqual("public", config["canonical_source"]["required_visibility"])
            channels = {row["channel_id"]: row for row in config["channels"]}
            self.assertEqual("Matthew-Beare/MIRA-Public-Experimental", channels["public-experimental"]["repository"])
            self.assertEqual("Matthew-Beare/MIRA-Institutional-Experimental", channels["institutional-experimental"]["repository"])
            self.assertEqual("public", channels["public-experimental"]["required_visibility"])
            self.assertEqual("public", channels["institutional-experimental"]["required_visibility"])
            shared = config["shared_code_contract"]
            self.assertTrue(shared["same_portable_source_revision_required"])
            self.assertFalse(shared["channel_specific_feature_code_allowed"])
            return

        self.assertTrue(generated_manifest.is_file(), "generated release must carry DEPLOYMENT_CHANNEL.json")
        manifest = json.loads(generated_manifest.read_text(encoding="utf-8"))
        self.assertTrue(manifest["generated_distribution"])
        self.assertFalse(manifest["manual_edits_allowed"])
        self.assertEqual("Matthew-Beare/MIRA-Personal-Production", manifest["canonical_source_repository"])
        self.assertRegex(manifest["canonical_source_revision"], r"^[0-9a-f]{40}$")
        self.assertIn(
            manifest["repository"],
            {
                "Matthew-Beare/MIRA-Public-Experimental",
                "Matthew-Beare/MIRA-Institutional-Experimental",
            },
        )
        self.assertIn(manifest["channel_id"], {"public-experimental", "institutional-experimental"})
        self.assertEqual("M.I.R.R.O.R.", manifest["product_name"])


if __name__ == "__main__":
    unittest.main()

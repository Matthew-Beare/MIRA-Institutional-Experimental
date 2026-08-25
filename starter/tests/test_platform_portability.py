from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "provider_capability_router", ROOT / "tools" / "provider_capability_router.py"
)
ROUTER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ROUTER)


def capabilities(**overrides: bool) -> dict[str, bool]:
    values = {key: False for key in ROUTER.CAPABILITY_KEYS}
    values.update(overrides)
    return values


def plan(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "runtime_id": "chatgpt",
        "storage_id": "google-workspace",
        "source_mode": "user-git",
        "environment": "personal",
        "data_classification": "personal",
        "organization_approved_for_data": False,
        "organization_approval_reference": "",
        "requested": {
            "stateful_modules": True,
            "retained_evidence": True,
            "email_evidence": True,
            "calendar_projection": True,
            "scheduled_dispatch": True,
        },
        "capabilities": capabilities(
            source_read=True,
            source_write=True,
            source_remote_readback=True,
            structured_state_read=True,
            structured_state_write=True,
            structured_state_readback=True,
            evidence_read=True,
            evidence_write=True,
            evidence_readback=True,
            email_read=True,
            calendar_read=True,
            calendar_write=True,
            calendar_readback=True,
            scheduled_dispatch=True,
            canonical_clock_gate=True,
            observed_scheduled_firing=True,
        ),
    }
    values.update(overrides)
    return values


class PlatformPortabilityTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_manifest_has_runtime_storage_source_and_claim_gates(self) -> None:
        manifest = json.loads(self.text("platform-capabilities.json"))
        self.assertEqual(1, manifest["schema_version"])
        self.assertTrue(manifest["claim_policy"]["provider_name_is_not_capability_proof"])
        self.assertTrue(manifest["claim_policy"]["live_write_and_readback_required_for_write_claims"])
        self.assertEqual(set(manifest["capability_ids"]), ROUTER.CAPABILITY_KEYS)
        self.assertTrue({"chatgpt", "claude", "microsoft-copilot-or-approved-organizational-ai"}.issubset(
            {row["id"] for row in manifest["ai_runtimes"]}
        ))
        self.assertTrue({"google-workspace", "microsoft-365", "apple-icloud"}.issubset(
            {row["id"] for row in manifest["storage_backends"]}
        ))
        self.assertTrue({"github-personal", "github-enterprise", "gitlab", "azure-repos", "managed-central-source"}.issubset(
            {row["id"] for row in manifest["source_backends"]}
        ))

    def test_full_personal_google_chatgpt_lane_is_ready_only_from_observed_caps(self) -> None:
        result = ROUTER.evaluate(plan())
        self.assertEqual("ready", result["decision"])
        self.assertFalse(result["provider_name_used_as_proof"])
        self.assertTrue(result["verified_claims"]["durable_source_write"])
        self.assertTrue(result["verified_claims"]["scheduled_delivery"])

    def test_claude_or_microsoft_brand_does_not_bypass_missing_write(self) -> None:
        for runtime_id in ("claude", "microsoft-copilot-or-approved-organizational-ai"):
            observed = capabilities(
                source_read=True,
                structured_state_read=True,
                structured_state_write=True,
                structured_state_readback=True,
            )
            result = ROUTER.evaluate(plan(
                runtime_id=runtime_id,
                capabilities=observed,
                requested={
                    "stateful_modules": True,
                    "retained_evidence": False,
                    "email_evidence": False,
                    "calendar_projection": False,
                    "scheduled_dispatch": False,
                },
            ))
            self.assertEqual("degraded", result["decision"])
            self.assertIn("durable-personal-source-mutation-unavailable", result["degradations"])
            self.assertFalse(result["verified_claims"]["durable_source_write"])

    def test_regulated_sensitive_data_is_blocked_without_exact_approval(self) -> None:
        result = ROUTER.evaluate(plan(
            environment="regulated",
            data_classification="regulated-sensitive",
            organization_approved_for_data=False,
        ))
        self.assertEqual("blocked", result["decision"])
        self.assertIn("runtime-or-storage-not-approved-for-regulated-sensitive-data", result["blocks"])

    def test_regulated_sensitive_data_rejects_unsubstantiated_approval_boolean(self) -> None:
        result = ROUTER.evaluate(plan(
            environment="regulated",
            data_classification="regulated-sensitive",
            organization_approved_for_data=True,
            organization_approval_reference="",
        ))
        self.assertEqual("blocked", result["decision"])
        self.assertIn("organization-approval-evidence-missing", result["blocks"])
        self.assertFalse(result["organization_approval_reference_present"])

    def test_approved_enterprise_microsoft_lane_can_use_managed_source(self) -> None:
        observed = capabilities(
            managed_release_read=True,
            structured_state_read=True,
            structured_state_write=True,
            structured_state_readback=True,
        )
        result = ROUTER.evaluate(plan(
            runtime_id="microsoft-copilot-or-approved-organizational-ai",
            storage_id="microsoft-365",
            source_mode="managed-central",
            environment="regulated",
            data_classification="regulated-sensitive",
            organization_approved_for_data=True,
            organization_approval_reference="current-approved-pilot-record",
            requested={
                "stateful_modules": True,
                "retained_evidence": False,
                "email_evidence": False,
                "calendar_projection": False,
                "scheduled_dispatch": False,
            },
            capabilities=observed,
        ))
        self.assertEqual("degraded", result["decision"])
        self.assertNotIn("runtime-or-storage-not-approved-for-regulated-sensitive-data", result["blocks"])
        self.assertIn("personal-policy-changes-require-managed-change-process", result["degradations"])
        self.assertTrue(result["verified_claims"]["structured_state_write"])

    def test_managed_source_write_is_not_verified_without_remote_readback(self) -> None:
        observed = capabilities(
            managed_release_read=True,
            source_write=True,
            structured_state_read=True,
            structured_state_write=True,
            structured_state_readback=True,
        )
        result = ROUTER.evaluate(plan(
            source_mode="managed-central",
            requested={
                "stateful_modules": True,
                "retained_evidence": False,
                "email_evidence": False,
                "calendar_projection": False,
                "scheduled_dispatch": False,
            },
            capabilities=observed,
        ))
        self.assertEqual("degraded", result["decision"])
        self.assertIn("managed-source-write-readback-unavailable", result["degradations"])
        self.assertFalse(result["verified_claims"]["durable_source_write"])

    def test_optional_email_and_calendar_failures_are_degraded_not_faked(self) -> None:
        observed = capabilities(
            source_read=True,
            source_write=True,
            source_remote_readback=True,
            structured_state_read=True,
            structured_state_write=True,
            structured_state_readback=True,
        )
        result = ROUTER.evaluate(plan(
            capabilities=observed,
            requested={
                "stateful_modules": True,
                "retained_evidence": False,
                "email_evidence": True,
                "calendar_projection": True,
                "scheduled_dispatch": False,
            },
        ))
        self.assertEqual("degraded", result["decision"])
        self.assertIn("email-evidence-adapter-unavailable", result["degradations"])
        self.assertIn("calendar-projection-contract-incomplete", result["degradations"])
        self.assertFalse(result["verified_claims"]["email_evidence_read"])
        self.assertFalse(result["verified_claims"]["calendar_projection_write"])

    def test_unknown_capability_and_request_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported capabilities"):
            ROUTER.evaluate(plan(capabilities={"imaginary_write": True}))
        with self.assertRaisesRegex(ValueError, "unsupported requested capabilities"):
            ROUTER.evaluate(plan(requested={"magic": True}))

    def test_icloud_is_documented_as_manual_not_fake_automated_drive(self) -> None:
        manifest = json.loads(self.text("platform-capabilities.json"))
        icloud = next(row for row in manifest["storage_backends"] if row["id"] == "apple-icloud")
        self.assertEqual("manual-bridge", icloud["automation_tier"])
        self.assertEqual([], icloud["structured_candidates"])
        self.assertIn("Do not claim general automated access", icloud["notes"])

    def test_enterprise_docs_forbid_personal_account_workarounds_and_false_parity(self) -> None:
        enterprise = self.text("ENTERPRISE_PILOT.md")
        portability = self.text("PLATFORM_PORTABILITY.md")
        provider_onboarding = self.text("PROVIDER_ONBOARDING.md")
        for phrase in (
            "Do not create a personal cloud account",
            "organization-approved",
            "regulated-sensitive",
            "read → bounded write → readback",
            "synthetic or public data",
        ):
            self.assertIn(phrase, enterprise)
        for phrase in (
            "ChatGPT",
            "Claude",
            "Microsoft 365",
            "OneDrive",
            "SharePoint",
            "Apple/iCloud",
            "no feature parity",
            "managed central source",
        ):
            self.assertIn(phrase.lower(), portability.lower())
        for phrase in (
            "Google Workspace lane",
            "Microsoft 365, OneDrive and SharePoint lane",
            "Apple and iCloud lane",
            "Claude and other AI runtimes",
            "Authority Registry",
            "bounded read",
            "provider record back",
            "no PHI/PII",
        ):
            self.assertIn(phrase.lower(), provider_onboarding.lower())

    def test_enterprise_demo_uses_generic_synthetic_personas_only(self) -> None:
        enterprise = self.text("ENTERPRISE_PILOT.md")
        for phrase in (
            "generic or synthetic personas",
            "real viewer identities",
            "private disclosures",
            "inferred motives",
        ):
            self.assertIn(phrase, enterprise)


if __name__ == "__main__":
    unittest.main()

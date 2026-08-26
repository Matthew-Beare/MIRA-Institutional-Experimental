from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class FutureRuntimeContractTests(unittest.TestCase):
    def test_runtime_contract_keeps_storage_and_clients_behind_interfaces(self):
        contract = load("runtime-interface-contract.json")
        self.assertTrue(contract["principles"]["provider_neutral_core"])
        self.assertTrue(contract["principles"]["clients_never_write_database_directly"])
        self.assertIn("postgresql", contract["interfaces"]["structured_state"]["candidate_adapters"])
        self.assertIn("s3_compatible_object_storage", contract["interfaces"]["evidence_store"]["candidate_adapters"])
        self.assertEqual(
            {"web", "windows_desktop", "linux_desktop", "android"},
            set(contract["client_surfaces"]),
        )
        self.assertTrue(contract["security"]["public_database_exposure_prohibited"])

    def test_model_router_is_deterministic_first_and_has_explicit_escalation(self):
        policy = load("model-routing-policy.json")
        self.assertEqual("deterministic", policy["default_path"])
        self.assertFalse(policy["tiers"]["deterministic"]["uses_model"])
        self.assertIn("required_validator_failed", policy["escalation_triggers"])
        self.assertIn("confidence_below_task_threshold", policy["escalation_triggers"])
        self.assertIn("do_not_mutate_canonical_state_from_an_unvalidated_lower_tier_result", policy["non_escalation_rules"])

    def test_barcode_contract_supports_product_asset_and_location_scans(self):
        contract = load("barcode-qr-contract.json")
        self.assertEqual(
            {"product_identifier", "asset_tag", "location_tag", "evidence_reference"},
            set(contract["scan_classes"]),
        )
        self.assertEqual("client_local", contract["capture"]["decode_preference"])
        self.assertTrue(contract["safety"]["unresolved_identity_never_invented"])
        self.assertTrue(contract["safety"]["canonical_uuid_preserved_across_storage_migration"])

    def test_appointment_contract_caches_identity_and_requires_verified_spoken_delivery(self):
        contract = load("appointment-identity-contract.json")
        self.assertEqual("known_entity_uuid_or_exact_source_binding", contract["resolution_order"][0])
        self.assertTrue(contract["safety"]["owner_correction_is_durable_evidence"])
        self.assertEqual("generic", contract["delivery"]["privacy_default"])
        self.assertIn("text_to_speech", contract["android"]["target_capabilities"])
        self.assertIn("spoken_notification", contract["android"]["target_capabilities"])

    def test_platform_capabilities_include_self_hosted_cloud_and_native_clients(self):
        platform = load("platform-capabilities.json")
        storage_ids = {row["id"] for row in platform["storage_backends"]}
        self.assertIn("self-hosted-linux", storage_ids)
        self.assertIn("cloud-native", storage_ids)
        clients = {row["id"] for row in platform["client_surfaces"]}
        self.assertEqual({"web", "windows-desktop", "linux-desktop", "android"}, clients)
        capability_ids = set(platform["capability_ids"])
        for capability in ("spoken_notification", "barcode_decode", "local_model", "authenticated_https_api"):
            self.assertIn(capability, capability_ids)

    def test_config_does_not_make_google_the_architectural_state_backend(self):
        config = load("config.example.json")
        self.assertIn("POSTGRESQL", config["STATE_BACKEND"])
        self.assertIn("VERSIONED_BOUNDED_SERVICE_API", config["CLIENT_API"])
        self.assertIn("ANDROID", config["CLIENT_SURFACES"])
        self.assertIn("SYSTEMD_TIMER", config["SCHEDULER_ADAPTER"])
        self.assertIn("NOT_SECOND_SPEND", config["FINANCIAL_DEDUPE_POLICY"])

    def test_onboarding_explicitly_asks_about_integrations_finance_inventory_and_spoken_reminders(self):
        questions = load("questions.profile-and-stock-services.json")
        ids = {
            question["id"]
            for section in questions["sections"]
            for question in section["questions"]
        }
        for question_id in (
            "integration_discovery_consent",
            "connected_devices_user_report",
            "financial_assistance_enabled",
            "financial_goals",
            "inventory_capture_enabled",
            "appointment_spoken_delivery",
        ):
            self.assertIn(question_id, ids)


if __name__ == "__main__":
    unittest.main()

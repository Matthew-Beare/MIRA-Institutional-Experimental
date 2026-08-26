from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClientSurfaceTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def load(self, relative: str) -> dict:
        return json.loads(self.text(relative))

    def test_pwa_is_installable_and_has_camera_keyboard_and_offline_capture(self) -> None:
        for relative in (
            "clients/pwa/index.html",
            "clients/pwa/app.js",
            "clients/pwa/manifest.webmanifest",
            "clients/pwa/sw.js",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        app = self.text("clients/pwa/app.js")
        html = self.text("clients/pwa/index.html")
        manifest = self.load("clients/pwa/manifest.webmanifest")
        self.assertIn("getUserMedia", app)
        self.assertIn("BarcodeDetector", app)
        self.assertIn("capture.barcode_qr_scan", app)
        self.assertIn("idempotency_key", app)
        self.assertIn("sync pending", html.lower())
        self.assertIn("usb/bluetooth scanner", html.lower())
        self.assertEqual("standalone", manifest["display"])

    def test_pwa_never_becomes_database_client_and_token_is_not_persisted(self) -> None:
        app = self.text("clients/pwa/app.js")
        contract = self.load("client-api-contract.json")
        self.assertIn("/v1/commands", app)
        self.assertNotIn("postgres://", app.lower())
        self.assertNotIn("postgresql://", app.lower())
        self.assertNotIn("localStorage.setItem(\"mirror.capture.token", app)
        self.assertTrue(contract["security"]["database_credentials_in_clients_prohibited"])

    def test_foreground_browser_speech_is_not_background_delivery_proof(self) -> None:
        app = self.text("clients/pwa/app.js")
        pwa = self.text("clients/pwa/README.md")
        android = self.text("clients/android/README.md")
        self.assertIn("speechSynthesis", app)
        self.assertIn("not background reminder-delivery evidence", app)
        self.assertIn("background appointment delivery", pwa)
        self.assertIn("must not set", pwa)
        self.assertIn("Android `TextToSpeech`", android)
        self.assertIn("Android's selected Text-to-Speech engine generates the actual voice locally", self.text("clients/README.md"))

    def test_barcode_contract_has_camera_keyboard_and_manual_adapters(self) -> None:
        contract = self.load("barcode-qr-contract.json")
        self.assertEqual("installable_pwa", contract["capture"]["baseline_client"])
        adapters = set(contract["capture"]["input_adapters"])
        self.assertIn("pwa_camera_barcode_detector_when_supported", adapters)
        self.assertIn("usb_or_bluetooth_keyboard_wedge_scanner", adapters)
        self.assertIn("manual_entry", adapters)
        self.assertTrue(contract["capture"]["secure_context_required_for_camera"])

    def test_rfid_contract_preserves_asset_identity_and_requires_verified_promotion(self) -> None:
        contract = self.load("rfid-asset-tracking-contract.json")
        self.assertEqual("immutable asset UUID", contract["canonical_identity"]["asset_identity"])
        self.assertTrue(contract["reader_semantics"]["single_observation_is_not_a_location_move"])
        self.assertFalse(contract["location_promotion"]["automatic_promotion_default"])
        self.assertIn("network_uhf_reader", contract["capture_adapters"])
        api = self.load("client-api-contract.json")
        self.assertIn("rfid_presence_observation", api["capture_surface"])
        runtime = self.load("runtime-interface-contract.json")
        self.assertIn("rfid", runtime["interfaces"])
        self.assertIn("network_uhf_epc_gen2_reader", runtime["interfaces"]["rfid"]["candidate_adapters"])


if __name__ == "__main__":
    unittest.main()

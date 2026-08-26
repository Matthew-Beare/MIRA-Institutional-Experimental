from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


class CrossPlatformClientContractTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def load(self, relative: str) -> dict:
        return json.loads(self.text(relative))

    def canonical_workflow(self, name: str) -> str:
        path = REPO_ROOT / ".github/workflows" / name
        if not path.is_file():
            self.skipTest("canonical-only platform build workflow is not part of generated distribution")
        return path.read_text(encoding="utf-8")

    def test_desktop_gui_and_cli_share_provider_neutral_api(self) -> None:
        cargo = self.text("clients/desktop/src-tauri/Cargo.toml")
        config = self.load("clients/desktop/src-tauri/tauri.conf.json")
        cli = self.text("clients/desktop/src-tauri/src/bin/mira-cli.rs")
        self.assertEqual("../../pwa", config["build"]["frontendDist"])
        self.assertIn('name = "mira-cli"', cargo)
        self.assertIn("/v1/commands", cli)
        self.assertIn("/v1/assets/", cli)
        self.assertIn("/v1/evidence", cli)
        self.assertIn("MIRA_ACCESS_TOKEN", cli)
        self.assertNotIn("postgres://", cli.lower())
        self.assertNotIn("postgresql://", cli.lower())

    def test_desktop_ci_builds_windows_linux_gui_and_cli_artifacts(self) -> None:
        workflow = self.canonical_workflow("desktop-clients.yml")
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("mira-desktop.exe", workflow)
        self.assertIn("mira-cli.exe", workflow)
        self.assertIn("mira-linux-clients", workflow)
        self.assertIn("mira-windows-clients", workflow)

    def test_android_ci_uploads_installable_debug_apk(self) -> None:
        workflow = self.canonical_workflow("android-client.yml")
        self.assertIn(":app:assembleDebug", workflow)
        self.assertIn("mira-android-debug-apk", workflow)
        self.assertIn("app-debug.apk", workflow)

    def test_asset_media_is_storage_neutral_and_gui_cli_compatible(self) -> None:
        contract = self.load("asset-media-contract.json")
        self.assertEqual("immutable asset UUID", contract["identity"]["asset_identity"])
        self.assertTrue(contract["identity"]["backend_migration_preserves_both_ids"])
        self.assertEqual("/v1/evidence", contract["write_contract"]["endpoint"])
        self.assertIn("s3_compatible_object_storage", contract["storage_adapters"])
        self.assertIn("google_drive", contract["storage_adapters"])
        self.assertIn("show thumbnails", contract["client_behavior"]["gui"])
        self.assertIn("download binary only on explicit command", contract["client_behavior"]["cli"])

    def test_hardware_contract_supports_camera_scanners_rfid_and_printers_by_adapter(self) -> None:
        hardware = self.load("hardware-capture-contract.json")
        camera_classes = {row["class"] for row in hardware["cameras"]}
        scanner_classes = {row["class"] for row in hardware["barcode_scanners"]}
        printer_classes = {row["class"] for row in hardware["printers"]}
        self.assertIn("browser_media_camera", camera_classes)
        self.assertIn("usb_or_bluetooth_hid_keyboard_wedge", scanner_classes)
        self.assertIn("serial_or_usb_cdc_scanner", scanner_classes)
        self.assertIn("thermal_label_printer", printer_classes)
        self.assertTrue(hardware["rfid"]["passive_observation_never_moves_asset_by_default"])
        self.assertTrue(hardware["capability_health"]["verify_real_sample_before_marking_healthy"])

    def test_web_gui_has_asset_photo_and_lookup_surfaces(self) -> None:
        html = self.text("clients/pwa/index.html")
        app = self.text("clients/pwa/app.js")
        self.assertIn("Asset photo", html)
        self.assertIn('accept="image/*"', html)
        self.assertIn("/v1/evidence", app)
        self.assertIn("photo_evidence", app)
        self.assertIn("/v1/assets/", app)


if __name__ == "__main__":
    unittest.main()

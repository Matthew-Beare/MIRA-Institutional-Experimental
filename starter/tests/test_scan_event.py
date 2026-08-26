from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "scan_event.py"
spec = importlib.util.spec_from_file_location("scan_event", MODULE)
subject = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(subject)

TAG = "61ac5e8f-9fb2-4e73-af0f-1ebffde34eb7"
ASSET = "33ac3159-bc0d-426c-8137-a0b2cdedc71e"
LOCATION = "79105779-a788-48c2-ad5f-ff9c46b02c15"
SCAN = "f70f13df-18b3-4fa0-97e8-1a25f2a9de03"


class ScanEventTests(unittest.TestCase):
    def test_valid_gtin_is_classified(self):
        result = subject.normalize_scan({
            "raw_value": "036000291452",
            "captured_at": "2026-08-25T12:00:00-04:00",
            "client_id": "android-fixture",
            "symbology": "UPC_A",
        })
        self.assertEqual("product_identifier", result["classification"]["scan_class"])
        self.assertEqual("gtin", result["classification"]["namespace"])

    def test_bad_gtin_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "check digit"):
            subject.normalize_scan({
                "raw_value": "036000291453",
                "captured_at": "2026-08-25T12:00:00-04:00",
                "client_id": "android-fixture",
                "symbology": "UPC_A",
            })

    def test_preprinted_tag_is_unassigned_until_bound(self):
        result = subject.resolve_tag({
            "scan": {
                "raw_value": f"MIRROR-TAG:{TAG}",
                "captured_at": "2026-08-25T12:00:00-04:00",
                "client_id": "android-fixture",
                "symbology": "QR_CODE",
            },
            "tag_registry": [],
        })
        self.assertEqual("unassigned", result["status"])

    def test_tag_binding_is_idempotent_and_cannot_be_recycled(self):
        first = subject.bind_tag({"tag_uuid": TAG, "target_type": "asset", "target_uuid": ASSET, "tag_registry": []})
        second = subject.bind_tag({"tag_uuid": TAG, "target_type": "asset", "target_uuid": ASSET, "tag_registry": first["tag_registry"]})
        self.assertEqual("already_bound", second["status"])
        with self.assertRaisesRegex(ValueError, "different live target"):
            subject.bind_tag({"tag_uuid": TAG, "target_type": "location", "target_uuid": LOCATION, "tag_registry": first["tag_registry"]})

    def test_move_event_is_deterministic(self):
        payload = {
            "asset_uuid": ASSET,
            "location_uuid": LOCATION,
            "moved_at": "2026-08-25T12:05:00-04:00",
            "source_scan_uuid": SCAN,
        }
        first = subject.move_asset(payload)
        second = subject.move_asset(payload)
        self.assertEqual(first["event"]["event_uuid"], second["event"]["event_uuid"])
        self.assertEqual("located_at", first["event"]["relationship_type"])

    def test_rfid_presence_observation_is_deterministic_and_not_a_move(self):
        payload = {
            "tag_id": "E20034120123456789012345",
            "protocol": "epc_gen2",
            "observed_at": "2026-08-25T12:06:00-04:00",
            "reader_id": "garage-reader-1",
            "zone_uuid": LOCATION,
            "antenna_id": "antenna-2",
            "rssi_dbm": -48.5,
        }
        first = subject.normalize_rfid_observation(payload)
        second = subject.normalize_rfid_observation(payload)
        self.assertEqual("candidate_presence_observation", first["status"])
        self.assertEqual(first["observation"]["observation_uuid"], second["observation"]["observation_uuid"])
        self.assertIn("MUST NOT", first["location_rule"])
        self.assertNotIn("relationship_type", first["observation"])

    def test_rfid_rejects_unknown_protocol_and_naive_time(self):
        base = {
            "tag_id": "fixture-tag",
            "protocol": "epc_gen2",
            "observed_at": "2026-08-25T12:06:00-04:00",
            "reader_id": "fixture-reader",
        }
        with self.assertRaisesRegex(ValueError, "protocol"):
            subject.normalize_rfid_observation({**base, "protocol": "telepathy"})
        with self.assertRaisesRegex(ValueError, "timezone"):
            subject.normalize_rfid_observation({**base, "observed_at": "2026-08-25T12:06:00"})

    def test_rfid_rssi_must_be_finite(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            subject.normalize_rfid_observation({
                "tag_id": "fixture-tag",
                "protocol": "nfc_uid",
                "observed_at": "2026-08-25T12:06:00-04:00",
                "reader_id": "fixture-reader",
                "rssi_dbm": float("nan"),
            })


if __name__ == "__main__":
    unittest.main()

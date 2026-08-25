from __future__ import annotations

import copy
import io
import json
import sys
import unittest
import uuid
from unittest import mock

import asset_evidence as subject


NOW = "2026-08-24T16:30:00-04:00"
WRX = "1ca838cc-494f-4185-80fa-7ea1e41f3f98"
WHEEL = "78d22b78-b91f-4100-936f-1cd901963fa6"
TIRE = "9ec4a66d-d030-437c-a04d-a21767711520"
OWNER = "2476c9dc-0670-4bb8-90f6-14d1255c4a98"
SIBLING_ASSET = "eef37f2d-63bc-462e-ab3d-b84f295c3613"
EVIDENCE = "a45a0114-44aa-4db4-b03a-9f6ce4e5f209"
IDENTIFIER = "d070733e-c76b-4872-97d6-a4505012832c"
KNOWLEDGE = "e167b329-761e-477b-97e8-df2405851780"
KNOWLEDGE_LINK = "d9bb6b38-efb3-4987-be99-916324ec3552"
SPECIFICATION = "ff861da7-8af0-47da-98f6-9bdde38ff2d8"
LOOKUP = "bfc9886f-2398-4cfa-99ef-7c15bb4c4fd4"


class UUIDFactory:
    def __init__(self, *values: str):
        self.values = iter(uuid.UUID(value) for value in values)

    def __call__(self) -> uuid.UUID:
        return next(self.values)


def evidence_intent(**overrides):
    row = {
        "evidence_uuid": EVIDENCE,
        "evidence_type": "receipt_photo",
        "entity_uuid": TIRE,
        "receipt_id": "TR-2026-08-20-VG04252",
        "receipt_line_id": "Receipt Details - Expandable!22",
        "source_authority": "purchase_receipt_archive",
        "source_record_id": "TR-2026-08-20-VG04252:line-22:photo-1",
        "source_uri": "https://example.invalid/evidence/tire-receipt",
        "drive_file_url": "",
        "drive_file_id": "",
        "content_hash": "sha256:fixture",
        "captured_et": NOW,
        "status": "retained",
        "notes": "Fixture evidence.",
    }
    row.update(overrides)
    return row


def identifier_intent(**overrides):
    row = {
        "identifier_uuid": IDENTIFIER,
        "entity_uuid": TIRE,
        "identifier_type": "vendor_sku",
        "value": "1020374",
        "namespace": "Tire Rack",
        "status": "verified",
        "evidence_uuid": EVIDENCE,
        "source_authority": "purchase_receipt_archive",
        "source_record_id": "TR-2026-08-20-VG04252:line-22:sku",
        "evidence_link": "https://example.invalid/evidence/tire-receipt",
        "notes": "Merchant SKU; not represented as a UPC.",
    }
    row.update(overrides)
    return row


def knowledge_intent(**overrides):
    row = {
        "knowledge_uuid": KNOWLEDGE,
        "title": "2015 Subaru WRX Factory Service Manual",
        "knowledge_type": "service_manual",
        "manufacturer": "Subaru",
        "model": "WRX",
        "part_sku": "",
        "source_url": "https://example.invalid/subaru/manual",
        "drive_file_url": "https://example.invalid/drive/manual-fixture",
        "drive_file_id": "fixture-drive-file",
        "version_revision": "2015 edition",
        "effective_date": "2014-01-01",
        "tags": "WRX, VA, factory service manual",
        "summary": "Canonical retained OEM service information.",
        "status": "retained",
        "source_authority": "google_drive",
        "source_record_id": "fixture-drive-file",
        "content_hash": "sha256:manual-fixture",
    }
    row.update(overrides)
    return row


def knowledge_relationship_intent(**overrides):
    row = {
        "relationship_uuid": KNOWLEDGE_LINK,
        "knowledge_uuid": KNOWLEDGE,
        "entity_uuid": WRX,
        "relationship_type": "manual_for",
        "status": "active",
        "source_authority": "knowledge_index",
        "source_record_id": "manual-for-wrx",
        "evidence_uuid": "",
        "notes": "Exact model applicability.",
    }
    row.update(overrides)
    return row


def specification_intent(**overrides):
    row = {
        "specification_uuid": SPECIFICATION,
        "subject_entity_uuid": WRX,
        "specification_type": "fluid_capacity",
        "label": "Manual transmission gear oil capacity",
        "value": "3.3",
        "unit": "L",
        "applicability": "2015 WRX non-STI 6MT TY75",
        "source_tier": "oem",
        "source_url": "",
        "knowledge_uuid": KNOWLEDGE,
        "source_locator": "6MT(TY75)-2, General Description > Specifications",
        "version_revision": "2015 edition",
        "status": "verified",
        "source_authority": "knowledge_index",
        "source_record_id": "wrx-ty75:gear-oil-capacity:2015-fsm",
        "evidence_uuid": "",
        "notes": "Do not apply to STI TY85.",
    }
    row.update(overrides)
    return row


def payload():
    return {
        "now": NOW,
        "known_entity_uuids": [OWNER],
        "assets": [
            {"entity_uuid": WRX, "label": "2015 Subaru WRX", "receipt_id": ""},
            {"entity_uuid": WHEEL, "label": "WORK Emotion M8R set", "receipt_id": ""},
            {
                "entity_uuid": TIRE,
                "label": "Hankook Ventus R-S4 265/35ZR18 set",
                "receipt_id": "TR-2026-08-20-VG04252",
                "receipt_line_id": "Receipt Details - Expandable!22",
            },
            {"entity_uuid": SIBLING_ASSET, "label": "Unrelated household tool", "receipt_id": "OTHER-1"},
        ],
        "relationships": [
            {
                "relationship_uuid": "49a82341-cc67-4132-a1ac-11a36be64fc7",
                "from_entity_uuid": TIRE,
                "relationship_type": "assigned_to",
                "to_entity_uuid": WHEEL,
                "status": "active",
            },
            {
                "relationship_uuid": "a5a7b06a-5537-4689-b682-01e9f9fa3fe9",
                "from_entity_uuid": WHEEL,
                "relationship_type": "assigned_to",
                "to_entity_uuid": WRX,
                "status": "active",
            },
            {
                "relationship_uuid": "e72c78e4-e8df-439c-b126-267f4a08b17d",
                "from_entity_uuid": SIBLING_ASSET,
                "relationship_type": "owned_by",
                "to_entity_uuid": OWNER,
                "status": "active",
            },
            {
                "relationship_uuid": "51ad4246-4978-4e07-b3ac-a3b48647ae8b",
                "from_entity_uuid": WRX,
                "relationship_type": "owned_by",
                "to_entity_uuid": OWNER,
                "status": "active",
            },
        ],
        "evidence_intents": [evidence_intent()],
        "identifier_intents": [identifier_intent()],
        "knowledge_intents": [knowledge_intent()],
        "knowledge_relationship_intents": [knowledge_relationship_intent()],
        "specification_intents": [specification_intent()],
        "lookup_intents": [],
    }


class AssetEvidenceTests(unittest.TestCase):
    def test_reconciles_normalized_evidence_graph(self):
        result = subject.reconcile(payload())
        self.assertEqual("ok", result["status"])
        self.assertEqual(1, result["counts"]["evidence"])
        self.assertEqual("1020374", result["identifiers"][0]["value"])
        self.assertEqual("Tire Rack", result["identifiers"][0]["namespace"])
        self.assertEqual("3.3", result["specifications"][0]["value"])

    def test_allocator_populates_missing_ids(self):
        data = payload()
        for collection, key in (
            ("evidence_intents", "evidence_uuid"),
            ("identifier_intents", "identifier_uuid"),
            ("knowledge_intents", "knowledge_uuid"),
            ("knowledge_relationship_intents", "relationship_uuid"),
            ("specification_intents", "specification_uuid"),
        ):
            data[collection][0].pop(key)
        # References still need the newly allocated IDs, so allocation is tested
        # on one independent evidence row rather than pretending clients can guess them.
        data["identifier_intents"] = []
        data["knowledge_intents"] = []
        data["knowledge_relationship_intents"] = []
        data["specification_intents"] = []
        allocated = "f8f19722-8bb4-4bb5-a0b3-c48c058392b3"
        result = subject.reconcile(data, UUIDFactory(allocated))
        self.assertEqual([allocated], result["changes"]["evidence"]["created"])

    def test_idempotent_replay_preserves_ids_and_updated_timestamp(self):
        first = subject.reconcile(payload())
        replay = {
            "now": "2026-08-24T17:00:00-04:00",
            "known_entity_uuids": [OWNER],
            "assets": first["assets"],
            "relationships": first["relationships"],
        }
        for name in subject.COLLECTIONS:
            replay[name] = first[name]
            replay[subject.INTENT_KEYS[name]] = copy.deepcopy(first[name])
        second = subject.reconcile(replay)
        for name in subject.COLLECTIONS:
            self.assertEqual([], second["changes"][name]["created"])
            self.assertEqual([], second["changes"][name]["updated"])
            self.assertEqual(first[name], second[name])

    def test_upc_preserves_leading_zero_and_validates_check_digit(self):
        data = payload()
        data["identifier_intents"][0] = identifier_intent(
            identifier_type="upc_a", value="036000" + "291452", namespace=""
        )
        result = subject.reconcile(data)
        self.assertEqual("036000" + "291452", result["identifiers"][0]["value"])
        self.assertEqual("036000" + "291452", result["identifiers"][0]["normalized_value"])

        data["identifier_intents"][0]["value"] = "036000" + "291453"
        with self.assertRaisesRegex(ValueError, "check-digit"):
            subject.reconcile(data)

    def test_imei_and_mac_are_normalized_and_validated(self):
        data = payload()
        data["identifier_intents"] = [
            identifier_intent(
                identifier_type="imei", value="4901542" + "03237518", namespace=""
            ),
            identifier_intent(
                identifier_uuid="8d27168b-3ffc-45ba-85fd-c90dad88dbce",
                identifier_type="mac_address",
                value="00:1a:2b:3c:4d:5e",
                namespace="",
                source_record_id="fixture-mac",
            ),
        ]
        result = subject.reconcile(data)
        self.assertEqual(
            "4901542" + "03237518", result["identifiers"][0]["normalized_value"]
        )
        self.assertEqual("001A2B3C4D5E", result["identifiers"][1]["normalized_value"])

        data["identifier_intents"][0]["value"] = "4901542" + "03237519"
        with self.assertRaisesRegex(ValueError, "valid IMEI"):
            subject.reconcile(data)

        data = payload()
        data["identifier_intents"][0] = identifier_intent(
            identifier_type="mac_address", value="not-a-mac", namespace=""
        )
        with self.assertRaisesRegex(ValueError, "valid 48-bit MAC"):
            subject.reconcile(data)

    def test_part_sku_model_and_serial_require_namespace(self):
        for identifier_type in (
            "vendor_sku", "manufacturer_part_number", "model_number", "serial_number"
        ):
            data = payload()
            data["identifier_intents"][0] = identifier_intent(
                identifier_type=identifier_type, value="ABC-123", namespace=""
            )
            with self.subTest(identifier_type=identifier_type):
                with self.assertRaisesRegex(ValueError, "namespace is required"):
                    subject.reconcile(data)

    def test_serial_collision_between_assets_is_rejected(self):
        second_evidence_uuid = "68e264c9-5acf-44ef-bff3-b8b3091f0d3e"
        first = identifier_intent(
            identifier_type="serial_number", value="SN-001", namespace="Acme"
        )
        second = identifier_intent(
            identifier_uuid="ca57ba25-da06-4ad6-8ac8-2e6c982fd00d",
            entity_uuid=SIBLING_ASSET,
            identifier_type="serial_number",
            value="SN-001",
            namespace="Acme",
            evidence_uuid=second_evidence_uuid,
            source_record_id="other-asset-serial",
        )
        data = payload()
        data["evidence_intents"].append(evidence_intent(
            evidence_uuid=second_evidence_uuid,
            evidence_type="serial_plate_photo",
            entity_uuid=SIBLING_ASSET,
            receipt_id="",
            receipt_line_id="",
            source_record_id="other-asset-serial-photo",
        ))
        data["identifier_intents"] = [first, second]
        with self.assertRaisesRegex(ValueError, "collides with another entity"):
            subject.reconcile(data)

    def test_identifier_cannot_use_another_assets_evidence(self):
        data = payload()
        data["evidence_intents"][0]["entity_uuid"] = WRX
        with self.assertRaisesRegex(ValueError, "evidence linked to another entity"):
            subject.reconcile(data)

    def test_non_owner_evidence_requires_a_retained_locator_or_hash(self):
        data = payload()
        data["evidence_intents"][0].update({
            "source_uri": "", "drive_file_id": "", "drive_file_url": "", "content_hash": ""
        })
        with self.assertRaisesRegex(ValueError, "lacks a retained source locator"):
            subject.reconcile(data)

    def test_unknown_entity_or_evidence_fails_closed(self):
        data = payload()
        data["identifier_intents"][0]["entity_uuid"] = "0a4b0362-d4cf-41e2-a130-a78773a058e9"
        with self.assertRaisesRegex(ValueError, "unknown entity"):
            subject.reconcile(data)

        data = payload()
        data["identifier_intents"][0]["evidence_uuid"] = "aa7b1937-fd17-46ac-981e-2f53d2c5afc2"
        with self.assertRaisesRegex(ValueError, "unknown evidence"):
            subject.reconcile(data)

    def test_duplicate_asset_or_wrong_known_entity_container_fails_closed(self):
        data = payload()
        data["assets"].append(copy.deepcopy(data["assets"][0]))
        with self.assertRaisesRegex(ValueError, "duplicates a known/entity UUID"):
            subject.reconcile(data)

        data = payload()
        data["known_entity_uuids"] = OWNER
        with self.assertRaisesRegex(ValueError, "must be a list"):
            subject.reconcile(data)

    def test_retained_manual_requires_drive_file_and_revision(self):
        data = payload()
        data["knowledge_intents"][0]["drive_file_id"] = ""
        with self.assertRaisesRegex(ValueError, "canonical Drive file ID and URL"):
            subject.reconcile(data)

        data = payload()
        data["knowledge_intents"][0]["version_revision"] = ""
        with self.assertRaisesRegex(ValueError, "version/revision"):
            subject.reconcile(data)

    def test_unknown_knowledge_relationship_or_spec_source_fails_closed(self):
        unknown = "c4476bf0-3436-49b2-8380-639d82083284"
        data = payload()
        data["knowledge_relationship_intents"][0]["knowledge_uuid"] = unknown
        with self.assertRaisesRegex(ValueError, "references unknown knowledge"):
            subject.reconcile(data)

        data = payload()
        data["specification_intents"][0]["knowledge_uuid"] = unknown
        with self.assertRaisesRegex(ValueError, "references unknown knowledge"):
            subject.reconcile(data)

    def test_queued_manual_may_wait_for_download_without_claiming_retention(self):
        data = payload()
        data["knowledge_intents"][0] = knowledge_intent(
            status="lookup_queued", drive_file_id="", drive_file_url="", version_revision=""
        )
        result = subject.reconcile(data)
        self.assertEqual("lookup_queued", result["knowledge"][0]["status"])

    def test_verified_safety_spec_requires_authoritative_exact_source(self):
        data = payload()
        data["specification_intents"][0]["source_tier"] = "owner_memory"
        with self.assertRaisesRegex(ValueError, "authoritative source"):
            subject.reconcile(data)

        data = payload()
        data["specification_intents"][0]["source_locator"] = ""
        with self.assertRaisesRegex(ValueError, "page/section provenance"):
            subject.reconcile(data)

        data = payload()
        data["specification_intents"][0]["knowledge_uuid"] = ""
        data["specification_intents"][0]["source_url"] = ""
        with self.assertRaisesRegex(ValueError, "source URL or retained knowledge UUID"):
            subject.reconcile(data)

    def test_verified_spec_cannot_be_silently_mutated(self):
        first = subject.reconcile(payload())
        replay = {
            "now": "2026-08-24T17:00:00-04:00",
            "known_entity_uuids": [OWNER],
            "assets": first["assets"],
            "relationships": first["relationships"],
        }
        for name in subject.COLLECTIONS:
            replay[name] = first[name]
            replay[subject.INTENT_KEYS[name]] = []
        changed = copy.deepcopy(first["specifications"][0])
        changed["value"] = "4.1"
        replay["specification_intents"] = [changed]
        with self.assertRaisesRegex(ValueError, "mutates immutable fields: value"):
            subject.reconcile(replay)

    def test_lookup_queue_and_success_state_are_explicit(self):
        data = payload()
        data["lookup_intents"] = [{
            "lookup_uuid": LOOKUP,
            "entity_uuid": TIRE,
            "lookup_type": "upc_product",
            "query": "036000" + "291452",
            "status": "queued",
            "evidence_uuid": EVIDENCE,
            "result_url": "",
            "notes": "Use manufacturer or authoritative product source first.",
            "source_authority": "evidence_index",
            "source_record_id": "lookup:upc:" + "036000" + "291452",
        }]
        result = subject.reconcile(data)
        self.assertEqual("queued", result["lookups"][0]["status"])

        data["lookup_intents"][0]["status"] = "succeeded"
        with self.assertRaisesRegex(ValueError, "requires result_url"):
            subject.reconcile(data)

    def test_lookup_status_enrichment_updates_without_replacing_uuid(self):
        data = payload()
        queued = {
            "lookup_uuid": LOOKUP,
            "entity_uuid": TIRE,
            "lookup_type": "manual",
            "query": "Hankook Ventus R-S4 product manual",
            "status": "queued",
            "evidence_uuid": EVIDENCE,
            "result_url": "",
            "notes": "Manufacturer source first.",
            "source_authority": "evidence_index",
            "source_record_id": "lookup:tire-rs4:manual",
        }
        data["lookup_intents"] = [queued]
        first = subject.reconcile(data)
        replay = {
            "now": "2026-08-24T17:15:00-04:00",
            "known_entity_uuids": [OWNER],
            "assets": first["assets"],
            "relationships": first["relationships"],
        }
        for name in subject.COLLECTIONS:
            replay[name] = first[name]
            replay[subject.INTENT_KEYS[name]] = []
        succeeded = copy.deepcopy(first["lookups"][0])
        succeeded.update({"status": "succeeded", "result_url": "https://example.invalid/manual"})
        replay["lookup_intents"] = [succeeded]
        second = subject.reconcile(replay)
        self.assertEqual([LOOKUP], second["changes"]["lookups"]["updated"])
        self.assertEqual("succeeded", second["lookups"][0]["status"])

    def test_vehicle_and_receipt_queries_return_same_connected_graph(self):
        result = subject.reconcile(payload())
        from_vehicle = subject.query_graph(result, entity_uuid=WRX)
        from_receipt = subject.query_graph(result, receipt_id="TR-2026-08-20-VG04252")
        expected = {WRX, WHEEL, TIRE}
        self.assertEqual(expected, set(from_vehicle["entity_uuids"]))
        self.assertEqual(expected, set(from_receipt["entity_uuids"]))
        self.assertEqual(["TR-2026-08-20-VG04252"], from_vehicle["receipt_ids"])
        self.assertEqual(KNOWLEDGE, from_vehicle["knowledge"][0]["knowledge_uuid"])
        self.assertEqual(SPECIFICATION, from_vehicle["specifications"][0]["specification_uuid"])
        self.assertNotIn(SIBLING_ASSET, from_vehicle["entity_uuids"])
        self.assertNotIn(OWNER, from_vehicle["entity_uuids"])

    def test_identifier_query_reaches_vehicle_and_receipt(self):
        result = subject.reconcile(payload())
        query = subject.query_graph(
            result,
            identifier_type="vendor_sku",
            identifier_value="1020374",
            identifier_namespace="Tire Rack",
        )
        self.assertEqual({WRX, WHEEL, TIRE}, set(query["entity_uuids"]))
        self.assertEqual(["TR-2026-08-20-VG04252"], query["receipt_ids"])

    def test_query_requires_exactly_one_selector(self):
        result = subject.reconcile(payload())
        with self.assertRaisesRegex(ValueError, "exactly one"):
            subject.query_graph(result)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            subject.query_graph(result, entity_uuid=WRX, receipt_id="x")

    def test_cli_success_and_invalid_json_failure(self):
        data = payload()
        with mock.patch.object(sys, "argv", ["asset_evidence.py"]), mock.patch.object(
            sys, "stdin", io.StringIO(json.dumps(data))
        ), mock.patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(0, subject.main())
            self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

        with mock.patch.object(sys, "argv", ["asset_evidence.py"]), mock.patch.object(
            sys, "stdin", io.StringIO("{")
        ), mock.patch.object(sys, "stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(2, subject.main())
            self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

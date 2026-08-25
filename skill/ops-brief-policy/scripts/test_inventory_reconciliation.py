from __future__ import annotations

import copy
import unittest
import uuid

import inventory_reconciliation as subject


NOW = "2026-08-24T15:56:53-04:00"
OWNER = "a2ef6237-a8d2-4869-af5e-56976f1a863f"
WHEEL = "4f58a7c8-628e-4ec1-99bb-87d2a568d3df"
TIRE = "8d30561d-9c07-44f3-af9c-3f12d03773c8"
RELATION = "6a450a53-1abe-4788-8e95-da475686258c"


class UUIDFactory:
    def __init__(self, *values: str):
        self.values = iter(uuid.UUID(value) for value in values)

    def __call__(self) -> uuid.UUID:
        return next(self.values)


def tire_intent(**overrides):
    row = {
        "source_authority": "purchase_receipt_archive",
        "source_record_id": "receipt-line:TR-2026-08-20-VG04252:22:tire-set",
        "receipt_id": "TR-2026-08-20-VG04252",
        "receipt_line_id": "Receipt Details - Expandable!22",
        "line_status": "delivered",
        "include_in_inventory": True,
        "asset": {
            "friendly_id": "ASSET-WRX-TIRESET-VG04252",
            "asset_type": "Tire Set",
            "label": "Hankook Ventus R-S4 265/35ZR18 XL set",
            "quantity": 4,
            "tracking_mode": "set",
            "lifecycle_status": "delivered",
            "owner_uuid": OWNER,
            "manufacturer": "Hankook",
            "model": "Ventus R-S4",
            "part_number": "1020374",
            "evidence_link": "https://example.invalid/receipt",
        },
        "assignments": [
            {
                "relationship_type": "assigned_to",
                "to_entity_uuid": WHEEL,
                "status": "active",
                "notes": "Assignment confirmed; physical installation not implied.",
            }
        ],
    }
    row.update(overrides)
    return row


def wheel_asset():
    return {
        "entity_uuid": WHEEL,
        "friendly_id": "ASSET-WRX-WORK-M8R",
        "asset_type": "Wheel Set",
        "label": "WORK Emotion M8R 18x9.5 +38 set",
        "quantity": 4,
        "tracking_mode": "set",
        "lifecycle_status": "in_service",
        "owner_uuid": OWNER,
        "source_authority": "people_assets",
        "source_record_id": "ASSET-WRX-WORK-M8R",
        "receipt_id": "",
        "receipt_line_id": "",
        "manufacturer": "WORK",
        "model": "Emotion M8R",
        "part_number": "",
        "evidence_link": "",
        "notes": "",
        "created_et": NOW,
        "updated_et": NOW,
        "schema_version": "1.0.0",
    }


class InventoryReconciliationTests(unittest.TestCase):
    def payload(self):
        return {
            "now": NOW,
            "assets": [wheel_asset()],
            "relationships": [],
            "known_entity_uuids": [OWNER],
            "receipt_line_intents": [tire_intent(entity_uuid=TIRE)],
        }

    def test_creates_one_set_asset_and_explicit_wheel_assignment(self):
        result = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["created_asset_uuids"], [TIRE])
        self.assertEqual(result["created_relationship_uuids"], [RELATION])
        tire = next(row for row in result["assets"] if row["entity_uuid"] == TIRE)
        self.assertEqual(tire["quantity"], 4)
        self.assertEqual(tire["tracking_mode"], "set")
        self.assertEqual(tire["receipt_line_id"], "Receipt Details - Expandable!22")
        relation = result["relationships"][0]
        self.assertEqual(relation["from_entity_uuid"], TIRE)
        self.assertEqual(relation["relationship_type"], "assigned_to")
        self.assertEqual(relation["to_entity_uuid"], WHEEL)
        self.assertNotEqual(relation["relationship_type"], "installed_on")

    def test_allocator_creates_rfc4122_uuid_once(self):
        payload = self.payload()
        payload["receipt_line_intents"][0].pop("entity_uuid")
        result = subject.reconcile(payload, UUIDFactory(TIRE, RELATION))
        self.assertEqual(result["created_asset_uuids"], [TIRE])
        self.assertEqual(result["created_relationship_uuids"], [RELATION])

    def test_idempotent_replay_preserves_both_uuids(self):
        first = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        replay = {
            "now": "2026-08-24T16:10:00-04:00",
            "assets": first["assets"],
            "relationships": first["relationships"],
            "known_entity_uuids": [OWNER],
            "receipt_line_intents": [tire_intent()],
        }
        second = subject.reconcile(replay, UUIDFactory("1a4e6559-37f8-4e1d-a359-592107299651"))
        self.assertEqual(second["created_asset_uuids"], [])
        self.assertEqual(second["created_relationship_uuids"], [])
        self.assertEqual(second["unchanged_asset_uuids"], [TIRE])
        self.assertEqual(second["unchanged_relationship_uuids"], [RELATION])

    def test_enrichment_updates_without_replacing_uuid(self):
        first = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        intent = tire_intent()
        intent["asset"]["notes"] = "Road-hazard coverage retained."
        result = subject.reconcile(
            {
                "now": "2026-08-24T16:10:00-04:00",
                "assets": first["assets"],
                "relationships": first["relationships"],
                "known_entity_uuids": [OWNER],
                "receipt_line_intents": [intent],
            }
        )
        self.assertEqual(result["updated_asset_uuids"], [TIRE])
        self.assertEqual(next(row for row in result["assets"] if row["entity_uuid"] == TIRE)["notes"], "Road-hazard coverage retained.")

    def test_cancelled_receipt_line_is_excluded_and_creates_nothing(self):
        cancelled = tire_intent(
            source_record_id="receipt-line:TR-2026-08-20-VG04252:23:cancelled-tire-set",
            receipt_line_id="Receipt Details - Expandable!23",
            include_in_inventory=False,
            line_status="cancelled",
            exclusion_reason="cancelled before shipment and excluded from spend",
        )
        result = subject.reconcile(
            {
                "now": NOW,
                "assets": [wheel_asset()],
                "relationships": [],
                "receipt_line_intents": [cancelled],
            }
        )
        self.assertEqual(result["created_asset_uuids"], [])
        self.assertEqual(len(result["assets"]), 1)
        self.assertEqual(result["excluded_receipt_lines"][0]["receipt_line_id"], "Receipt Details - Expandable!23")

    def test_cancelled_line_cannot_be_forced_into_inventory(self):
        intent = tire_intent(entity_uuid=TIRE, line_status="cancelled")
        with self.assertRaisesRegex(ValueError, "cancelled receipt line cannot create inventory"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]}
            )

    def test_excluded_line_cannot_orphan_an_existing_asset(self):
        first = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        excluded = tire_intent(include_in_inventory=False)
        with self.assertRaisesRegex(ValueError, "already owns an asset UUID"):
            subject.reconcile(
                {
                    "now": NOW,
                    "assets": first["assets"],
                    "relationships": first["relationships"],
                    "receipt_line_intents": [excluded],
                }
            )

    def test_unknown_assignment_target_fails_before_result(self):
        intent = tire_intent(entity_uuid=TIRE)
        intent["assignments"][0]["to_entity_uuid"] = "094764bd-f9f7-4ed8-809e-6f393e30f4de"
        with self.assertRaisesRegex(ValueError, "unknown entity"):
            subject.reconcile(
                {"now": NOW, "assets": [], "relationships": [], "receipt_line_intents": [intent]},
                UUIDFactory(RELATION),
            )

    def test_existing_relationship_may_reference_declared_external_entity(self):
        relationship = {
            "relationship_uuid": RELATION,
            "from_entity_uuid": WHEEL,
            "relationship_type": "assigned_to",
            "to_entity_uuid": OWNER,
            "status": "active",
            "source_authority": "owner_confirmation",
            "source_record_id": "wheel-owner",
            "receipt_id": "",
            "receipt_line_id": "",
            "evidence_link": "",
            "notes": "",
            "effective_from_et": NOW,
            "effective_to_et": "",
            "updated_et": NOW,
            "schema_version": "1.0.0",
        }
        result = subject.reconcile(
            {
                "now": NOW,
                "assets": [wheel_asset()],
                "relationships": [relationship],
                "known_entity_uuids": [OWNER],
                "receipt_line_intents": [],
            }
        )
        self.assertEqual(result["relationships"][0]["to_entity_uuid"], OWNER)

    def test_existing_relationship_unknown_endpoint_is_rejected(self):
        relationship = {
            "relationship_uuid": RELATION,
            "from_entity_uuid": WHEEL,
            "relationship_type": "assigned_to",
            "to_entity_uuid": "094764bd-f9f7-4ed8-809e-6f393e30f4de",
            "status": "active",
            "source_authority": "owner_confirmation",
            "source_record_id": "wheel-unknown",
            "updated_et": NOW,
        }
        with self.assertRaisesRegex(ValueError, "unknown entity"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset()], "relationships": [relationship], "receipt_line_intents": []}
            )

    def test_assignment_does_not_claim_physical_installation(self):
        result = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        self.assertEqual(result["relationships"][0]["relationship_type"], "assigned_to")
        self.assertIn("physical installation not implied", result["relationships"][0]["notes"])

    def test_duplicate_source_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate receipt-line intent source identity"):
            subject.reconcile(
                {
                    "now": NOW,
                    "assets": [wheel_asset()],
                    "relationships": [],
                    "receipt_line_intents": [tire_intent(), copy.deepcopy(tire_intent())],
                }
            )

    def test_duplicate_entity_uuid_is_rejected(self):
        duplicate = wheel_asset()
        duplicate["source_record_id"] = "another-wheel"
        with self.assertRaisesRegex(ValueError, "duplicate entity_uuid"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset(), duplicate], "relationships": [], "receipt_line_intents": []}
            )

    def test_source_replay_cannot_replace_entity_uuid(self):
        first = subject.reconcile(self.payload(), UUIDFactory(RELATION))
        changed = tire_intent(entity_uuid="5af0fef4-4c1b-48d9-bde2-f4837041865c")
        with self.assertRaisesRegex(ValueError, "replace immutable entity_uuid"):
            subject.reconcile(
                {
                    "now": NOW,
                    "assets": first["assets"],
                    "relationships": first["relationships"],
                    "receipt_line_intents": [changed],
                }
            )

    def test_individual_tracking_rejects_quantity_greater_than_one(self):
        intent = tire_intent(entity_uuid=TIRE)
        intent["asset"]["tracking_mode"] = "individual"
        with self.assertRaisesRegex(ValueError, "individual tracking requires quantity 1"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]}
            )

    def test_quantity_rejects_bool_zero_decimal_and_negative(self):
        for value in (True, 0, -1, 1.5, "1.5"):
            with self.subTest(value=value):
                intent = tire_intent(entity_uuid=TIRE)
                intent["asset"]["quantity"] = value
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    subject.reconcile(
                        {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]}
                    )

    def test_noncanonical_or_non_rfc_uuid_is_rejected(self):
        for value in ("not-a-uuid", TIRE.upper(), "aaaaaaaa-aaaa-4aaa-7aaa-aaaaaaaaaaaa"):
            with self.subTest(value=value):
                intent = tire_intent(entity_uuid=value)
                with self.assertRaisesRegex(ValueError, "canonical RFC 4122 UUID"):
                    subject.reconcile(
                        {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]}
                    )

    def test_allocator_skips_uuid_collision(self):
        result = subject.reconcile(self.payload(), UUIDFactory(WHEEL, RELATION))
        self.assertEqual(result["created_relationship_uuids"], [RELATION])

    def test_explicit_relationship_uuid_cannot_collide_with_entity_uuid(self):
        intent = tire_intent(entity_uuid=TIRE)
        intent["assignments"][0]["relationship_uuid"] = WHEEL
        with self.assertRaisesRegex(ValueError, "another identity"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]}
            )

    def test_self_relationship_is_rejected(self):
        intent = tire_intent(entity_uuid=TIRE)
        intent["assignments"][0]["to_entity_uuid"] = TIRE
        with self.assertRaisesRegex(ValueError, "itself"):
            subject.reconcile(
                {"now": NOW, "assets": [wheel_asset()], "relationships": [], "receipt_line_intents": [intent]},
                UUIDFactory(RELATION),
            )

    def test_naive_now_is_rejected(self):
        payload = self.payload()
        payload["now"] = "2026-08-24T15:56:53"
        with self.assertRaisesRegex(ValueError, "timezone/UTC offset"):
            subject.reconcile(payload)

    def test_existing_timestamps_require_offsets(self):
        asset = wheel_asset()
        asset["updated_et"] = "2026-08-24T15:56:53"
        with self.assertRaisesRegex(ValueError, "timezone/UTC offset"):
            subject.reconcile({"now": NOW, "assets": [asset], "relationships": [], "receipt_line_intents": []})

    def test_cli_contract_returns_error_without_partial_state(self):
        with self.assertRaisesRegex(ValueError, "input JSON root"):
            subject.reconcile([])


if __name__ == "__main__":
    unittest.main()

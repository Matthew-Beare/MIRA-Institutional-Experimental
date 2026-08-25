#!/usr/bin/env python3
"""Tests for deterministic shipment reconciliation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("reconcile_shipments.py")
SPEC = importlib.util.spec_from_file_location("reconcile_shipments", MODULE_PATH)
assert SPEC and SPEC.loader
reconciler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconciler)


def row(
    shipment_id: str = "SHIP-001",
    vendor: str = "Example Vendor",
    order: str = "ORDER-1",
    item: str = "Example part",
    tracking: str = "TRACK-1",
    status: str = "Shipped",
) -> dict[str, str]:
    return {
        "Shipment ID": shipment_id,
        "Vendor": vendor,
        "Order Number": order,
        "Item": item,
        "Carrier": "FedEx",
        "Tracking Number": tracking,
        "Package Count": "1",
        "Order Date": "8/1/2026",
        "Shipped Date": "8/2/2026",
        "ETA (ET)": "8/5/2026",
        "Status": status,
        "Last Progress (ET)": "8/3/2026 9:00 AM ET",
        "Notes": "",
        "Updated (ET)": "8/3/2026 9:05 AM ET",
    }


def payload(rows: list[dict[str, str]], evidence: list[dict[str, object]]) -> dict[str, object]:
    return {
        "now": "2026-08-16T05:00:00-04:00",
        "shipments": rows,
        "evidence": evidence,
    }


class ReconcileShipmentTests(unittest.TestCase):
    def test_exact_tracking_delivery_deletes_active_row(self):
        result = reconciler.reconcile(
            payload(
                [row()],
                [
                    {
                        "source": "FedEx",
                        "event": "delivered",
                        "tracking_number": "TRACK-1",
                        "event_at": "2026-08-15T14:04:00-04:00",
                    }
                ],
            )
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["delete_ids"], ["SHIP-001"])
        self.assertEqual(result["active_rows"], [])

    def test_explicit_user_delivery_beats_newer_vendor_shipped_status(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="")],
                [
                    {
                        "source": "user",
                        "event": "delivered",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "observed_at": "2026-08-15T08:00:00-04:00",
                    },
                    {
                        "source": "vendor",
                        "event": "shipped",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "observed_at": "2026-08-16T08:00:00-04:00",
                    },
                ],
            )
        )
        self.assertEqual(result["delete_ids"], ["SHIP-001"])
        self.assertEqual(result["active_rows"], [])

    def test_carrier_delivery_beats_later_vendor_status(self):
        result = reconciler.reconcile(
            payload(
                [row()],
                [
                    {
                        "source": "carrier",
                        "event": "delivered",
                        "tracking_number": "TRACK-1",
                        "observed_at": "2026-08-15T12:00:00-04:00",
                    },
                    {
                        "source": "vendor",
                        "event": "shipped",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "observed_at": "2026-08-16T12:00:00-04:00",
                    },
                ],
            )
        )
        self.assertEqual(result["delete_ids"], ["SHIP-001"])
        self.assertEqual(result["active_rows"], [])

    def test_split_tracking_numbers_create_one_active_row_each(self):
        result = reconciler.reconcile(
            payload(
                [],
                [
                    {
                        "source": "vendor",
                        "event": "shipped",
                        "vendor": "Split Vendor",
                        "order_number": "SPLIT-9",
                        "item": "Wheel set",
                        "carrier": "UPS",
                        "tracking_numbers": ["1Z-A", "1Z-B"],
                        "shipped_date": "8/14/2026",
                    }
                ],
            )
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual([item["shipment_id"] for item in result["active_rows"]], ["SHIP-001", "SHIP-002"])
        self.assertEqual(
            [item["tracking_number"] for item in result["active_rows"]],
            ["1Z-A", "1Z-B"],
        )
        self.assertTrue(all(item["package_count"] == "1" for item in result["active_rows"]))

    def test_split_tracking_numbers_accept_normalized_header_and_reject_bad_shape(self):
        result = reconciler.reconcile(
            payload(
                [],
                [{
                    "source": "vendor",
                    "event": "shipped",
                    "vendor": "Split Vendor",
                    "order_number": "SPLIT-10",
                    "item": "Parts",
                    "Tracking Numbers": ["TRACK-A", "TRACK-B"],
                }],
            )
        )
        self.assertEqual(
            [item["tracking_number"] for item in result["active_rows"]],
            ["TRACK-A", "TRACK-B"],
        )

        bad = reconciler.reconcile(
            payload(
                [],
                [{
                    "source": "vendor",
                    "event": "shipped",
                    "vendor": "Split Vendor",
                    "order_number": "SPLIT-10",
                    "item": "Parts",
                    "tracking_numbers": "TRACK-A",
                }],
            )
        )
        self.assertEqual("error", bad["status"])
        self.assertIn("tracking_numbers must be an array", bad["errors"][0])

    def test_ambiguous_order_without_tracking_changes_nothing(self):
        rows = [
            row(shipment_id="SHIP-001", tracking="TRACK-A"),
            row(shipment_id="SHIP-002", tracking="TRACK-B"),
        ]
        result = reconciler.reconcile(
            payload(
                rows,
                [
                    {
                        "source": "vendor",
                        "event": "delayed",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                    }
                ],
            )
        )
        self.assertEqual(len(result["active_rows"]), 2)
        self.assertEqual(result["upserts"], [])
        self.assertEqual(result["unresolved"][0]["reason"], "Ambiguous match; no active row was changed.")

    def test_exact_tracking_updates_eta_and_progress(self):
        result = reconciler.reconcile(
            payload(
                [row()],
                [
                    {
                        "source": "carrier",
                        "event": "in_transit",
                        "tracking_number": "TRACK-1",
                        "eta": "8/17/2026, 9:50 AM–1:50 PM ET",
                        "event_at": "8/16/2026 12:46 AM ET",
                        "notes": "Scheduled for delivery tomorrow.",
                    }
                ],
            )
        )
        active = result["active_rows"][0]
        self.assertEqual(active["eta_et"], "8/17/2026, 9:50 AM–1:50 PM ET")
        self.assertEqual(active["last_progress_et"], "8/16/2026 12:46 AM ET")
        self.assertEqual(active["status"], "Shipped")
        self.assertEqual([item["shipment_id"] for item in result["upserts"]], ["SHIP-001"])

    def test_delivery_without_active_row_does_not_create_history(self):
        result = reconciler.reconcile(
            payload(
                [],
                [
                    {
                        "source": "carrier",
                        "event": "delivered",
                        "tracking_number": "OLD-TRACKING",
                    }
                ],
            )
        )
        self.assertEqual(result["active_rows"], [])
        self.assertEqual(result["delete_ids"], [])
        self.assertEqual(result["ignored"][0]["reason"], "Delivered with no active row.")

    def test_confirmed_full_cancellation_deletes_active_row(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="")],
                [
                    {
                        "source": "user",
                        "event": "cancelled",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "observed_at": "2026-08-16T08:00:00-04:00",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], ["SHIP-001"])
        self.assertEqual(result["active_rows"], [])

    def test_order_scope_cancellation_deletes_all_split_fulfillments(self):
        rows = [
            row(shipment_id="SHIP-001", tracking="TRACK-A"),
            row(shipment_id="SHIP-002", tracking="TRACK-B"),
        ]
        result = reconciler.reconcile(
            payload(
                rows,
                [
                    {
                        "source": "user",
                        "event": "order_cancelled",
                        "scope": "order",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], ["SHIP-001", "SHIP-002"])
        self.assertEqual(result["active_rows"], [])

    def test_partial_cancellation_keeps_only_confirmed_remaining_item_active(self):
        result = reconciler.reconcile(
            payload(
                [row(item="WRX 265 tires + FL5 275 tires", tracking="", status="Exception")],
                [
                    {
                        "source": "user",
                        "event": "partial_cancellation_confirmed",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "cancelled_item": "FL5 275 tires",
                        "remaining_item": "WRX 265 tires",
                        "remaining_status": "Awaiting Shipment",
                        "eta": "8/25/2026",
                        "notes": "FL5 line cancelled before shipment.",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], [])
        self.assertEqual(len(result["active_rows"]), 1)
        active = result["active_rows"][0]
        self.assertEqual(active["item"], "WRX 265 tires")
        self.assertEqual(active["status"], "Awaiting Shipment")
        self.assertEqual(active["eta_et"], "8/25/2026")

    def test_partial_cancellation_requires_explicit_remaining_item(self):
        result = reconciler.reconcile(
            payload(
                [row(item="WRX 265 tires + FL5 275 tires", tracking="", status="Exception")],
                [
                    {
                        "source": "vendor",
                        "event": "partial_cancellation_confirmed",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "cancelled_item": "FL5 275 tires",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], [])
        self.assertEqual(result["active_rows"][0]["item"], "WRX 265 tires + FL5 275 tires")
        self.assertEqual(
            result["unresolved"][0]["reason"],
            "Confirmed partial cancellation requires remaining_item.",
        )

    def test_partial_cancellation_matches_original_item_before_replacing_it(self):
        existing = row(
            item="Original kit",
            order="",
            tracking="",
            status="Exception",
        )
        result = reconciler.reconcile(
            payload(
                [existing],
                [{
                    "source": "vendor",
                    "event": "partial_cancellation_confirmed",
                    "vendor": "Example Vendor",
                    "item": "Original kit",
                    "order_date": "8/1/2026",
                    "remaining_item": "Surviving part",
                    "remaining_status": "Awaiting Shipment",
                }],
            )
        )
        self.assertEqual("ok", result["status"])
        self.assertEqual(1, len(result["active_rows"]))
        self.assertEqual("SHIP-001", result["active_rows"][0]["shipment_id"])
        self.assertEqual("Surviving part", result["active_rows"][0]["item"])

    def test_cancellation_request_stays_actionable_until_confirmed(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="", status="Awaiting Shipment")],
                [
                    {
                        "source": "user",
                        "event": "partial_cancellation_requested",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "notes": "Remove one unavailable line and ship the rest.",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], [])
        self.assertEqual(result["active_rows"][0]["status"], "Exception")

    def test_confirmed_replacement_atomically_closes_original_and_creates_new(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="", status="Exception")],
                [
                    {
                        "source": "user",
                        "event": "order_replaced",
                        "scope": "order",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "original_cancel_confirmed": True,
                        "replacement_order_number": "ORDER-2",
                        "replacement_item": "Replacement part",
                        "replacement_status": "Awaiting Shipment",
                        "original_receipt_id": "RCPT-001",
                        "replacement_receipt_id": "RCPT-002",
                        "replacement_group_id": "REPL-001",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], ["SHIP-001"])
        self.assertEqual(len(result["active_rows"]), 1)
        self.assertEqual(result["active_rows"][0]["order_number"], "ORDER-2")
        self.assertEqual(result["active_rows"][0]["item"], "Replacement part")
        self.assertEqual(result["replacement_links"][0]["state"], "confirmed")
        self.assertEqual(result["replacement_links"][0]["replacement_receipt_id"], "RCPT-002")

    def test_unconfirmed_replacement_keeps_original_exception_and_new_active(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="", status="Awaiting Shipment")],
                [
                    {
                        "source": "vendor",
                        "event": "replacement_confirmed",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "replacement_order_number": "ORDER-2",
                        "replacement_item": "Replacement part",
                    }
                ],
            )
        )
        self.assertEqual(result["delete_ids"], [])
        self.assertEqual(len(result["active_rows"]), 2)
        by_order = {item["order_number"]: item for item in result["active_rows"]}
        self.assertEqual(by_order["ORDER-1"]["status"], "Exception")
        self.assertEqual(by_order["ORDER-2"]["status"], "Awaiting Shipment")
        self.assertEqual(
            result["replacement_links"][0]["state"],
            "pending_original_cancellation",
        )

    def test_replacement_requires_new_order_and_item(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="", status="Exception")],
                [
                    {
                        "source": "user",
                        "event": "order_replaced",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                    }
                ],
            )
        )
        self.assertEqual(result["active_rows"][0]["order_number"], "ORDER-1")
        self.assertEqual(
            result["unresolved"][0]["reason"],
            "Confirmed replacement requires replacement_order_number and replacement_item.",
        )

    def test_same_order_replacement_is_routed_to_revision(self):
        result = reconciler.reconcile(
            payload(
                [row(tracking="", status="Exception")],
                [
                    {
                        "source": "user",
                        "event": "order_replaced",
                        "vendor": "Example Vendor",
                        "order_number": "ORDER-1",
                        "replacement_order_number": "ORDER-1",
                        "replacement_item": "Surviving part",
                    }
                ],
            )
        )
        self.assertEqual(len(result["active_rows"]), 1)
        self.assertEqual(
            result["unresolved"][0]["reason"],
            "Replacement order matches the original; use same-order revision handling.",
        )

    def test_raw_sheet_schema_round_trips_in_canonical_order(self):
        values = [reconciler.HEADERS, list(row().values())]
        result = reconciler.reconcile(
            {
                "now": "2026-08-16T05:00:00-04:00",
                "shipments_values": values,
                "evidence": [],
            }
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["active_values"][0], reconciler.HEADERS)
        self.assertEqual(result["active_values"][1][0], "SHIP-001")

    def test_delivered_is_not_a_valid_active_sheet_status(self):
        result = reconciler.reconcile(payload([row(status="Delivered")], []))
        self.assertEqual(result["status"], "error")
        self.assertIn("invalid active status Delivered", result["errors"][0])

    def test_active_sheet_ids_counts_and_headers_fail_closed(self):
        invalid_id = reconciler.reconcile(payload([row(shipment_id="bad-id")], []))
        self.assertEqual("error", invalid_id["status"])
        self.assertTrue(any("invalid Shipment ID" in item for item in invalid_id["errors"]))

        invalid_count_row = row()
        invalid_count_row["Package Count"] = "zero"
        invalid_count = reconciler.reconcile(payload([invalid_count_row], []))
        self.assertEqual("error", invalid_count["status"])
        self.assertTrue(any("invalid Package Count" in item for item in invalid_count["errors"]))

        duplicate_headers = reconciler.HEADERS + ["Shipment ID"]
        duplicate_values = [list(row().values()) + ["SHIP-999"]]
        result = reconciler.reconcile({
            "now": "2026-08-16T05:00:00-04:00",
            "shipments_values": [duplicate_headers, *duplicate_values],
            "evidence": [],
        })
        self.assertEqual("error", result["status"])
        self.assertTrue(any("duplicate columns" in item for item in result["errors"]))

    def test_unresolved_evidence_marks_run_degraded(self):
        result = reconciler.reconcile(
            payload(
                [row()],
                [{"source": "vendor", "event": "teleported"}],
            )
        )
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(len(result["unresolved"]), 1)

    def test_invalid_event_timestamp_is_rejected(self):
        result = reconciler.reconcile(
            payload(
                [row()],
                [
                    {
                        "source": "carrier",
                        "event": "shipped",
                        "tracking_number": "TRACK-1",
                        "observed_at": "definitely-not-a-time",
                    }
                ],
            )
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("invalid event timestamp", result["errors"][0])

    def test_now_must_be_offset_aware(self):
        bad = payload([row()], [])
        bad["now"] = "2026-08-16T05:00:00"
        with self.assertRaisesRegex(ValueError, "timezone/UTC offset"):
            reconciler.reconcile(bad)

    def test_non_object_shipment_row_is_rejected(self):
        result = reconciler.reconcile(payload(["bad-row"], []))
        self.assertEqual(result["status"], "error")
        self.assertIn("is not an object", result["errors"][0])

    def test_progress_note_appends_without_erasing_existing_notes(self):
        existing = row()
        existing["Notes"] = "Original evidence."
        result = reconciler.reconcile(
            payload(
                [existing],
                [
                    {
                        "source": "carrier",
                        "event": "progress",
                        "tracking_number": "TRACK-1",
                        "notes": "New checkpoint.",
                    }
                ],
            )
        )
        self.assertEqual(
            result["active_rows"][0]["notes"],
            "Original evidence. New checkpoint.",
        )

    def test_note_dedupe_uses_complete_notes_not_substrings(self):
        existing = row()
        existing["Notes"] = "Delivery not scheduled."
        result = reconciler.reconcile(
            payload(
                [existing],
                [{
                    "source": "carrier",
                    "event": "progress",
                    "tracking_number": "TRACK-1",
                    "notes": "scheduled",
                }],
            )
        )
        self.assertEqual(
            "Delivery not scheduled. scheduled",
            result["active_rows"][0]["notes"],
        )

    def test_non_object_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "root must be an object"):
            reconciler.reconcile([])


if __name__ == "__main__":
    unittest.main()

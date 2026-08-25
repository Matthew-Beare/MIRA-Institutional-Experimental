#!/usr/bin/env python3
"""Regression tests for stable shipment-evidence ordering."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("reconcile_shipments.py")
SPEC = importlib.util.spec_from_file_location("reconcile_shipments_ordering", MODULE_PATH)
assert SPEC and SPEC.loader
reconciler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconciler)


def shipment() -> dict[str, str]:
    return {
        "Shipment ID": "SHIP-001",
        "Vendor": "Example Vendor",
        "Order Number": "ORDER-1",
        "Item": "Example part",
        "Carrier": "",
        "Tracking Number": "",
        "Package Count": "1",
        "Order Date": "8/1/2026",
        "Shipped Date": "",
        "ETA (ET)": "",
        "Status": "Awaiting Shipment",
        "Last Progress (ET)": "",
        "Notes": "",
        "Updated (ET)": "8/1/2026 9:00 AM ET",
    }


class ShipmentEvidenceOrderingTests(unittest.TestCase):
    def test_tenth_equal_priority_equal_time_event_remains_last(self) -> None:
        observed_at = "2026-08-16T08:00:00-04:00"
        evidence = [
            {
                "source": "vendor",
                "event": "shipped",
                "vendor": "Example Vendor",
                "order_number": "ORDER-1",
                "eta": f"ETA-{index}",
                "observed_at": observed_at,
            }
            for index in range(1, 11)
        ]
        result = reconciler.reconcile(
            {
                "now": "2026-08-16T09:00:00-04:00",
                "shipments": [shipment()],
                "evidence": evidence,
            }
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["active_rows"][0]["eta_et"], "ETA-10")

    def test_human_et_timestamp_orders_as_eastern_not_utc(self) -> None:
        evidence = [
            {
                "source": "vendor",
                "event": "shipped",
                "vendor": "Example Vendor",
                "order_number": "ORDER-1",
                "eta": "HUMAN-23:00-ET",
                "observed_at": "8/16/2026 11:00 PM ET",
            },
            {
                "source": "vendor",
                "event": "shipped",
                "vendor": "Example Vendor",
                "order_number": "ORDER-1",
                "eta": "ISO-20:30-ET",
                "observed_at": "2026-08-16T20:30:00-04:00",
            },
        ]
        result = reconciler.reconcile(
            {
                "now": "2026-08-17T00:00:00-04:00",
                "shipments": [shipment()],
                "evidence": evidence,
            }
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["active_rows"][0]["eta_et"], "HUMAN-23:00-ET")


if __name__ == "__main__":
    unittest.main()

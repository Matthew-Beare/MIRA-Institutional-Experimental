#!/usr/bin/env python3

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import financial_resolution as policy


TZ = ZoneInfo("America/New_York")


class FinancialResolutionTests(unittest.TestCase):
    def test_revised_before_settlement_needs_no_refund(self):
        case = {
            "receipt_id": "TR-1",
            "financial_resolution_status": "revised_before_settlement",
        }
        result = policy.resolve_case(case, datetime(2026, 8, 31, 12, tzinfo=TZ))
        self.assertEqual(result["status"], "resolved")
        self.assertFalse(result["action_required"])

    def test_five_business_days_preserve_clock_time(self):
        start = datetime(2026, 8, 21, 14, 15, tzinfo=TZ)  # Friday
        self.assertEqual(
            policy.add_business_days(start, 5),
            datetime(2026, 8, 28, 14, 15, tzinfo=TZ),
        )

    def test_pending_refund_not_actionable_before_deadline(self):
        case = {
            "receipt_id": "TR-2",
            "vendor": "Tire Rack",
            "order_number": "VG00001",
            "financial_resolution_status": "refund_expected",
            "cancellation_confirmed_at": "2026-08-21T14:15:00-04:00",
            "expected_amount": "1540.03",
        }
        result = policy.resolve_case(case, datetime(2026, 8, 28, 14, 14, tzinfo=TZ))
        self.assertEqual(result["status"], "pending")
        self.assertFalse(result["action_required"])

    def test_pending_refund_actionable_at_deadline(self):
        case = {
            "receipt_id": "TR-2",
            "vendor": "Tire Rack",
            "order_number": "VG00001",
            "financial_resolution_status": "refund_expected",
            "cancellation_confirmed_at": "2026-08-21T14:15:00-04:00",
            "expected_amount": "1540.03",
            "missing_evidence": "posted refund/reversal",
        }
        result = policy.resolve_case(case, datetime(2026, 8, 28, 14, 15, tzinfo=TZ))
        self.assertEqual(result["status"], "overdue")
        self.assertTrue(result["action_required"])
        self.assertIn("$1,540.03", result["detail"])
        self.assertIn("posted refund/reversal", result["detail"])

    def test_verified_credit_clears_action(self):
        case = {
            "receipt_id": "TR-3",
            "financial_resolution_status": "verified",
            "cancellation_confirmed_at": "2026-08-01T10:00:00-04:00",
        }
        result = policy.resolve_case(case, datetime(2026, 8, 31, 12, tzinfo=TZ))
        self.assertFalse(result["action_required"])

    def test_non_object_case_fails_closed(self):
        with self.assertRaisesRegex(ValueError, r"cases\[1\]"):
            policy.resolve({
                "now": "2026-08-31T12:00:00-04:00",
                "cases": ["not-a-case"],
            })

    def test_non_finite_expected_amount_is_rejected(self):
        for value in ("NaN", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid money value"):
                    policy.money(value)

    def test_refunded_status_is_terminal(self):
        result = policy.resolve_case(
            {"receipt_id": "TR-4", "financial_resolution_status": "refunded"},
            datetime(2026, 8, 31, 12, tzinfo=TZ),
        )
        self.assertEqual("resolved", result["status"])
        self.assertFalse(result["action_required"])

    def test_negative_business_day_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            policy.add_business_days(datetime(2026, 8, 31, 12, tzinfo=TZ), -1)

    def test_naive_financial_times_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "timezone/UTC offset"):
            policy.resolve({"now": "2026-08-31T12:00:00", "cases": []})
        with self.assertRaisesRegex(ValueError, "timezone/UTC offset"):
            policy.add_business_days(datetime(2026, 8, 31, 12), 1)

    def test_blank_missing_evidence_uses_stable_default(self):
        case = {
            "receipt_id": "TR-5",
            "financial_resolution_status": "refund_expected",
            "cancellation_confirmed_at": "2026-08-21T14:15:00-04:00",
            "missing_evidence": "   ",
        }
        result = policy.resolve_case(case, datetime(2026, 8, 28, 14, 15, tzinfo=TZ))
        self.assertIn("posted refund/reversal or confirmed revised charge", result["detail"])

    def test_duplicate_receipt_id_is_rejected(self):
        payload = {
            "now": "2026-08-31T12:00:00-04:00",
            "cases": [
                {"receipt_id": "TR-DUP", "financial_resolution_status": "verified"},
                {"receipt_id": "TR-DUP", "financial_resolution_status": "verified"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "duplicate receipt_id"):
            policy.resolve(payload)

    def test_non_object_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "root must be an object"):
            policy.resolve([])


if __name__ == "__main__":
    unittest.main()

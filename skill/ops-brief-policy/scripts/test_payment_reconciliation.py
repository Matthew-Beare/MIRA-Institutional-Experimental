from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("payment_reconciliation", ROOT / "payment_reconciliation.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PaymentReconciliationTests(unittest.TestCase):
    def test_missing_charge_stays_open(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-1",
            "receipt_id": "R-1",
            "expected_amount": "1479.93",
            "observations": [],
        })
        self.assertEqual("Awaiting Settlement", row["status"])
        self.assertFalse(row["action_required"])

    def test_exact_posted_charge_matches(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-2",
            "receipt_id": "R-2",
            "expected_amount": "660.86",
            "observations": [{"amount": "660.86", "pending": False}],
        })
        self.assertEqual("Matched", row["status"])
        self.assertEqual("$0.00", row["difference"])

    def test_string_false_pending_is_posted_not_pending(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-2S",
            "receipt_id": "R-2S",
            "expected_amount": "660.86",
            "observations": [{"amount": "660.86", "pending": "false"}],
        })
        self.assertEqual("Matched", row["status"])
        self.assertEqual("$0.00", row["observed_pending_amount"])

    def test_split_charge_matches(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-3",
            "receipt_id": "R-3",
            "expected_amount": "100.00",
            "observations": [
                {"amount": "60.00", "pending": False},
                {"amount": "40.00", "pending": False},
            ],
        })
        self.assertEqual("Split Settlement", row["status"])

    def test_pending_exact_amount_is_not_final(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-4",
            "receipt_id": "R-4",
            "expected_amount": "1692.22",
            "observations": [{"amount": "1692.22", "pending": True}],
        })
        self.assertEqual("Pending Match", row["status"])
        self.assertFalse(row["action_required"])

    def test_overcharge_is_actionable(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-5",
            "receipt_id": "R-5",
            "expected_amount": "100.00",
            "observations": [{"amount": "125.00", "pending": False}],
        })
        self.assertEqual("Overcharged", row["status"])
        self.assertTrue(row["action_required"])
        self.assertEqual("$25.00", row["difference"])

    def test_string_false_settlement_window_does_not_force_undercharge(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-5S",
            "receipt_id": "R-5S",
            "expected_amount": "100.00",
            "settlement_window_complete": "false",
            "observations": [{"amount": "75.00", "pending": False}],
        })
        self.assertEqual("Awaiting Settlement", row["status"])
        self.assertFalse(row["action_required"])

    def test_invalid_boolean_text_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid boolean"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-BAD",
                "receipt_id": "R-BAD",
                "expected_amount": "100.00",
                "observations": [{"amount": "100.00", "pending": "perhaps"}],
            })

    def test_non_object_observation_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, r"observations\[1\]"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-BAD-OBS",
                "receipt_id": "R-BAD-OBS",
                "expected_amount": "100.00",
                "observations": ["not-a-row"],
            })

    def test_non_object_case_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, r"cases\[1\]"):
            MODULE.reconcile({"cases": ["not-a-case"]})

    def test_non_finite_money_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid money value"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-NAN",
                "receipt_id": "R-NAN",
                "expected_amount": "NaN",
                "observations": [],
            })

    def test_invalid_direction_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid direction"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-DIR",
                "receipt_id": "R-DIR",
                "expected_amount": "100.00",
                "observations": [{"amount": "100.00", "pending": False, "direction": "sideways"}],
            })

    def test_same_order_removed_before_settlement_resolves_without_refund(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-6",
            "receipt_id": "R-6",
            "expected_amount": "1540.03",
            "merchant_resolution": "revised_before_settlement",
            "observations": [],
        })
        self.assertEqual("Resolved No Settlement", row["status"])
        self.assertFalse(row["action_required"])

    def test_no_settlement_cannot_hide_a_posted_debit(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-7",
            "receipt_id": "R-7",
            "expected_amount": "100.00",
            "merchant_resolution": "no_settlement",
            "observations": [{"amount": "100.00", "pending": False}],
        })
        self.assertEqual("Settlement Contradiction", row["status"])
        self.assertEqual("$100.00", row["observed_posted_amount"])
        self.assertTrue(row["action_required"])

    def test_posted_debit_and_credit_resolve_no_settlement_at_zero_net(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-7R",
            "receipt_id": "R-7R",
            "expected_amount": "100.00",
            "merchant_resolution": "no_settlement",
            "observations": [
                {"amount": "100.00", "direction": "debit", "pending": False},
                {"amount": "100.00", "direction": "credit", "pending": False},
            ],
        })
        self.assertEqual("Resolved No Settlement", row["status"])
        self.assertEqual("$0.00", row["difference"])
        self.assertFalse(row["action_required"])

    def test_pending_credit_is_not_silently_dropped(self) -> None:
        row = MODULE.reconcile_case({
            "payment_case_id": "PAY-7P",
            "receipt_id": "R-7P",
            "expected_amount": "80.00",
            "observations": [
                {"amount": "100.00", "direction": "debit", "pending": False},
                {"amount": "20.00", "direction": "credit", "pending": True},
            ],
        })
        self.assertEqual("Pending Match", row["status"])
        self.assertEqual("-$20.00", row["observed_pending_amount"])
        self.assertEqual("$20.00", row["observed_pending_credit_amount"])
        self.assertFalse(row["action_required"])

    def test_wrong_falsy_case_and_observation_containers_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "cases must be a list"):
            MODULE.reconcile({"cases": {}})
        with self.assertRaisesRegex(ValueError, "observations must be a list"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-SHAPE",
                "receipt_id": "R-SHAPE",
                "expected_amount": "1.00",
                "observations": {},
            })

    def test_unknown_merchant_resolution_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid merchant_resolution"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-STATE",
                "receipt_id": "R-STATE",
                "expected_amount": "1.00",
                "merchant_resolution": "probably fine",
                "observations": [],
            })

    def test_negative_expected_charge_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            MODULE.reconcile_case({
                "payment_case_id": "PAY-NEG",
                "receipt_id": "R-NEG",
                "expected_amount": "-1.00",
                "observations": [],
            })

    def test_duplicate_case_id_is_rejected(self) -> None:
        case = {
            "payment_case_id": "PAY-DUP",
            "receipt_id": "R-DUP",
            "expected_amount": "1.00",
            "observations": [],
        }
        with self.assertRaisesRegex(ValueError, "duplicate payment_case_id"):
            MODULE.reconcile({"cases": [case, dict(case)]})

    def test_duplicate_receipt_id_is_rejected(self) -> None:
        first = {
            "payment_case_id": "PAY-A",
            "receipt_id": "R-DUP",
            "expected_amount": "1.00",
            "observations": [],
        }
        second = {**first, "payment_case_id": "PAY-B"}
        with self.assertRaisesRegex(ValueError, "duplicate receipt_id"):
            MODULE.reconcile({"cases": [first, second]})

    def test_non_object_root_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "root must be an object"):
            MODULE.reconcile([])


if __name__ == "__main__":
    unittest.main()

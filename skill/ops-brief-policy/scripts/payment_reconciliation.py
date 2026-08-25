#!/usr/bin/env python3
"""Reconcile expected merchant charges against pending/posted account observations."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from typing import Any

POLICY_VERSION = "1.1.0"
CENT = Decimal("0.01")
NO_SETTLEMENT_RESOLUTIONS = {
    "no_settlement",
    "revised_before_settlement",
    "cancelled_before_settlement",
}
SETTLEMENT_RESOLUTIONS = {"", "expected", "pending", "settled", "settlement_expected"}


def dec(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value).replace("$", "").replace(",", "")).quantize(CENT)
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"invalid money value: {value!r}") from exc
    if not amount.is_finite():
        raise ValueError(f"invalid money value: {value!r}")
    return amount


def money(value: Decimal) -> str:
    amount = value.quantize(CENT)
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


def boolish(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean for {field}: {value!r}")


def reconcile_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("payment_case_id") or "").strip()
    receipt_id = str(case.get("receipt_id") or "").strip()
    if not case_id:
        raise ValueError("payment_case_id must not be blank")
    if not receipt_id:
        raise ValueError(f"receipt_id must not be blank for {case_id}")
    expected = dec(case.get("expected_amount"))
    if expected < 0:
        raise ValueError(
            f"expected_amount cannot be negative for {case_id or receipt_id}"
        )
    merchant_resolution = str(case.get("merchant_resolution") or "").strip().lower()
    if merchant_resolution not in NO_SETTLEMENT_RESOLUTIONS | SETTLEMENT_RESOLUTIONS:
        raise ValueError(
            f"invalid merchant_resolution for {case_id}: {merchant_resolution!r}"
        )

    observations = case.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError(f"observations must be a list for {case_id or receipt_id}")

    posted_debits: list[Decimal] = []
    pending_debits: list[Decimal] = []
    posted_credits: list[Decimal] = []
    pending_credits: list[Decimal] = []

    for index, row in enumerate(observations, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"observations[{index}] must be an object for {case_id or receipt_id}")
        amount = dec(row.get("amount"))
        pending = boolish(row.get("pending", False), "pending")
        direction = str(row.get("direction") or ("credit" if amount < 0 else "debit")).strip().lower()
        if direction not in {"credit", "debit"}:
            raise ValueError(f"invalid direction for {case_id or receipt_id}: {direction!r}")
        absolute = abs(amount)
        if direction == "credit":
            if pending:
                pending_credits.append(absolute)
            else:
                posted_credits.append(absolute)
            continue
        if pending:
            pending_debits.append(absolute)
        else:
            posted_debits.append(absolute)

    posted = sum(posted_debits, Decimal("0.00")).quantize(CENT)
    pending = sum(pending_debits, Decimal("0.00")).quantize(CENT)
    credits = sum(posted_credits, Decimal("0.00")).quantize(CENT)
    pending_credit = sum(pending_credits, Decimal("0.00")).quantize(CENT)
    net_posted = (posted - credits).quantize(CENT)
    net_pending = (pending - pending_credit).quantize(CENT)
    projected = (net_posted + net_pending).quantize(CENT)
    difference = (net_posted - expected).quantize(CENT)
    posted_activity = bool(posted_debits or posted_credits)
    pending_activity = bool(pending_debits or pending_credits)

    no_settlement = merchant_resolution in NO_SETTLEMENT_RESOLUTIONS
    if no_settlement:
        if pending_activity:
            status = "Pending Release"
            action = False
            detail = None
        elif net_posted != 0:
            status = "Settlement Contradiction"
            action = True
            detail = (
                f"merchant reports no settlement, but {money(net_posted)} "
                "is posted; verify the charge or credit."
            )
        else:
            status = "Resolved No Settlement"
            action = False
            detail = None
        return {
            "payment_case_id": case_id,
            "receipt_id": receipt_id,
            "status": status,
            "expected_amount": money(expected),
            "observed_posted_amount": money(net_posted),
            "observed_pending_amount": money(net_pending),
            "observed_pending_credit_amount": money(pending_credit),
            "difference": money(net_posted),
            "action_required": action,
            "detail": detail,
        }

    settlement_window_complete = boolish(
        case.get("settlement_window_complete", False),
        "settlement_window_complete",
    )
    if not posted_activity and not pending_activity:
        status = "Matched" if expected == 0 else "Awaiting Settlement"
        action = False
    elif pending_activity and projected == expected:
        status = "Pending Match"
        action = False
    elif posted_activity and not pending_activity and net_posted == expected:
        status = "Split Settlement" if len(posted_debits) > 1 or credits else "Matched"
        action = False
    elif net_posted > expected:
        status = "Overcharged"
        action = True
    elif settlement_window_complete and not pending_activity:
        status = "Undercharged"
        action = True
    else:
        status = "Awaiting Settlement"
        action = False

    detail = None
    if status == "Overcharged":
        detail = (
            f"possible merchant overcharge: expected {money(expected)}, "
            f"posted {money(net_posted)}, difference {money(difference)}"
        )
    elif status == "Undercharged":
        detail = (
            f"merchant settlement mismatch: expected {money(expected)}, "
            f"posted {money(net_posted)}, difference {money(difference)}"
        )

    return {
        "payment_case_id": case_id,
        "receipt_id": receipt_id,
        "status": status,
        "expected_amount": money(expected),
        "observed_posted_amount": money(net_posted),
        "observed_pending_amount": money(net_pending),
        "observed_pending_credit_amount": money(pending_credit),
        "difference": money(difference),
        "action_required": action,
        "detail": detail,
    }


def reconcile(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("input JSON root must be an object")
    raw_cases = payload.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("cases must be a list")
    results = []
    seen_case_ids: set[str] = set()
    seen_receipt_ids: set[str] = set()
    for index, row in enumerate(raw_cases, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"cases[{index}] must be an object")
        case_id = str(row.get("payment_case_id") or "").strip()
        if not case_id:
            raise ValueError(f"cases[{index}] has a blank payment_case_id")
        if case_id in seen_case_ids:
            raise ValueError(f"duplicate payment_case_id: {case_id}")
        receipt_id = str(row.get("receipt_id") or "").strip()
        if receipt_id in seen_receipt_ids:
            raise ValueError(f"duplicate receipt_id in payment cases: {receipt_id}")
        seen_case_ids.add(case_id)
        seen_receipt_ids.add(receipt_id)
        results.append(reconcile_case(row))
    return {
        "policy_version": POLICY_VERSION,
        "status": "ok",
        "cases": results,
        "actions_required": [
            {
                "code": "merchant_charge_mismatch",
                "payment_case_id": row["payment_case_id"],
                "receipt_id": row["receipt_id"],
                "detail": row["detail"],
            }
            for row in results
            if row["action_required"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        if args.input == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        output = reconcile(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        output = {"policy_version": POLICY_VERSION, "status": "error", "errors": [str(exc)]}
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if output.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

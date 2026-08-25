#!/usr/bin/env python3
"""Deterministically reconcile normalized email evidence with active shipments."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


POLICY_VERSION = "1.3.0"
ACTIVE_STATUSES = {"Awaiting Shipment", "Shipped", "Exception"}
EASTERN = ZoneInfo("America/New_York")
HEADERS = [
    "Shipment ID",
    "Vendor",
    "Order Number",
    "Item",
    "Carrier",
    "Tracking Number",
    "Package Count",
    "Order Date",
    "Shipped Date",
    "ETA (ET)",
    "Status",
    "Last Progress (ET)",
    "Notes",
    "Updated (ET)",
]
FIELDS = [
    "shipment_id",
    "vendor",
    "order_number",
    "item",
    "carrier",
    "tracking_number",
    "package_count",
    "order_date",
    "shipped_date",
    "eta_et",
    "status",
    "last_progress_et",
    "notes",
    "updated_et",
]


def _key(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


HEADER_MAP = {_key(header): field for header, field in zip(HEADERS, FIELDS)}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _identity(value: Any) -> str:
    return "".join(ch.upper() for ch in _text(value) if ch.isalnum())


def _words(value: Any) -> str:
    return " ".join(_text(value).lower().split())


def _parse_time(value: Any, field: str = "event timestamp") -> float:
    text = _text(value)
    if not text:
        return 0.0
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in (
            "%m/%d/%Y %I:%M %p",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.strptime(text.replace(" ET", ""), fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"invalid {field}: {value!r}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=EASTERN)
    return parsed.timestamp()


def _normalize_now(value: Any) -> str:
    text = _text(value)
    if not text:
        raise ValueError("missing required now timestamp")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid now timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("now timestamp must include a timezone/UTC offset")
    return parsed.astimezone(EASTERN).isoformat()


def _record_from_mapping(raw: dict[str, Any], row_number: int) -> dict[str, str]:
    record = {field: "" for field in FIELDS}
    for name, value in raw.items():
        field = HEADER_MAP.get(_key(name), _key(name))
        if field in record:
            record[field] = _text(value)
    record["_row"] = str(row_number)
    return record


def _records_from_values(values: Any) -> tuple[list[dict[str, str]], list[str]]:
    if not isinstance(values, list) or not values:
        return [], ["Shipments values are missing or empty."]
    if not isinstance(values[0], list):
        return [], ["Shipments header row is not an array."]
    mapped_headers = [HEADER_MAP.get(_key(value), "") for value in values[0]]
    duplicate_headers = sorted(
        field for field in set(mapped_headers) if field and mapped_headers.count(field) > 1
    )
    if duplicate_headers:
        return [], [f"Shipments schema has duplicate columns: {', '.join(duplicate_headers)}."]
    missing = [field for field in FIELDS if field not in mapped_headers]
    if missing:
        return [], [f"Shipments schema is missing: {', '.join(missing)}."]
    records: list[dict[str, str]] = []
    for row_number, row in enumerate(values[1:], start=2):
        if not isinstance(row, list) or not any(_text(value) for value in row):
            continue
        raw = {
            mapped_headers[index]: row[index] if index < len(row) else ""
            for index in range(len(mapped_headers))
            if mapped_headers[index]
        }
        records.append(_record_from_mapping(raw, row_number))
    return records, []


def _load_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    if "shipments_values" in payload:
        rows, errors = _records_from_values(payload.get("shipments_values"))
    else:
        raw_rows = payload.get("shipments", [])
        if not isinstance(raw_rows, list):
            return [], ["shipments must be an array."]
        rows = []
        errors = []
        for row_number, raw in enumerate(raw_rows, start=2):
            if not isinstance(raw, dict):
                errors.append(f"Shipments row {row_number} is not an object.")
                continue
            mapped_names = [HEADER_MAP.get(_key(name), _key(name)) for name in raw]
            duplicates = sorted(
                name for name in set(mapped_names) if mapped_names.count(name) > 1
            )
            if duplicates:
                errors.append(
                    f"Shipments row {row_number} has duplicate normalized fields: "
                    + ", ".join(duplicates)
                    + "."
                )
            rows.append(_record_from_mapping(raw, row_number))

    seen_ids: set[str] = set()
    seen_tracking: set[str] = set()
    for row in rows:
        row_id = row["shipment_id"]
        if not row_id:
            errors.append(f"Shipments row {row['_row']} has no Shipment ID.")
        elif not re.fullmatch(r"SHIP-\d{1,12}", row_id):
            errors.append(f"Shipments row {row['_row']} has invalid Shipment ID {row_id}.")
        elif row_id in seen_ids:
            errors.append(f"Duplicate Shipment ID: {row_id}.")
        seen_ids.add(row_id)
        if row["status"] not in ACTIVE_STATUSES:
            errors.append(
                f"{row_id or 'Shipments row ' + row['_row']} has invalid active status "
                f"{row['status'] or '<blank>'}."
            )
        tracking = _identity(row["tracking_number"])
        if tracking and tracking in seen_tracking:
            errors.append(f"Duplicate active tracking number: {row['tracking_number']}.")
        if tracking:
            seen_tracking.add(tracking)
        package_count = row["package_count"]
        if package_count and (
            not re.fullmatch(r"\d+", package_count) or not package_count.strip("0")
        ):
            errors.append(
                f"{row_id or 'Shipments row ' + row['_row']} has invalid Package Count "
                f"{package_count}."
            )
    return rows, errors


def _expand_evidence(raw_events: Any) -> tuple[list[dict[str, str]], list[str]]:
    if not isinstance(raw_events, list):
        return [], ["evidence must be an array."]
    events: list[dict[str, str]] = []
    errors: list[str] = []
    for index, raw in enumerate(raw_events, start=1):
        if not isinstance(raw, dict):
            errors.append(f"Evidence {index} is not an object.")
            continue
        normalized: dict[str, Any] = {}
        duplicate = False
        for name, value in raw.items():
            key = _key(name)
            if key in normalized:
                errors.append(f"Evidence {index}: duplicate normalized field {key}.")
                duplicate = True
            normalized[key] = value
        if duplicate:
            continue
        tracking_numbers = normalized.pop("trackingnumbers", None)
        base = {name: _text(value) for name, value in normalized.items()}
        if tracking_numbers is not None and not isinstance(tracking_numbers, list):
            errors.append(f"Evidence {index}: tracking_numbers must be an array.")
            continue
        if isinstance(tracking_numbers, list) and tracking_numbers:
            if any(
                isinstance(tracking, bool)
                or not isinstance(tracking, (str, int))
                or not _text(tracking)
                for tracking in tracking_numbers
            ):
                errors.append(
                    f"Evidence {index}: tracking_numbers must contain nonblank strings or integers."
                )
                continue
            total = len(tracking_numbers)
            for piece, tracking in enumerate(tracking_numbers, start=1):
                event = dict(base)
                event["trackingnumber"] = _text(tracking)
                event["packagecount"] = "1"
                note = event.get("notes", "")
                suffix = f"Package {piece} of {total}."
                event["notes"] = f"{note} {suffix}".strip()
                event["_evidence_index"] = f"{index}.{piece}"
                events.append(event)
        else:
            base["_evidence_index"] = str(index)
            events.append(base)
    for event in events:
        try:
            _event_time(event)
        except ValueError as exc:
            errors.append(f"Evidence {event['_evidence_index']}: {exc}")
    return events, errors


def _event_name(event: dict[str, str]) -> str:
    return _key(event.get("event") or event.get("status"))


def _source_name(event: dict[str, str]) -> str:
    return _key(event.get("source"))


def _is_delivered(event: dict[str, str]) -> bool:
    return _event_name(event) in {"delivered", "received", "userdelivered", "pickedup"}


FULL_CANCELLATION_EVENTS = {
    "cancelled",
    "canceled",
    "ordercancelled",
    "ordercanceled",
    "cancellationconfirmed",
    "cancelconfirmed",
}
PARTIAL_CANCELLATION_EVENTS = {
    "partialcancellationconfirmed",
    "partialcancelconfirmed",
}
CANCELLATION_REQUEST_EVENTS = {
    "cancellationrequested",
    "cancelrequested",
    "partialcancellationrequested",
    "partialcancelrequested",
}
REPLACEMENT_EVENTS = {
    "replacementconfirmed",
    "orderreplacementconfirmed",
    "orderreplaced",
    "replaced",
}


def _is_cancelled(event: dict[str, str]) -> bool:
    return _event_name(event) in FULL_CANCELLATION_EVENTS


def _is_partial_cancellation(event: dict[str, str]) -> bool:
    return _event_name(event) in PARTIAL_CANCELLATION_EVENTS


def _is_cancellation_requested(event: dict[str, str]) -> bool:
    return _event_name(event) in CANCELLATION_REQUEST_EVENTS


def _is_replacement(event: dict[str, str]) -> bool:
    return _event_name(event) in REPLACEMENT_EVENTS


def _is_truthy(value: Any) -> bool:
    return _key(value) in {"1", "true", "yes", "confirmed"}


def _is_terminal(event: dict[str, str]) -> bool:
    return _is_delivered(event) or _is_cancelled(event)


def _is_order_scope(event: dict[str, str]) -> bool:
    return _key(event.get("scope")) in {"order", "entireorder", "fullorder"}


def _active_status(event: dict[str, str]) -> str | None:
    name = _event_name(event)
    if _is_partial_cancellation(event):
        status = _text(event.get("remainingstatus")) or "Awaiting Shipment"
        return status if status in ACTIVE_STATUSES else None
    if _is_cancellation_requested(event):
        return "Exception"
    if name in {"order", "ordered", "confirmed", "orderconfirmed", "awaitingshipment"}:
        return "Awaiting Shipment"
    if name in {
        "shipped",
        "intransit",
        "outfordelivery",
        "deliveryscheduled",
        "progress",
    }:
        return "Shipped"
    if name in {
        "exception",
        "delayed",
        "lost",
        "held",
        "returntosender",
    }:
        return "Exception"
    return None


def _priority(event: dict[str, str]) -> int:
    source = _source_name(event)
    name = _event_name(event)
    if source in {"user", "explicituser"}:
        return 550 if _is_delivered(event) else 500
    if source in {"carrier", "usps", "fedex", "ups", "dhl"}:
        if _is_delivered(event):
            return 450
        if name in {"exception", "delayed", "lost", "held", "returntosender"}:
            return 400
        return 350
    if source in {"vendor", "merchant", "retailer"}:
        if _is_delivered(event):
            return 300
        if _is_cancelled(event) or _is_partial_cancellation(event) or _is_replacement(event):
            return 275
        if name in {"exception", "delayed", "lost", "held", "returntosender"}:
            return 250
        if _is_cancellation_requested(event):
            return 250
        return 200
    return 100


def _event_time(event: dict[str, str]) -> float:
    return _parse_time(
        event.get("observedat")
        or event.get("eventat")
        or event.get("lastprogresset")
        or event.get("updatedet")
    )


def _candidate_rows(rows: list[dict[str, str]], event: dict[str, str]) -> list[dict[str, str]]:
    tracking = _identity(event.get("trackingnumber"))
    if tracking:
        exact = [row for row in rows if _identity(row["tracking_number"]) == tracking]
        if exact:
            return exact

    vendor = _words(event.get("vendor"))
    order = _identity(event.get("ordernumber"))
    if vendor and order:
        candidates = [
            row
            for row in rows
            if _words(row["vendor"]) == vendor and _identity(row["order_number"]) == order
        ]
        if tracking:
            candidates = [row for row in candidates if not _identity(row["tracking_number"])]
        if candidates:
            return candidates

    if order:
        candidates = [row for row in rows if _identity(row["order_number"]) == order]
        if tracking:
            candidates = [row for row in candidates if not _identity(row["tracking_number"])]
        if candidates:
            return candidates

    item = _words(event.get("item"))
    order_date = _text(event.get("orderdate"))
    if vendor and item and order_date:
        candidates = [
            row
            for row in rows
            if _words(row["vendor"]) == vendor
            and _words(row["item"]) == item
            and _text(row["order_date"]) == order_date
        ]
        if candidates:
            return candidates
    return []


def _fingerprints(row_or_event: dict[str, str]) -> set[str]:
    get = row_or_event.get
    tracking = _identity(get("tracking_number") or get("trackingnumber"))
    vendor = _words(get("vendor"))
    order = _identity(get("order_number") or get("ordernumber"))
    item = _words(get("item"))
    order_date = _text(get("order_date") or get("orderdate"))
    result: set[str] = set()
    if tracking:
        result.add(f"tracking:{tracking}")
    if vendor and order:
        result.add(f"vendor-order:{vendor}:{order}")
    if order:
        result.add(f"order:{order}")
    if vendor and item and order_date:
        result.add(f"vendor-item-date:{vendor}:{item}:{order_date}")
    return result


def _next_id(rows: list[dict[str, str]], allocated: set[str]) -> str:
    highest = 0
    for value in [row["shipment_id"] for row in rows] + list(allocated):
        match = re.fullmatch(r"SHIP-(\d+)", value or "")
        if match:
            highest = max(highest, int(match.group(1)))
    candidate = highest + 1
    while f"SHIP-{candidate:03d}" in allocated:
        candidate += 1
    return f"SHIP-{candidate:03d}"


def _value(event: dict[str, str], *names: str) -> str:
    for name in names:
        value = _text(event.get(_key(name)))
        if value:
            return value
    return ""


def _apply_event(row: dict[str, str], event: dict[str, str], now: str, status: str) -> None:
    updates = {
        "vendor": _value(event, "vendor"),
        "order_number": _value(event, "order_number"),
        "item": _value(event, "item"),
        "carrier": _value(event, "carrier"),
        "tracking_number": _value(event, "tracking_number"),
        "package_count": _value(event, "package_count"),
        "order_date": _value(event, "order_date"),
        "shipped_date": _value(event, "shipped_date"),
        "eta_et": _value(event, "eta_et", "eta"),
        "last_progress_et": _value(event, "event_at", "last_progress_et", "observed_at"),
    }
    for field, value in updates.items():
        if value:
            row[field] = value
    note = _value(event, "notes")
    existing_notes = {
        _words(part)
        for part in re.split(r"(?<=[.!?])\s+|\s+\|\s+", row["notes"])
        if _words(part)
    }
    if note and _words(note) not in existing_notes:
        row["notes"] = f"{row['notes']} {note}".strip()
    row["status"] = status
    row["updated_et"] = now


def _new_row(shipment_id: str) -> dict[str, str]:
    row = {field: "" for field in FIELDS}
    row["shipment_id"] = shipment_id
    row["_row"] = ""
    return row


def _replacement_active_event(event: dict[str, str]) -> dict[str, str]:
    return {
        "_evidence_index": event["_evidence_index"],
        "source": event.get("source", ""),
        "event": _value(event, "replacement_status") or "Awaiting Shipment",
        "vendor": _value(event, "replacement_vendor", "vendor"),
        "ordernumber": _value(event, "replacement_order_number"),
        "item": _value(event, "replacement_item"),
        "carrier": _value(event, "replacement_carrier"),
        "trackingnumber": _value(event, "replacement_tracking_number"),
        "packagecount": _value(event, "replacement_package_count"),
        "orderdate": _value(event, "replacement_order_date"),
        "shippeddate": _value(event, "replacement_shipped_date"),
        "eta": _value(event, "replacement_eta", "eta"),
        "observedat": _value(event, "observed_at", "event_at"),
        "notes": _value(event, "replacement_notes", "notes"),
    }


def _public_row(row: dict[str, str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in FIELDS}


def _values(rows: list[dict[str, str]]) -> list[list[str]]:
    return [HEADERS] + [[row.get(field, "") for field in FIELDS] for row in rows]


def reconcile(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("input JSON root must be an object")
    now = _normalize_now(payload.get("now"))
    rows, row_errors = _load_rows(payload)
    events, evidence_errors = _expand_evidence(payload.get("evidence", []))
    errors = row_errors + evidence_errors
    if errors:
        return {
            "status": "error",
            "policy_version": POLICY_VERSION,
            "errors": errors,
            "active_rows": [_public_row(row) for row in rows],
            "active_values": _values(rows),
            "upserts": [],
            "delete_ids": [],
            "unresolved": [],
            "ignored": [],
            "replacement_links": [],
        }

    allocated = {row["shipment_id"] for row in rows}
    upsert_ids: set[str] = set()
    delete_ids: list[str] = []
    unresolved: list[dict[str, str]] = []
    ignored: list[dict[str, str]] = []
    replacement_links: list[dict[str, str]] = []
    closed_fingerprints: set[str] = set()

    events.sort(
        key=lambda event: (
            _priority(event),
            _event_time(event),
            tuple(int(part) for part in event["_evidence_index"].split(".")),
        )
    )
    for event in events:
        event_index = event["_evidence_index"]
        event_name = _event_name(event)
        if _is_replacement(event):
            replacement_order = _value(event, "replacement_order_number")
            replacement_item = _value(event, "replacement_item")
            if not replacement_order or not replacement_item:
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Confirmed replacement requires replacement_order_number and replacement_item.",
                    }
                )
                continue
            original_order = _value(event, "order_number")
            if original_order and _identity(original_order) == _identity(replacement_order):
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Replacement order matches the original; use same-order revision handling.",
                    }
                )
                continue
            original_candidates = _candidate_rows(rows, event)
            if len(original_candidates) > 1 and not _is_order_scope(event):
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Ambiguous original replacement match; no active row was changed.",
                    }
                )
                continue

            replacement_event = _replacement_active_event(event)
            replacement_status = _active_status(replacement_event)
            if replacement_status is None:
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Replacement status must be Awaiting Shipment, Shipped, or Exception.",
                    }
                )
                continue
            replacement_candidates = _candidate_rows(rows, replacement_event)
            if len(replacement_candidates) > 1:
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Ambiguous replacement shipment match; no active row was changed.",
                    }
                )
                continue

            cancellation_confirmed = _is_truthy(event.get("originalcancelconfirmed"))
            if original_candidates:
                originals = original_candidates if _is_order_scope(event) else original_candidates[:1]
                if cancellation_confirmed:
                    for original in originals:
                        delete_ids.append(original["shipment_id"])
                        closed_fingerprints.update(_fingerprints(original))
                        rows.remove(original)
                else:
                    for original in originals:
                        original["status"] = "Exception"
                        original["updated_et"] = now
                        note = "Replacement ordered; original cancellation unconfirmed."
                        original["notes"] = f"{original['notes']} {note}".strip()
                        upsert_ids.add(original["shipment_id"])

            if replacement_candidates:
                replacement_row = replacement_candidates[0]
            else:
                shipment_id = _next_id(rows, allocated)
                allocated.add(shipment_id)
                replacement_row = _new_row(shipment_id)
                rows.append(replacement_row)
            _apply_event(replacement_row, replacement_event, now, replacement_status)
            upsert_ids.add(replacement_row["shipment_id"])
            replacement_links.append(
                {
                    "evidence": event_index,
                    "original_order_number": original_order,
                    "replacement_order_number": replacement_order,
                    "original_receipt_id": _value(event, "original_receipt_id", "receipt_id"),
                    "replacement_receipt_id": _value(event, "replacement_receipt_id"),
                    "replacement_group_id": _value(event, "replacement_group_id"),
                    "state": "confirmed" if cancellation_confirmed else "pending_original_cancellation",
                }
            )
            continue
        match_event = event
        if _is_partial_cancellation(event):
            remaining_item = _value(event, "remaining_item")
            if not remaining_item:
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Confirmed partial cancellation requires remaining_item.",
                    }
                )
                continue
            event = dict(event)
            event["item"] = remaining_item
        status = _active_status(event)
        if not _is_terminal(event) and status is None:
            unresolved.append(
                {"evidence": event_index, "reason": f"Unsupported event: {event_name or '<blank>'}."}
            )
            continue

        candidates = _candidate_rows(rows, match_event)
        if len(candidates) > 1 and not (_is_cancelled(event) and _is_order_scope(event)):
            unresolved.append(
                {
                    "evidence": event_index,
                    "reason": "Ambiguous match; no active row was changed.",
                }
            )
            continue

        if _is_terminal(event):
            if candidates:
                terminal_rows = candidates if _is_cancelled(event) and _is_order_scope(event) else candidates[:1]
                for row in terminal_rows:
                    delete_ids.append(row["shipment_id"])
                    closed_fingerprints.update(_fingerprints(row))
                    rows.remove(row)
                closed_fingerprints.update(_fingerprints(event))
            elif _fingerprints(event) & closed_fingerprints:
                ignored.append({"evidence": event_index, "reason": "Duplicate terminal evidence."})
            else:
                terminal_name = "Delivered" if _is_delivered(event) else "Cancelled"
                ignored.append({"evidence": event_index, "reason": f"{terminal_name} with no active row."})
            continue

        if _is_partial_cancellation(event) and not candidates:
            unresolved.append(
                {
                    "evidence": event_index,
                    "reason": "Confirmed partial cancellation has no unique active row.",
                }
            )
            continue

        if candidates:
            row = candidates[0]
        else:
            has_identity = bool(
                _identity(event.get("trackingnumber"))
                or (_words(event.get("vendor")) and _identity(event.get("ordernumber")))
            )
            if not has_identity:
                unresolved.append(
                    {
                        "evidence": event_index,
                        "reason": "Insufficient identity to create an active shipment.",
                    }
                )
                continue
            shipment_id = _next_id(rows, allocated)
            allocated.add(shipment_id)
            row = _new_row(shipment_id)
            rows.append(row)
        _apply_event(row, event, now, status or "Exception")
        upsert_ids.add(row["shipment_id"])

    rows.sort(
        key=lambda row: (
            int(re.fullmatch(r"SHIP-(\d+)", row["shipment_id"]).group(1))
            if re.fullmatch(r"SHIP-(\d+)", row["shipment_id"])
            else sys.maxsize,
            row["shipment_id"],
        )
    )
    _, invariant_errors = _load_rows({"shipments": [_public_row(row) for row in rows]})
    active_ids = {row["shipment_id"] for row in rows}
    overlap = active_ids.intersection(delete_ids)
    if overlap:
        invariant_errors.append(
            "Active and deleted Shipment IDs overlap: " + ", ".join(sorted(overlap))
        )
    status = "error" if invariant_errors else "degraded" if unresolved else "ok"
    return {
        "status": status,
        "policy_version": POLICY_VERSION,
        "active_rows": [_public_row(row) for row in rows],
        "active_values": _values(rows),
        "upserts": [
            _public_row(row) for row in rows if row["shipment_id"] in upsert_ids
        ],
        "delete_ids": list(dict.fromkeys(delete_ids)),
        "unresolved": unresolved,
        "ignored": ignored,
        "replacement_links": replacement_links,
        "errors": invariant_errors,
    }


def _read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--input", required=True, help="UTF-8 JSON file or - for stdin")
    reconcile_parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        output = reconcile(_read_json(args.input))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        output = {"status": "error", "policy_version": POLICY_VERSION, "errors": [str(exc)]}
    json.dump(output, sys.stdout, indent=2 if args.pretty else None, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if output.get("status") in {"ok", "degraded"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

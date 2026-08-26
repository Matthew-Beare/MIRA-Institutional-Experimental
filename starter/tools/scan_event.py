#!/usr/bin/env python3
"""Normalize barcode/QR/RFID observations, bind tags, and create location events."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SCAN_NAMESPACE = uuid.UUID("46cfdb27-e298-43d7-bd0b-fbdb3e013c8f")
MOVE_NAMESPACE = uuid.UUID("8ecab95c-24a2-4c54-92e8-5177f6724e89")
RFID_NAMESPACE = uuid.UUID("19853b4d-d292-430b-af41-ad22721f0f62")
TAG_PATTERN = re.compile(r"^MIRROR-TAG:([0-9a-fA-F-]{36})$")
SUPPORTED_GTIN_LENGTHS = {8, 12, 13, 14}
RFID_PROTOCOLS = {"epc_gen2", "nfc_uid", "hf_uid", "other"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _uuid(value: Any, field: str) -> str:
    raw = _required(value, field)
    try:
        parsed = uuid.UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be a UUID") from exc
    return str(parsed)


def _timestamp(value: Any, field: str) -> str:
    raw = _required(value, field)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include timezone/offset")
    return parsed.isoformat()


def _optional_uuid(value: Any, field: str) -> str:
    raw = _text(value)
    return _uuid(raw, field) if raw else ""


def _optional_finite_number(value: Any, field: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _gtin_valid(value: str) -> bool:
    if not value.isdigit() or len(value) not in SUPPORTED_GTIN_LENGTHS:
        return False
    digits = [int(char) for char in value]
    check = digits.pop()
    total = 0
    for index, digit in enumerate(reversed(digits)):
        total += digit * (3 if index % 2 == 0 else 1)
    return (10 - (total % 10)) % 10 == check


def classify(raw_value: str, symbology: str = "") -> dict[str, Any]:
    raw = _required(raw_value, "raw_value")
    match = TAG_PATTERN.fullmatch(raw)
    if match:
        tag_uuid = _uuid(match.group(1), "tag_uuid")
        return {"scan_class": "mirror_tag", "tag_uuid": tag_uuid, "identifier": raw}
    digits = re.sub(r"\s+", "", raw)
    if digits.isdigit() and len(digits) in SUPPORTED_GTIN_LENGTHS:
        if not _gtin_valid(digits):
            raise ValueError("GTIN/UPC/EAN check digit is invalid")
        return {"scan_class": "product_identifier", "namespace": "gtin", "identifier": digits}
    return {
        "scan_class": "external_or_unresolved_identifier",
        "namespace": _text(symbology).lower() or "unknown",
        "identifier": raw,
    }


def normalize_scan(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    raw = _required(payload.get("raw_value"), "raw_value")
    captured_at = _timestamp(payload.get("captured_at"), "captured_at")
    client_id = _required(payload.get("client_id"), "client_id")
    symbology = _text(payload.get("symbology"))
    scan_uuid = _text(payload.get("scan_uuid")) or str(
        uuid.uuid5(SCAN_NAMESPACE, f"{client_id}\x1f{captured_at}\x1f{symbology}\x1f{raw}")
    )
    scan_uuid = _uuid(scan_uuid, "scan_uuid")
    return {
        "schema_version": SCHEMA_VERSION,
        "scan_uuid": scan_uuid,
        "captured_at": captured_at,
        "client_id": client_id,
        "raw_value": raw,
        "symbology": symbology,
        "classification": classify(raw, symbology),
        "photo_evidence_uuid": _optional_uuid(payload.get("photo_evidence_uuid"), "photo_evidence_uuid"),
    }


def normalize_rfid_observation(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize one reader observation without pretending presence is a location move."""

    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    tag_id = _required(payload.get("tag_id"), "tag_id")
    protocol = _required(payload.get("protocol"), "protocol").lower()
    if protocol not in RFID_PROTOCOLS:
        raise ValueError("protocol must be epc_gen2, nfc_uid, hf_uid, or other")
    observed_at = _timestamp(payload.get("observed_at"), "observed_at")
    reader_id = _required(payload.get("reader_id"), "reader_id")
    zone_uuid = _optional_uuid(payload.get("zone_uuid"), "zone_uuid")
    antenna_id = _text(payload.get("antenna_id"))
    rssi_dbm = _optional_finite_number(payload.get("rssi_dbm"), "rssi_dbm")
    observation_uuid = _text(payload.get("observation_uuid")) or str(
        uuid.uuid5(
            RFID_NAMESPACE,
            f"{protocol}\x1f{tag_id}\x1f{reader_id}\x1f{zone_uuid}\x1f{antenna_id}\x1f{observed_at}",
        )
    )
    observation_uuid = _uuid(observation_uuid, "observation_uuid")
    observation = {
        "observation_uuid": observation_uuid,
        "tag_id": tag_id,
        "protocol": protocol,
        "observed_at": observed_at,
        "reader_id": reader_id,
        "zone_uuid": zone_uuid,
        "antenna_id": antenna_id,
        "rssi_dbm": rssi_dbm,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_presence_observation",
        "observation": observation,
        "identity_rule": "RFID tag identifiers are aliases/evidence linked to immutable asset UUIDs; they never replace canonical identity.",
        "location_rule": "One RFID observation is presence evidence only and MUST NOT silently create or replace a canonical asset location event.",
        "promotion_rule": "A configured bounded rule may promote corroborated reader/zone evidence to a location event only through canonical inventory authority with idempotency and readback.",
    }


def _registry(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("tag_registry", [])
    if not isinstance(rows, list):
        raise ValueError("tag_registry must be a list")
    output: list[dict[str, Any]] = []
    seen_tags: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"tag_registry[{index}] must be an object")
        tag_uuid = _uuid(raw.get("tag_uuid"), f"tag_registry[{index}].tag_uuid")
        if tag_uuid in seen_tags:
            raise ValueError("tag_registry contains duplicate tag_uuid")
        seen_tags.add(tag_uuid)
        target_type = _required(raw.get("target_type"), f"tag_registry[{index}].target_type")
        if target_type not in {"asset", "location", "evidence"}:
            raise ValueError("tag target_type must be asset, location, or evidence")
        output.append({
            "tag_uuid": tag_uuid,
            "target_type": target_type,
            "target_uuid": _uuid(raw.get("target_uuid"), f"tag_registry[{index}].target_uuid"),
            "status": _text(raw.get("status")) or "active",
        })
    return output


def bind_tag(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    tag_uuid = _uuid(payload.get("tag_uuid"), "tag_uuid")
    target_type = _required(payload.get("target_type"), "target_type")
    if target_type not in {"asset", "location", "evidence"}:
        raise ValueError("target_type must be asset, location, or evidence")
    target_uuid = _uuid(payload.get("target_uuid"), "target_uuid")
    registry = _registry(payload)
    existing = next((row for row in registry if row["tag_uuid"] == tag_uuid), None)
    if existing:
        if existing["target_type"] == target_type and existing["target_uuid"] == target_uuid and existing["status"] == "active":
            return {"status": "already_bound", "binding": existing, "tag_registry": registry}
        raise ValueError("tag_uuid is already bound to a different live target")
    binding = {"tag_uuid": tag_uuid, "target_type": target_type, "target_uuid": target_uuid, "status": "active"}
    registry.append(binding)
    return {"status": "bound", "binding": binding, "tag_registry": registry}


def resolve_tag(payload: dict[str, Any]) -> dict[str, Any]:
    scan = normalize_scan(payload.get("scan", {}))
    if scan["classification"]["scan_class"] != "mirror_tag":
        raise ValueError("scan is not a M.I.R.R.O.R. preprinted tag")
    tag_uuid = scan["classification"]["tag_uuid"]
    registry = _registry(payload)
    binding = next((row for row in registry if row["tag_uuid"] == tag_uuid and row["status"] == "active"), None)
    return {"scan": scan, "status": "bound" if binding else "unassigned", "binding": binding}


def move_asset(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    asset_uuid = _uuid(payload.get("asset_uuid"), "asset_uuid")
    location_uuid = _uuid(payload.get("location_uuid"), "location_uuid")
    moved_at = _timestamp(payload.get("moved_at"), "moved_at")
    source_scan_uuid = _uuid(payload.get("source_scan_uuid"), "source_scan_uuid")
    event_uuid = str(uuid.uuid5(MOVE_NAMESPACE, f"{asset_uuid}\x1f{location_uuid}\x1f{source_scan_uuid}"))
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_location_event",
        "event": {
            "event_uuid": event_uuid,
            "asset_uuid": asset_uuid,
            "location_uuid": location_uuid,
            "moved_at": moved_at,
            "source_scan_uuid": source_scan_uuid,
            "relationship_type": "located_at",
        },
        "mutation_rule": "Write through canonical inventory/location authority with idempotency and readback before reporting completion.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["normalize", "bind", "resolve", "move", "rfid"])
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        fn = {
            "normalize": normalize_scan,
            "bind": bind_tag,
            "resolve": resolve_tag,
            "move": move_asset,
            "rfid": normalize_rfid_observation,
        }[args.action]
        print(json.dumps(fn(payload), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

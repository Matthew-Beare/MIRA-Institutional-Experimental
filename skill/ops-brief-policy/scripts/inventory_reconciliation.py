#!/usr/bin/env python3
"""Reconcile receipt lines into immutable asset identities and relationships."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo


POLICY_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
EASTERN = ZoneInfo("America/New_York")

TRACKING_MODES = {"individual", "set", "lot"}
LIFECYCLE_STATUSES = {
    "ordered",
    "in_transit",
    "delivered",
    "in_service",
    "installed",
    "returned",
    "disposed",
    "retired",
}
RELATIONSHIP_TYPES = {
    "owned_by",
    "assigned_to",
    "installed_on",
    "stored_at",
    "replaces",
    "alias_of",
    "used_with",
}
RELATIONSHIP_STATUSES = {"planned", "active", "inactive", "retired"}
LINE_STATUSES = {
    "included",
    "ordered",
    "shipped",
    "delivered",
    "returned",
    "refunded",
    "cancelled",
    "removed_before_settlement",
}
EXCLUDED_LINE_STATUSES = {"cancelled", "removed_before_settlement"}

ASSET_FIELDS = (
    "entity_uuid",
    "friendly_id",
    "asset_type",
    "label",
    "quantity",
    "tracking_mode",
    "lifecycle_status",
    "owner_uuid",
    "source_authority",
    "source_record_id",
    "receipt_id",
    "receipt_line_id",
    "manufacturer",
    "model",
    "part_number",
    "evidence_link",
    "notes",
    "created_et",
    "updated_et",
    "schema_version",
)
RELATIONSHIP_FIELDS = (
    "relationship_uuid",
    "from_entity_uuid",
    "relationship_type",
    "to_entity_uuid",
    "status",
    "source_authority",
    "source_record_id",
    "receipt_id",
    "receipt_line_id",
    "evidence_link",
    "notes",
    "effective_from_et",
    "effective_to_et",
    "updated_et",
    "schema_version",
)


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required_text(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _normalized_token(value: Any, field: str) -> str:
    token = _required_text(value, field).lower()
    if not all(ch.isalnum() or ch == "_" for ch in token):
        raise ValueError(f"{field} must use lowercase snake_case: {value!r}")
    return token


def _timestamp(value: Any, field: str, *, required: bool = True) -> str:
    text = _text(value)
    if not text:
        if required:
            raise ValueError(f"{field} must be nonblank")
        return ""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone/UTC offset")
    return parsed.astimezone(EASTERN).isoformat()


def _parse_now(value: Any) -> str:
    return _timestamp(value, "now timestamp")


def _uuid(value: Any, field: str) -> str:
    raw = _required_text(value, field)
    text = raw.lower()
    try:
        parsed = uuid.UUID(text)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID: {value!r}") from exc
    if raw != text or str(parsed) != text or parsed.variant != uuid.RFC_4122 or parsed.version not in {1, 3, 4, 5}:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID: {value!r}")
    return text


def _optional_uuid(value: Any, field: str) -> str:
    return "" if not _text(value) else _uuid(value, field)


def _quantity(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and value.strip().isdigit():
        result = int(value.strip())
    else:
        raise ValueError(f"{field} must be a positive integer")
    if result < 1:
        raise ValueError(f"{field} must be a positive integer")
    return result


def _source_key(authority: Any, record_id: Any, prefix: str) -> tuple[str, str, str]:
    source_authority = _normalized_token(authority, f"{prefix}.source_authority")
    source_record_id = _required_text(record_id, f"{prefix}.source_record_id")
    return source_authority, source_record_id, f"{source_authority}\x1f{source_record_id}"


def _new_uuid(factory: Callable[[], uuid.UUID], used: set[str]) -> str:
    for _ in range(10):
        candidate = _uuid(str(factory()), "allocated UUID")
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise ValueError("UUID allocator produced repeated collisions")


def _asset(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"assets[{index}] must be an object")
    prefix = f"assets[{index}]"
    source_authority, source_record_id, _ = _source_key(
        raw.get("source_authority"), raw.get("source_record_id"), prefix
    )
    tracking_mode = _normalized_token(raw.get("tracking_mode"), f"{prefix}.tracking_mode")
    if tracking_mode not in TRACKING_MODES:
        raise ValueError(f"{prefix}.tracking_mode is unsupported: {tracking_mode}")
    quantity = _quantity(raw.get("quantity"), f"{prefix}.quantity")
    if tracking_mode == "individual" and quantity != 1:
        raise ValueError(f"{prefix}: individual tracking requires quantity 1")
    lifecycle = _normalized_token(raw.get("lifecycle_status"), f"{prefix}.lifecycle_status")
    if lifecycle not in LIFECYCLE_STATUSES:
        raise ValueError(f"{prefix}.lifecycle_status is unsupported: {lifecycle}")
    created = _timestamp(raw.get("created_et"), f"{prefix}.created_et")
    updated = _timestamp(raw.get("updated_et"), f"{prefix}.updated_et")
    result: dict[str, Any] = {field: _text(raw.get(field)) for field in ASSET_FIELDS}
    result.update(
        {
            "entity_uuid": _uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid"),
            "asset_type": _required_text(raw.get("asset_type"), f"{prefix}.asset_type"),
            "label": _required_text(raw.get("label"), f"{prefix}.label"),
            "quantity": quantity,
            "tracking_mode": tracking_mode,
            "lifecycle_status": lifecycle,
            "owner_uuid": _optional_uuid(raw.get("owner_uuid"), f"{prefix}.owner_uuid"),
            "source_authority": source_authority,
            "source_record_id": source_record_id,
            "created_et": created,
            "updated_et": updated,
            "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
        }
    )
    return result


def _relationship(raw: Any, index: int) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError(f"relationships[{index}] must be an object")
    prefix = f"relationships[{index}]"
    source_authority, source_record_id, _ = _source_key(
        raw.get("source_authority"), raw.get("source_record_id"), prefix
    )
    relationship_type = _normalized_token(
        raw.get("relationship_type"), f"{prefix}.relationship_type"
    )
    if relationship_type not in RELATIONSHIP_TYPES:
        raise ValueError(f"{prefix}.relationship_type is unsupported: {relationship_type}")
    status = _normalized_token(raw.get("status"), f"{prefix}.status")
    if status not in RELATIONSHIP_STATUSES:
        raise ValueError(f"{prefix}.status is unsupported: {status}")
    result = {field: _text(raw.get(field)) for field in RELATIONSHIP_FIELDS}
    result.update(
        {
            "relationship_uuid": _uuid(
                raw.get("relationship_uuid"), f"{prefix}.relationship_uuid"
            ),
            "from_entity_uuid": _uuid(
                raw.get("from_entity_uuid"), f"{prefix}.from_entity_uuid"
            ),
            "relationship_type": relationship_type,
            "to_entity_uuid": _uuid(raw.get("to_entity_uuid"), f"{prefix}.to_entity_uuid"),
            "status": status,
            "source_authority": source_authority,
            "source_record_id": source_record_id,
            "effective_from_et": _timestamp(
                raw.get("effective_from_et"), f"{prefix}.effective_from_et", required=False
            ),
            "effective_to_et": _timestamp(
                raw.get("effective_to_et"), f"{prefix}.effective_to_et", required=False
            ),
            "updated_et": _timestamp(raw.get("updated_et"), f"{prefix}.updated_et"),
            "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
        }
    )
    if result["from_entity_uuid"] == result["to_entity_uuid"]:
        raise ValueError(f"{prefix} cannot link an entity to itself")
    return result


def _validate_unique_existing(
    assets: list[dict[str, Any]], relationships: list[dict[str, str]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]], set[str]]:
    assets_by_source: dict[str, dict[str, Any]] = {}
    relationships_by_source: dict[str, dict[str, str]] = {}
    used: set[str] = set()
    for row in assets:
        source = f"{row['source_authority']}\x1f{row['source_record_id']}"
        if source in assets_by_source:
            raise ValueError(f"duplicate asset source identity: {source.replace(chr(31), ':')}")
        if row["entity_uuid"] in used:
            raise ValueError(f"duplicate entity_uuid: {row['entity_uuid']}")
        assets_by_source[source] = row
        used.add(row["entity_uuid"])
    relationship_uuids: set[str] = set()
    for row in relationships:
        source = f"{row['source_authority']}\x1f{row['source_record_id']}"
        if source in relationships_by_source:
            raise ValueError(
                f"duplicate relationship source identity: {source.replace(chr(31), ':')}"
            )
        if row["relationship_uuid"] in relationship_uuids or row["relationship_uuid"] in used:
            raise ValueError(f"duplicate UUID across identity graph: {row['relationship_uuid']}")
        relationships_by_source[source] = row
        relationship_uuids.add(row["relationship_uuid"])
        used.add(row["relationship_uuid"])
    return assets_by_source, relationships_by_source, used


def _intent_asset(
    raw: dict[str, Any], index: int, now: str, entity_uuid: str
) -> dict[str, Any]:
    prefix = f"receipt_line_intents[{index}]"
    asset_raw = raw.get("asset")
    if not isinstance(asset_raw, dict):
        raise ValueError(f"{prefix}.asset must be an object")
    source_authority, source_record_id, _ = _source_key(
        raw.get("source_authority"), raw.get("source_record_id"), prefix
    )
    tracking_mode = _normalized_token(
        asset_raw.get("tracking_mode"), f"{prefix}.asset.tracking_mode"
    )
    if tracking_mode not in TRACKING_MODES:
        raise ValueError(f"{prefix}.asset.tracking_mode is unsupported: {tracking_mode}")
    quantity = _quantity(asset_raw.get("quantity"), f"{prefix}.asset.quantity")
    if tracking_mode == "individual" and quantity != 1:
        raise ValueError(f"{prefix}: individual tracking requires quantity 1")
    lifecycle = _normalized_token(
        asset_raw.get("lifecycle_status"), f"{prefix}.asset.lifecycle_status"
    )
    if lifecycle not in LIFECYCLE_STATUSES:
        raise ValueError(f"{prefix}.asset.lifecycle_status is unsupported: {lifecycle}")
    result = {field: "" for field in ASSET_FIELDS}
    for field in (
        "friendly_id",
        "manufacturer",
        "model",
        "part_number",
        "evidence_link",
        "notes",
    ):
        result[field] = _text(asset_raw.get(field))
    result.update(
        {
            "entity_uuid": entity_uuid,
            "asset_type": _required_text(asset_raw.get("asset_type"), f"{prefix}.asset.asset_type"),
            "label": _required_text(asset_raw.get("label"), f"{prefix}.asset.label"),
            "quantity": quantity,
            "tracking_mode": tracking_mode,
            "lifecycle_status": lifecycle,
            "owner_uuid": _optional_uuid(asset_raw.get("owner_uuid"), f"{prefix}.asset.owner_uuid"),
            "source_authority": source_authority,
            "source_record_id": source_record_id,
            "receipt_id": _required_text(raw.get("receipt_id"), f"{prefix}.receipt_id"),
            "receipt_line_id": _required_text(
                raw.get("receipt_line_id"), f"{prefix}.receipt_line_id"
            ),
            "created_et": now,
            "updated_et": now,
            "schema_version": SCHEMA_VERSION,
        }
    )
    return result


def _merge_asset(existing: dict[str, Any], desired: dict[str, Any], now: str) -> bool:
    immutable = ("entity_uuid", "source_authority", "source_record_id", "created_et")
    if any(existing[field] != desired[field] for field in immutable[:3]):
        raise ValueError("attempted to mutate immutable asset identity")
    changed = False
    for field in ASSET_FIELDS:
        if field in immutable or field == "updated_et":
            continue
        desired_value = desired[field]
        if desired_value not in ("", None) and existing.get(field) != desired_value:
            existing[field] = desired_value
            changed = True
    if changed:
        existing["updated_et"] = now
    return changed


def reconcile(
    payload: Any, uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("input JSON root must be an object")
    now = _parse_now(payload.get("now"))
    raw_assets = payload.get("assets", [])
    raw_relationships = payload.get("relationships", [])
    raw_intents = payload.get("receipt_line_intents", [])
    if not isinstance(raw_assets, list):
        raise ValueError("assets must be an array")
    if not isinstance(raw_relationships, list):
        raise ValueError("relationships must be an array")
    if not isinstance(raw_intents, list):
        raise ValueError("receipt_line_intents must be an array")

    assets = [_asset(row, index) for index, row in enumerate(raw_assets, start=1)]
    relationships = [
        _relationship(row, index) for index, row in enumerate(raw_relationships, start=1)
    ]
    assets_by_source, relationships_by_source, used = _validate_unique_existing(
        assets, relationships
    )

    known_external: set[str] = set()
    raw_known = payload.get("known_entity_uuids", [])
    if not isinstance(raw_known, list):
        raise ValueError("known_entity_uuids must be an array")
    for index, value in enumerate(raw_known, start=1):
        parsed = _uuid(value, f"known_entity_uuids[{index}]")
        known_external.add(parsed)
        used.add(parsed)

    known_before_intents = {row["entity_uuid"] for row in assets} | known_external
    for index, row in enumerate(relationships, start=1):
        for field in ("from_entity_uuid", "to_entity_uuid"):
            if row[field] not in known_before_intents:
                raise ValueError(f"relationships[{index}].{field} references an unknown entity")

    created_assets: list[str] = []
    updated_assets: list[str] = []
    unchanged_assets: list[str] = []
    created_relationships: list[str] = []
    updated_relationships: list[str] = []
    unchanged_relationships: list[str] = []
    excluded: list[dict[str, str]] = []
    pending_assignments: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    seen_intent_sources: set[str] = set()

    for index, raw in enumerate(raw_intents, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"receipt_line_intents[{index}] must be an object")
        prefix = f"receipt_line_intents[{index}]"
        source_authority, source_record_id, source = _source_key(
            raw.get("source_authority"), raw.get("source_record_id"), prefix
        )
        if source in seen_intent_sources:
            raise ValueError(f"duplicate receipt-line intent source identity: {source_authority}:{source_record_id}")
        seen_intent_sources.add(source)
        include = raw.get("include_in_inventory", True)
        if not isinstance(include, bool):
            raise ValueError(f"{prefix}.include_in_inventory must be boolean")
        receipt_id = _required_text(raw.get("receipt_id"), f"{prefix}.receipt_id")
        receipt_line_id = _required_text(raw.get("receipt_line_id"), f"{prefix}.receipt_line_id")
        line_status = _normalized_token(raw.get("line_status", "included"), f"{prefix}.line_status")
        if line_status not in LINE_STATUSES:
            raise ValueError(f"{prefix}.line_status is unsupported: {line_status}")
        if include and line_status in EXCLUDED_LINE_STATUSES:
            raise ValueError(f"{prefix}: {line_status} receipt line cannot create inventory")
        if not include:
            if source in assets_by_source:
                raise ValueError(f"{prefix} excludes a receipt line that already owns an asset UUID")
            excluded.append(
                {
                    "receipt_id": receipt_id,
                    "receipt_line_id": receipt_line_id,
                    "source_record_id": source_record_id,
                    "reason": _text(raw.get("exclusion_reason")) or "excluded from inventory",
                }
            )
            continue

        existing = assets_by_source.get(source)
        requested_uuid = _optional_uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid")
        if existing:
            if requested_uuid and requested_uuid != existing["entity_uuid"]:
                raise ValueError(f"{prefix} attempts to replace immutable entity_uuid")
            entity_uuid = existing["entity_uuid"]
        else:
            if requested_uuid:
                if requested_uuid in used:
                    raise ValueError(f"{prefix}.entity_uuid already belongs to another identity")
                entity_uuid = requested_uuid
                used.add(entity_uuid)
            else:
                entity_uuid = _new_uuid(uuid_factory, used)
        desired = _intent_asset(raw, index, now, entity_uuid)
        if existing:
            if _merge_asset(existing, desired, now):
                updated_assets.append(entity_uuid)
            else:
                unchanged_assets.append(entity_uuid)
        else:
            assets.append(desired)
            assets_by_source[source] = desired
            created_assets.append(entity_uuid)

        assignments = raw.get("assignments", [])
        if not isinstance(assignments, list):
            raise ValueError(f"{prefix}.assignments must be an array")
        for assignment in assignments:
            if not isinstance(assignment, dict):
                raise ValueError(f"{prefix}.assignments entries must be objects")
            pending_assignments.append((index, desired, assignment))

    known_entities = {row["entity_uuid"] for row in assets} | known_external
    seen_assignment_sources: set[str] = set()
    for intent_index, asset, raw in pending_assignments:
        prefix = f"receipt_line_intents[{intent_index}].assignments"
        relationship_type = _normalized_token(
            raw.get("relationship_type"), f"{prefix}.relationship_type"
        )
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(f"{prefix}.relationship_type is unsupported: {relationship_type}")
        status = _normalized_token(raw.get("status", "active"), f"{prefix}.status")
        if status not in RELATIONSHIP_STATUSES:
            raise ValueError(f"{prefix}.status is unsupported: {status}")
        target = _uuid(raw.get("to_entity_uuid"), f"{prefix}.to_entity_uuid")
        if target not in known_entities:
            raise ValueError(f"{prefix}.to_entity_uuid references an unknown entity")
        if target == asset["entity_uuid"]:
            raise ValueError(f"{prefix} cannot link an entity to itself")
        source_authority = asset["source_authority"]
        relation_source_record = _text(raw.get("source_record_id")) or (
            f"{asset['source_record_id']}:{relationship_type}:{target}"
        )
        relation_source = f"{source_authority}\x1f{relation_source_record}"
        if relation_source in seen_assignment_sources:
            raise ValueError(f"duplicate assignment source identity: {source_authority}:{relation_source_record}")
        seen_assignment_sources.add(relation_source)
        existing = relationships_by_source.get(relation_source)
        requested_uuid = _optional_uuid(
            raw.get("relationship_uuid"), f"{prefix}.relationship_uuid"
        )
        if existing:
            if requested_uuid and requested_uuid != existing["relationship_uuid"]:
                raise ValueError(f"{prefix} attempts to replace immutable relationship_uuid")
            if (
                existing["from_entity_uuid"] != asset["entity_uuid"]
                or existing["relationship_type"] != relationship_type
                or existing["to_entity_uuid"] != target
            ):
                raise ValueError(f"{prefix} source identity resolves to a different relationship")
            changed = False
            for field, value in (
                ("status", status),
                ("evidence_link", _text(raw.get("evidence_link")) or asset["evidence_link"]),
                ("notes", _text(raw.get("notes"))),
                (
                    "effective_from_et",
                    _timestamp(
                        raw.get("effective_from_et"),
                        f"{prefix}.effective_from_et",
                        required=False,
                    ),
                ),
                (
                    "effective_to_et",
                    _timestamp(
                        raw.get("effective_to_et"),
                        f"{prefix}.effective_to_et",
                        required=False,
                    ),
                ),
            ):
                if value and existing.get(field) != value:
                    existing[field] = value
                    changed = True
            if changed:
                existing["updated_et"] = now
                updated_relationships.append(existing["relationship_uuid"])
            else:
                unchanged_relationships.append(existing["relationship_uuid"])
            continue

        if requested_uuid:
            if requested_uuid in used:
                raise ValueError(f"{prefix}.relationship_uuid already belongs to another identity")
            relationship_uuid = requested_uuid
            used.add(relationship_uuid)
        else:
            relationship_uuid = _new_uuid(uuid_factory, used)
        relationship = {
            "relationship_uuid": relationship_uuid,
            "from_entity_uuid": asset["entity_uuid"],
            "relationship_type": relationship_type,
            "to_entity_uuid": target,
            "status": status,
            "source_authority": source_authority,
            "source_record_id": relation_source_record,
            "receipt_id": asset["receipt_id"],
            "receipt_line_id": asset["receipt_line_id"],
            "evidence_link": _text(raw.get("evidence_link")) or asset["evidence_link"],
            "notes": _text(raw.get("notes")),
            "effective_from_et": _timestamp(
                raw.get("effective_from_et"), f"{prefix}.effective_from_et", required=False
            ) or now,
            "effective_to_et": _timestamp(
                raw.get("effective_to_et"), f"{prefix}.effective_to_et", required=False
            ),
            "updated_et": now,
            "schema_version": SCHEMA_VERSION,
        }
        relationships.append(relationship)
        relationships_by_source[relation_source] = relationship
        created_relationships.append(relationship_uuid)

    assets.sort(key=lambda row: (row["source_authority"], row["source_record_id"]))
    relationships.sort(key=lambda row: (row["source_authority"], row["source_record_id"]))
    return {
        "status": "ok",
        "policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "now": now,
        "assets": copy.deepcopy(assets),
        "relationships": copy.deepcopy(relationships),
        "created_asset_uuids": created_assets,
        "updated_asset_uuids": updated_assets,
        "unchanged_asset_uuids": unchanged_assets,
        "created_relationship_uuids": created_relationships,
        "updated_relationship_uuids": updated_relationships,
        "unchanged_relationship_uuids": unchanged_relationships,
        "excluded_receipt_lines": excluded,
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
        output = {"status": "error", "policy_version": POLICY_VERSION, "errors": [str(exc)]}
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if output.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

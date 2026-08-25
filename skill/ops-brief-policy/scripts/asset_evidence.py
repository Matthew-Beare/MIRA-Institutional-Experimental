#!/usr/bin/env python3
"""Reconcile product evidence, identifiers, manuals, and technical specifications.

The module is deliberately provider-neutral.  Gmail, Drive, image/OCR, web, and
Sheet adapters collect evidence; this module validates and joins the resulting
records before any provider write.  It also supplies the bidirectional query
used by receipt and asset/vehicle views.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo


POLICY_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
EASTERN = ZoneInfo("America/New_York")

EVIDENCE_TYPES = {
    "gmail",
    "receipt_photo",
    "receipt_screenshot",
    "product_photo",
    "serial_plate_photo",
    "barcode_photo",
    "merchant_account",
    "manual",
    "manufacturer_page",
    "owner_confirmation",
    "other",
}
EVIDENCE_STATUSES = {"retained", "available", "queued", "unavailable", "superseded"}
IDENTIFIER_TYPES = {
    "upc_a",
    "ean_13",
    "gtin_8",
    "gtin_12",
    "gtin_13",
    "gtin_14",
    "manufacturer_part_number",
    "vendor_sku",
    "model_number",
    "serial_number",
    "imei",
    "mac_address",
}
NAMESPACED_IDENTIFIER_TYPES = {
    "manufacturer_part_number",
    "vendor_sku",
    "model_number",
    "serial_number",
}
IDENTIFIER_STATUSES = {"observed", "verified", "superseded", "invalid"}
KNOWLEDGE_TYPES = {"manual", "service_manual", "datasheet", "bulletin", "reference"}
KNOWLEDGE_STATUSES = {
    "retained",
    "lookup_queued",
    "download_blocked",
    "unavailable",
    "superseded",
}
KNOWLEDGE_RELATIONSHIP_TYPES = {
    "applies_to",
    "manual_for",
    "datasheet_for",
    "bulletin_for",
    "reference_for",
}
RELATIONSHIP_STATUSES = {"planned", "active", "inactive", "retired"}
SPECIFICATION_STATUSES = {"verified", "candidate", "superseded", "rejected"}
AUTHORITATIVE_SOURCE_TIERS = {"oem", "manufacturer", "authoritative_regulatory"}
SAFETY_CRITICAL_SPEC_TYPES = {
    "torque",
    "tire_pressure",
    "fluid_capacity",
    "fluid_specification",
    "alignment",
    "load_limit",
}
LOOKUP_TYPES = {
    "product_identity",
    "upc_product",
    "manual",
    "technical_specification",
    "part_fitment",
}
LOOKUP_STATUSES = {"queued", "in_progress", "succeeded", "blocked", "failed", "no_match"}

EVIDENCE_FIELDS = (
    "evidence_uuid", "evidence_type", "entity_uuid", "receipt_id", "receipt_line_id",
    "source_authority", "source_record_id", "source_uri", "drive_file_url",
    "drive_file_id", "content_hash", "captured_et", "status", "notes",
    "updated_et", "schema_version",
)
IDENTIFIER_FIELDS = (
    "identifier_uuid", "entity_uuid", "identifier_type", "value", "normalized_value",
    "namespace", "status", "evidence_uuid", "source_authority", "source_record_id",
    "evidence_link", "notes", "updated_et", "schema_version",
)
KNOWLEDGE_FIELDS = (
    "knowledge_uuid", "title", "knowledge_type", "manufacturer", "model", "part_sku",
    "source_url", "drive_file_url", "drive_file_id", "version_revision",
    "effective_date", "tags", "summary", "status", "source_authority",
    "source_record_id", "content_hash", "updated_et", "schema_version",
)
KNOWLEDGE_RELATIONSHIP_FIELDS = (
    "relationship_uuid", "knowledge_uuid", "entity_uuid", "relationship_type", "status",
    "source_authority", "source_record_id", "evidence_uuid", "notes", "updated_et",
    "schema_version",
)
SPECIFICATION_FIELDS = (
    "specification_uuid", "subject_entity_uuid", "specification_type", "label", "value",
    "unit", "applicability", "source_tier", "source_url", "knowledge_uuid",
    "source_locator", "version_revision", "status", "source_authority",
    "source_record_id", "evidence_uuid", "notes", "updated_et", "schema_version",
)
LOOKUP_FIELDS = (
    "lookup_uuid", "entity_uuid", "lookup_type", "query", "status", "evidence_uuid",
    "result_url", "notes", "source_authority", "source_record_id", "updated_et",
    "schema_version",
)

COLLECTIONS = {
    "evidence": ("evidence_uuid", EVIDENCE_FIELDS),
    "identifiers": ("identifier_uuid", IDENTIFIER_FIELDS),
    "knowledge": ("knowledge_uuid", KNOWLEDGE_FIELDS),
    "knowledge_relationships": ("relationship_uuid", KNOWLEDGE_RELATIONSHIP_FIELDS),
    "specifications": ("specification_uuid", SPECIFICATION_FIELDS),
    "lookups": ("lookup_uuid", LOOKUP_FIELDS),
}
INTENT_KEYS = {
    "evidence": "evidence_intents",
    "identifiers": "identifier_intents",
    "knowledge": "knowledge_intents",
    "knowledge_relationships": "knowledge_relationship_intents",
    "specifications": "specification_intents",
    "lookups": "lookup_intents",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _token(value: Any, field: str) -> str:
    result = _required(value, field).lower().replace("-", "_").replace(" ", "_")
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", result):
        raise ValueError(f"{field} must be a lowercase token")
    return result


def _choice(value: Any, field: str, choices: set[str]) -> str:
    result = _token(value, field)
    if result not in choices:
        raise ValueError(f"{field} is unsupported: {result}")
    return result


def _uuid(value: Any, field: str) -> str:
    raw = _required(value, field)
    try:
        parsed = uuid.UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID") from exc
    canonical = str(parsed)
    if raw != canonical or parsed.variant != uuid.RFC_4122 or parsed.version not in {1, 3, 4, 5}:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID")
    return canonical


def _optional_uuid(value: Any, field: str) -> str:
    return "" if not _text(value) else _uuid(value, field)


def _timestamp(value: Any, field: str, *, required: bool = True) -> str:
    raw = _text(value)
    if not raw:
        if required:
            raise ValueError(f"{field} must be nonblank")
        return ""
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone/UTC offset")
    return parsed.astimezone(EASTERN).isoformat()


def _date(value: Any, field: str) -> str:
    raw = _text(value)
    if not raw:
        return ""
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc


def _source(raw: dict[str, Any], prefix: str) -> tuple[str, str]:
    return (
        _token(raw.get("source_authority"), f"{prefix}.source_authority"),
        _required(raw.get("source_record_id"), f"{prefix}.source_record_id"),
    )


def _base(raw: Any, prefix: str, fields: Iterable[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{prefix} must be an object")
    return {field: _text(raw.get(field)) for field in fields}


def _gtin_check(value: str) -> bool:
    if not value.isdigit() or len(value) not in {8, 12, 13, 14}:
        return False
    digits = [int(ch) for ch in value]
    body = digits[:-1]
    total = sum(digit * (3 if offset % 2 == 0 else 1) for offset, digit in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == digits[-1]


def _luhn(value: str) -> bool:
    if not value.isdigit():
        return False
    total = 0
    parity = len(value) % 2
    for index, char in enumerate(value):
        digit = int(char)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _normalize_identifier(identifier_type: str, value: str) -> str:
    if identifier_type in {"upc_a", "ean_13", "gtin_8", "gtin_12", "gtin_13", "gtin_14", "imei"}:
        return re.sub(r"[\s-]", "", value)
    if identifier_type == "mac_address":
        return re.sub(r"[^0-9a-fA-F]", "", value).upper()
    return re.sub(r"\s+", " ", value).upper()


def _validate_identifier_value(identifier_type: str, value: str, prefix: str) -> str:
    normalized = _normalize_identifier(identifier_type, value)
    gtin_length = {
        "upc_a": 12,
        "ean_13": 13,
        "gtin_8": 8,
        "gtin_12": 12,
        "gtin_13": 13,
        "gtin_14": 14,
    }
    if identifier_type in gtin_length:
        if len(normalized) != gtin_length[identifier_type] or not _gtin_check(normalized):
            raise ValueError(f"{prefix}.value is not a valid {identifier_type} check-digit value")
    elif identifier_type == "imei":
        if len(normalized) != 15 or not _luhn(normalized):
            raise ValueError(f"{prefix}.value is not a valid IMEI")
    elif identifier_type == "mac_address":
        if not re.fullmatch(r"[0-9A-F]{12}", normalized):
            raise ValueError(f"{prefix}.value is not a valid 48-bit MAC address")
    return normalized


def _evidence(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, EVIDENCE_FIELDS)
    row.update({
        "evidence_uuid": _uuid(raw.get("evidence_uuid"), f"{prefix}.evidence_uuid"),
        "evidence_type": _choice(raw.get("evidence_type"), f"{prefix}.evidence_type", EVIDENCE_TYPES),
        "entity_uuid": _optional_uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid"),
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "captured_et": _timestamp(raw.get("captured_et"), f"{prefix}.captured_et", required=False),
        "status": _choice(raw.get("status"), f"{prefix}.status", EVIDENCE_STATUSES),
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    if not any(row[field] for field in ("entity_uuid", "receipt_id", "receipt_line_id")):
        raise ValueError(f"{prefix} must link an entity, receipt, or exact receipt line")
    if not any(row[field] for field in ("source_uri", "drive_file_id", "drive_file_url", "content_hash")) and row["evidence_type"] != "owner_confirmation":
        raise ValueError(f"{prefix} lacks a retained source locator or content hash")
    return row


def _identifier(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, IDENTIFIER_FIELDS)
    identifier_type = _choice(raw.get("identifier_type"), f"{prefix}.identifier_type", IDENTIFIER_TYPES)
    value = _required(raw.get("value"), f"{prefix}.value")
    namespace = _text(raw.get("namespace"))
    if identifier_type in NAMESPACED_IDENTIFIER_TYPES and not namespace:
        raise ValueError(f"{prefix}.namespace is required for {identifier_type}")
    row.update({
        "identifier_uuid": _uuid(raw.get("identifier_uuid"), f"{prefix}.identifier_uuid"),
        "entity_uuid": _uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid"),
        "identifier_type": identifier_type,
        "value": value,
        "normalized_value": _validate_identifier_value(identifier_type, value, prefix),
        "namespace": namespace,
        "status": _choice(raw.get("status"), f"{prefix}.status", IDENTIFIER_STATUSES),
        "evidence_uuid": _uuid(raw.get("evidence_uuid"), f"{prefix}.evidence_uuid"),
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    return row


def _knowledge(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, KNOWLEDGE_FIELDS)
    status = _choice(raw.get("status"), f"{prefix}.status", KNOWLEDGE_STATUSES)
    knowledge_type = _choice(raw.get("knowledge_type"), f"{prefix}.knowledge_type", KNOWLEDGE_TYPES)
    row.update({
        "knowledge_uuid": _uuid(raw.get("knowledge_uuid"), f"{prefix}.knowledge_uuid"),
        "title": _required(raw.get("title"), f"{prefix}.title"),
        "knowledge_type": knowledge_type,
        "effective_date": _date(raw.get("effective_date"), f"{prefix}.effective_date"),
        "status": status,
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    if status == "retained":
        if not row["drive_file_id"] or not row["drive_file_url"]:
            raise ValueError(f"{prefix}: retained knowledge requires canonical Drive file ID and URL")
        if knowledge_type in {"manual", "service_manual", "datasheet", "bulletin"} and not row["version_revision"]:
            raise ValueError(f"{prefix}: retained {knowledge_type} requires a version/revision or explicit edition")
    return row


def _knowledge_relationship(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, KNOWLEDGE_RELATIONSHIP_FIELDS)
    row.update({
        "relationship_uuid": _uuid(raw.get("relationship_uuid"), f"{prefix}.relationship_uuid"),
        "knowledge_uuid": _uuid(raw.get("knowledge_uuid"), f"{prefix}.knowledge_uuid"),
        "entity_uuid": _uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid"),
        "relationship_type": _choice(raw.get("relationship_type"), f"{prefix}.relationship_type", KNOWLEDGE_RELATIONSHIP_TYPES),
        "status": _choice(raw.get("status"), f"{prefix}.status", RELATIONSHIP_STATUSES),
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "evidence_uuid": _optional_uuid(raw.get("evidence_uuid"), f"{prefix}.evidence_uuid"),
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    return row


def _specification(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, SPECIFICATION_FIELDS)
    specification_type = _token(raw.get("specification_type"), f"{prefix}.specification_type")
    status = _choice(raw.get("status"), f"{prefix}.status", SPECIFICATION_STATUSES)
    source_tier = _token(raw.get("source_tier"), f"{prefix}.source_tier")
    row.update({
        "specification_uuid": _uuid(raw.get("specification_uuid"), f"{prefix}.specification_uuid"),
        "subject_entity_uuid": _uuid(raw.get("subject_entity_uuid"), f"{prefix}.subject_entity_uuid"),
        "specification_type": specification_type,
        "label": _required(raw.get("label"), f"{prefix}.label"),
        "value": _required(raw.get("value"), f"{prefix}.value"),
        "unit": _required(raw.get("unit"), f"{prefix}.unit"),
        "applicability": _required(raw.get("applicability"), f"{prefix}.applicability"),
        "source_tier": source_tier,
        "knowledge_uuid": _optional_uuid(raw.get("knowledge_uuid"), f"{prefix}.knowledge_uuid"),
        "status": status,
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "evidence_uuid": _optional_uuid(raw.get("evidence_uuid"), f"{prefix}.evidence_uuid"),
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    if status == "verified" and specification_type in SAFETY_CRITICAL_SPEC_TYPES:
        if source_tier not in AUTHORITATIVE_SOURCE_TIERS:
            raise ValueError(f"{prefix}: verified safety-critical specification requires an authoritative source")
        if not row["source_locator"]:
            raise ValueError(f"{prefix}: verified safety-critical specification requires page/section provenance")
        if not row["source_url"] and not row["knowledge_uuid"]:
            raise ValueError(f"{prefix}: verified safety-critical specification requires a source URL or retained knowledge UUID")
    return row


def _lookup(raw: Any, prefix: str, now: str) -> dict[str, Any]:
    row = _base(raw, prefix, LOOKUP_FIELDS)
    row.update({
        "lookup_uuid": _uuid(raw.get("lookup_uuid"), f"{prefix}.lookup_uuid"),
        "entity_uuid": _uuid(raw.get("entity_uuid"), f"{prefix}.entity_uuid"),
        "lookup_type": _choice(raw.get("lookup_type"), f"{prefix}.lookup_type", LOOKUP_TYPES),
        "query": _required(raw.get("query"), f"{prefix}.query"),
        "status": _choice(raw.get("status"), f"{prefix}.status", LOOKUP_STATUSES),
        "evidence_uuid": _optional_uuid(raw.get("evidence_uuid"), f"{prefix}.evidence_uuid"),
        "source_authority": _source(raw, prefix)[0],
        "source_record_id": _source(raw, prefix)[1],
        "updated_et": now,
        "schema_version": _text(raw.get("schema_version")) or SCHEMA_VERSION,
    })
    if row["status"] == "succeeded" and not row["result_url"]:
        raise ValueError(f"{prefix}: succeeded lookup requires result_url")
    return row


VALIDATORS = {
    "evidence": _evidence,
    "identifiers": _identifier,
    "knowledge": _knowledge,
    "knowledge_relationships": _knowledge_relationship,
    "specifications": _specification,
    "lookups": _lookup,
}

STABLE_FIELDS = {
    "evidence": {"evidence_uuid", "evidence_type", "source_authority", "source_record_id", "source_uri", "drive_file_id", "content_hash"},
    "identifiers": {"identifier_uuid", "entity_uuid", "identifier_type", "value", "normalized_value", "namespace", "source_authority", "source_record_id"},
    "knowledge": {"knowledge_uuid", "knowledge_type", "source_authority", "source_record_id", "drive_file_id", "content_hash"},
    "knowledge_relationships": {"relationship_uuid", "knowledge_uuid", "entity_uuid", "relationship_type", "source_authority", "source_record_id"},
    "specifications": {"specification_uuid", "subject_entity_uuid", "specification_type", "label", "value", "unit", "applicability", "source_tier", "source_url", "knowledge_uuid", "source_locator", "version_revision", "source_authority", "source_record_id"},
    "lookups": {"lookup_uuid", "entity_uuid", "lookup_type", "query", "source_authority", "source_record_id"},
}


def _new_uuid(factory: Callable[[], uuid.UUID], used: set[str]) -> str:
    for _ in range(10):
        value = _uuid(str(factory()), "allocated UUID")
        if value not in used:
            used.add(value)
            return value
    raise ValueError("UUID allocator produced repeated collisions")


def _existing_rows(payload: dict[str, Any], name: str, now: str) -> list[dict[str, Any]]:
    raw_rows = payload.get(name, [])
    if not isinstance(raw_rows, list):
        raise ValueError(f"{name} must be a list")
    validator = VALIDATORS[name]
    rows = [validator(raw, f"{name}[{index}]", _timestamp(raw.get("updated_et"), f"{name}[{index}].updated_et")) for index, raw in enumerate(raw_rows)]
    id_field = COLLECTIONS[name][0]
    ids: set[str] = set()
    sources: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if row[id_field] in ids:
            raise ValueError(f"{name}[{index}] duplicates {id_field}")
        ids.add(row[id_field])
        source = (row["source_authority"], row["source_record_id"])
        if source in sources:
            raise ValueError(f"{name}[{index}] duplicates source identity")
        sources.add(source)
    return rows


def _upsert_collection(
    name: str,
    existing: list[dict[str, Any]],
    intents: Any,
    now: str,
    factory: Callable[[], uuid.UUID],
    used_uuids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    intent_key = INTENT_KEYS[name]
    if intents is None:
        intents = []
    if not isinstance(intents, list):
        raise ValueError(f"{intent_key} must be a list")
    id_field = COLLECTIONS[name][0]
    by_source = {(row["source_authority"], row["source_record_id"]): row for row in existing}
    by_id = {row[id_field]: row for row in existing}
    output = copy.deepcopy(existing)
    positions = {row[id_field]: index for index, row in enumerate(output)}
    seen_intent_sources: set[tuple[str, str]] = set()
    changes = {"created": [], "updated": [], "unchanged": []}

    for index, original in enumerate(intents):
        if not isinstance(original, dict):
            raise ValueError(f"{intent_key}[{index}] must be an object")
        raw = copy.deepcopy(original)
        source = _source(raw, f"{intent_key}[{index}]")
        if source in seen_intent_sources:
            raise ValueError(f"duplicate {name} intent source identity")
        seen_intent_sources.add(source)
        current = by_source.get(source)
        if not _text(raw.get(id_field)):
            raw[id_field] = current[id_field] if current else _new_uuid(factory, used_uuids)
        proposed_id = _uuid(raw[id_field], f"{intent_key}[{index}].{id_field}")
        if current and proposed_id != current[id_field]:
            raise ValueError(f"{intent_key}[{index}] cannot replace immutable {id_field}")
        if proposed_id in by_id and by_id[proposed_id] is not current:
            raise ValueError(f"{intent_key}[{index}] reuses {id_field} under another source identity")
        raw["updated_et"] = now
        row = VALIDATORS[name](raw, f"{intent_key}[{index}]", now)
        if current:
            changed_stable = sorted(field for field in STABLE_FIELDS[name] if row[field] != current[field])
            if changed_stable:
                raise ValueError(f"{intent_key}[{index}] mutates immutable fields: {', '.join(changed_stable)}")
            semantic_row = {key: value for key, value in row.items() if key != "updated_et"}
            semantic_current = {key: value for key, value in current.items() if key != "updated_et"}
            if semantic_row == semantic_current:
                changes["unchanged"].append(proposed_id)
            else:
                output[positions[proposed_id]] = row
                by_source[source] = row
                by_id[proposed_id] = row
                changes["updated"].append(proposed_id)
        else:
            positions[proposed_id] = len(output)
            output.append(row)
            by_source[source] = row
            by_id[proposed_id] = row
            changes["created"].append(proposed_id)
    return output, changes


def _known_entities(payload: dict[str, Any]) -> set[str]:
    entities: set[str] = set()
    known = payload.get("known_entity_uuids", [])
    if not isinstance(known, list):
        raise ValueError("known_entity_uuids must be a list")
    for index, value in enumerate(known):
        entities.add(_uuid(value, f"known_entity_uuids[{index}]"))
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("assets must be a list")
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"assets[{index}] must be an object")
        entity_uuid = _uuid(asset.get("entity_uuid"), f"assets[{index}].entity_uuid")
        if entity_uuid in entities:
            raise ValueError(f"assets[{index}] duplicates a known/entity UUID")
        entities.add(entity_uuid)
    return entities


def _cross_validate(state: dict[str, Any], entities: set[str]) -> None:
    evidence_ids = {row["evidence_uuid"] for row in state["evidence"]}
    knowledge_ids = {row["knowledge_uuid"] for row in state["knowledge"]}
    for name, field in (("evidence", "entity_uuid"), ("identifiers", "entity_uuid"), ("knowledge_relationships", "entity_uuid"), ("specifications", "subject_entity_uuid"), ("lookups", "entity_uuid")):
        for index, row in enumerate(state[name]):
            if row[field] and row[field] not in entities:
                raise ValueError(f"{name}[{index}].{field} references an unknown entity")
    for name in ("identifiers", "knowledge_relationships", "specifications", "lookups"):
        for index, row in enumerate(state[name]):
            if row.get("evidence_uuid") and row["evidence_uuid"] not in evidence_ids:
                raise ValueError(f"{name}[{index}].evidence_uuid references unknown evidence")
    evidence_by_id = {row["evidence_uuid"]: row for row in state["evidence"]}
    for index, row in enumerate(state["identifiers"]):
        evidence_entity = evidence_by_id[row["evidence_uuid"]]["entity_uuid"]
        if evidence_entity and evidence_entity != row["entity_uuid"]:
            raise ValueError(f"identifiers[{index}] uses evidence linked to another entity")
    for index, row in enumerate(state["knowledge_relationships"]):
        if row["knowledge_uuid"] not in knowledge_ids:
            raise ValueError(f"knowledge_relationships[{index}].knowledge_uuid references unknown knowledge")
    for index, row in enumerate(state["specifications"]):
        if row["knowledge_uuid"] and row["knowledge_uuid"] not in knowledge_ids:
            raise ValueError(f"specifications[{index}].knowledge_uuid references unknown knowledge")

    seen_identifier: set[tuple[str, str, str, str]] = set()
    serial_owner: dict[tuple[str, str, str], str] = {}
    for index, row in enumerate(state["identifiers"]):
        key = (row["entity_uuid"], row["identifier_type"], row["namespace"].casefold(), row["normalized_value"])
        if key in seen_identifier:
            raise ValueError(f"identifiers[{index}] duplicates an identifier on the same entity")
        seen_identifier.add(key)
        if row["identifier_type"] in {"serial_number", "imei", "mac_address"} and row["status"] in {"observed", "verified"}:
            serial_key = (row["identifier_type"], row["namespace"].casefold(), row["normalized_value"])
            owner = serial_owner.setdefault(serial_key, row["entity_uuid"])
            if owner != row["entity_uuid"]:
                raise ValueError(f"identifiers[{index}] collides with another entity's unique identifier")


def reconcile(payload: dict[str, Any], uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4) -> dict[str, Any]:
    """Validate existing state and idempotently reconcile normalized intents."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    now = _timestamp(payload.get("now"), "now")
    entities = _known_entities(payload)
    state: dict[str, Any] = {
        "status": "ok",
        "policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "now": now,
        "assets": copy.deepcopy(payload.get("assets", [])),
        "relationships": copy.deepcopy(payload.get("relationships", [])),
    }
    used_uuids: set[str] = set(entities)
    existing: dict[str, list[dict[str, Any]]] = {}
    for name in COLLECTIONS:
        existing[name] = _existing_rows(payload, name, now)
        used_uuids.update(row[COLLECTIONS[name][0]] for row in existing[name])

    change_summary: dict[str, dict[str, list[str]]] = {}
    for name in COLLECTIONS:
        rows, changes = _upsert_collection(
            name,
            existing[name],
            payload.get(INTENT_KEYS[name], []),
            now,
            uuid_factory,
            used_uuids,
        )
        state[name] = rows
        change_summary[name] = changes
    _cross_validate(state, entities)
    state["changes"] = change_summary
    state["counts"] = {name: len(state[name]) for name in COLLECTIONS}
    return state


def _relationship_edge(row: Any, index: int) -> tuple[str, str] | None:
    if not isinstance(row, dict):
        raise ValueError(f"relationships[{index}] must be an object")
    relationship_type = _token(row.get("relationship_type"), f"relationships[{index}].relationship_type")
    if relationship_type == "owned_by" or _text(row.get("status")).lower() not in {"active", "planned"}:
        return None
    return (
        _uuid(row.get("from_entity_uuid"), f"relationships[{index}].from_entity_uuid"),
        _uuid(row.get("to_entity_uuid"), f"relationships[{index}].to_entity_uuid"),
    )


def query_graph(
    state: dict[str, Any],
    *,
    entity_uuid: str | None = None,
    receipt_id: str | None = None,
    identifier_type: str | None = None,
    identifier_value: str | None = None,
    identifier_namespace: str = "",
) -> dict[str, Any]:
    """Return the same connected records from a receipt, asset, or identifier query."""
    selectors = sum(bool(value) for value in (entity_uuid, receipt_id, identifier_value))
    if selectors != 1:
        raise ValueError("query requires exactly one of entity_uuid, receipt_id, or identifier_value")
    assets = state.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("assets must be a list")
    asset_by_id: dict[str, dict[str, Any]] = {}
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"assets[{index}] must be an object")
        asset_by_id[_uuid(asset.get("entity_uuid"), f"assets[{index}].entity_uuid")] = asset

    starts: set[str] = set()
    if entity_uuid:
        starts.add(_uuid(entity_uuid, "entity_uuid"))
    elif receipt_id:
        target = _required(receipt_id, "receipt_id")
        starts.update(key for key, asset in asset_by_id.items() if _text(asset.get("receipt_id")) == target)
        starts.update(_uuid(row["entity_uuid"], "evidence.entity_uuid") for row in state.get("evidence", []) if _text(row.get("receipt_id")) == target and row.get("entity_uuid"))
    else:
        kind = _choice(identifier_type, "identifier_type", IDENTIFIER_TYPES)
        normalized = _normalize_identifier(kind, _required(identifier_value, "identifier_value"))
        namespace = _text(identifier_namespace).casefold()
        starts.update(
            row["entity_uuid"] for row in state.get("identifiers", [])
            if row.get("identifier_type") == kind
            and row.get("normalized_value") == normalized
            and (not namespace or _text(row.get("namespace")).casefold() == namespace)
        )

    adjacency: dict[str, set[str]] = {}
    relevant_relationships: list[dict[str, Any]] = []
    for index, relationship in enumerate(state.get("relationships", [])):
        edge = _relationship_edge(relationship, index)
        if edge:
            left, right = edge
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
            relevant_relationships.append(relationship)
    connected = set(starts)
    queue = list(starts)
    while queue:
        current = queue.pop(0)
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor not in connected:
                connected.add(neighbor)
                queue.append(neighbor)

    selected_assets = [asset for key, asset in asset_by_id.items() if key in connected]
    receipt_ids = {_text(asset.get("receipt_id")) for asset in selected_assets if _text(asset.get("receipt_id"))}
    if receipt_id:
        receipt_ids.add(_text(receipt_id))
    selected_evidence = [row for row in state.get("evidence", []) if row.get("entity_uuid") in connected or row.get("receipt_id") in receipt_ids]
    knowledge_links = [row for row in state.get("knowledge_relationships", []) if row.get("entity_uuid") in connected and row.get("status") in {"active", "planned"}]
    knowledge_ids = {row["knowledge_uuid"] for row in knowledge_links}
    output = {
        "status": "ok",
        "query": {
            "entity_uuid": entity_uuid or "",
            "receipt_id": receipt_id or "",
            "identifier_type": identifier_type or "",
            "identifier_value": identifier_value or "",
            "identifier_namespace": identifier_namespace,
        },
        "entity_uuids": sorted(connected),
        "receipt_ids": sorted(receipt_ids),
        "assets": sorted(selected_assets, key=lambda row: row["entity_uuid"]),
        "relationships": sorted(
            [row for row in relevant_relationships if row.get("from_entity_uuid") in connected and row.get("to_entity_uuid") in connected],
            key=lambda row: _text(row.get("relationship_uuid")),
        ),
        "evidence": sorted(selected_evidence, key=lambda row: row["evidence_uuid"]),
        "identifiers": sorted([row for row in state.get("identifiers", []) if row.get("entity_uuid") in connected], key=lambda row: row["identifier_uuid"]),
        "knowledge_relationships": sorted(knowledge_links, key=lambda row: row["relationship_uuid"]),
        "knowledge": sorted([row for row in state.get("knowledge", []) if row.get("knowledge_uuid") in knowledge_ids], key=lambda row: row["knowledge_uuid"]),
        "specifications": sorted([row for row in state.get("specifications", []) if row.get("subject_entity_uuid") in connected and row.get("status") == "verified"], key=lambda row: row["specification_uuid"]),
        "lookups": sorted([row for row in state.get("lookups", []) if row.get("entity_uuid") in connected], key=lambda row: row["lookup_uuid"]),
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    parser.add_argument("--query-entity")
    parser.add_argument("--query-receipt")
    parser.add_argument("--query-identifier-type")
    parser.add_argument("--query-identifier-value")
    parser.add_argument("--query-identifier-namespace", default="")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = reconcile(json.loads(raw))
        if any((args.query_entity, args.query_receipt, args.query_identifier_value)):
            result = query_graph(
                result,
                entity_uuid=args.query_entity,
                receipt_id=args.query_receipt,
                identifier_type=args.query_identifier_type,
                identifier_value=args.query_identifier_value,
                identifier_namespace=args.query_identifier_namespace,
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Resolve appointment provider identity from durable cache and bounded enrichment evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ENTITY_NAMESPACE = uuid.UUID("8cd7c2e2-63f1-4d43-8d43-36c6bc088530")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _normalize(value: Any) -> str:
    text = _text(value).casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _entity_uuid(source_key: str) -> str:
    return str(uuid.uuid5(ENTITY_NAMESPACE, source_key))


def _directory(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("directory", [])
    if not isinstance(rows, list):
        raise ValueError("directory must be a list")
    output: list[dict[str, Any]] = []
    seen_uuid: set[str] = set()
    seen_alias: dict[str, str] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"directory[{index}] must be an object")
        entity_uuid = _required(raw.get("entity_uuid"), f"directory[{index}].entity_uuid")
        try:
            uuid.UUID(entity_uuid)
        except ValueError as exc:
            raise ValueError(f"directory[{index}].entity_uuid must be a UUID") from exc
        if entity_uuid in seen_uuid:
            raise ValueError("directory contains duplicate entity_uuid")
        seen_uuid.add(entity_uuid)
        display_name = _required(raw.get("display_name"), f"directory[{index}].display_name")
        aliases = raw.get("aliases", [])
        if not isinstance(aliases, list):
            raise ValueError(f"directory[{index}].aliases must be a list")
        alias_values = sorted({_text(value) for value in aliases if _text(value)} | {display_name})
        for alias in alias_values:
            key = _normalize(alias)
            existing = seen_alias.get(key)
            if existing and existing != entity_uuid:
                raise ValueError(f"directory alias is ambiguous: {alias}")
            seen_alias[key] = entity_uuid
        output.append({
            "entity_uuid": entity_uuid,
            "display_name": display_name,
            "entity_type": _text(raw.get("entity_type")) or "service_provider",
            "organization": _text(raw.get("organization")),
            "category_or_specialty": _text(raw.get("category_or_specialty")),
            "aliases": alias_values,
            "contact_identifiers": deepcopy(raw.get("contact_identifiers", {})) if isinstance(raw.get("contact_identifiers", {}), dict) else {},
            "source_bindings": deepcopy(raw.get("source_bindings", [])) if isinstance(raw.get("source_bindings", []), list) else [],
            "provenance": deepcopy(raw.get("provenance", [])) if isinstance(raw.get("provenance", []), list) else [],
            "verification_status": _text(raw.get("verification_status")) or "verified",
        })
    return output


def _source_key(candidate: dict[str, Any]) -> str:
    return f"{_required(candidate.get('source_authority'), 'candidate.source_authority')}::{_required(candidate.get('source_record_id'), 'candidate.source_record_id')}"


def _match_cached(candidate: dict[str, Any], directory: list[dict[str, Any]]) -> dict[str, Any] | None:
    source_key = _source_key(candidate)
    name_key = _normalize(candidate.get("person_or_organization_name") or candidate.get("raw_title"))
    email = _normalize(candidate.get("email"))
    phone = re.sub(r"\D", "", _text(candidate.get("phone")))
    matches: list[dict[str, Any]] = []
    for row in directory:
        if source_key in {_text(value) for value in row.get("source_bindings", [])}:
            return row
        alias_keys = {_normalize(value) for value in row.get("aliases", [])}
        contacts = row.get("contact_identifiers", {})
        contact_email = _normalize(contacts.get("email"))
        contact_phone = re.sub(r"\D", "", _text(contacts.get("phone")))
        if name_key and name_key in alias_keys:
            matches.append(row)
        elif email and contact_email and email == contact_email:
            matches.append(row)
        elif phone and contact_phone and phone == contact_phone:
            matches.append(row)
    unique = {row["entity_uuid"]: row for row in matches}
    if len(unique) == 1:
        return next(iter(unique.values()))
    if len(unique) > 1:
        raise ValueError("candidate matches multiple cached provider entities")
    return None


def _validate_research(candidate: dict[str, Any], research: dict[str, Any] | None) -> dict[str, Any] | None:
    if research is None:
        return None
    if not isinstance(research, dict):
        raise ValueError("research_candidate must be an object")
    display_name = _required(research.get("display_name"), "research_candidate.display_name")
    source_url = _required(research.get("source_url"), "research_candidate.source_url")
    confidence = research.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise ValueError("research_candidate.confidence must be 0..1")
    if float(confidence) < 0.8:
        return None
    raw_name = _normalize(candidate.get("person_or_organization_name") or candidate.get("raw_title"))
    resolved_name = _normalize(display_name)
    if raw_name and resolved_name and raw_name not in resolved_name and resolved_name not in raw_name:
        aliases = research.get("aliases", [])
        if not isinstance(aliases, list) or raw_name not in {_normalize(value) for value in aliases}:
            return None
    return {
        "entity_uuid": _text(research.get("entity_uuid")) or _entity_uuid(source_url + "::" + resolved_name),
        "display_name": display_name,
        "entity_type": _text(research.get("entity_type")) or "service_provider",
        "organization": _text(research.get("organization")),
        "category_or_specialty": _text(research.get("category_or_specialty")),
        "aliases": sorted({_text(value) for value in research.get("aliases", []) if _text(value)} | {display_name, _text(candidate.get("person_or_organization_name"))} - {""}),
        "contact_identifiers": deepcopy(research.get("contact_identifiers", {})) if isinstance(research.get("contact_identifiers", {}), dict) else {},
        "source_bindings": [_source_key(candidate)],
        "provenance": [{"source_url": source_url, "confidence": float(confidence), "kind": "public_research"}],
        "verification_status": "research_supported",
    }


def _canonical_title(candidate: dict[str, Any], entity: dict[str, Any] | None) -> str:
    if not entity:
        return _required(candidate.get("raw_title") or candidate.get("person_or_organization_name"), "candidate.raw_title")
    category = _text(entity.get("category_or_specialty"))
    name = _required(entity.get("display_name"), "entity.display_name")
    return f"{category} — {name}" if category else name


def resolve(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    candidate = payload.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be an object")
    _source_key(candidate)
    directory = _directory(payload)
    cached = _match_cached(candidate, directory)
    if cached:
        if _source_key(candidate) not in cached["source_bindings"]:
            cached = deepcopy(cached)
            cached["source_bindings"] = sorted(set(cached["source_bindings"] + [_source_key(candidate)]))
            directory = [cached if row["entity_uuid"] == cached["entity_uuid"] else row for row in directory]
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "resolved_cached",
            "appointment": {**deepcopy(candidate), "provider_entity_uuid": cached["entity_uuid"], "canonical_title": _canonical_title(candidate, cached)},
            "entity": cached,
            "directory": directory,
            "research_required": False,
        }
    research = _validate_research(candidate, payload.get("research_candidate"))
    if research:
        directory.append(research)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "resolved_research",
            "appointment": {**deepcopy(candidate), "provider_entity_uuid": research["entity_uuid"], "canonical_title": _canonical_title(candidate, research)},
            "entity": research,
            "directory": directory,
            "research_required": False,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "needs_research_or_owner_confirmation",
        "appointment": {**deepcopy(candidate), "provider_entity_uuid": "", "canonical_title": _canonical_title(candidate, None)},
        "entity": None,
        "directory": directory,
        "research_required": True,
    }


def correct(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    candidate = payload.get("candidate")
    correction = payload.get("correction")
    if not isinstance(candidate, dict) or not isinstance(correction, dict):
        raise ValueError("candidate and correction must be objects")
    source_key = _source_key(candidate)
    directory = _directory(payload)
    target_uuid = _text(correction.get("entity_uuid"))
    target = next((row for row in directory if row["entity_uuid"] == target_uuid), None) if target_uuid else None
    if target is None:
        display_name = _required(correction.get("display_name"), "correction.display_name")
        target_uuid = _entity_uuid("owner::" + source_key + "::" + _normalize(display_name))
        target = {
            "entity_uuid": target_uuid,
            "display_name": display_name,
            "entity_type": _text(correction.get("entity_type")) or "service_provider",
            "organization": _text(correction.get("organization")),
            "category_or_specialty": _text(correction.get("category_or_specialty")),
            "aliases": [],
            "contact_identifiers": {},
            "source_bindings": [],
            "provenance": [],
            "verification_status": "owner_confirmed",
        }
        directory.append(target)
    else:
        target = deepcopy(target)
    alias = _text(candidate.get("person_or_organization_name") or candidate.get("raw_title"))
    target["aliases"] = sorted(set(target.get("aliases", []) + [target["display_name"], alias]) - {""})
    target["source_bindings"] = sorted(set(target.get("source_bindings", []) + [source_key]))
    if _text(correction.get("display_name")):
        target["display_name"] = _text(correction.get("display_name"))
    if "category_or_specialty" in correction:
        target["category_or_specialty"] = _text(correction.get("category_or_specialty"))
    target["verification_status"] = "owner_confirmed"
    target["provenance"] = list(target.get("provenance", [])) + [{"kind": "owner_correction", "source_record_id": source_key}]
    directory = [target if row["entity_uuid"] == target["entity_uuid"] else row for row in directory]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "corrected",
        "appointment": {**deepcopy(candidate), "provider_entity_uuid": target["entity_uuid"], "canonical_title": _canonical_title(candidate, target)},
        "entity": target,
        "directory": directory,
        "research_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["resolve", "correct"])
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        result = resolve(payload) if args.action == "resolve" else correct(payload)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

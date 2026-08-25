#!/usr/bin/env python3
"""Normalize employer/shared run-sheet evidence into unique canonical Route upserts.

Historical run sheets are evidence for reusable terminal-pair paid mileage. They do
NOT create one historical Trip/Mileage row per source occurrence. Actual LifeOS
Trips remain the separately audited work occurrences created from live/company
evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

PAIR_RE = re.compile(r"^\s*([A-Za-z0-9]{2,8})\s*-\s*([A-Za-z0-9]{2,8})\s*$")

def normalize_aliases(raw: dict[str, Any] | None) -> dict[str, str]:
    """Validate explicit, source-specific terminal aliases.

    Aliases are evidence, not universal policy, so callers must supply them.  The
    public importer deliberately carries no employer-specific corrections.
    """
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("terminal aliases must be an object")
    direct: dict[str, str] = {}
    for source, target in raw.items():
        left = re.sub(r"\s+", "", str(source)).upper()
        right = re.sub(r"\s+", "", str(target)).upper()
        if not left or not right or not re.fullmatch(r"[A-Z0-9]{2,8}", left):
            raise ValueError(f"invalid terminal alias source: {source!r}")
        if not re.fullmatch(r"[A-Z0-9]{2,8}", right):
            raise ValueError(f"invalid terminal alias target for {source!r}: {target!r}")
        if left in direct and direct[left] != right:
            raise ValueError(f"conflicting normalized terminal alias source: {source!r}")
        direct[left] = right

    aliases: dict[str, str] = {}
    for source in direct:
        current = source
        visited: set[str] = set()
        while current in direct and direct[current] != current:
            if current in visited:
                raise ValueError(f"cyclic terminal aliases include {source!r}")
            visited.add(current)
            current = direct[current]
        aliases[source] = current
    return aliases


def normalize_code(value: str, aliases: dict[str, str] | None = None) -> str:
    code = re.sub(r"\s+", "", value or "").upper()
    return (aliases or {}).get(code, code)


def parse_miles(value: Any) -> int | None:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    try:
        number = float(text)
        if not math.isfinite(number):
            return None
        miles = int(round(number))
    except (OverflowError, ValueError):
        return None
    return miles if miles > 0 else None


def _parse_observed_at(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid observed_at timestamp: {text!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"observed_at must include a UTC offset: {text!r}")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_row(
    row: dict[str, Any], aliases: dict[str, str] | None = None
) -> dict[str, Any] | None:
    """Return one normalized terminal-pair observation or None.

    Accept conventional TRIP/MILES keys. Connector adapters should normalize odd
    column layouts into those keys before calling this contract.
    """
    trip = str(row.get("trip") or row.get("TRIP") or "").strip()
    match = PAIR_RE.match(trip)
    miles = parse_miles(row.get("miles") if "miles" in row else row.get("MILES"))
    if not match or miles is None:
        return None
    origin, destination = (normalize_code(part, aliases) for part in match.groups())
    if not origin or not destination or origin == destination:
        return None
    pair = tuple(sorted((origin, destination)))
    return {
        "origin": origin,
        "destination": destination,
        "pair_a": pair[0],
        "pair_b": pair[1],
        "paid_miles": miles,
        "source_tab": str(row.get("source_tab") or "").strip(),
        "source_date": str(row.get("date") or row.get("DATE") or "").strip(),
        "observed_at": _parse_observed_at(row.get("observed_at")),
    }


def choose_pair_value(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose reusable paid miles while retaining variant counts as provenance."""
    values = [int(record["paid_miles"]) for record in records]
    counts = Counter(values)
    max_count = max(counts.values())
    modes = {value for value, count in counts.items() if count == max_count}
    if len(modes) == 1:
        chosen = next(iter(modes))
        basis = "modal"
    else:
        chosen = None
        basis = "ambiguous-modal-tie"

    return {
        "paid_miles": chosen,
        "selection_basis": basis,
        "observation_count": len(records),
        "source_variants": dict(sorted(counts.items())),
    }


def reconcile(
    rows: list[dict[str, Any]], terminal_aliases: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    aliases = normalize_aliases(terminal_aliases)
    observations: list[dict[str, Any]] = []
    seen_observations: set[tuple[str, str, int, str, str]] = set()
    malformed = 0

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row {index} must be an object")
        item = normalize_row(row, aliases)
        if item is None:
            malformed += 1
            continue
        evidence_key = (
            item["origin"],
            item["destination"],
            int(item["paid_miles"]),
            item["source_tab"],
            item["source_date"],
        )
        if evidence_key in seen_observations:
            continue
        seen_observations.add(evidence_key)
        observations.append(item)

    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in observations:
        by_pair[(item["pair_a"], item["pair_b"])].append(item)

    route_upserts = []
    unresolved_routes = []
    for (a, b), records in sorted(by_pair.items()):
        records.sort(key=lambda record: (
            record["observed_at"],
            record["source_date"],
            record["source_tab"],
            record["origin"],
            record["destination"],
            int(record["paid_miles"]),
        ))
        choice = choose_pair_value(records)
        if choice["paid_miles"] is None:
            unresolved_routes.append({
                "pair_a": a,
                "pair_b": b,
                "reason": choice["selection_basis"],
                "observation_count": choice["observation_count"],
                "source_variants": choice["source_variants"],
            })
            continue
        route_upserts.append({
            "pair_a": a,
            "pair_b": b,
            "paid_miles_a_to_b": choice["paid_miles"],
            "paid_miles_b_to_a": choice["paid_miles"],
            "selection_basis": choice["selection_basis"],
            "observation_count": choice["observation_count"],
            "source_variants": choice["source_variants"],
        })

    return {
        "status": "degraded" if malformed or unresolved_routes else "ok",
        "symmetric_paid_miles": True,
        "source_row_count": len(rows),
        "valid_observation_count": len(observations),
        "ignored_malformed_count": malformed,
        "route_pair_count": len(route_upserts),
        "unresolved_route_count": len(unresolved_routes),
        "historical_occurrences_imported": False,
        "route_upserts": route_upserts,
        "unresolved_routes": unresolved_routes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSON list of normalized source row objects")
    parser.add_argument("--aliases", help="JSON object mapping proven source codes to canonical codes")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        if args.input == "-":
            rows = json.load(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as handle:
                rows = json.load(handle)
        if not isinstance(rows, list):
            raise ValueError("input must be a JSON list")
        aliases = None
        if args.aliases:
            with open(args.aliases, "r", encoding="utf-8") as handle:
                aliases = json.load(handle)
            if not isinstance(aliases, dict):
                raise ValueError("aliases must be a JSON object")
        output = reconcile(rows, aliases)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        output = {"status": "error", "errors": [str(exc)]}
    json.dump(output, sys.stdout, indent=2 if args.pretty else None, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if output.get("status") in {"ok", "degraded"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate and verify a deployment-owned M.I.R.R.O.R. brief schedule.

The portable product has no default brief time. Onboarding records only times the
user explicitly selected. The resulting non-secret schedule configuration belongs
in that deployment's version-controlled source and the live scheduler must be read
back against it exactly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class ScheduleError(ValueError):
    """Raised when versioned brief configuration is invalid."""


def _load(path: str) -> dict[str, Any]:
    try:
        if path == "-":
            value = json.load(sys.stdin)
        else:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScheduleError(f"cannot read schedule JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ScheduleError("schedule JSON root must be an object")
    return value


def normalize(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ScheduleError("schedule configuration must be an object")
    if config.get("schema_version") != 1:
        raise ScheduleError("schedule schema_version must be 1")

    timezone_name = str(config.get("canonical_timezone") or "").strip()
    if not timezone_name:
        raise ScheduleError("canonical_timezone is required")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ScheduleError("canonical_timezone must be a valid IANA timezone") from exc

    briefs = config.get("briefs")
    if not isinstance(briefs, list):
        raise ScheduleError("briefs must be an array; use [] when recurring briefs are disabled")
    if len(briefs) > 16:
        raise ScheduleError("briefs may contain at most 16 user-selected slots")

    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    enabled_times: set[str] = set()
    for index, raw in enumerate(briefs, start=1):
        if not isinstance(raw, dict):
            raise ScheduleError(f"brief {index} must be an object")
        unknown = sorted(set(raw) - {"id", "time", "enabled", "notification_mode"})
        if unknown:
            raise ScheduleError(f"brief {index} has unsupported keys: {', '.join(unknown)}")
        slot_id = str(raw.get("id") or "").strip().lower()
        if not ID_RE.fullmatch(slot_id):
            raise ScheduleError(f"brief {index} id must be a lowercase stable identifier")
        if slot_id in ids:
            raise ScheduleError(f"duplicate brief id: {slot_id}")
        ids.add(slot_id)

        local_time = str(raw.get("time") or "").strip()
        if not TIME_RE.fullmatch(local_time):
            raise ScheduleError(f"brief {slot_id} time must be exact local 24-hour HH:MM")

        enabled = raw.get("enabled")
        if not isinstance(enabled, bool):
            raise ScheduleError(f"brief {slot_id} enabled must be boolean")
        if enabled and local_time in enabled_times:
            raise ScheduleError(f"duplicate enabled brief time: {local_time}")
        if enabled:
            enabled_times.add(local_time)

        notification_mode = str(raw.get("notification_mode") or "").strip()
        if not notification_mode or len(notification_mode) > 80 or any(
            char in notification_mode for char in "\r\n"
        ):
            raise ScheduleError(
                f"brief {slot_id} notification_mode must be 1-80 characters on one line"
            )

        normalized.append(
            {
                "id": slot_id,
                "time": local_time,
                "enabled": enabled,
                "notification_mode": notification_mode,
            }
        )

    return {
        "schema_version": 1,
        "canonical_timezone": timezone_name,
        "briefs": normalized,
    }


def desired_dispatch(config: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize(config)
    return {
        "canonical_timezone": normalized["canonical_timezone"],
        "slots": [
            {
                "id": row["id"],
                "time": row["time"],
                "notification_mode": row["notification_mode"],
            }
            for row in normalized["briefs"]
            if row["enabled"]
        ],
    }


def verify(config: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    desired = desired_dispatch(config)
    if not isinstance(observed, dict):
        raise ScheduleError("observed scheduler readback must be an object")

    blocks: list[str] = []
    degradations: list[str] = []
    if observed.get("definition_readback") is not True:
        blocks.append("schedule-definition-readback-missing")
    if observed.get("canonical_timezone") != desired["canonical_timezone"]:
        blocks.append("schedule-timezone-mismatch")
    if observed.get("slots") != desired["slots"]:
        blocks.append("schedule-slots-mismatch")
    if desired["slots"] and observed.get("observed_firing") is not True:
        degradations.append("schedule-awaiting-observed-firing")

    decision = "blocked" if blocks else "degraded" if degradations else "ready"
    return {
        "decision": decision,
        "desired": desired,
        "blocks": blocks,
        "degradations": degradations,
        "recurring_briefs_enabled": bool(desired["slots"]),
    }


def _emit(value: dict[str, Any], pretty: bool) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2 if pretty else None)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--config", required=True)
    validate_parser.add_argument("--pretty", action="store_true")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--config", required=True)
    verify_parser.add_argument("--observed", required=True)
    verify_parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args(argv)
    try:
        config = _load(args.config)
        if args.command == "validate":
            output = {"status": "ok", "schedule": desired_dispatch(config)}
            code = 0
        else:
            observed = _load(args.observed)
            output = verify(config, observed)
            code = 0 if output["decision"] == "ready" else 3
    except ScheduleError as exc:
        output = {"status": "error", "errors": [str(exc)]}
        code = 2
    _emit(output, args.pretty)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

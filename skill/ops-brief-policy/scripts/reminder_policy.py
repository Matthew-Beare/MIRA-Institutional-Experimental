#!/usr/bin/env python3
"""Plan appointment and medication reminders without per-event automations."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


POLICY_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
REMINDER_NAMESPACE = uuid.UUID("ca23436b-efb3-44bb-b1ad-96cc11531fae")
MAX_HORIZON_DAYS = 31
APPOINTMENT_STATUSES = {"confirmed", "tentative", "cancelled"}
MEDICATION_STATUSES = {"active", "paused", "ended"}
MEDICATION_SOURCE_AUTHORITIES = {
    "owner_confirmation",
    "prescription_label",
    "pharmacy",
    "clinician",
}
DEFAULT_APPOINTMENT_PROFILE = {
    "day_before_local_time": "18:00",
    "morning_of_local_time": "08:00",
    "relative_minutes_before": 60,
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _bool(value: Any, field: str, *, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    normalized = _text(value).lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    raise ValueError(f"{field} must be an explicit boolean")


def _token(value: Any, field: str) -> str:
    result = _required(value, field).lower().replace("-", "_").replace(" ", "_")
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", result):
        raise ValueError(f"{field} must be a lowercase token")
    return result


def _uuid(value: Any, field: str) -> str:
    raw = _required(value, field)
    try:
        parsed = uuid.UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID") from exc
    if raw != str(parsed) or parsed.variant != uuid.RFC_4122 or parsed.version not in {1, 3, 4, 5}:
        raise ValueError(f"{field} must be a canonical RFC 4122 UUID")
    return raw


def _zone(value: Any) -> ZoneInfo:
    name = _required(value, "timezone")
    try:
        zone = ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"timezone is not an installed IANA timezone: {name}") from exc
    if name.upper() in {"EST", "EDT", "CST", "CDT", "MST", "MDT", "PST", "PDT"}:
        raise ValueError("timezone must be a named IANA zone, not a fixed offset/abbreviation")
    return zone


def _timestamp(value: Any, field: str, zone: ZoneInfo) -> datetime:
    raw = _required(value, field)
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone/UTC offset")
    return parsed.astimezone(zone)


def _clock(value: Any, field: str) -> time:
    raw = _required(value, field)
    try:
        parsed = time.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be HH:MM or HH:MM:SS") from exc
    if parsed.tzinfo is not None:
        raise ValueError(f"{field} must be a local wall time without an offset")
    return parsed.replace(microsecond=0)


def _local_datetime(day: date, wall_time: time, zone: ZoneInfo, field: str) -> datetime:
    candidate = datetime.combine(day, wall_time).replace(tzinfo=zone, fold=0)
    round_trip = candidate.astimezone(timezone.utc).astimezone(zone)
    if round_trip.replace(tzinfo=None) != candidate.replace(tzinfo=None):
        raise ValueError(f"{field} falls in a nonexistent local time caused by a clock change")
    alternate = candidate.replace(fold=1)
    if alternate.utcoffset() != candidate.utcoffset():
        raise ValueError(f"{field} is ambiguous during a clock change; configure an explicit safe local time")
    return candidate


def _deterministic_id(kind: str, source_id: str, fire_at: datetime) -> str:
    identity = f"{kind}\x1f{source_id}\x1f{fire_at.astimezone(timezone.utc).isoformat()}"
    return str(uuid.uuid5(REMINDER_NAMESPACE, identity))


def _profile(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("appointment_reminder_profile")
    if raw in (None, ""):
        raw = DEFAULT_APPOINTMENT_PROFILE
    if not isinstance(raw, dict):
        raise ValueError("appointment_reminder_profile must be an object")
    unknown = sorted(set(raw) - set(DEFAULT_APPOINTMENT_PROFILE))
    if unknown:
        raise ValueError("appointment_reminder_profile has unknown fields: " + ", ".join(unknown))
    relative = raw.get("relative_minutes_before", 60)
    if isinstance(relative, bool) or not isinstance(relative, int) or not 1 <= relative <= 10080:
        raise ValueError("appointment_reminder_profile.relative_minutes_before must be 1..10080")
    return {
        "day_before_local_time": _clock(
            raw.get("day_before_local_time", DEFAULT_APPOINTMENT_PROFILE["day_before_local_time"]),
            "appointment_reminder_profile.day_before_local_time",
        ),
        "morning_of_local_time": _clock(
            raw.get("morning_of_local_time", DEFAULT_APPOINTMENT_PROFILE["morning_of_local_time"]),
            "appointment_reminder_profile.morning_of_local_time",
        ),
        "relative_minutes_before": relative,
    }


def _source_identity(raw: dict[str, Any], prefix: str) -> tuple[str, str]:
    return (
        _token(raw.get("source_authority"), f"{prefix}.source_authority"),
        _required(raw.get("source_record_id"), f"{prefix}.source_record_id"),
    )


def _appointment_rows(payload: dict[str, Any], zone: ZoneInfo) -> list[dict[str, Any]]:
    raw_rows = payload.get("appointments", [])
    if not isinstance(raw_rows, list):
        raise ValueError("appointments must be a list")
    output: list[dict[str, Any]] = []
    ids: set[str] = set()
    sources: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_rows):
        prefix = f"appointments[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{prefix} must be an object")
        event_id = _required(raw.get("event_id"), f"{prefix}.event_id")
        source = _source_identity(raw, prefix)
        if event_id in ids or source in sources:
            raise ValueError(f"{prefix} duplicates an appointment identity")
        ids.add(event_id)
        sources.add(source)
        status = _token(raw.get("status"), f"{prefix}.status")
        if status not in APPOINTMENT_STATUSES:
            raise ValueError(f"{prefix}.status is unsupported: {status}")
        output.append({
            "event_id": event_id,
            "title": _required(raw.get("title"), f"{prefix}.title"),
            "start_at": _timestamp(raw.get("start_at"), f"{prefix}.start_at", zone),
            "status": status,
            "reminder_enabled": _bool(raw.get("reminder_enabled"), f"{prefix}.reminder_enabled", default=True),
            "source_authority": source[0],
            "source_record_id": source[1],
        })
    return output


def _medication_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_rows = payload.get("medications", [])
    if not isinstance(raw_rows, list):
        raise ValueError("medications must be a list")
    output: list[dict[str, Any]] = []
    ids: set[str] = set()
    sources: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_rows):
        prefix = f"medications[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{prefix} must be an object")
        regimen_uuid = _uuid(raw.get("regimen_uuid"), f"{prefix}.regimen_uuid")
        source = _source_identity(raw, prefix)
        if regimen_uuid in ids or source in sources:
            raise ValueError(f"{prefix} duplicates a medication-regimen identity")
        ids.add(regimen_uuid)
        sources.add(source)
        if source[0] not in MEDICATION_SOURCE_AUTHORITIES:
            raise ValueError(f"{prefix}.source_authority is not permitted for medication timing")
        status = _token(raw.get("status"), f"{prefix}.status")
        if status not in MEDICATION_STATUSES:
            raise ValueError(f"{prefix}.status is unsupported: {status}")
        schedule = raw.get("schedule_times")
        if not isinstance(schedule, list) or not schedule:
            raise ValueError(f"{prefix}.schedule_times must be a non-empty explicit list")
        clocks = [_clock(value, f"{prefix}.schedule_times[{offset}]") for offset, value in enumerate(schedule)]
        if len(clocks) != len(set(clocks)):
            raise ValueError(f"{prefix}.schedule_times contains duplicates")
        confirmed = _bool(raw.get("schedule_confirmed"), f"{prefix}.schedule_confirmed")
        if status == "active" and not confirmed:
            raise ValueError(f"{prefix}: an active schedule must be explicitly confirmed")
        output.append({
            "regimen_uuid": regimen_uuid,
            "display_name": _required(raw.get("display_name"), f"{prefix}.display_name"),
            "instructions_text": _text(raw.get("instructions_text")),
            "schedule_times": sorted(clocks),
            "schedule_confirmed": confirmed,
            "status": status,
            "reminder_enabled": _bool(raw.get("reminder_enabled"), f"{prefix}.reminder_enabled", default=True),
            "source_authority": source[0],
            "source_record_id": source[1],
        })
    return output


def _in_window(fire_at: datetime, lower: datetime, upper: datetime) -> bool:
    return lower <= fire_at < upper


def plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Return bounded deterministic reminders for the consolidated control cycle."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    zone = _zone(payload.get("timezone"))
    now = _timestamp(payload.get("now"), "now", zone)
    window_start = _timestamp(payload.get("window_start"), "window_start", zone)
    window_end = _timestamp(payload.get("window_end"), "window_end", zone)
    if window_start >= window_end:
        raise ValueError("window_start must be before window_end")
    if window_end - window_start > timedelta(days=MAX_HORIZON_DAYS):
        raise ValueError(f"planning horizon must not exceed {MAX_HORIZON_DAYS} days")
    lower = max(now, window_start)
    appointment_enabled = _bool(payload.get("appointment_reminders_enabled"), "appointment_reminders_enabled")
    medication_enabled = _bool(payload.get("medication_reminders_enabled"), "medication_reminders_enabled")
    caregiver_sharing = _bool(payload.get("caregiver_sharing_enabled"), "caregiver_sharing_enabled")
    caregiver_recipient_id = _text(payload.get("caregiver_recipient_id"))
    if caregiver_sharing and not caregiver_recipient_id:
        raise ValueError("caregiver_recipient_id is required when caregiver sharing is enabled")
    audience = "caregiver_and_user" if caregiver_sharing else "user"

    reminders: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    profile = _profile(payload)
    if appointment_enabled:
        for event in _appointment_rows(payload, zone):
            if event["status"] == "cancelled" or not event["reminder_enabled"]:
                suppressed.append({"source_id": event["event_id"], "kind": "appointment", "reason": "cancelled_or_disabled"})
                continue
            start = event["start_at"]
            candidates = [
                (
                    "day_before",
                    _local_datetime(start.date() - timedelta(days=1), profile["day_before_local_time"], zone, "appointment day-before reminder"),
                ),
                (
                    "morning_of",
                    _local_datetime(start.date(), profile["morning_of_local_time"], zone, "appointment morning-of reminder"),
                ),
                ("relative", start - timedelta(minutes=profile["relative_minutes_before"])),
            ]
            grouped: dict[datetime, list[str]] = {}
            for trigger, fire_at in candidates:
                if fire_at >= start:
                    suppressed.append({"source_id": event["event_id"], "kind": "appointment", "trigger": trigger, "reason": "would_fire_at_or_after_start"})
                elif _in_window(fire_at, lower, window_end):
                    grouped.setdefault(fire_at, []).append(trigger)
            for fire_at, triggers in grouped.items():
                reminders.append({
                    "reminder_uuid": _deterministic_id("appointment", event["event_id"], fire_at),
                    "kind": "appointment",
                    "source_id": event["event_id"],
                    "title": event["title"],
                    "fire_at": fire_at.isoformat(),
                    "event_start_at": start.isoformat(),
                    "triggers": sorted(triggers),
                    "audience": audience,
                    "caregiver_recipient_id": caregiver_recipient_id if caregiver_sharing else "",
                    "source_authority": event["source_authority"],
                    "source_record_id": event["source_record_id"],
                })

    if medication_enabled:
        day = lower.date()
        last_day = window_end.date()
        for regimen in _medication_rows(payload):
            if regimen["status"] != "active" or not regimen["reminder_enabled"]:
                suppressed.append({"source_id": regimen["regimen_uuid"], "kind": "medication", "reason": "inactive_or_disabled"})
                continue
            current_day = day
            while current_day <= last_day:
                for wall_time in regimen["schedule_times"]:
                    fire_at = _local_datetime(current_day, wall_time, zone, "medication reminder")
                    if _in_window(fire_at, lower, window_end):
                        reminders.append({
                            "reminder_uuid": _deterministic_id("medication", regimen["regimen_uuid"], fire_at),
                            "kind": "medication",
                            "source_id": regimen["regimen_uuid"],
                            "title": regimen["display_name"],
                            "instructions_text": regimen["instructions_text"],
                            "fire_at": fire_at.isoformat(),
                            "triggers": ["explicit_regimen_time"],
                            "audience": audience,
                            "caregiver_recipient_id": caregiver_recipient_id if caregiver_sharing else "",
                            "source_authority": regimen["source_authority"],
                            "source_record_id": regimen["source_record_id"],
                        })
                current_day += timedelta(days=1)

    reminders.sort(key=lambda row: (row["fire_at"], row["kind"], row["source_id"]))
    ids = [row["reminder_uuid"] for row in reminders]
    if len(ids) != len(set(ids)):
        raise ValueError("reminder planner produced a duplicate deterministic identity")
    return {
        "status": "ok",
        "policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "timezone": zone.key,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "appointment_reminders_enabled": appointment_enabled,
        "medication_reminders_enabled": medication_enabled,
        "caregiver_sharing_enabled": caregiver_sharing,
        "delivery_model": "single_control_cycle_projection_no_per_event_automations",
        "reminders": reminders,
        "suppressed": suppressed,
        "safety": {
            "medication_schedule_requires_explicit_supported_evidence": True,
            "dose_or_schedule_inference_prohibited": True,
            "missed_dose_advice_prohibited": True,
            "caregiver_sharing_requires_opt_in": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        print(json.dumps(plan(json.loads(raw)), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

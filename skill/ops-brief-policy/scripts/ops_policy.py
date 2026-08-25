#!/usr/bin/env python3
"""Deterministic policy engine for the user's Daily Ops Briefs."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import OrderedDict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from time import sleep as _sleep
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


POLICY_VERSION = "4.2.0"
TZ_NAME = "America/New_York"
TZ = ZoneInfo(TZ_NAME)
CANONICAL_BRIEF_SLOTS: tuple[tuple[int, int], ...] = ((2, 45), (14, 45))
DEFAULT_SLOT_GRACE_MINUTES = 15
DEFAULT_SLOT_EARLY_GRACE_SECONDS = 60
MAX_DECIMAL_MAGNITUDE = Decimal("1000000000000")
TIER_ORDER = {"Persistent": 0, "High": 1, "Medium": 2, "Low": 3}
NORMAL_TIERS = {"High", "Medium", "Low"}
VISIBILITIES = {"Home", "Road", "Both"}


def _key(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


TASK_KEYS = {
    "taskid": "task_id",
    "tier": "tier",
    "classification": "classification",
    "subsystem": "subsystem",
    "task": "task",
    "status": "status",
    "visibility": "visibility",
    "activefrom": "active_from",
    "activethrough": "active_through",
    "recurrencestaterule": "recurrence",
    "notes": "notes",
    "updatedet": "updated_et",
}

CONTROL_KEYS = {
    "recordid": "record_id",
    "type": "type",
    "item": "item",
    "state": "state",
    "startsatet": "starts_at",
    "expiresatet": "expires_at",
    "notes": "notes",
    "status": "status",
    "updatedet": "updated_et",
}

APPOINTMENT_KEYS = {
    "id": "id",
    "title": "title",
    "name": "title",
    "start": "start",
    "starttime": "start",
    "end": "end",
    "endtime": "end",
    "preparation": "preparation",
    "prep": "preparation",
}

ROUTE_KEYS = {
    "routeid": "route_id",
    "endpointa": "endpoint_a",
    "endpointb": "endpoint_b",
    "routeab": "route_ab",
    "routeba": "route_ba",
    "avgabhrs": "avg_ab_hours",
    "avgabhours": "avg_ab_hours",
    "avgbahrs": "avg_ba_hours",
    "avgbahours": "avg_ba_hours",
    "operationprofile": "operation_profile",
    "status": "status",
    "notes": "notes",
    "createdet": "created_et",
    "updatedet": "updated_et",
    "paidmilesab": "paid_miles_ab",
    "paidmilesba": "paid_miles_ba",
    "milessourceab": "miles_source_ab",
    "milessourceba": "miles_source_ba",
}

TRIP_KEYS = {
    "tripid": "trip_id",
    "routeid": "route_id",
    "origin": "origin",
    "destination": "destination",
    "departureet": "departure_et",
    "etaet": "eta_et",
    "etasource": "eta_source",
    "currentlocation": "current_location",
    "locationtimeet": "location_time_et",
    "weatherwatch": "weather_watch",
    "watchexpireset": "watch_expires_et",
    "status": "status",
    "routeoverride": "route_override",
    "notes": "notes",
    "updatedet": "updated_et",
}

SETTING_KEYS = {
    "settingid": "setting_id",
    "setting": "setting",
    "value": "value",
    "notes": "notes",
    "status": "status",
    "updatedet": "updated_et",
}

MILEAGE_KEYS = {
    "entryid": "entry_id",
    "weekendingthu": "week_ending",
    "weekending": "week_ending",
    "tripid": "trip_id",
    "routeid": "route_id",
    "departureet": "departure_et",
    "arrivalet": "arrival_et",
    "origin": "origin",
    "destination": "destination",
    "companypaidmiles": "company_paid_miles",
    "ratepermile": "rate_per_mile",
    "ratemile": "rate_per_mile",
    "grosspayestimate": "gross_pay_estimate",
    "milessource": "miles_source",
    "status": "status",
    "notes": "notes",
    "updatedet": "updated_et",
}

MILEAGE_SETTING_KEYS = {
    "setting": "setting",
    "value": "value",
}

MILEAGE_STATUSES = {"Planned", "Estimated", "Final", "Voided"}
CORE_INPUT_KEYS = (
    "tasks_values",
    "control_values",
)

OPTIONAL_INPUT_KEYS = (
    "routes_values",
    "trips_values",
    "travel_settings_values",
    "mileage_values",
    "mileage_settings_values",
    "appointments",
)

STRICT_INPUT_KEYS = (*CORE_INPUT_KEYS, *OPTIONAL_INPUT_KEYS)

VALUE_RANGE_SCHEMAS = {
    "tasks_values": set(TASK_KEYS.values()),
    "control_values": set(CONTROL_KEYS.values()),
    "routes_values": set(ROUTE_KEYS.values()),
    "trips_values": set(TRIP_KEYS.values()),
    "travel_settings_values": set(SETTING_KEYS.values()),
    "mileage_values": set(MILEAGE_KEYS.values()),
    "mileage_settings_values": set(MILEAGE_SETTING_KEYS.values()),
}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _canonical(value: Any, mapping: dict[str, str]) -> str:
    normalized = _key(value)
    return mapping.get(normalized, normalized)


def _objects_from_values(values: Any, mapping: dict[str, str]) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        return []
    headers = [_canonical(v, mapping) for v in values[0]]
    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(values[1:], start=2):
        if not isinstance(row, list) or not any(str(v).strip() for v in row):
            continue
        record = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
        record["_row"] = row_number
        records.append(record)
    return records


def _normalize_objects(values: Any, mapping: dict[str, str]) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    records: list[dict[str, Any]] = []
    for row_number, raw in enumerate(values, start=2):
        if not isinstance(raw, dict):
            continue
        record = {_canonical(k, mapping): v for k, v in raw.items()}
        record.setdefault("_row", row_number)
        records.append(record)
    return records


def _load_records(
    payload: dict[str, Any],
    object_key: str,
    values_key: str,
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    if values_key in payload:
        return _objects_from_values(payload.get(values_key), mapping)
    return _normalize_objects(payload.get(object_key, []), mapping)


def parse_datetime(value: Any, field: str = "timestamp") -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time.min)
    elif isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        try:
            result = datetime(1899, 12, 30) + timedelta(days=float(value))
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid {field}: {value!r}") from exc
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            result = datetime.fromisoformat(text)
        except ValueError:
            result = None
            for fmt in (
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y %I:%M:%S %p",
                "%m/%d/%Y %I:%M %p",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%m/%d/%Y",
                "%Y-%m-%d",
            ):
                try:
                    result = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            if result is None:
                raise ValueError(f"Invalid {field}: {value!r}")
    if result.tzinfo is None:
        candidate = result.replace(tzinfo=TZ, fold=0)
        round_trip = candidate.astimezone(timezone.utc).astimezone(TZ)
        if round_trip.replace(tzinfo=None) != result:
            raise ValueError(f"Invalid {field}: nonexistent Eastern local time {value!r}")
        result = candidate
    return result.astimezone(TZ)


def parse_aware_instant(value: Any, field: str = "instant") -> datetime:
    """Parse an actual instant; unlike sheet datetimes, never guess an offset."""
    if isinstance(value, datetime):
        result = value
    else:
        text_value = str(value or "").strip()
        if not text_value:
            raise ValueError(f"Missing required {field}.")
        if text_value.endswith("Z"):
            text_value = text_value[:-1] + "+00:00"
        try:
            result = datetime.fromisoformat(text_value)
        except ValueError as exc:
            raise ValueError(f"Invalid {field}: {value!r}") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field.capitalize()} must include a timezone/UTC offset.")
    return result


def _normalize_slots(
    slots: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    normalized: list[tuple[int, int]] = []
    try:
        raw_slots = list(slots)
    except TypeError as exc:
        raise ValueError("Canonical slots must be an iterable of (hour, minute) pairs.") from exc
    for raw in raw_slots:
        if not isinstance(raw, (tuple, list)) or len(raw) != 2:
            raise ValueError("Each canonical slot must be an (hour, minute) pair.")
        raw_hour, raw_minute = raw
        if (
            isinstance(raw_hour, bool)
            or isinstance(raw_minute, bool)
            or not isinstance(raw_hour, int)
            or not isinstance(raw_minute, int)
        ):
            raise ValueError("Canonical slot hours and minutes must be integers.")
        hour, minute = raw_hour, raw_minute
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid canonical slot: {hour:02d}:{minute:02d}")
        if (hour, minute) not in normalized:
            normalized.append((hour, minute))
    if not normalized:
        raise ValueError("At least one canonical slot is required.")
    return tuple(sorted(normalized))


def _parse_slot(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", str(value or ""))
    if not match:
        raise ValueError(f"Invalid slot {value!r}; expected HH:MM")
    return int(match.group(1)), int(match.group(2))


def _effective_local_slot(
    day: date,
    hour: int,
    minute: int,
    target_tz: ZoneInfo,
) -> tuple[datetime, str | None]:
    """Resolve a wall-clock slot through DST gaps and repeated hours.

    A nonexistent spring-forward slot moves to the first valid local instant
    after the gap. A repeated fall-back slot uses the first occurrence so one
    logical slot cannot enter twice.
    """
    naive = datetime.combine(day, time(hour, minute))

    def valid(candidate: datetime) -> bool:
        round_trip = candidate.astimezone(timezone.utc).astimezone(target_tz)
        return (
            round_trip.replace(tzinfo=None) == naive
            and round_trip.fold == candidate.fold
        )

    candidates = [
        naive.replace(tzinfo=target_tz, fold=fold)
        for fold in (0, 1)
    ]
    valid_candidates = [candidate for candidate in candidates if valid(candidate)]
    if valid_candidates:
        chosen = min(
            valid_candidates,
            key=lambda value: value.astimezone(timezone.utc),
        )
        adjustment = "first_repeated_occurrence" if len(valid_candidates) > 1 else None
        return chosen, adjustment

    for minutes_after in range(1, 181):
        shifted_naive = naive + timedelta(minutes=minutes_after)
        shifted = shifted_naive.replace(tzinfo=target_tz, fold=0)
        round_trip = shifted.astimezone(timezone.utc).astimezone(target_tz)
        if round_trip.replace(tzinfo=None) == shifted_naive:
            return shifted, "nonexistent_slot_to_first_valid_instant"
    raise ValueError(f"Unable to resolve local slot {naive.isoformat()} in {target_tz.key}.")


def canonical_slot_evidence(
    moment: datetime,
    *,
    timezone_name: str = TZ_NAME,
    slots: Iterable[tuple[int, int]] = CANONICAL_BRIEF_SLOTS,
    grace_minutes: int = DEFAULT_SLOT_GRACE_MINUTES,
    early_grace_seconds: int = DEFAULT_SLOT_EARLY_GRACE_SECONDS,
) -> dict[str, Any]:
    """Return DST-safe entry evidence with a bounded post-slot grace window."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("Current instant must include a timezone/UTC offset.")
    if not isinstance(grace_minutes, int) or isinstance(grace_minutes, bool):
        raise ValueError("Slot grace must be a whole number of minutes.")
    if grace_minutes < 0 or grace_minutes > 60:
        raise ValueError("Slot grace must be between 0 and 60 minutes.")
    if (
        not isinstance(early_grace_seconds, int)
        or isinstance(early_grace_seconds, bool)
    ):
        raise ValueError("Early slot grace must be a whole number of seconds.")
    if early_grace_seconds < 0 or early_grace_seconds > 300:
        raise ValueError("Early slot grace must be between 0 and 300 seconds.")
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        raise ValueError("Timezone name must be a nonblank IANA timezone string.")
    try:
        target_tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {timezone_name}") from exc
    normalized = _normalize_slots(slots)
    local = moment.astimezone(target_tz)
    slot_candidates = [
        (*slot, *_effective_local_slot(day, *slot, target_tz))
        for day in (
            local.date() - timedelta(days=1),
            local.date(),
            local.date() + timedelta(days=1),
        )
        for slot in normalized
    ]
    local_utc = local.astimezone(timezone.utc)
    scheduled_record = min(
        slot_candidates,
        key=lambda candidate: abs(
            (
                local_utc
                - candidate[2].astimezone(timezone.utc)
            ).total_seconds()
        ),
    )
    hour, minute, scheduled, dst_adjustment = scheduled_record
    raw_delay_seconds = (
        local_utc - scheduled.astimezone(timezone.utc)
    ).total_seconds()
    delay_seconds: int | float = (
        int(raw_delay_seconds)
        if raw_delay_seconds.is_integer()
        else round(raw_delay_seconds, 6)
    )
    grace_seconds = grace_minutes * 60
    entry_allowed = -early_grace_seconds <= delay_seconds <= grace_seconds
    exact = delay_seconds == 0
    logical_clock_exact = (
        exact
        and dst_adjustment != "nonexistent_slot_to_first_valid_instant"
    )
    matched_slot = f"{hour:02d}:{minute:02d}"
    if dst_adjustment == "nonexistent_slot_to_first_valid_instant" and entry_allowed:
        state = "dst_gap_adjusted"
    elif exact:
        state = "exact"
    elif entry_allowed:
        state = (
            "early_within_grace"
            if delay_seconds < 0
            else "delayed_within_grace"
        )
    elif delay_seconds < 0:
        state = "before_next_slot"
    else:
        state = "outside_grace"
    return {
        "timezone": timezone_name,
        "canonical_now": local.isoformat(),
        "canonical_date": local.date().isoformat(),
        "canonical_clock": local.strftime("%H:%M"),
        "configured_slots": [
            f"{hour:02d}:{minute:02d}" for hour, minute in normalized
        ],
        "grace_minutes": grace_minutes,
        "early_grace_seconds": early_grace_seconds,
        "scheduled_slot": scheduled.isoformat(),
        "logical_scheduled_slot": matched_slot,
        "dst_adjustment": dst_adjustment,
        "matched_slot": matched_slot if entry_allowed else None,
        "delay_seconds": delay_seconds,
        "exact_slot_match": logical_clock_exact,
        "effective_instant_match": exact,
        "slot_match": entry_allowed,
        "entry_allowed": entry_allowed,
        "state": state,
    }


def _runtime_utc_now() -> datetime:
    """Capture the execution host's current instant without model-supplied time."""
    return datetime.now(timezone.utc)


def live_slot_evidence(
    *,
    timezone_name: str = TZ_NAME,
    slots: Iterable[tuple[int, int]] = CANONICAL_BRIEF_SLOTS,
    grace_minutes: int = DEFAULT_SLOT_GRACE_MINUTES,
    early_grace_seconds: int = DEFAULT_SLOT_EARLY_GRACE_SECONDS,
    clock: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Own the production clock and absorb only bounded early dispatch jitter.

    Scheduled callers must use this path instead of constructing a timestamp in
    a prompt. If the scheduler hands control to the runtime up to the configured
    early-grace boundary before the slot, wait once until the slot and recapture
    the system clock. Anything earlier remains a scheduler-integrity failure.
    """
    clock_fn = clock or _runtime_utc_now
    sleep_fn = sleeper or _sleep
    evidence = canonical_slot_evidence(
        clock_fn(),
        timezone_name=timezone_name,
        slots=slots,
        grace_minutes=grace_minutes,
        early_grace_seconds=early_grace_seconds,
    )
    waited_seconds: int | float = 0
    if evidence["state"] == "early_within_grace":
        waited_seconds = -evidence["delay_seconds"]
        sleep_fn(float(waited_seconds))
        evidence = canonical_slot_evidence(
            clock_fn(),
            timezone_name=timezone_name,
            slots=slots,
            grace_minutes=grace_minutes,
            early_grace_seconds=early_grace_seconds,
        )
    return {
        **evidence,
        "clock_source": "runtime_system_clock",
        "waited_seconds": waited_seconds,
    }


def canonical_clock(moment: datetime, timezone_name: str = TZ_NAME) -> datetime:
    """Represent an offset-aware instant in the configured IANA timezone."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("Current instant must include an explicit timezone/UTC offset.")
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        raise ValueError("Timezone name must be a nonblank IANA timezone string.")
    try:
        target_tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {timezone_name}") from exc
    return moment.astimezone(target_tz)


def parse_date(value: Any, field: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.astimezone(TZ).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        parsed = parse_datetime(value, field)
        return parsed.date() if parsed else None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return parse_datetime(text, field).date()


def parse_decimal(value: Any, field: str) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        result = value
    else:
        text = str(value).strip().replace("$", "").replace(",", "")
        if not text:
            return None
        try:
            result = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid {field}: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Invalid {field}: {value!r}")
    if abs(result) > MAX_DECIMAL_MAGNITUDE:
        raise ValueError(f"{field} exceeds the supported magnitude.")
    return result


def _weekly_transition(value: Any, field: str) -> tuple[int, time]:
    """Parse a portable weekly transition such as ``Wednesday 16:30``."""
    text_value = str(value or "").strip()
    match = re.fullmatch(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"([01]?\d|2[0-3]):([0-5]\d)",
        text_value,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(
            f"Invalid {field}: {value!r}; expected weekday and 24-hour HH:MM."
        )
    return (
        WEEKDAYS[match.group(1).lower()],
        time(int(match.group(2)), int(match.group(3))),
    )


def normal_mode(
    moment: datetime,
    settings: dict[str, dict[str, Any]],
) -> str:
    """Resolve the configured recurring context without personal code defaults."""
    home_value = _setting_value(settings, "Weekly HOME transition")
    road_value = _setting_value(settings, "Weekly ROAD transition")
    if not home_value or not road_value:
        raise ValueError(
            "Travel Settings must define Weekly HOME transition and "
            "Weekly ROAD transition."
        )
    home_day, home_time = _weekly_transition(
        home_value, "Weekly HOME transition"
    )
    road_day, road_time = _weekly_transition(
        road_value, "Weekly ROAD transition"
    )
    if (home_day, home_time) == (road_day, road_time):
        raise ValueError("Weekly HOME and ROAD transitions cannot be identical.")

    local = moment.astimezone(TZ)

    def latest_transition(day: int, clock: time) -> datetime:
        days_back = (local.weekday() - day) % 7
        candidate, _ = _effective_local_slot(
            local.date() - timedelta(days=days_back),
            clock.hour,
            clock.minute,
            TZ,
        )
        if candidate.astimezone(timezone.utc) > local.astimezone(timezone.utc):
            candidate, _ = _effective_local_slot(
                candidate.date() - timedelta(days=7),
                clock.hour,
                clock.minute,
                TZ,
            )
        return candidate

    home_at = latest_transition(home_day, home_time)
    road_at = latest_transition(road_day, road_time)
    return (
        "HOME"
        if home_at.astimezone(timezone.utc) > road_at.astimezone(timezone.utc)
        else "ROAD"
    )


def prepare_overrides(
    controls: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    prepared: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    for row in controls:
        if (
            _key(row.get("type")) != "modeoverride"
            or _key(row.get("status")) != "active"
        ):
            continue
        record_id = str(row.get("record_id") or "").strip()
        row_name = record_id or f"Control row {row.get('_row', '?')}"
        if not record_id:
            errors.append(f"{row_name} has a blank Record ID.")
            continue
        if record_id in seen_ids:
            errors.append(f"Duplicate active Mode Override Record ID {record_id}.")
            continue
        seen_ids.add(record_id)
        state = str(row.get("state") or "").strip().upper()
        if state not in {"HOME", "ROAD"}:
            errors.append(
                f"{record_id} has invalid Mode Override state {state or '<blank>'}."
            )
            continue
        try:
            start = parse_datetime(
                row.get("starts_at"), f"Starts At for {record_id}"
            )
            expiry = parse_datetime(
                row.get("expires_at"), f"Expires At for {record_id}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if start and expiry and expiry <= start:
            errors.append(f"{record_id} expires at or before it starts.")
            continue
        prepared.append(
            {**row, "_state": state, "_start": start, "_expiry": expiry}
        )
    return prepared, errors


def resolve_mode_at(
    moment: datetime,
    overrides: list[dict[str, Any]],
    settings: dict[str, dict[str, Any]],
    *,
    active_trip: bool = False,
) -> tuple[str | None, str, dict[str, Any] | None, str | None]:
    local = moment.astimezone(TZ)
    active = [
        row
        for row in overrides
        if (row["_start"] is None or local >= row["_start"])
        and (row["_expiry"] is None or local < row["_expiry"])
    ]
    if not active:
        if active_trip:
            return "ROAD", "active_trip", None, None
        try:
            return normal_mode(local, settings), "weekly_schedule", None, None
        except ValueError as exc:
            return None, "unresolved", None, str(exc)
    floor = datetime.min.replace(tzinfo=timezone.utc)
    latest_start = max((row["_start"] or floor) for row in active)
    latest = [
        row for row in active if (row["_start"] or floor) == latest_start
    ]
    states = {row["_state"] for row in latest}
    if len(states) != 1:
        ids = ", ".join(
            str(row.get("record_id") or row.get("_row")) for row in latest
        )
        return (
            None,
            "conflict",
            None,
            f"Conflicting equally recent Mode Overrides: {ids}.",
        )
    selected = max(latest, key=lambda row: int(row.get("_row") or 0))
    return selected["_state"], "override", selected, None


def appointment_window(
    moment: datetime,
) -> tuple[dict[str, Any] | None, list[str]]:
    local = moment.astimezone(TZ)
    day_start = datetime.combine(local.date(), time.min, TZ)

    # Appointment reminders are slot-based and mode-independent. Saturday AM
    # is the weekly seven-day preview. Other AM briefs show today; PM briefs
    # show tomorrow. This yields one day-before reminder and one morning-of
    # reminder without exposing appointment-confirmation state.
    if local.weekday() == 5 and local.hour < 12:
        return {
            "kind": "saturday_seven_day_preview",
            "start": day_start.isoformat(),
            "end": (day_start + timedelta(days=7)).isoformat(),
            "used_seven_day_fallback": False,
        }, []

    if local.hour < 12:
        start = day_start
        kind = "morning_of"
    else:
        start = day_start + timedelta(days=1)
        kind = "day_before"
    return {
        "kind": kind,
        "start": start.isoformat(),
        "end": (start + timedelta(days=1)).isoformat(),
        "used_seven_day_fallback": False,
    }, []


def _title_case_enum(value: Any) -> str:
    text = str(value or "").strip().lower()
    return {
        "persistent": "Persistent",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "home": "Home",
        "road": "Road",
        "both": "Both",
    }.get(text, str(value or "").strip())


def eligible_tasks(
    tasks: list[dict[str, Any]],
    today: date,
) -> tuple[list[dict[str, Any]], list[str]]:
    eligible: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    for row in tasks:
        task_id = str(row.get("task_id") or "").strip()
        if task_id:
            if task_id in seen_ids:
                errors.append(f"Duplicate Task ID {task_id}.")
                continue
            seen_ids.add(task_id)
        status = str(row.get("status") or "").strip().lower()
        if status not in {"active", "scheduled"}:
            continue
        label = str(row.get("task") or "").strip()
        tier = _title_case_enum(row.get("tier"))
        classification = str(row.get("classification") or "").strip()
        visibility = _title_case_enum(row.get("visibility"))
        row_name = task_id or f"Tasks row {row.get('_row', '?')}"
        if not task_id:
            errors.append(f"{row_name} has a blank Task ID.")
            continue
        if not label:
            errors.append(f"{row_name} has a blank Task.")
            continue
        if tier not in TIER_ORDER:
            errors.append(
                f"{row_name} has invalid Tier {tier or '<blank>'}."
            )
            continue
        if not classification:
            errors.append(f"{row_name} has a blank Classification.")
            continue
        if tier != "Persistent" and visibility not in VISIBILITIES:
            errors.append(
                f"{row_name} has invalid Visibility {visibility or '<blank>'}."
            )
            continue
        try:
            active_from = parse_date(
                row.get("active_from"), f"Active From for {row_name}"
            )
            active_through = parse_date(
                row.get("active_through"),
                f"Active Through for {row_name}",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if active_from and active_through and active_through < active_from:
            errors.append(f"{row_name} ends before it starts.")
            continue
        if status == "scheduled" and (
            (active_from and today < active_from)
            or (active_through and today > active_through)
        ):
            continue
        eligible.append(
            {
                **row,
                "task_id": task_id,
                "task": label,
                "tier": tier,
                "classification": classification,
                "subsystem": str(row.get("subsystem") or "").strip(),
                "visibility": visibility,
            }
        )
    eligible.sort(
        key=lambda row: (
            TIER_ORDER[row["tier"]],
            int(row.get("_row") or 0),
        )
    )
    return eligible, errors


def _group_rows(rows: list[dict[str, Any]]) -> OrderedDict[str, Any]:
    tiers: OrderedDict[str, Any] = OrderedDict()
    for row in rows:
        tier = tiers.setdefault(row["tier"], OrderedDict())
        classification = tier.setdefault(
            row["classification"],
            {"direct": [], "subsystems": OrderedDict()},
        )
        if row["subsystem"]:
            classification["subsystems"].setdefault(
                row["subsystem"], []
            ).append(row)
        else:
            classification["direct"].append(row)
    return tiers


def _render_grouped(
    rows: list[dict[str, Any]],
    indent: int = 0,
) -> list[str]:
    lines: list[str] = []
    for tier_name, classifications in _group_rows(rows).items():
        lines.append(" " * indent + f"- {tier_name}")
        for class_name, contents in classifications.items():
            lines.append(" " * (indent + 2) + f"- {class_name}")
            for row in contents["direct"]:
                lines.append(" " * (indent + 4) + f"- {row['task']}")
            for subsystem, subsystem_rows in contents[
                "subsystems"
            ].items():
                lines.append(" " * (indent + 4) + f"- {subsystem}")
                for row in subsystem_rows:
                    lines.append(
                        " " * (indent + 6) + f"- {row['task']}"
                    )
    return lines


def task_output(
    tasks: list[dict[str, Any]],
    moment: datetime,
    mode: str,
    brief_slot: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, list[str]]:
    eligible, errors = eligible_tasks(tasks, moment.astimezone(TZ).date())
    allowed = {"Home", "Both"} if mode == "HOME" else {"Road", "Both"}
    visible = [
        row
        for row in eligible
        if row["tier"] == "Persistent" or row["visibility"] in allowed
    ]
    next_home: list[dict[str, Any]] = []
    local = moment.astimezone(TZ)
    if (
        mode == "ROAD"
        and local.weekday() == 5
        and brief_slot.upper() == "AM"
    ):
        candidates = [
            row
            for row in eligible
            if row["tier"] in NORMAL_TIERS
            and row["visibility"] == "Home"
        ]
        if candidates:
            best_rank = min(TIER_ORDER[row["tier"]] for row in candidates)
            next_home = [
                row
                for row in candidates
                if TIER_ORDER[row["tier"]] == best_rank
            ]
    lines = _render_grouped(visible)
    if next_home:
        lines.append("- Next Home")
        lines.extend(_render_grouped(next_home, indent=2))
    return visible, next_home, "\n".join(lines), errors


def filter_appointments(
    raw_appointments: Any,
    window: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if window is None:
        return [], []
    if not isinstance(raw_appointments, list):
        return [], ["Appointments must be a list."]
    errors = [
        f"Appointment row {index} must be an object."
        for index, row in enumerate(raw_appointments, start=2)
        if not isinstance(row, dict)
    ]
    appointments = _normalize_objects(raw_appointments, APPOINTMENT_KEYS)
    start = parse_datetime(window["start"], "appointment-window start")
    end = parse_datetime(window["end"], "appointment-window end")
    due: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in appointments:
        title = str(row.get("title") or "").strip()
        identity = str(
            row.get("id")
            or title
            or f"appointment row {row.get('_row', '?')}"
        )
        if not title:
            errors.append(f"Appointment {identity} has a blank title.")
            continue
        try:
            event_start = parse_datetime(
                row.get("start"), f"start for appointment {identity}"
            )
            event_end = parse_datetime(
                row.get("end"), f"end for appointment {identity}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if event_start is None:
            errors.append(f"Appointment {identity} has no start time.")
            continue
        if event_end is not None and event_end <= event_start:
            errors.append(f"Appointment {identity} ends at or before it starts.")
            continue
        event_identity = (str(row.get("id") or title).strip(), event_start.isoformat())
        if event_identity in seen:
            errors.append(f"Duplicate appointment {identity} at {event_start.isoformat()}.")
            continue
        seen.add(event_identity)
        if start <= event_start < end:
            due.append(
                {
                    "id": str(row.get("id") or ""),
                    "title": title,
                    "start": event_start.isoformat(),
                    "end": event_end.isoformat() if event_end else None,
                    "preparation": str(
                        row.get("preparation") or ""
                    ).strip(),
                }
            )
    due.sort(key=lambda row: row["start"])
    return due, errors


def mowing_season(moment: datetime) -> bool:
    """Return whether the local date is in April 1-November 1."""
    local_date = moment.astimezone(TZ).date()
    return date(local_date.year, 4, 1) <= local_date < date(
        local_date.year, 11, 1
    )


def _positive_hours(value: Any, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"Invalid {field}: {value!r}")
    if result <= 0:
        raise ValueError(f"{field} must be greater than zero.")
    return result


def reverse_route_overview(value: Any) -> str:
    """Reverse a segment-based route overview for the opposite direction."""
    text = str(value or "").strip()
    if not text:
        return ""
    segments = [
        segment.strip()
        for segment in re.split(r"\s*(?:→|->|\|)\s*", text)
        if segment.strip()
    ]
    if len(segments) < 2:
        return text
    return " → ".join(reversed(segments))


def prepare_routes(
    routes: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    prepared: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for row in routes:
        route_id = str(row.get("route_id") or "").strip()
        if route_id:
            if route_id in seen_ids:
                errors.append(f"Duplicate Route ID {route_id}.")
                continue
            seen_ids.add(route_id)
        if _key(row.get("status")) != "active":
            continue
        row_name = route_id or f"Routes row {row.get('_row', '?')}"
        endpoint_a = str(row.get("endpoint_a") or "").strip()
        endpoint_b = str(row.get("endpoint_b") or "").strip()
        route_ab = str(row.get("route_ab") or "").strip()
        if not route_id:
            errors.append(f"{row_name} has a blank Route ID.")
            continue
        if not endpoint_a or not endpoint_b:
            errors.append(f"{row_name} has a blank endpoint.")
            continue
        if _key(endpoint_a) == _key(endpoint_b):
            errors.append(f"{row_name} has identical endpoints.")
            continue
        if not route_ab:
            errors.append(f"{row_name} has a blank Route A → B.")
            continue
        pair = tuple(sorted((_key(endpoint_a), _key(endpoint_b))))
        if pair in seen_pairs:
            errors.append(
                f"Duplicate active endpoint pair for {endpoint_a} and "
                f"{endpoint_b}."
            )
            continue
        seen_pairs.add(pair)
        try:
            avg_ab = _positive_hours(
                row.get("avg_ab_hours"), f"Avg A → B for {row_name}"
            )
            avg_ba = _positive_hours(
                row.get("avg_ba_hours"), f"Avg B → A for {row_name}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        prepared.append(
            {
                **row,
                "route_id": route_id,
                "endpoint_a": endpoint_a,
                "endpoint_b": endpoint_b,
                "route_ab": route_ab,
                "route_ba": str(row.get("route_ba") or "").strip(),
                "avg_ab_hours": avg_ab,
                "avg_ba_hours": avg_ba,
                "operation_profile": str(
                    row.get("operation_profile") or ""
                ).strip(),
                "_endpoint_a_key": _key(endpoint_a),
                "_endpoint_b_key": _key(endpoint_b),
            }
        )
    return prepared, errors


def find_route(
    routes: list[dict[str, Any]],
    origin: Any,
    destination: Any,
    route_id: Any = "",
) -> tuple[dict[str, Any] | None, str | None]:
    origin_text = str(origin or "").strip()
    destination_text = str(destination or "").strip()
    if not origin_text or not destination_text:
        return None, None
    origin_key = _key(origin_text)
    destination_key = _key(destination_text)
    requested_id = str(route_id or "").strip()
    candidates = routes
    if requested_id:
        candidates = [row for row in routes if row["route_id"] == requested_id]
        if not candidates:
            return None, f"Unknown active Route ID {requested_id}."
    matches: list[tuple[dict[str, Any], bool]] = []
    for row in candidates:
        direct = (
            origin_key == row["_endpoint_a_key"]
            and destination_key == row["_endpoint_b_key"]
        )
        reverse = (
            origin_key == row["_endpoint_b_key"]
            and destination_key == row["_endpoint_a_key"]
        )
        if direct or reverse:
            matches.append((row, reverse))
    if not matches:
        if requested_id:
            return (
                None,
                f"Route ID {requested_id} does not match {origin_text} to "
                f"{destination_text}.",
            )
        return None, None
    if len(matches) > 1:
        return None, f"Multiple active routes match {origin_text} to {destination_text}."
    row, reverse = matches[0]
    if reverse:
        overview = row["route_ba"] or reverse_route_overview(row["route_ab"])
        average = row["avg_ba_hours"]
        eta_source = "Route Average"
        if average is None and row["avg_ab_hours"] is not None:
            average = row["avg_ab_hours"]
            eta_source = "Reverse Average Fallback"
        direction = "B_TO_A"
    else:
        overview = row["route_ab"]
        average = row["avg_ab_hours"]
        eta_source = "Route Average"
        if average is None and row["avg_ba_hours"] is not None:
            average = row["avg_ba_hours"]
            eta_source = "Reverse Average Fallback"
        direction = "A_TO_B"
    return {
        "route_id": row["route_id"],
        "direction": direction,
        "origin": origin_text,
        "destination": destination_text,
        "route_overview": overview,
        "average_hours": average,
        "eta_source": eta_source if average is not None else None,
        "operation_profile": row["operation_profile"],
    }, None


def prepare_settings(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    settings: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    seen_ids: set[str] = set()
    for row in rows:
        if _key(row.get("status")) != "active":
            continue
        setting = str(row.get("setting") or "").strip()
        setting_id = str(row.get("setting_id") or "").strip()
        row_name = setting_id or f"Travel Settings row {row.get('_row', '?')}"
        if not setting_id:
            errors.append(f"{row_name} has a blank Setting ID.")
            continue
        if setting_id in seen_ids:
            errors.append(f"Duplicate active Travel Setting ID {setting_id}.")
            continue
        seen_ids.add(setting_id)
        if not setting:
            errors.append(f"{row_name} has a blank Setting.")
            continue
        normalized = _key(setting)
        if normalized in settings:
            errors.append(f"Duplicate active Travel Setting {setting}.")
            continue
        settings[normalized] = {
            "setting_id": setting_id,
            "setting": setting,
            "value": str(row.get("value") or "").strip(),
            "notes": str(row.get("notes") or "").strip(),
        }
    return settings, errors


def _setting_value(
    settings: dict[str, dict[str, Any]], name: str, default: str = ""
) -> str:
    record = settings.get(_key(name))
    return record["value"] if record else default


def _setting_switch(
    settings: dict[str, dict[str, Any]], name: str
) -> tuple[bool, str | None]:
    value = _setting_value(settings, name)
    if not value:
        return False, None
    normalized = _key(value)
    if normalized in {"enabled", "true", "yes", "on", "1"}:
        return True, None
    if normalized in {"disabled", "false", "no", "off", "0"}:
        return False, None
    return False, f"Travel Setting {name} must be Enabled or Disabled, not {value!r}."


def _action(code: str, message: str, trip_id: str = "") -> dict[str, str]:
    result = {"code": code, "message": message}
    if trip_id:
        result["trip_id"] = trip_id
    return result


def _dedupe_actions(actions: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for action in actions:
        identity = (
            action.get("code", ""),
            action.get("message", ""),
            action.get("trip_id", ""),
        )
        if identity not in seen:
            seen.add(identity)
            result.append(action)
    return result


def pay_week(moment: datetime) -> tuple[date, date, datetime, datetime]:
    """Return Friday-through-Thursday pay-week boundaries in Eastern time."""
    local_date = moment.astimezone(TZ).date()
    days_since_friday = (local_date.weekday() - 4) % 7
    week_start_date = local_date - timedelta(days=days_since_friday)
    next_friday_date = week_start_date + timedelta(days=7)
    week_end_date = next_friday_date - timedelta(days=1)
    return (
        week_start_date,
        week_end_date,
        datetime.combine(week_start_date, time.min, TZ),
        datetime.combine(next_friday_date, time.min, TZ),
    )


def _mileage_settings(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, str], list[str]]:
    settings: dict[str, str] = {}
    errors: list[str] = []
    for row in rows:
        name = str(row.get("setting") or "").strip()
        value = str(row.get("value") or "").strip()
        if not name and not value:
            continue
        row_name = f"Mileage Settings row {row.get('_row', '?')}"
        if not name:
            errors.append(f"{row_name} has a blank Setting.")
            continue
        normalized = _key(name)
        if normalized in settings:
            errors.append(f"Duplicate Mileage Setting {name}.")
            continue
        settings[normalized] = value
    return settings, errors


def _mileage_rate(settings: dict[str, str]) -> tuple[Decimal | None, str | None]:
    for name in (
        "Rate per mile",
        "Rate per paid mile",
        "Default rate per mile",
        "Current rate per mile",
        "Company rate per mile",
    ):
        value = settings.get(_key(name))
        if value is not None:
            try:
                rate = parse_decimal(value, "mileage Rate per Mile")
            except ValueError as exc:
                return None, str(exc)
            if rate is None or rate <= 0:
                return None, "Mileage Rate per Mile must be greater than zero."
            return rate, None
    return None, "Mileage Settings is missing Rate per Mile."


def _mileage_row_has_data(row: dict[str, Any]) -> bool:
    """Ignore preformatted blank rows whose only value is a rate formula."""
    meaningful = (
        "entry_id",
        "week_ending",
        "trip_id",
        "route_id",
        "departure_et",
        "arrival_et",
        "origin",
        "destination",
        "company_paid_miles",
        "miles_source",
        "status",
        "notes",
        "updated_et",
    )
    return any(str(row.get(field) or "").strip() for field in meaningful)


def _format_miles(value: Decimal) -> str:
    text = f"{value:,.3f}".rstrip("0").rstrip(".")
    return text or "0"


def mileage_output(
    raw_mileage: list[dict[str, Any]],
    raw_mileage_settings: list[dict[str, Any]],
    raw_trips: list[dict[str, Any]],
    travel_settings: dict[str, dict[str, Any]],
    moment: datetime,
    inputs_present: bool,
) -> tuple[dict[str, Any], list[str]]:
    """Resolve the Thursday company-paid mileage and gross-pay summary."""
    is_thursday = moment.astimezone(TZ).weekday() == 3
    if not is_thursday:
        return {
            "mileage_summary_allowed": False,
            "mileage_summary_due": False,
            "mileage_summary": None,
            "mileage_summary_markdown": "",
            "actions_required": [],
        }, []
    enabled, enabled_error = _setting_switch(
        travel_settings, "Thursday mileage summary"
    )
    due = enabled or enabled_error is not None
    empty = {
        "mileage_summary_allowed": due,
        "mileage_summary_due": due,
        "mileage_summary": None,
        "mileage_summary_markdown": "",
        "actions_required": [],
    }
    if enabled_error:
        empty["actions_required"] = [
            _action(
                "mileage_summary_configuration_invalid",
                "Action Required — configure Thursday mileage summary as Enabled or Disabled.",
            )
        ]
        return empty, [enabled_error]
    if not enabled:
        return empty, []
    if not inputs_present:
        return empty, [
            "Mileage tracker inputs are unavailable; read Mileage Log and Settings."
        ]

    settings, errors = _mileage_settings(raw_mileage_settings)
    default_rate, rate_error = _mileage_rate(settings)
    if rate_error:
        errors.append(rate_error)

    week_start, week_end, week_start_at, next_friday_at = pay_week(moment)
    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    actions: list[dict[str, str]] = []

    for row in raw_mileage:
        if not _mileage_row_has_data(row):
            continue
        entry_id = str(row.get("entry_id") or "").strip()
        row_name = entry_id or f"Mileage Log row {row.get('_row', '?')}"
        if not entry_id:
            errors.append(f"{row_name} has a blank Entry ID.")
            continue
        if entry_id in seen_ids:
            errors.append(f"Duplicate Mileage Entry ID {entry_id}.")
            continue
        seen_ids.add(entry_id)

        status = str(row.get("status") or "").strip().title()
        if status not in MILEAGE_STATUSES:
            errors.append(
                f"{row_name} has invalid Status {status or '<blank>'}."
            )
            continue
        try:
            row_week_end = parse_date(
                row.get("week_ending"), f"Week Ending for {row_name}"
            )
            departure = parse_datetime(
                row.get("departure_et"), f"Departure for {row_name}"
            )
            miles = parse_decimal(
                row.get("company_paid_miles"),
                f"Company-Paid Miles for {row_name}",
            )
            row_rate = parse_decimal(
                row.get("rate_per_mile"), f"Rate per Mile for {row_name}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if row_week_end is None and departure is not None:
            row_week_end = pay_week(departure)[1]
        if row_week_end is None:
            errors.append(f"{row_name} has no Week Ending or Departure.")
            continue
        if row_week_end.weekday() != 3:
            errors.append(f"{row_name} Week Ending is not a Thursday.")
            continue
        if miles is not None and miles < 0:
            errors.append(f"{row_name} Company-Paid Miles cannot be negative.")
            continue
        if row_rate is not None and row_rate <= 0:
            errors.append(f"{row_name} Rate per Mile must be greater than zero.")
            continue

        entries.append(
            {
                "entry_id": entry_id,
                "trip_id": str(row.get("trip_id") or "").strip(),
                "week_ending": row_week_end,
                "status": status,
                "miles": miles,
                "rate": row_rate,
            }
        )

    current_entries = [
        row
        for row in entries
        if row["week_ending"] == week_end and row["status"] != "Voided"
    ]
    total_miles = Decimal("0")
    gross = Decimal("0")
    miles_by_status = {
        "Planned": Decimal("0"),
        "Estimated": Decimal("0"),
        "Final": Decimal("0"),
    }
    represented_trip_ids: set[str] = set()
    incomplete = False
    for row in current_entries:
        if row["trip_id"]:
            represented_trip_ids.add(row["trip_id"])
        if row["miles"] is None:
            incomplete = True
            if due:
                actions.append(
                    _action(
                        "company_paid_miles_required",
                        f"Provide company-paid miles for {row['entry_id']}.",
                        row["trip_id"],
                    )
                )
            continue
        effective_rate = row["rate"] or default_rate
        if effective_rate is None:
            incomplete = True
            errors.append(
                f"{row['entry_id']} has company-paid miles but no usable Rate per Mile."
            )
            continue
        total_miles += row["miles"]
        gross += row["miles"] * effective_rate
        miles_by_status[row["status"]] += row["miles"]
    known_week_trips: list[str] = []
    for row in raw_trips:
        trip_id = str(row.get("trip_id") or "").strip()
        if not trip_id or _key(row.get("status")) not in {"active", "arrived"}:
            continue
        try:
            departure = parse_datetime(
                row.get("departure_et"), f"Departure for {trip_id}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if departure is not None and week_start_at <= departure < next_friday_at:
            known_week_trips.append(trip_id)
    for trip_id in _dedupe(known_week_trips):
        if trip_id not in represented_trip_ids:
            incomplete = True
            if due:
                actions.append(
                    _action(
                        "trip_mileage_entry_required",
                        f"Record company-paid miles for {trip_id} for week ending {week_end.isoformat()}.",
                        trip_id,
                    )
                )

    gross = gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    summary = {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_paid_miles": _format_miles(total_miles),
        "final_paid_miles": _format_miles(miles_by_status["Final"]),
        "estimated_paid_miles": _format_miles(miles_by_status["Estimated"]),
        "planned_paid_miles": _format_miles(miles_by_status["Planned"]),
        "gross_pay_estimate": f"{gross:.2f}",
        "entry_count": len(current_entries),
        "data_complete": not incomplete,
        "rate_per_mile": (
            f"{default_rate:f}" if default_rate is not None else None
        ),
    }
    markdown = (
        f"- Week ending {week_end.strftime('%b %-d')} — "
        f"{_format_miles(total_miles)} company-paid miles — "
        f"${gross:,.2f} gross estimate "
        f"(final {_format_miles(miles_by_status['Final'])}; "
        f"estimated {_format_miles(miles_by_status['Estimated'])})"
    )
    result = {
        "mileage_summary_allowed": due,
        "mileage_summary_due": due,
        "mileage_summary": summary if due else None,
        "mileage_summary_markdown": markdown if due else "",
        "actions_required": _dedupe_actions(actions) if due else [],
    }
    return result, errors


def travel_output(
    raw_trips: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    settings: dict[str, dict[str, Any]],
    moment: datetime,
    mode: str,
    brief_slot: str,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    actions: list[dict[str, str]] = []
    prepared: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    local = moment.astimezone(TZ)

    for row in raw_trips:
        trip_id = str(row.get("trip_id") or "").strip()
        if trip_id:
            if trip_id in seen_ids:
                errors.append(f"Duplicate Trip ID {trip_id}.")
                continue
            seen_ids.add(trip_id)
        status_key = _key(row.get("status"))
        if status_key not in {"planned", "active"}:
            continue
        row_name = trip_id or f"Trips row {row.get('_row', '?')}"
        if not trip_id:
            errors.append(f"{row_name} has a blank Trip ID.")
            continue
        origin = str(row.get("origin") or "").strip()
        destination = str(row.get("destination") or "").strip()
        route_override = str(row.get("route_override") or "").strip()
        weather_key = _key(row.get("weather_watch"))
        weather_watch = {
            "": "Off",
            "off": "Off",
            "active": "Active",
            "pendingexpiry": "Pending Expiry",
        }.get(weather_key)
        if weather_watch is None:
            errors.append(
                f"{row_name} has invalid Weather Watch "
                f"{row.get('weather_watch') or '<blank>'}."
            )
            continue
        try:
            departure = parse_datetime(
                row.get("departure_et"), f"Departure for {row_name}"
            )
            eta = parse_datetime(row.get("eta_et"), f"ETA for {row_name}")
            location_time = parse_datetime(
                row.get("location_time_et"), f"Location Time for {row_name}"
            )
            watch_expiry = (
                parse_datetime(
                    row.get("watch_expires_et"),
                    f"Watch Expires for {row_name}",
                )
                if weather_watch != "Off"
                else None
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue

        route_match = None
        if origin and destination:
            route_match, route_error = find_route(
                routes, origin, destination, row.get("route_id")
            )
            if route_error:
                errors.append(route_error)
            if route_match is None and not route_error:
                actions.append(
                    _action(
                        "route_overview_required",
                        f"Provide the preferred route overview for {origin} to "
                        f"{destination}; it will be stored bidirectionally.",
                        trip_id,
                    )
                )
        elif origin or destination:
            missing = "destination" if origin else "origin"
            actions.append(
                _action(
                    f"trip_{missing}_required",
                    f"Provide the {missing} for {trip_id}.",
                    trip_id,
                )
            )
        elif not route_override:
            actions.append(
                _action(
                    "trip_corridor_required",
                    f"Provide an origin and destination or a road corridor for {trip_id}.",
                    trip_id,
                )
            )

        eta_source = str(row.get("eta_source") or "").strip()
        if eta is not None:
            eta_source = eta_source or "User"
        elif departure is not None and route_match:
            average = route_match.get("average_hours")
            if average is not None:
                eta = departure + timedelta(hours=float(average))
                eta_source = str(route_match.get("eta_source") or "Route Average")
        if departure and eta and eta <= departure:
            errors.append(f"{row_name} ETA is at or before departure.")
            continue

        derived_watch_expiry = False
        if weather_watch == "Active" and watch_expiry is None:
            if eta is not None:
                watch_expiry = eta
                derived_watch_expiry = True
            else:
                weather_watch = "Pending Expiry"
                actions.append(
                    _action(
                        "watch_expiry_required",
                        f"Provide a weather-watch expiration or destination ETA for {trip_id}.",
                        trip_id,
                    )
                )
        elif weather_watch == "Pending Expiry":
            actions.append(
                _action(
                    "watch_expiry_required",
                    f"Provide a weather-watch expiration or destination ETA for {trip_id}.",
                    trip_id,
                )
            )
        if watch_expiry and departure and watch_expiry <= departure:
            errors.append(f"{row_name} weather watch expires at or before departure.")
            continue

        overview = route_override or (
            str(route_match.get("route_overview") or "") if route_match else ""
        )
        progress = None
        if departure and eta and eta > departure:
            progress = (local - departure).total_seconds() / (
                eta - departure
            ).total_seconds()
            progress = round(max(0.0, min(1.0, progress)), 4)
        prepared.append(
            {
                "trip_id": trip_id,
                "status": "Active" if status_key == "active" else "Planned",
                "origin": origin,
                "destination": destination,
                "departure": departure,
                "eta": eta,
                "eta_source": eta_source or None,
                "current_location": str(
                    row.get("current_location") or ""
                ).strip(),
                "location_time": location_time,
                "route_id": (
                    str(route_match.get("route_id") or "")
                    if route_match
                    else str(row.get("route_id") or "").strip()
                ),
                "route_overview": overview,
                "operation_profile": (
                    str(route_match.get("operation_profile") or "")
                    if route_match
                    else ""
                ),
                "weather_watch": weather_watch,
                "watch_expiry": watch_expiry,
                "derived_watch_expiry": derived_watch_expiry,
                "progress_fraction": progress,
            }
        )

    active_trips = [
        row
        for row in prepared
        if row["status"] == "Active" and row["origin"] and row["destination"]
    ]
    if len(active_trips) > 1:
        errors.append(
            "Multiple active endpoint-to-endpoint trips are present: "
            + ", ".join(row["trip_id"] for row in active_trips)
            + "."
        )

    trip_status_row: dict[str, Any] | None = None
    if mode == "ROAD":
        if active_trips:
            trip_status_row = active_trips[0]
        else:
            future = [
                row
                for row in prepared
                if row["status"] == "Planned"
                and row["origin"]
                and row["destination"]
                and (row["departure"] is None or row["departure"] >= local)
            ]
            future.sort(
                key=lambda row: row["departure"]
                or datetime.max.replace(tzinfo=TZ)
            )
            if future:
                trip_status_row = future[0]

    if mode == "ROAD" and trip_status_row:
        trip_id = trip_status_row["trip_id"]
        if trip_status_row["departure"] is None:
            actions.append(
                _action(
                    "trip_departure_required",
                    f"Provide the departure time for {trip_id}.",
                    trip_id,
                )
            )
        if trip_status_row["eta"] is None:
            actions.append(
                _action(
                    "trip_eta_required",
                    f"Provide the destination ETA or average route runtime for {trip_id}.",
                    trip_id,
                )
            )
        saturday_am = (
            local.weekday() == 5 and brief_slot.upper() == "AM"
        )
        location_time = trip_status_row["location_time"]
        location_is_fresh = (
            location_time is not None
            and timedelta(0) <= local - location_time <= timedelta(hours=2)
        )
        if trip_status_row["status"] == "Active" and saturday_am:
            if not trip_status_row["current_location"] or not location_is_fresh:
                actions.append(
                    _action(
                        "saturday_location_update_requested",
                        f"Provide the current location for {trip_id} at the "
                        "Saturday 2:45 AM checkpoint.",
                        trip_id,
                    )
                )
        elif (
            trip_status_row["status"] == "Active"
            and not trip_status_row["current_location"]
        ):
            actions.append(
                _action(
                    "current_location_requested",
                    f"Provide the current location for {trip_id} when practical.",
                    trip_id,
                )
            )
        if (
            trip_status_row["status"] == "Active"
            and trip_status_row["eta"] is not None
            and local >= trip_status_row["eta"]
        ):
            actions.append(
                _action(
                    "trip_status_update_required",
                    f"Confirm arrival or update the ETA for {trip_id}.",
                    trip_id,
                )
            )

    watches: list[dict[str, Any]] = []
    expired_ids = [
        row["trip_id"]
        for row in prepared
        if row["weather_watch"] == "Active"
        and row["watch_expiry"] is not None
        and local >= row["watch_expiry"]
    ]
    if mode == "ROAD":
        for row in prepared:
            if row["weather_watch"] != "Active":
                continue
            if row["watch_expiry"] is not None and local >= row["watch_expiry"]:
                continue
            if not row["route_overview"]:
                continue
            watches.append(
                {
                    "trip_id": row["trip_id"],
                    "trip_status": row["status"],
                    "origin": row["origin"] or None,
                    "destination": row["destination"] or None,
                    "departure": (
                        row["departure"].isoformat() if row["departure"] else None
                    ),
                    "eta": row["eta"].isoformat() if row["eta"] else None,
                    "eta_source": row["eta_source"],
                    "current_location": row["current_location"] or None,
                    "location_time": (
                        row["location_time"].isoformat()
                        if row["location_time"]
                        else None
                    ),
                    "route_id": row["route_id"] or None,
                    "route_overview": row["route_overview"],
                    "operation_profile": row["operation_profile"] or None,
                    "watch_expires": (
                        row["watch_expiry"].isoformat()
                        if row["watch_expiry"]
                        else None
                    ),
                    "watch_expiry_source": (
                        "ETA" if row["derived_watch_expiry"] else "User"
                    ),
                    "progress_fraction": row["progress_fraction"],
                }
            )

    if (
        mode == "ROAD"
        and local.weekday() == 4
        and brief_slot.upper() == "PM"
    ):
        friday_enabled, friday_error = _setting_switch(
            settings, "Friday PM destination confirmation"
        )
        if friday_error:
            errors.append(friday_error)
        if friday_enabled:
            friday_trip = any(
                row["origin"]
                and row["destination"]
                and row["status"] in {"Planned", "Active"}
                and (
                    row["status"] == "Active"
                    or (
                        row["departure"] is not None
                        and row["departure"].date() == local.date()
                    )
                )
                for row in prepared
            )
            if not friday_trip:
                origin = _setting_value(settings, "Default terminal origin")
                departure = _setting_value(settings, "Default Friday departure")
                common = _setting_value(settings, "Common terminal destination")
                if not origin or not departure:
                    actions.append(
                        _action(
                            "terminal_departure_configuration_required",
                            "Configure the default departure origin and time, or "
                            "record the planned trip.",
                        )
                    )
                else:
                    message = (
                        f"Confirm the terminal destination for the {departure} "
                        f"departure from {origin}."
                    )
                    if common:
                        message = message[:-1] + f"; configured usual destination is {common}."
                    actions.append(
                        _action("terminal_destination_confirmation", message)
                    )

    def public_trip(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "trip_id": row["trip_id"],
            "status": row["status"],
            "origin": row["origin"],
            "destination": row["destination"],
            "departure": row["departure"].isoformat() if row["departure"] else None,
            "eta": row["eta"].isoformat() if row["eta"] else None,
            "eta_source": row["eta_source"],
            "current_location": row["current_location"] or None,
            "location_time": (
                row["location_time"].isoformat() if row["location_time"] else None
            ),
            "route_id": row["route_id"] or None,
            "route_overview": row["route_overview"] or None,
            "operation_profile": row["operation_profile"] or None,
            "progress_fraction": row["progress_fraction"],
        }

    if mode != "ROAD":
        actions = []

    return {
        "route_weather_allowed": bool(watches),
        "route_weather_watches": watches,
        "trip_status": public_trip(trip_status_row),
        "actions_required": _dedupe_actions(actions),
        "expired_watch_trip_ids": expired_ids,
    }, errors


def _public_override(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "record_id": str(row.get("record_id") or ""),
        "item": str(row.get("item") or ""),
        "state": row["_state"],
        "starts_at": row["_start"].isoformat() if row["_start"] else None,
        "expires_at": (
            row["_expiry"].isoformat() if row["_expiry"] else None
        ),
    }


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(OrderedDict((item, None) for item in items if item))


def _strict_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    normalized = _key(value)
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    raise ValueError(f"strict_inputs must be boolean-like, not {value!r}")


def _dataset_available(
    payload: dict[str, Any], values_key: str, object_key: str
) -> bool:
    if values_key in payload:
        value = payload.get(values_key)
        return (
            isinstance(value, list)
            and bool(value)
            and isinstance(value[0], list)
        )
    return object_key in payload and isinstance(payload.get(object_key), list)


def input_health(payload: dict[str, Any]) -> dict[str, Any]:
    """Separate core-authority failures from optional module degradation."""
    strict = _strict_flag(payload.get("strict_inputs"))
    if not strict:
        return {
            "strict": False,
            "status": "not_enforced",
            "issues": [],
            "fatal_issues": [],
            "summary": "Not enforced",
        }

    issues: list[str] = []
    for key in STRICT_INPUT_KEYS:
        if key not in payload:
            issues.append(f"missing {key}")
            continue
        value = payload[key]
        if key == "appointments":
            if not isinstance(value, list):
                issues.append("appointments is not a list")
        elif (
            not isinstance(value, list)
            or not value
            or not isinstance(value[0], list)
        ):
            issues.append(f"{key} is not a readable sheet range")
        else:
            mapping = {
                "tasks_values": TASK_KEYS,
                "control_values": CONTROL_KEYS,
                "routes_values": ROUTE_KEYS,
                "trips_values": TRIP_KEYS,
                "travel_settings_values": SETTING_KEYS,
                "mileage_values": MILEAGE_KEYS,
                "mileage_settings_values": MILEAGE_SETTING_KEYS,
            }[key]
            headers = [_canonical(item, mapping) for item in value[0]]
            missing = sorted(VALUE_RANGE_SCHEMAS[key] - set(headers))
            if missing:
                issues.append(f"{key} is missing columns: {', '.join(missing)}")
            if len(headers) != len(set(headers)):
                issues.append(f"{key} contains duplicate columns")
            if any(not isinstance(row, list) for row in value[1:]):
                issues.append(f"{key} contains a non-array row")
    fatal = [
        issue
        for issue in issues
        if any(core_key in issue for core_key in CORE_INPUT_KEYS)
    ]
    if fatal:
        status = "error"
        summary = "Core missing/invalid: " + "; ".join(fatal)
    elif issues:
        status = "degraded"
        summary = "Optional missing/invalid: " + "; ".join(issues)
    else:
        status = "ok"
        summary = "OK"
    return {
        "strict": True,
        "status": status,
        "issues": issues,
        "fatal_issues": fatal,
        "summary": summary,
    }


def resolve(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "policy_version": POLICY_VERSION,
            "status": "error",
            "errors": ["Input JSON root must be an object."],
        }

    errors: list[str] = []
    warnings: list[str] = []
    try:
        health = input_health(payload)
    except ValueError as exc:
        return {
            "policy_version": POLICY_VERSION,
            "status": "error",
            "errors": [str(exc)],
        }
    if health["fatal_issues"]:
        errors.append(
            "Strict core input check failed: "
            + "; ".join(health["fatal_issues"])
        )
    warnings.extend(
        f"input: {issue}"
        for issue in health["issues"]
        if issue not in health["fatal_issues"]
    )

    brief_slot = str(payload.get("brief_slot") or "").strip().upper()
    if brief_slot not in {"AM", "PM"} and (brief_slot or health["strict"]):
        errors.append("Brief slot must be AM or PM.")

    try:
        now = parse_aware_instant(payload.get("now"), "current instant").astimezone(TZ)
    except ValueError as exc:
        errors.append(str(exc))
        return {
            "policy_version": POLICY_VERSION,
            "status": "error",
            "input_health": health,
            "errors": _dedupe(errors),
        }
    slot_evidence = canonical_slot_evidence(now)
    if slot_evidence["slot_match"] and brief_slot in {"AM", "PM"}:
        expected_slot = (
            "AM" if slot_evidence["logical_scheduled_slot"] == "02:45" else "PM"
        )
        if brief_slot != expected_slot:
            errors.append(
                f"Brief slot {brief_slot} contradicts canonical "
                f"{slot_evidence['logical_scheduled_slot']} {expected_slot} slot."
            )

    tasks = _load_records(payload, "tasks", "tasks_values", TASK_KEYS)
    controls = _load_records(payload, "controls", "control_values", CONTROL_KEYS)
    route_rows = _load_records(payload, "routes", "routes_values", ROUTE_KEYS)
    trip_rows = _load_records(payload, "trips", "trips_values", TRIP_KEYS)
    setting_rows = _load_records(
        payload, "travel_settings", "travel_settings_values", SETTING_KEYS
    )
    mileage_rows = _load_records(
        payload, "mileage", "mileage_values", MILEAGE_KEYS
    )
    mileage_setting_rows = _load_records(
        payload,
        "mileage_settings",
        "mileage_settings_values",
        MILEAGE_SETTING_KEYS,
    )

    overrides, override_errors = prepare_overrides(controls)
    errors.extend(override_errors)
    routes, route_errors = prepare_routes(route_rows)
    settings, setting_errors = prepare_settings(setting_rows)
    travel_warnings = [*route_errors, *setting_errors]

    active_trip = any(_key(row.get("status")) == "active" for row in trip_rows)
    mode, source, selected, mode_error = resolve_mode_at(
        now, overrides, settings, active_trip=active_trip
    )
    context_actions: list[dict[str, str]] = []
    if mode_error:
        if source == "conflict":
            errors.append(mode_error)
        else:
            travel_warnings.append(mode_error)
            context_actions.append(
                _action(
                    "context_configuration_required",
                    "Configure the weekly HOME/ROAD transitions or record an "
                    "explicit mode override.",
                )
            )

    window, window_errors = appointment_window(now)
    warnings.extend(f"appointments: {item}" for item in window_errors)
    appointments_due: list[dict[str, Any]] = []
    appointment_available = (
        "appointments" in payload and isinstance(payload.get("appointments"), list)
    )
    appointment_errors: list[str] = []
    if appointment_available:
        appointments_due, appointment_errors = filter_appointments(
            payload.get("appointments"), window
        )
        warnings.extend(f"appointments: {item}" for item in appointment_errors)
    elif health["strict"]:
        warnings.append("appointments: authority unavailable")

    visible_tasks: list[dict[str, Any]] = []
    next_home_tasks: list[dict[str, Any]] = []
    markdown = ""
    if mode is not None:
        visible_tasks, next_home_tasks, markdown, task_errors = task_output(
            tasks, now, mode, brief_slot
        )
        errors.extend(task_errors)
    else:
        eligible, task_errors = eligible_tasks(tasks, now.date())
        errors.extend(task_errors)
        visible_tasks = [row for row in eligible if row["tier"] == "Persistent"]
        markdown = "\n".join(_render_grouped(visible_tasks))

    travel = {
        "route_weather_allowed": False,
        "route_weather_watches": [],
        "trip_status": None,
        "actions_required": [],
        "expired_watch_trip_ids": [],
    }
    travel_available = (
        _dataset_available(payload, "trips_values", "trips")
        and _dataset_available(
            payload, "travel_settings_values", "travel_settings"
        )
    )
    if mode is not None and travel_available:
        travel, runtime_travel_errors = travel_output(
            trip_rows, routes, settings, now, mode, brief_slot
        )
        travel_warnings.extend(runtime_travel_errors)
    elif health["strict"] and not travel_available:
        travel_warnings.append("travel authority unavailable")
    warnings.extend(f"travel: {item}" for item in travel_warnings)

    mileage = {
        "mileage_summary_allowed": False,
        "mileage_summary_due": False,
        "mileage_summary": None,
        "mileage_summary_markdown": "",
        "actions_required": [],
    }
    mileage_available = (
        _dataset_available(payload, "mileage_values", "mileage")
        and _dataset_available(
            payload, "mileage_settings_values", "mileage_settings"
        )
    )
    mileage, mileage_errors = mileage_output(
        mileage_rows,
        mileage_setting_rows,
        trip_rows,
        settings,
        now,
        mileage_available,
    )
    warnings.extend(f"mileage: {item}" for item in mileage_errors)
    if (
        mileage["mileage_summary_due"]
        and not mileage_available
        and not mileage["actions_required"]
    ):
        mileage["actions_required"] = [
            _action(
                "mileage_pay_sheet_unavailable",
                "Action Required — mileage/pay Sheet unavailable",
            )
        ]

    module_health = {
        "appointments": {
            "status": (
                "degraded"
                if appointment_errors
                else "ok"
                if appointment_available
                else "unavailable"
            ),
            "issues": appointment_errors,
        },
        "travel": {
            "status": (
                "degraded"
                if travel_warnings
                else "ok"
                if travel_available
                else "unavailable"
            ),
            "issues": travel_warnings,
        },
        "mileage": {
            "status": (
                "not_due"
                if not mileage["mileage_summary_due"]
                else "degraded"
                if mileage_errors
                else "ok"
                if mileage_available
                else "unavailable"
            ),
            "issues": mileage_errors,
        },
    }

    errors = _dedupe(errors)
    warnings = _dedupe(warnings)
    actions_required = _dedupe_actions(
        [
            *context_actions,
            *travel["actions_required"],
            *mileage["actions_required"],
        ]
    )
    degraded = bool(warnings) or health["status"] == "degraded"
    status = "error" if errors else "degraded" if degraded else "ok"
    run_status = {"ok": "OK", "degraded": "Degraded", "error": "Error"}[status]
    run_id = f"OPS-{now.date().isoformat()}-{brief_slot or 'UNKNOWN'}"
    run_log_fields = {
        "Run ID": run_id,
        "Scheduled Date (ET)": now.date().isoformat(),
        "Slot": brief_slot or "UNKNOWN",
        "Started (ET)": now.isoformat(),
        "Completed (ET)": "",
        "Phase": "policy_resolved",
        "Policy Version": POLICY_VERSION,
        "Mode": mode or "UNKNOWN",
        "Status": run_status,
        "Input Health": health["summary"],
        "Canonical Clock (ET)": slot_evidence["canonical_clock"],
        "Canonical Slot Match": slot_evidence["slot_match"],
        "Logical Slot": slot_evidence["logical_scheduled_slot"],
        "Effective Scheduled Instant": slot_evidence["scheduled_slot"],
        "Dispatch Delay (s)": slot_evidence["delay_seconds"],
        "DST Adjustment": slot_evidence["dst_adjustment"] or "None",
        "Dispatch State": slot_evidence["state"],
        "External Evidence": "",
        "Mutations": "",
        "Action Count": len(actions_required),
        "Error / Notes": " | ".join([*errors, *warnings]),
    }
    return {
        "policy_version": POLICY_VERSION,
        "status": status,
        "timezone": TZ_NAME,
        "now": now.isoformat(),
        "brief_slot": brief_slot or None,
        "canonical_clock_evidence": slot_evidence,
        "input_health": health,
        "module_health": module_health,
        "run_log_fields": run_log_fields,
        "mode": mode,
        "mode_source": source,
        "weather_allowed": mode == "HOME",
        "home_weather_allowed": mode == "HOME",
        "mowing_season": mowing_season(now),
        "mowing_weather_focus": mode == "HOME" and mowing_season(now),
        "route_weather_allowed": travel["route_weather_allowed"],
        "route_weather_watches": travel["route_weather_watches"],
        "trip_status": travel["trip_status"],
        "actions_required": actions_required,
        "expired_watch_trip_ids": travel["expired_watch_trip_ids"],
        "mileage_summary_allowed": mileage["mileage_summary_allowed"],
        "mileage_summary_due": mileage["mileage_summary_due"],
        "mileage_summary": mileage["mileage_summary"],
        "mileage_summary_markdown": mileage["mileage_summary_markdown"],
        "active_override": _public_override(selected),
        "appointment_window": window,
        "appointments_due": appointments_due,
        "visible_task_ids": [row["task_id"] for row in visible_tasks],
        "next_home_task_ids": [row["task_id"] for row in next_home_tasks],
        "ops_status_markdown": markdown,
        "warnings": warnings,
        "errors": errors,
    }


def next_friday_1500(moment: datetime) -> datetime:
    local = moment.astimezone(TZ)
    days_ahead = (4 - local.weekday()) % 7
    candidate = datetime.combine(
        local.date() + timedelta(days=days_ahead), time(15, 0), TZ
    )
    if candidate <= local:
        candidate += timedelta(days=7)
    return candidate


def home_early(moment: datetime) -> dict[str, Any]:
    local = moment.astimezone(TZ)
    expiry = next_friday_1500(local)
    return {
        "policy_version": POLICY_VERSION,
        "status": "ok",
        "timezone": TZ_NAME,
        "starts_at": local.isoformat(),
        "expires_at": expiry.isoformat(),
        "work_cycle_close_at": local.isoformat(),
        "sheet_fields": {
            "Type": "Mode Override",
            "Item": "Home early",
            "State": "HOME",
            "Starts At (ET)": local.strftime("%-m/%-d/%Y %-H:%M:%S"),
            "Expires At (ET)": expiry.strftime("%-m/%-d/%Y %-H:%M:%S"),
            "Notes": (
                "Force HOME through the next Friday 2:45 PM brief; expiry is "
                "Friday 3:00 PM Eastern and exclusive. Close the current work-"
                "cycle mileage accrual at the confirmed home-arrival time."
            ),
            "Status": "Active",
            "Updated (ET)": local.strftime("%-m/%-d/%Y"),
        },
    }


def _read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _emit(value: dict[str, Any], pretty: bool) -> None:
    json.dump(
        value,
        sys.stdout,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=False,
    )
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser(
        "resolve", help="Resolve brief policy from JSON input"
    )
    resolve_parser.add_argument(
        "--input", default="-", help="JSON file path, or - for stdin"
    )
    resolve_parser.add_argument("--pretty", action="store_true")

    home_parser = subparsers.add_parser(
        "home-early", help="Create deterministic Home early override fields"
    )
    home_parser.add_argument("--now", required=True, help="Current timestamp")
    home_parser.add_argument("--pretty", action="store_true")

    slot_parser = subparsers.add_parser(
        "slot-check", help="Check canonical scheduled-entry eligibility"
    )
    slot_parser.add_argument(
        "--now",
        default=None,
        help=(
            "Offset-aware diagnostic timestamp. Production scheduled runs must "
            "omit this so the runtime captures its own system clock."
        ),
    )
    slot_parser.add_argument("--timezone", default=TZ_NAME)
    slot_parser.add_argument("--slot", action="append", default=None)
    slot_parser.add_argument(
        "--grace-minutes", type=int, default=DEFAULT_SLOT_GRACE_MINUTES
    )
    slot_parser.add_argument(
        "--early-grace-seconds",
        type=int,
        default=DEFAULT_SLOT_EARLY_GRACE_SECONDS,
    )
    slot_parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "resolve":
            output = resolve(_read_json(args.input))
        elif args.command == "home-early":
            now = parse_aware_instant(args.now, "current instant")
            output = home_early(now)
        else:
            slots = (
                tuple(_parse_slot(value) for value in args.slot)
                if args.slot
                else CANONICAL_BRIEF_SLOTS
            )
            if args.now is None:
                evidence = live_slot_evidence(
                    timezone_name=args.timezone,
                    slots=slots,
                    grace_minutes=args.grace_minutes,
                    early_grace_seconds=args.early_grace_seconds,
                )
            else:
                now = parse_aware_instant(args.now, "current instant")
                evidence = {
                    **canonical_slot_evidence(
                        now,
                        timezone_name=args.timezone,
                        slots=slots,
                        grace_minutes=args.grace_minutes,
                        early_grace_seconds=args.early_grace_seconds,
                    ),
                    "clock_source": "explicit_diagnostic_input",
                    "waited_seconds": 0,
                }
            output = {
                "policy_version": POLICY_VERSION,
                "status": "ok" if evidence["entry_allowed"] else "not_due",
                **evidence,
            }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        output = {
            "policy_version": POLICY_VERSION,
            "status": "error",
            "errors": [str(exc)],
        }
    _emit(output, args.pretty)
    if output.get("status") in {"ok", "degraded"}:
        return 0
    if output.get("status") == "not_due":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

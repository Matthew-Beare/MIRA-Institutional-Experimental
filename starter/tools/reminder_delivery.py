#!/usr/bin/env python3
"""Project canonical reminders into visual and optional spoken delivery intents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DETAIL_MODES = {"generic", "title"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _required(value: Any, field: str) -> str:
    result = _text(value)
    if not result:
        raise ValueError(f"{field} must be nonblank")
    return result


def _spoken_phrase(reminder: dict[str, Any], detail_mode: str) -> str:
    title = _required(reminder.get("title"), "reminder.title")
    subject = title if detail_mode == "title" else "You have an appointment"
    triggers = set(reminder.get("triggers", []))
    if "relative" in triggers:
        return f"{subject} in one hour."
    if "morning_of" in triggers:
        return f"{subject} today."
    if "day_before" in triggers:
        return f"{subject} tomorrow."
    return f"{subject}."


def project(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    reminders = payload.get("reminders", [])
    if not isinstance(reminders, list):
        raise ValueError("reminders must be a list")
    capabilities = payload.get("verified_capabilities", [])
    if not isinstance(capabilities, list):
        raise ValueError("verified_capabilities must be a list")
    capability_set = {_text(value) for value in capabilities if _text(value)}
    spoken_enabled = payload.get("spoken_enabled", False)
    if not isinstance(spoken_enabled, bool):
        raise ValueError("spoken_enabled must be boolean")
    detail_mode = _text(payload.get("spoken_detail_mode")) or "generic"
    if detail_mode not in DETAIL_MODES:
        raise ValueError("spoken_detail_mode must be generic or title")

    intents: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for index, reminder in enumerate(reminders):
        if not isinstance(reminder, dict):
            raise ValueError(f"reminders[{index}] must be an object")
        reminder_uuid = _required(reminder.get("reminder_uuid"), f"reminders[{index}].reminder_uuid")
        fire_at = _required(reminder.get("fire_at"), f"reminders[{index}].fire_at")
        title = _required(reminder.get("title"), f"reminders[{index}].title")
        intents.append({
            "reminder_uuid": reminder_uuid,
            "channel": "visual_notification",
            "fire_at": fire_at,
            "title": title,
            "body": "Appointment reminder" if reminder.get("kind") == "appointment" else title,
        })
        if spoken_enabled and reminder.get("kind") == "appointment":
            if "spoken_notification" in capability_set:
                intents.append({
                    "reminder_uuid": reminder_uuid,
                    "channel": "spoken_notification",
                    "fire_at": fire_at,
                    "speech_text": _spoken_phrase(reminder, detail_mode),
                    "detail_mode": detail_mode,
                })
            else:
                warnings.append({
                    "reminder_uuid": reminder_uuid,
                    "status": "degraded",
                    "missing_capability": "spoken_notification",
                    "message": "Spoken reminders are enabled, but this device has not verified spoken-notification delivery. Visual reminders remain active.",
                })
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "degraded" if warnings else "ready",
        "delivery_intents": intents,
        "warnings": warnings,
        "rules": {
            "canonical_reminder_not_duplicated_by_channel": True,
            "spoken_delivery_requires_verified_capability": True,
            "generic_detail_is_privacy_default": True,
            "client_owns_tts_and_audio_routing": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        print(json.dumps(project(json.loads(raw)), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic first-boot life-profile, context-mode, and stock-service router."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 4
ROLE_ORDER = (
    "dependent_minor",
    "working",
    "self_employed",
    "retired",
    "nonworking",
    "parent_guardian",
    "caregiver",
    "household_manager",
    "student",
    "custom",
)
ROLE_ALIASES = {
    "employed": "working",
    "self-employed": "self_employed",
    "self employed": "self_employed",
    "not working": "nonworking",
    "between jobs": "nonworking",
    "unemployed": "nonworking",
    "parent": "parent_guardian",
    "guardian": "parent_guardian",
    "household manager": "household_manager",
    "minor": "dependent_minor",
    "dependent child": "dependent_minor",
}
SERVICE_CATALOG = (
    "briefs",
    "next_actions",
    "email_triage",
    "orders_shipments",
    "receipt_archive",
    "finance",
    "appointments_calendar",
    "appointment_reminders",
    "health_organization",
    "medication_reminders",
    "shopping",
    "recipes_meals",
    "household_admin",
    "household_routines",
    "routines_fitness",
    "education",
    "family_school",
    "travel",
    "work_trips",
    "assets",
    "knowledge",
    "recovery",
    "skill_builder",
)
LEGACY_SERVICE_FIELDS = {
    "briefs_enabled": "briefs",
    "order_lifecycle_enabled": "orders_shipments",
    "recipe_library_enabled": "recipes_meals",
    "household_routines_enabled": "household_routines",
}
ACTIVATION_STATES = {
    "enabled",
    "disabled",
    "unresolved",
    "not_applicable",
    "deferred",
}
ROLE_PRESENTATION = {
    "dependent_minor": ("Dependent", "Family, School & Routines"),
    "working": ("Working", "Work & Personal Operations"),
    "self_employed": ("Self-employed", "Business & Personal Operations"),
    "retired": ("Retired", "Personal Schedule & Wellbeing"),
    "nonworking": ("Not currently working", "Personal Priorities & Next Actions"),
    "parent_guardian": ("Parent or guardian", "Family & Household Coordination"),
    "caregiver": ("Caregiver", "Care & Household Coordination"),
    "household_manager": ("Household manager", "Household Operations"),
    "student": ("Student", "Study & Personal Operations"),
    "custom": ("Custom", "Personal Operations"),
}


def boolish(value: Any, field: str) -> bool | None:
    """Parse explicit boolean-like input; None/blank means unresolved."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    raise ValueError(f"invalid boolean for {field}: {value!r}")


def text(value: Any) -> str:
    return str(value or "").strip()


def _canonical_role(value: Any) -> str:
    role = text(value).lower().replace("/", "_")
    role = ROLE_ALIASES.get(role, role.replace(" ", "_"))
    if role not in ROLE_ORDER:
        raise ValueError(f"unsupported role: {value!r}")
    return role


def classify_roles(payload: dict[str, Any]) -> list[str]:
    """Return composable roles without conflating retirement and non-employment."""
    explicit = payload.get("roles")
    roles: set[str] = set()
    explicit_roles: list[str] | None = None
    if explicit not in (None, ""):
        if not isinstance(explicit, list) or not explicit:
            raise ValueError("roles must be a non-empty list")
        explicit_roles = [_canonical_role(value) for value in explicit]
        if len(explicit_roles) != len(set(explicit_roles)):
            raise ValueError("roles must not contain duplicates")
        if "custom" in explicit_roles and len(explicit_roles) > 1:
            raise ValueError("custom cannot be combined with another role")
        roles.update(explicit_roles)
    else:
        employment_status = payload.get("employment_status")
        if employment_status not in (None, "") and not isinstance(employment_status, str):
            raise ValueError("employment_status must be a string")
        status = text(employment_status).lower()
        phrases = (
            ("self-employed", "self_employed"),
            ("self employed", "self_employed"),
            ("between jobs", "nonworking"),
            ("not working", "nonworking"),
            ("not employed", "nonworking"),
            ("nonworking", "nonworking"),
            ("unemployed", "nonworking"),
            ("retired", "retired"),
            ("caregiv", "caregiver"),
            ("household manager", "household_manager"),
            ("parent", "parent_guardian"),
            ("guardian", "parent_guardian"),
            ("student", "student"),
            ("studying", "student"),
            ("dependent minor", "dependent_minor"),
        )
        for phrase, role in phrases:
            if phrase in status:
                roles.add(role)
        stripped = status
        for phrase in (
            "self-employed", "self employed", "between jobs", "not working",
            "not employed", "nonworking", "unemployed",
        ):
            stripped = stripped.replace(phrase, "")
        if "working" in stripped or "employed" in stripped:
            roles.add("working")

    flag_roles = {
        "is_parent_guardian": "parent_guardian",
        "is_caregiver": "caregiver",
        "is_household_manager": "household_manager",
        "is_dependent_minor": "dependent_minor",
    }
    for field, role in flag_roles.items():
        enabled = boolish(payload.get(field), field)
        if enabled is True:
            roles.add(role)
        elif enabled is False:
            if explicit_roles is not None and role in explicit_roles:
                raise ValueError(f"{field} conflicts with explicit role {role}")
            roles.discard(role)

    if not roles:
        roles.add("custom")
    if len(roles) > 1:
        roles.discard("custom")
    return [role for role in ROLE_ORDER if role in roles]


def primary_role(payload: dict[str, Any], roles: list[str]) -> str:
    if "dependent_minor" in roles:
        return "dependent_minor"
    requested = payload.get("primary_role")
    if requested not in (None, ""):
        selected = _canonical_role(requested)
        if selected not in roles:
            raise ValueError("primary_role must also appear in roles")
        return selected
    if len(roles) > 1:
        raise ValueError("primary_role is required when multiple roles apply")
    return roles[0]


def role_family(job_title: str) -> str:
    role = job_title.lower()
    if any(
        re.search(rf"\b{re.escape(token)}\b", role)
        for token in ("truck", "driver", "courier", "delivery", "over-the-road")
    ):
        return "driver"
    if any(
        re.search(rf"\b{re.escape(token)}\b", role)
        for token in (
            "field", "lineman", "technician", "service tech", "construction",
            "traveling", "travelling", "flight crew", "crew",
        )
    ):
        return "field"
    if any(re.search(rf"\b{token}\b", role) for token in ("student", "campus")):
        return "campus"
    return "generic"


def custom_modes(payload: dict[str, Any]) -> list[str] | None:
    raw = payload.get("context_mode_names")
    if raw in (None, ""):
        return None
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("context_mode_names must be a two-item list")
    if any(not isinstance(value, str) for value in raw):
        raise ValueError("context_mode_names items must be strings")
    values = [text(value).upper() for value in raw]
    if not all(values) or values[0] == values[1]:
        raise ValueError("context_mode_names must contain two distinct nonblank labels")
    if any(
        len(value) > 32 or not re.fullmatch(r"[A-Z0-9][A-Z0-9 _-]*", value)
        for value in values
    ):
        raise ValueError(
            "context_mode_names labels must be 1-32 letters, numbers, spaces, underscores, or hyphens"
        )
    return values


def context_route(payload: dict[str, Any], roles: list[str]) -> dict[str, Any]:
    explicit = boolish(payload.get("works_away_from_home"), "works_away_from_home")
    selected = custom_modes(payload)
    job_title = payload.get("job_title")
    if job_title not in (None, "") and not isinstance(job_title, str):
        raise ValueError("job_title must be a string")
    role = role_family(text(job_title))

    if selected and explicit is False:
        raise ValueError(
            "context_mode_names conflicts with works_away_from_home=false"
        )

    if "dependent_minor" in roles and explicit is not True:
        return {
            "status": "bypassed",
            "primary_modes": [],
            "alternatives": [],
            "reason": "a dependent-minor profile requires explicit approval before any recurring away context",
        }

    if selected:
        return {
            "status": "selected",
            "primary_modes": selected,
            "alternatives": [],
            "reason": "explicit user-selected context labels",
        }

    work_context_roles = {"working", "self_employed", "student"}
    if not work_context_roles.intersection(roles) and explicit is not True:
        return {
            "status": "bypassed",
            "primary_modes": [],
            "alternatives": [],
            "reason": "no working, self-employed, or student role has a confirmed recurring away context",
        }

    if explicit is False:
        return {
            "status": "bypassed",
            "primary_modes": [],
            "alternatives": [],
            "reason": "user explicitly reported no recurring away-work context",
        }

    suggestions = {
        "driver": (["HOME", "ROAD"], [["HOME", "TRUCK"]]),
        "field": (["HOME", "FIELD"], [["HOME", "AWAY"]]),
        "campus": (["HOME", "CAMPUS"], [["HOME", "AWAY"]]),
        "generic": (["HOME", "AWAY"], []),
    }
    primary, alternatives = suggestions[role]

    if explicit is True:
        return {
            "status": "recommended",
            "primary_modes": primary,
            "alternatives": alternatives,
            "reason": "recurring away-work context confirmed; labels still require user confirmation",
        }

    if role in {"driver", "field"}:
        return {
            "status": "needs_confirmation",
            "primary_modes": primary,
            "alternatives": alternatives,
            "reason": "job duties suggest a context split but recurring away-work evidence is unresolved",
        }

    return {
        "status": "unresolved",
        "primary_modes": [],
        "alternatives": [],
        "reason": "insufficient evidence to justify a context split",
    }


def activation(value: Any, field: str) -> str:
    if value is None or value == "":
        return "unresolved"
    if isinstance(value, bool):
        return "enabled" if value else "disabled"
    normalized = text(value).lower().replace("-", "_").replace(" ", "_")
    normalized = {"yes": "enabled", "true": "enabled", "on": "enabled",
                  "no": "disabled", "false": "disabled", "off": "disabled",
                  "n_a": "not_applicable", "na": "not_applicable"}.get(normalized, normalized)
    if normalized not in ACTIVATION_STATES:
        raise ValueError(f"invalid activation state for {field}: {value!r}")
    return normalized


def resolve_services(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = payload.get("service_states")
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("service_states must be an object")
    unknown = sorted(
        (repr(key) for key in raw if not isinstance(key, str) or key not in SERVICE_CATALOG)
    )
    if unknown:
        raise ValueError("unsupported service_states: " + ", ".join(unknown))

    states = {name: activation(raw.get(name), f"service_states.{name}") for name in SERVICE_CATALOG}
    for field, service in LEGACY_SERVICE_FIELDS.items():
        if field not in payload:
            continue
        legacy_state = activation(payload.get(field), field)
        if service in raw and states[service] != legacy_state:
            raise ValueError(f"conflicting activation states for {service}")
        states[service] = legacy_state
    return {
        name: {
            "activation": state,
            "catalogued": True,
            "implementation_status": "requires_capability_verification",
        }
        for name, state in states.items()
    }


def recommended_services(roles: list[str], services: dict[str, dict[str, Any]]) -> list[str]:
    candidates: list[str] = ["briefs", "next_actions", "recovery"]
    by_role = {
        "working": ["work_trips", "email_triage", "finance"],
        "self_employed": ["finance", "email_triage", "work_trips"],
        "retired": [
            "appointments_calendar", "appointment_reminders", "medication_reminders",
            "household_admin", "household_routines", "travel", "knowledge",
        ],
        "nonworking": ["next_actions", "household_admin", "household_routines", "skill_builder"],
        "parent_guardian": [
            "family_school", "household_admin", "household_routines", "appointments_calendar",
            "appointment_reminders", "shopping",
        ],
        "caregiver": [
            "appointments_calendar", "appointment_reminders", "medication_reminders",
            "household_admin", "household_routines", "health_organization",
        ],
        "household_manager": [
            "household_admin", "household_routines", "shopping", "assets", "recipes_meals",
        ],
        "student": ["education", "skill_builder", "appointments_calendar"],
        "dependent_minor": ["education", "family_school", "routines_fitness"],
        "custom": [],
    }
    for role in roles:
        candidates.extend(by_role[role])
    output: list[str] = []
    for service in candidates:
        if service not in output and services[service]["activation"] not in {"disabled", "not_applicable"}:
            output.append(service)
    return output


def resolve(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    roles = classify_roles(payload)
    primary = primary_role(payload, roles)
    profile = primary if len(roles) == 1 or primary == "dependent_minor" else "mixed"
    alias_raw = payload.get("profile_alias")
    if alias_raw is not None and not isinstance(alias_raw, str):
        raise ValueError("profile_alias must be a string")
    alias = text(alias_raw) or None
    context = context_route(payload, roles)
    services = resolve_services(payload)

    appointment_tracking = boolish(payload.get("appointment_tracking"), "appointment_tracking")
    brief_focus: list[str] = []
    role_focus = {
        "working": ["next_actions", "work_context"],
        "self_employed": ["next_actions", "work_context", "finance"],
        "retired": ["household_admin", "family_commitments", "hobbies_projects", "travel"],
        "nonworking": ["next_actions", "household_admin"],
        "parent_guardian": ["family_school", "appointments", "household_admin", "next_actions"],
        "caregiver": ["appointments", "responsibilities", "next_actions"],
        "household_manager": ["household_admin", "shopping", "next_actions"],
        "student": ["deadlines", "study_next_actions"],
        "dependent_minor": ["family_school", "education", "routines"],
        "custom": ["next_actions"],
    }
    for role in roles:
        for focus in role_focus[role]:
            if focus not in brief_focus:
                brief_focus.append(focus)
    if appointment_tracking is True and "appointments" not in brief_focus:
        brief_focus.insert(0, "appointments")

    primary_label, support_template = ROLE_PRESENTATION[primary]

    return {
        "schema_version": SCHEMA_VERSION,
        "profile_model": "composable_roles",
        "life_profile": profile,
        "roles": roles,
        "primary_role": primary,
        "primary_role_label": primary_label,
        "support_template": support_template,
        "profile_alias": alias,
        "profile_alias_storage": "private-mutable-state",
        "context": context,
        "service_catalog": services,
        "recommended_services": recommended_services(roles, services),
        "brief_focus": brief_focus,
        "reminder_templates": {
            "appointments": {
                "activation": "requires_explicit_user_confirmation",
                "day_before_local_time": "18:00",
                "morning_of_local_time": "08:00",
                "relative_minutes_before": 60,
                "delivery": "single_control_cycle_projection_no_per_event_automations",
            },
            "medications": {
                "activation": "requires_explicit_user_confirmation",
                "schedule_source": "explicit_owner_prescription_pharmacy_or_clinician_evidence_only",
                "dose_or_schedule_inference": "prohibited",
                "missed_dose_advice": "prohibited",
                "caregiver_sharing": "disabled_until_explicit_opt_in",
            },
            "household_routines": {
                "activation": "requires_explicit_user_confirmation",
                "state": "canonical_routine_or_task_authority",
                "delivery": "consolidated_brief_or_calendar_projection_no_per_chore_automations",
                "examples": [
                    "laundry_start",
                    "washer_to_dryer",
                    "fold_and_put_away",
                    "dry_cleaning_or_repair_pickup",
                ],
                "ownership_inference": "prohibited",
            },
        },
        "age_or_ability_inference": "prohibited",
        "canonical_timezone_rule": "context-never-overrides-canonical-iana-timezone",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input file; stdin when omitted")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        print(json.dumps(resolve(payload), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

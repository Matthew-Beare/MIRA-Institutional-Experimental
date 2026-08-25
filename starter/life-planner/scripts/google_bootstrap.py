#!/usr/bin/env python3
"""Plan and verify a deterministic personal Google Life Planner bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLUEPRINT = ROOT / "assets" / "personal-google-blueprint.json"
DEFAULT_QUESTIONS = ROOT.parent / "questions.json"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CONFIG_KEYS = {
    "deployment_uuid",
    "deployment_label",
    "owner_uuid",
    "owner_display_name",
    "canonical_timezone",
    "source_repository",
    "source_commit",
    "enabled_modules",
    "google_identity",
    "gmail_enabled",
    "calendar_enabled",
    "scheduled_dispatch_enabled",
    "generated_at",
}
SEED_VERIFICATION_COLUMNS = {
    "Metadata": ["Deployment UUID", "Logical Resource ID", "Schema Version", "Generated At"],
    "Deployment": ["Deployment UUID", "Deployment Label", "Schema Version", "Canonical Timezone", "Source Repository", "Source Commit", "Created At"],
    "Authority Registry": ["Authority UUID", "Logical Resource ID", "Data Class", "Provider", "Resource Type", "Failure Domain", "Owner UUID", "Scope", "Sharing Policy", "Recovery Policy"],
    "Interview Ledger": ["Question ID", "Section ID", "Section Title", "Required", "Prompt", "Applies When"],
    "Integration Registry": ["Module ID", "Capability ID", "Role", "Provider", "Failure Domain"],
    "People": ["Person UUID", "Display Name", "Relationship", "Canonical Timezone", "Created At"],
    "Services": ["Service ID", "Service Name", "Timezone"],
}
TIMESTAMP_VERIFICATION_COLUMNS = {"Generated At", "Created At"}


class BootstrapError(ValueError):
    """Raised for deterministic bootstrap contract violations."""


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise BootstrapError(f"{label} must be a JSON object")
    return value


def _uuid(value: Any, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = uuid.UUID(text)
    except (ValueError, AttributeError) as exc:
        raise BootstrapError(f"{label} must be an RFC 4122 UUID") from exc
    return str(parsed)


def _aware_datetime(value: Any, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BootstrapError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BootstrapError(f"{label} must include an offset")
    return parsed.isoformat()


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise BootstrapError(f"{label} must be boolean")
    return value


def validate_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    if blueprint.get("schema_version") != 1:
        raise BootstrapError("blueprint schema_version must be 1")
    if blueprint.get("provider") != "google-workspace":
        raise BootstrapError("blueprint provider must be google-workspace")
    modules = blueprint.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise BootstrapError("blueprint modules must be a non-empty object")
    required = blueprint.get("required_modules")
    if not isinstance(required, list) or not required:
        raise BootstrapError("blueprint required_modules must be a non-empty array")
    unknown_required = sorted(set(required) - set(modules))
    if unknown_required:
        raise BootstrapError("unknown required modules: " + ", ".join(unknown_required))

    workbook_titles: set[str] = set()
    tab_names: dict[str, str] = {}
    for module_id, module in modules.items():
        if not isinstance(module_id, str) or not module_id:
            raise BootstrapError("module IDs must be non-empty strings")
        if not isinstance(module, dict):
            raise BootstrapError(f"module {module_id} must be an object")
        title = module.get("title")
        if not isinstance(title, str) or "{deployment_label}" not in title:
            raise BootstrapError(f"module {module_id} title must contain {{deployment_label}}")
        if title in workbook_titles:
            raise BootstrapError(f"duplicate workbook title template: {title}")
        workbook_titles.add(title)
        failure_domain = module.get("failure_domain")
        if not isinstance(failure_domain, str) or not failure_domain.strip():
            raise BootstrapError(f"module {module_id} requires a failure_domain")
        folders = module.get("folders", [])
        if not isinstance(folders, list) or any(not isinstance(item, str) or not item for item in folders):
            raise BootstrapError(f"module {module_id} folders must be non-empty strings")
        tabs = module.get("tabs")
        if not isinstance(tabs, dict) or not tabs:
            raise BootstrapError(f"module {module_id} tabs must be a non-empty object")
        for tab_name, headers in tabs.items():
            if not isinstance(tab_name, str) or not tab_name or len(tab_name) > 100:
                raise BootstrapError(f"module {module_id} has an invalid tab name")
            if not isinstance(headers, list) or not headers:
                raise BootstrapError(f"tab {tab_name} must have headers")
            if any(not isinstance(header, str) or not header.strip() for header in headers):
                raise BootstrapError(f"tab {tab_name} has an invalid header")
            if len(headers) != len(set(headers)):
                raise BootstrapError(f"tab {tab_name} has duplicate headers")
            previous = tab_names.get(tab_name)
            if previous is not None and previous != module_id:
                raise BootstrapError(f"tab {tab_name} appears in more than one module")
            tab_names[tab_name] = module_id
    return blueprint


def _questions_rows(question_bank: dict[str, Any]) -> list[dict[str, Any]]:
    sections = question_bank.get("sections")
    if not isinstance(sections, list) or not sections:
        raise BootstrapError("question bank sections must be a non-empty array")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            raise BootstrapError("question-bank sections must be objects")
        section_id = str(section.get("id", "")).strip()
        section_title = str(section.get("title", "")).strip()
        questions = section.get("questions")
        if not section_id or not section_title or not isinstance(questions, list):
            raise BootstrapError("each question-bank section requires id, title, and questions")
        for question in questions:
            if not isinstance(question, dict):
                raise BootstrapError(f"section {section_id} contains a non-object question")
            question_id = str(question.get("id", "")).strip()
            prompt = str(question.get("prompt", "")).strip()
            if not question_id or not prompt or question_id in seen:
                raise BootstrapError(f"invalid or duplicate question ID: {question_id!r}")
            seen.add(question_id)
            required = question.get("required", False)
            if not isinstance(required, bool):
                raise BootstrapError(f"question {question_id} required must be boolean")
            rows.append({
                "Question ID": question_id,
                "Section ID": section_id,
                "Section Title": section_title,
                "Required": required,
                "Prompt": prompt,
                "Applies When": str(question.get("applies_when", "")),
                "Status": "Unresolved",
                "Answer": "",
                "Evidence Type": "",
                "Evidence Reference": "",
                "Answered At": "",
                "Notes": "",
            })
    return rows


def _validate_config(config: dict[str, Any], modules: set[str]) -> dict[str, Any]:
    unknown = sorted(set(config) - CONFIG_KEYS)
    missing = sorted(CONFIG_KEYS - set(config))
    if unknown:
        raise BootstrapError("unsupported config keys: " + ", ".join(unknown))
    if missing:
        raise BootstrapError("missing config keys: " + ", ".join(missing))
    normalized = dict(config)
    normalized["deployment_uuid"] = _uuid(config["deployment_uuid"], "deployment_uuid")
    normalized["owner_uuid"] = _uuid(config["owner_uuid"], "owner_uuid")
    for key in ("deployment_label", "owner_display_name"):
        value = str(config[key] or "").strip()
        if not value or len(value) > 80 or any(char in value for char in "\r\n"):
            raise BootstrapError(f"{key} must be 1-80 characters on one line")
        normalized[key] = value
    timezone = str(config["canonical_timezone"] or "").strip()
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise BootstrapError("canonical_timezone must be a valid IANA timezone") from exc
    normalized["canonical_timezone"] = timezone
    repository = str(config["source_repository"] or "").strip()
    if not REPO_RE.fullmatch(repository):
        raise BootstrapError("source_repository must use owner/name")
    normalized["source_repository"] = repository
    commit = str(config["source_commit"] or "").strip()
    if not SHA_RE.fullmatch(commit):
        raise BootstrapError("source_commit must be a lowercase 40-character SHA")
    normalized["source_commit"] = commit
    enabled = config["enabled_modules"]
    if not isinstance(enabled, list) or any(not isinstance(item, str) for item in enabled):
        raise BootstrapError("enabled_modules must be an array of module IDs")
    unknown_modules = sorted(set(enabled) - modules)
    if unknown_modules:
        raise BootstrapError("unknown enabled modules: " + ", ".join(unknown_modules))
    normalized["enabled_modules"] = list(dict.fromkeys(enabled))
    identity = str(config["google_identity"] or "").strip().lower()
    if not EMAIL_RE.fullmatch(identity):
        raise BootstrapError("google_identity must be an email address")
    normalized["google_identity"] = identity
    for key in ("gmail_enabled", "calendar_enabled", "scheduled_dispatch_enabled"):
        normalized[key] = _bool(config[key], key)
    normalized["generated_at"] = _aware_datetime(config["generated_at"], "generated_at")
    return normalized


def _resource_uuid(deployment_uuid: str, logical_id: str) -> str:
    return str(uuid.uuid5(uuid.UUID(deployment_uuid), logical_id))


def _metadata_headers() -> list[str]:
    return ["Deployment UUID", "Logical Resource ID", "Schema Version", "Generated At"]


def build_plan(
    config: dict[str, Any],
    blueprint: dict[str, Any],
    question_bank: dict[str, Any],
) -> dict[str, Any]:
    blueprint = validate_blueprint(blueprint)
    modules = blueprint["modules"]
    config = _validate_config(config, set(modules))
    selected = list(dict.fromkeys(blueprint["required_modules"] + config["enabled_modules"]))
    workbooks: list[dict[str, Any]] = []
    folders: list[dict[str, Any]] = [{
        "logical_id": "drive-root",
        "name": f"Life Planner - {config['deployment_label']}",
        "parent_ref": "google-drive-root",
    }]
    seen_folders: set[str] = set()
    for module_id in selected:
        module = modules[module_id]
        tabs = [{
            "name": "Metadata",
            "headers": _metadata_headers(),
            "rows": [{
                "Deployment UUID": config["deployment_uuid"],
                "Logical Resource ID": f"workbook:{module_id}",
                "Schema Version": blueprint["schema_version"],
                "Generated At": config["generated_at"],
            }],
        }]
        tabs.extend(
            {"name": name, "headers": headers, "rows": []}
            for name, headers in module["tabs"].items()
        )
        workbooks.append({
            "logical_id": f"workbook:{module_id}",
            "module_id": module_id,
            "title": module["title"].format(deployment_label=config["deployment_label"]),
            "failure_domain": module["failure_domain"],
            "spreadsheet_timezone": config["canonical_timezone"],
            "native_google_sheets_required": True,
            "tabs": tabs,
        })
        for folder_name in module.get("folders", []):
            if folder_name in seen_folders:
                continue
            seen_folders.add(folder_name)
            folders.append({
                "logical_id": "folder:" + re.sub(r"[^a-z0-9]+", "-", folder_name.lower()).strip("-"),
                "name": folder_name,
                "parent_ref": "drive-root",
            })

    by_tab = {
        tab["name"]: tab
        for workbook in workbooks
        for tab in workbook["tabs"]
    }
    by_tab["Deployment"]["rows"] = [{
        "Deployment UUID": config["deployment_uuid"],
        "Deployment Label": config["deployment_label"],
        "Schema Version": blueprint["schema_version"],
        "Canonical Timezone": config["canonical_timezone"],
        "Source Repository": config["source_repository"],
        "Source Commit": config["source_commit"],
        "Created At": config["generated_at"],
        "Status": "Provisioning",
    }]
    by_tab["People"]["rows"] = [{
        "Person UUID": config["owner_uuid"],
        "Display Name": config["owner_display_name"],
        "Relationship": "self",
        "Roles": "unresolved",
        "Canonical Timezone": config["canonical_timezone"],
        "Active": True,
        "Created At": config["generated_at"],
        "Updated At": config["generated_at"],
        "Notes": "",
    }]
    by_tab["Interview Ledger"]["rows"] = _questions_rows(question_bank)
    by_tab["Services"]["rows"] = [
        {
            "Service ID": module_id,
            "Service Name": module_id.replace("-", " ").title(),
            "State": "Enabled" if module_id != "core" else "Required",
            "Cadence": "Unresolved",
            "Slots": "Unresolved",
            "Timezone": config["canonical_timezone"],
            "Notification Mode": "Unresolved",
            "Configuration": "",
            "Last Verified": "",
            "Notes": "",
        }
        for module_id in selected
    ]

    authority_rows = []
    for workbook in workbooks:
        authority_rows.append({
            "Authority UUID": _resource_uuid(config["deployment_uuid"], workbook["logical_id"]),
            "Logical Resource ID": workbook["logical_id"],
            "Data Class": workbook["module_id"],
            "Provider": "google-workspace",
            "Resource Type": "google-spreadsheet",
            "Resource ID": "${" + workbook["logical_id"] + ".provider_id}",
            "Resource URL": "${" + workbook["logical_id"] + ".url}",
            "Failure Domain": workbook["failure_domain"],
            "Owner UUID": config["owner_uuid"],
            "Scope": "personal",
            "Capability Status": "Provisioning",
            "Sharing Policy": "owner-only",
            "Last Verified": "",
            "Recovery Policy": "provider-version-history-plus-explicit-export",
            "Notes": "Resolve placeholders after provider creation and readback.",
        })
    for folder in folders:
        authority_rows.append({
            "Authority UUID": _resource_uuid(config["deployment_uuid"], folder["logical_id"]),
            "Logical Resource ID": folder["logical_id"],
            "Data Class": "retained-evidence" if folder["logical_id"] != "drive-root" else "deployment-root",
            "Provider": "google-workspace",
            "Resource Type": "google-drive-folder",
            "Resource ID": "${" + folder["logical_id"] + ".provider_id}",
            "Resource URL": "${" + folder["logical_id"] + ".url}",
            "Failure Domain": "evidence",
            "Owner UUID": config["owner_uuid"],
            "Scope": "personal",
            "Capability Status": "Provisioning",
            "Sharing Policy": "owner-only",
            "Last Verified": "",
            "Recovery Policy": "provider-trash-and-version-history",
            "Notes": "Resolve placeholders after provider creation and readback.",
        })
    by_tab["Authority Registry"]["rows"] = authority_rows

    integrations = [
        ("source", capability, "required", "github", "source")
        for capability in ("read", "write", "remote-readback", "ci")
    ]
    integrations.extend(
        (workbook["module_id"], capability, "required", "google-sheets", workbook["failure_domain"])
        for workbook in workbooks
        for capability in ("read", "write", "readback")
    )
    integrations.extend(("evidence", capability, "required", "google-drive", "evidence") for capability in ("read", "write", "readback"))
    if config["gmail_enabled"]:
        integrations.append(("email-evidence", "read", "optional", "gmail", "email"))
    if config["calendar_enabled"]:
        integrations.extend(("calendar-projection", capability, "optional", "google-calendar", "calendar") for capability in ("read", "write", "readback"))
    if config["scheduled_dispatch_enabled"]:
        integrations.extend(("control-cycle", capability, "required", "chatgpt-scheduler", "scheduler") for capability in ("definition-readback", "canonical-clock-gate", "observed-firing"))
    by_tab["Integration Registry"]["rows"] = [
        {
            "Module ID": module_id,
            "Capability ID": capability,
            "Role": role,
            "Provider": provider,
            "Resource ID": "",
            "Failure Domain": failure_domain,
            "Health": "Unknown",
            "Circuit State": "Closed",
            "Last Verified": "",
            "Last Error": "",
            "Next Action": "Run bounded provider test and read back.",
        }
        for module_id, capability, role, provider, failure_domain in integrations
    ]

    for workbook in workbooks:
        for tab in workbook["tabs"]:
            tab["verification_columns"] = SEED_VERIFICATION_COLUMNS.get(tab["name"], [])

    plan = {
        "schema_version": 1,
        "provider": "google-workspace",
        "deployment": config,
        "selected_modules": selected,
        "folders": folders,
        "workbooks": workbooks,
        "gmail_test": {
            "enabled": config["gmail_enabled"],
            "identity": config["google_identity"],
            "mutation_allowed": False,
        },
        "calendar_test": {
            "enabled": config["calendar_enabled"],
            "identity": config["google_identity"],
            "marker": f"LIFE-PLANNER-SETUP-{config['deployment_uuid']}",
            "synthetic": True,
        },
        "schedule_test": {
            "enabled": config["scheduled_dispatch_enabled"],
            "canonical_timezone": config["canonical_timezone"],
            "observed_firing_required_for_full_readiness": True,
        },
    }
    encoded = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    plan["plan_sha256"] = hashlib.sha256(encoded).hexdigest()
    return plan


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BootstrapError(f"{label} must be an object")
    return value


def _verify_plan_hash(plan: dict[str, Any]) -> None:
    expected = str(plan.get("plan_sha256", ""))
    payload = dict(plan)
    payload.pop("plan_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual = hashlib.sha256(encoded).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or expected != actual:
        raise BootstrapError("plan_sha256 does not match the bootstrap plan")


def _tab_values(value: Any) -> list[list[Any]] | None:
    if not isinstance(value, list) or not value or any(not isinstance(row, list) for row in value):
        return None
    width = len(value[0])
    if width == 0:
        return None
    return [
        [("" if cell is None else cell) for cell in row[:width]] + [""] * max(0, width - len(row))
        for row in value
    ]


def _timestamp_instant(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        instant = datetime(1899, 12, 30, tzinfo=timezone.utc) + timedelta(seconds=round(float(value) * 86400))
        return instant.isoformat()
    if not isinstance(value, str):
        return None
    text = value.removeprefix("'").strip()
    try:
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if instant.tzinfo is None or instant.utcoffset() is None:
        return None
    return instant.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _seed_cell_matches(header: str, expected: Any, actual: Any) -> bool:
    if header in TIMESTAMP_VERIFICATION_COLUMNS:
        expected_instant = _timestamp_instant(expected)
        actual_instant = _timestamp_instant(actual)
        return expected_instant is not None and expected_instant == actual_instant
    return expected == actual


def verify(plan: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    _verify_plan_hash(plan)
    if plan.get("schema_version") != 1 or plan.get("provider") != "google-workspace":
        raise BootstrapError("unsupported plan")
    deployment = _mapping(plan.get("deployment"), "plan.deployment")
    observed = _mapping(observed, "observed")
    blocks: list[str] = []
    degradations: list[str] = []

    identity = str(deployment.get("google_identity", "")).lower()
    profiles = _mapping(observed.get("profiles", {}), "observed.profiles")
    if str(profiles.get("drive", "")).lower() != identity:
        blocks.append("google-drive-identity-mismatch")
    if plan.get("gmail_test", {}).get("enabled") and str(profiles.get("gmail", "")).lower() != identity:
        degradations.append("gmail-identity-mismatch")
    if plan.get("calendar_test", {}).get("enabled") and str(profiles.get("calendar", "")).lower() != identity:
        degradations.append("calendar-identity-mismatch")

    source = _mapping(observed.get("source", {}), "observed.source")
    if source.get("repository") != deployment.get("source_repository"):
        blocks.append("source-repository-mismatch")
    if source.get("head_commit") != deployment.get("source_commit"):
        blocks.append("source-commit-mismatch")
    for field in ("read_verified", "write_verified", "remote_readback_verified", "ci_green"):
        if source.get(field) is not True:
            blocks.append("source-" + field.replace("_", "-") + "-missing")

    observed_workbooks = _mapping(observed.get("workbooks", {}), "observed.workbooks")
    for workbook in plan.get("workbooks", []):
        logical_id = workbook["logical_id"]
        actual = observed_workbooks.get(logical_id)
        if not isinstance(actual, dict):
            blocks.append(f"missing-{logical_id}")
            continue
        if actual.get("title") != workbook["title"]:
            blocks.append(f"title-mismatch-{logical_id}")
        if actual.get("native_google_sheets") is not True:
            blocks.append(f"not-native-google-sheets-{logical_id}")
        if actual.get("spreadsheet_timezone") != workbook.get("spreadsheet_timezone"):
            blocks.append(f"spreadsheet-timezone-mismatch-{logical_id}")
        if not str(actual.get("provider_id", "")).strip() or not str(actual.get("url", "")).strip():
            blocks.append(f"provider-readback-missing-{logical_id}")
        actual_tabs = _mapping(actual.get("tabs", {}), f"observed.workbooks.{logical_id}.tabs")
        for tab in workbook["tabs"]:
            actual_tab = actual_tabs.get(tab["name"])
            if not isinstance(actual_tab, dict):
                blocks.append(f"missing-tab-{logical_id}-{tab['name']}")
                continue
            values = _tab_values(actual_tab.get("values"))
            if values is None:
                blocks.append(f"cell-readback-missing-{logical_id}-{tab['name']}")
                continue
            if values[0] != tab["headers"]:
                blocks.append(f"header-mismatch-{logical_id}-{tab['name']}")
                continue
            expected_seed = tab.get("rows", [])
            verification_columns = tab.get("verification_columns", [])
            if expected_seed:
                indexes = [tab["headers"].index(column) for column in verification_columns]
                actual_seed = values[1:1 + len(expected_seed)]
                seed_matches = len(actual_seed) == len(expected_seed) and all(
                    _seed_cell_matches(
                        tab["headers"][index],
                        expected_row.get(tab["headers"][index], ""),
                        actual_row[index],
                    )
                    for expected_row, actual_row in zip(expected_seed, actual_seed)
                    for index in indexes
                )
                if not seed_matches:
                    blocks.append(f"seed-mismatch-{logical_id}-{tab['name']}")

    observed_folders = _mapping(observed.get("folders", {}), "observed.folders")
    for folder in plan.get("folders", []):
        actual = observed_folders.get(folder["logical_id"])
        if not isinstance(actual, dict):
            blocks.append(f"missing-{folder['logical_id']}")
            continue
        if actual.get("name") != folder["name"]:
            blocks.append(f"folder-name-mismatch-{folder['logical_id']}")
        if not str(actual.get("provider_id", "")).strip() or not str(actual.get("url", "")).strip():
            blocks.append(f"folder-readback-missing-{folder['logical_id']}")

    if plan.get("gmail_test", {}).get("enabled"):
        gmail = _mapping(observed.get("gmail", {}), "observed.gmail")
        if gmail.get("read_verified") is not True:
            degradations.append("gmail-read-unverified")
    if plan.get("calendar_test", {}).get("enabled"):
        calendar = _mapping(observed.get("calendar", {}), "observed.calendar")
        for field in ("read_verified", "write_verified", "readback_verified"):
            if calendar.get(field) is not True:
                degradations.append("calendar-" + field.replace("_", "-") + "-missing")
        if calendar.get("test_marker") != plan["calendar_test"]["marker"]:
            degradations.append("calendar-test-marker-mismatch")
        if not str(calendar.get("event_id", "")).strip():
            degradations.append("calendar-event-id-missing")
    if plan.get("schedule_test", {}).get("enabled"):
        schedule = _mapping(observed.get("schedule", {}), "observed.schedule")
        if schedule.get("definition_readback") is not True:
            blocks.append("schedule-definition-readback-missing")
        if schedule.get("canonical_clock_gate") is not True:
            blocks.append("schedule-canonical-clock-gate-missing")
        if schedule.get("observed_firing") is not True:
            degradations.append("schedule-awaiting-observed-firing")

    blocks = list(dict.fromkeys(blocks))
    degradations = list(dict.fromkeys(degradations))
    decision = "blocked" if blocks else "degraded" if degradations else "ready"
    scheduled_dispatch_selected = plan.get("schedule_test", {}).get("enabled") is True
    return {
        "decision": decision,
        "deployment_uuid": deployment.get("deployment_uuid"),
        "provider": "google-workspace",
        "blocks": blocks,
        "degradations": degradations,
        "ready_for_manual_use": not blocks,
        "scheduled_dispatch_selected": scheduled_dispatch_selected,
        "ready_for_scheduled_use": scheduled_dispatch_selected and not blocks and not degradations,
    }


def _write_json(value: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(text, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Wrote {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("blueprint-check")
    check.add_argument("--blueprint", type=Path, default=DEFAULT_BLUEPRINT)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--config", type=Path, required=True)
    plan.add_argument("--blueprint", type=Path, default=DEFAULT_BLUEPRINT)
    plan.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    plan.add_argument("--output", type=Path)
    verification = subparsers.add_parser("verify")
    verification.add_argument("--plan", type=Path, required=True)
    verification.add_argument("--observed", type=Path, required=True)
    verification.add_argument("--output", type=Path)
    verification.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "blueprint-check":
            validate_blueprint(_load_json(args.blueprint, "blueprint"))
            print("Personal Google blueprint is valid.")
            return 0
        if args.command == "plan":
            result = build_plan(
                _load_json(args.config, "config"),
                _load_json(args.blueprint, "blueprint"),
                _load_json(args.questions, "question bank"),
            )
            _write_json(result, args.output)
            return 0
        result = verify(_load_json(args.plan, "plan"), _load_json(args.observed, "observed"))
        _write_json(result, args.output)
        return 3 if args.strict and result["decision"] != "ready" else 0
    except BootstrapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

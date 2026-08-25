#!/usr/bin/env python3
"""Validate coherent Personal Ops Planner public-release, starter, and reference contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from policy_fingerprint import compute

REQUIRED = (
    ".gitignore", "LICENSE", "README.md", ".github/workflows/ci.yml",
    "project/INSTRUCTIONS.md.tmpl", "project/POLICY_FINGERPRINT.txt",
    "policy/ops-brief-policy.yaml",
    "docs/automation-contracts.md", "docs/automation-design.md",
    "docs/data-platform-grafana.md", "docs/feature-audit-2026-08-22.md",
    "docs/feature-ledger-2026-08-24.md", "docs/feature-catalog.json",
    "docs/feature-catalog.md", "docs/beta-hardening-audit-2026-08-24.md",
    "docs/platform-portability-audit-2026-08-25.md",
    "docs/household-financial-reconciliation.md", "docs/lyfeos-data-model.md",
    "docs/asset-evidence-schema.md",
    "docs/code-inventory.json",
    "starter/README.md", "starter/START_HERE.md", "starter/LIFE_INTERVIEW.md",
    "starter/MODULE_CATALOG.md", "starter/DEPENDENCIES.md", "starter/VERSIONING.md",
    "starter/PERSONAL_FORK_LIFECYCLE.md", "starter/CAPABILITY_DISCOVERY.md",
    "starter/PLATFORM_PORTABILITY.md", "starter/ENTERPRISE_PILOT.md",
    "starter/STATE_AUTHORITY_MODEL.md", "starter/INTERVIEW_LEDGER.md",
    "starter/GIT_STATE_MODEL.md", "starter/SHARED_FEATURE_WORKFLOW.md",
    "starter/config.example.json", "starter/questions.json", "starter/INSTRUCTIONS.md.tmpl",
    "starter/install-flow.json", "starter/platform-capabilities.json",
    "starter/tools/provider_capability_router.py", "starter/tests/test_platform_portability.py",
    "starter/features/meal-planning/feature.json", "starter/features/meal-planning/FEATURE.md",
    "starter/features/appointment-reconciliation/feature.json", "starter/features/appointment-reconciliation/FEATURE.md",
    "skill/ops-brief-policy/SKILL.md",
    "skill/ops-brief-policy/agents/openai.yaml",
    "skill/ops-brief-policy/assets/icon.svg",
    "skill/ops-brief-policy/references/brief-run.md",
    "skill/ops-brief-policy/references/state-maintenance.md",
    "skill/ops-brief-policy/references/module-circuit-breaker-report.md",
    "skill/ops-brief-policy/references/receipt-ingestion.md",
    "skill/ops-brief-policy/references/receipt-classification-fitment.md",
    "skill/ops-brief-policy/references/receipt-photo-intake.md",
    "skill/ops-brief-policy/references/email-reconciliation.md",
    "skill/ops-brief-policy/references/asset-acquisition.md",
    "skill/ops-brief-policy/references/knowledge-manual-ingestion.md",
    "skill/ops-brief-policy/references/life-planning-accountability.md",
    "skill/ops-brief-policy/references/calendar-projection.md",
    "skill/ops-brief-policy/references/household-reimbursement.md",
    "skill/ops-brief-policy/references/payment-reconciliation.md",
    "skill/ops-brief-policy/references/vendor-contact.md",
    "skill/ops-brief-policy/references/chat-portability.md",
    "skill/ops-brief-policy/scripts/ops_policy.py",
    "skill/ops-brief-policy/scripts/inventory_reconciliation.py",
    "skill/ops-brief-policy/scripts/asset_evidence.py",
    "skill/ops-brief-policy/scripts/reminder_policy.py",
    "scripts/import_run_sheet.py", "scripts/audit_public_source.py",
    "scripts/audit_starter_privacy.py", "scripts/feature_catalog.py",
    "privacy/starter-blocklist.txt",
)

MAX_PROJECT_INSTRUCTIONS_CHARS = 3_000
MAX_START_HERE_CHARS = 12_000


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def all_terms(value: str, *terms: str) -> bool:
    lower = value.lower()
    return all(term.lower() in lower for term in terms)


def any_term(value: str, *terms: str) -> bool:
    lower = value.lower()
    return any(term.lower() in lower for term in terms)


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for relative in REQUIRED:
        require((root / relative).is_file(), f"missing required file: {relative}", errors)
    if errors:
        return errors

    def text(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    def load_json(path: str):
        try:
            return json.loads(text(path))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path}: {exc}")
            return {}

    readme = text("README.md")
    gitignore = text(".gitignore")
    license_text = text("LICENSE")
    ci = text(".github/workflows/ci.yml")
    project = text("project/INSTRUCTIONS.md.tmpl")

    skill = text("skill/ops-brief-policy/SKILL.md")
    agent_metadata = text("skill/ops-brief-policy/agents/openai.yaml")
    brief = text("skill/ops-brief-policy/references/brief-run.md")
    maintenance = text("skill/ops-brief-policy/references/state-maintenance.md")
    breaker = text("skill/ops-brief-policy/references/module-circuit-breaker-report.md")
    runtime = text("skill/ops-brief-policy/scripts/ops_policy.py")
    inventory_runtime = text("skill/ops-brief-policy/scripts/inventory_reconciliation.py")
    evidence_runtime = text("skill/ops-brief-policy/scripts/asset_evidence.py")
    reminder_runtime = text("skill/ops-brief-policy/scripts/reminder_policy.py")
    receipt = text("skill/ops-brief-policy/references/receipt-ingestion.md")
    fitment = text("skill/ops-brief-policy/references/receipt-classification-fitment.md")
    photo = text("skill/ops-brief-policy/references/receipt-photo-intake.md")
    email = text("skill/ops-brief-policy/references/email-reconciliation.md")
    asset = text("skill/ops-brief-policy/references/asset-acquisition.md")
    manual = text("skill/ops-brief-policy/references/knowledge-manual-ingestion.md")
    life = text("skill/ops-brief-policy/references/life-planning-accountability.md")
    calendar = text("skill/ops-brief-policy/references/calendar-projection.md")
    reimbursement = text("skill/ops-brief-policy/references/household-reimbursement.md")
    payment = text("skill/ops-brief-policy/references/payment-reconciliation.md")
    contact = text("skill/ops-brief-policy/references/vendor-contact.md")
    chat = text("skill/ops-brief-policy/references/chat-portability.md")
    cycle = text("skill/ops-brief-policy/references/consolidated-cycle.md")
    jobs = text("skill/ops-brief-policy/references/qualified-job-watch.md")

    automation = text("docs/automation-contracts.md")
    automation_design = text("docs/automation-design.md")
    data_platform = text("docs/data-platform-grafana.md")
    historical = text("docs/feature-audit-2026-08-22.md")
    feature_ledger = text("docs/feature-ledger-2026-08-24.md")
    feature_catalog = load_json("docs/feature-catalog.json")
    beta_audit = text("docs/beta-hardening-audit-2026-08-24.md")
    portability_audit = text("docs/platform-portability-audit-2026-08-25.md")
    household = text("docs/household-financial-reconciliation.md")
    asset_schema = text("docs/asset-evidence-schema.md")
    compatibility = text("policy/ops-brief-policy.yaml")

    start = text("starter/START_HERE.md")
    interview = text("starter/LIFE_INTERVIEW.md")
    catalog = text("starter/MODULE_CATALOG.md")
    deps = text("starter/DEPENDENCIES.md")
    starter_readme = text("starter/README.md")
    versioning = text("starter/VERSIONING.md")
    lifecycle = text("starter/PERSONAL_FORK_LIFECYCLE.md")
    discovery = text("starter/CAPABILITY_DISCOVERY.md")
    portability = text("starter/PLATFORM_PORTABILITY.md")
    enterprise = text("starter/ENTERPRISE_PILOT.md")
    capability_router = text("starter/tools/provider_capability_router.py")
    platform_manifest = load_json("starter/platform-capabilities.json")
    install_flow = load_json("starter/install-flow.json")
    state_model = text("starter/STATE_AUTHORITY_MODEL.md")
    interview_ledger = text("starter/INTERVIEW_LEDGER.md")
    git_state_redirect = text("starter/GIT_STATE_MODEL.md")
    shared = text("starter/SHARED_FEATURE_WORKFLOW.md")
    generic = text("starter/INSTRUCTIONS.md.tmpl")
    meal_feature = text("starter/features/meal-planning/FEATURE.md")
    appointment_feature = text("starter/features/appointment-reconciliation/FEATURE.md")
    importer = text("scripts/import_run_sheet.py")
    public_audit = text("scripts/audit_public_source.py")

    # Stable reference bootstrap and content-sensitive policy fingerprint.
    require(len(project) <= MAX_PROJECT_INSTRUCTIONS_CHARS, f"project contract exceeds {MAX_PROJECT_INSTRUCTIONS_CHARS} characters: {len(project)}", errors)
    for term in (
        "BOOTSTRAP_CONTRACT_VERSION: 4", "project/POLICY_FINGERPRINT.txt",
        "sole durable source", "LyfeOS Control Cycle",
        "BYHOUR=2,14;BYMINUTE=45;BYSECOND=0", "PM qualified-job watch",
        "standalone", "without `--now`", "deterministic Run ID",
        "Paid terminal miles are symmetric A↔B", "immutable UUID",
        "Do you want me to send this email?",
    ):
        require(term in project, f"project contract lacks: {term}", errors)
    fingerprint = text("project/POLICY_FINGERPRINT.txt").strip()
    require(bool(re.fullmatch(r"[0-9a-f]{64}", fingerprint)), "Git-side policy fingerprint is invalid", errors)
    if re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        expected = compute(root / "skill/ops-brief-policy")
        require(fingerprint == expected, f"policy fingerprint mismatch: expected {expected}", errors)
    require(
        all_terms(
            agent_metadata,
            'display_name: "Ops Brief Policy"',
            'short_description: "Reconciled briefs, orders, travel, and mileage"',
            'icon_small: "./assets/icon.svg"',
            'icon_large: "./assets/icon.svg"',
            'default_prompt: "Use $ops-brief-policy',
            "allow_implicit_invocation: true",
        ),
        "skill agent metadata is incomplete or noncanonical",
        errors,
    )
    require("products:" not in agent_metadata, "skill agent metadata contains unsupported products policy", errors)
    require(all_terms(inventory_runtime, "receipt_line_intents", "entity_uuid", "relationship_uuid", "assigned_to", "include_in_inventory"), "inventory reconciler lacks identity/relationship contract", errors)
    require(all_terms(asset, "Asset Relationships", "exact receipt line", "assigned_to", "installed_on", "inventory_reconciliation.py"), "asset policy lacks executable receipt-line relationship contract", errors)
    require(all_terms(evidence_runtime, "identifier_intents", "evidence_intents", "knowledge_intents", "specification_intents", "query_graph", "upc_a", "serial_number", "source_locator", "authoritative"), "asset evidence reconciler lacks identifier/knowledge/specification/query contract", errors)
    require(all_terms(reminder_runtime, "day_before", "morning_of", "relative_minutes_before", "medication", "schedule_confirmed", "caregiver_sharing", "no_per_event_automations"), "reminder planner lacks appointment/medication safety contract", errors)
    feature_rows = [row for category in feature_catalog.get("categories", []) if isinstance(category, dict) for row in category.get("features", []) if isinstance(row, dict)] if isinstance(feature_catalog, dict) else []
    require(len(feature_rows) >= 70, "machine-readable feature catalog is incomplete", errors)
    require(all_terms(feature_ledger, "bidirectional receipt/order", "namespaced upc/gtin", "medication reminders", "personal schedule & wellbeing", "hierarchical machine-readable feature catalog"), "forensic feature ledger lacks current integrated requirements", errors)
    require(all_terms(asset_schema, "Evidence Index", "Asset Identifiers", "Knowledge Relationships", "Technical Specifications", "Asset Lookup Queue", "Asset Browser", "leading zeroes", "owned_by", "page/section"), "asset/evidence provider schema is incomplete", errors)

    # Public upstream and starter source/state boundary.
    require(all_terms(readme, "intentionally public", "starter/start_here.md", "google sheets", "google drive", "mutable operational state", "public-source audit"), "README lacks public-upstream/external-state boundary", errors)
    require(all_terms(starter_readme, "google sheets", "google drive", "interview ledger", "git", "mutable personal records"), "starter README lacks source/state/interview boundary", errors)
    require(all_terms(state_model, "google sheets", "google drive", "authority registry", "one canonical authority", "sharing state and sharing a feature are different operations"), "starter state authority model is incomplete", errors)
    require(all_terms(git_state_redirect, "git is not the default mutable personal-state database", "state_authority_model.md", "google sheets", "google drive"), "legacy Git-state document does not redirect to current authority model", errors)
    require(all_terms(versioning, "routine mutable state changes do not create git commits", "google sheets", "google drive", "feature/*"), "starter versioning conflates source and mutable state", errors)
    require(all_terms(lifecycle, "routine state changes happen in the canonical mutable authority, not git", "authority registry", "interview ledger", "google sheets"), "personal lifecycle lacks external-state contract", errors)
    require(all_terms(shared, "structured state authority", "drive/evidence authority", "synthetic fixtures", "publication authority"), "shared feature workflow blurs portable source and live state", errors)
    require(all_terms(discovery, "google sheets", "drive", "connected apps/tools/connectors", "available plugins/apps", "one canonical structured authority per mutable data class"), "capability discovery lacks external-authority model", errors)
    require(all_terms(deps, "google sheets", "google drive", "structured mutable state authority", "provider contract", "canonical-clock"), "starter dependencies lack authority/scheduler contract", errors)
    require(all_terms(generic, "structured mutable state", "interview ledger", "google sheets", "google drive", "iana timezone"), "starter template lacks external-state/interview/canonical-time contract", errors)
    require("{{REPOSITORY_VISIBILITY}}" in generic, "starter template lacks REPOSITORY_VISIBILITY", errors)

    # Provider-neutral personal, enterprise, and regulated deployment contracts.
    capability_ids = set(platform_manifest.get("capability_ids", [])) if isinstance(platform_manifest, dict) else set()
    require(platform_manifest.get("schema_version") == 1, "platform capability manifest schema is invalid", errors)
    require(platform_manifest.get("claim_policy", {}).get("organization_approval_evidence_required_for_regulated_sensitive_data") is True, "platform manifest permits unsubstantiated regulated-data approval", errors)
    require({
        "source_read", "source_write", "source_remote_readback", "managed_release_read",
        "structured_state_read", "structured_state_write", "structured_state_readback",
        "evidence_read", "evidence_write", "evidence_readback", "email_read",
        "calendar_read", "calendar_write", "calendar_readback", "scheduled_dispatch",
        "canonical_clock_gate", "observed_scheduled_firing",
    } <= capability_ids, "platform capability manifest lacks required read/write/readback gates", errors)
    runtime_ids = {row.get("id") for row in platform_manifest.get("ai_runtimes", []) if isinstance(row, dict)}
    storage_ids = {row.get("id") for row in platform_manifest.get("storage_backends", []) if isinstance(row, dict)}
    source_ids = {row.get("id") for row in platform_manifest.get("source_backends", []) if isinstance(row, dict)}
    require({"chatgpt", "claude", "microsoft-copilot-or-approved-organizational-ai", "google-gemini"} <= runtime_ids, "platform manifest lacks supported AI runtime candidates", errors)
    require({"google-workspace", "microsoft-365", "apple-icloud", "portable-files"} <= storage_ids, "platform manifest lacks storage portability candidates", errors)
    require({"github-personal", "github-enterprise", "gitlab", "azure-repos", "managed-central-source"} <= source_ids, "platform manifest lacks source-control portability candidates", errors)
    require(all_terms(portability, "no feature parity", "ChatGPT", "Claude", "Microsoft 365", "OneDrive", "SharePoint", "Apple/iCloud", "managed central source", "provider readback"), "platform portability contract is incomplete", errors)
    require(all_terms(enterprise, "Do not create a personal cloud account", "regulated-sensitive", "synthetic or public data", "read → bounded write → readback", "VA-specific deployment gate", "observed firing"), "enterprise/VA pilot contract is incomplete", errors)
    require(all_terms(capability_router, "organization_approved_for_data", "organization_approval_reference", "unsupported capabilities", "structured_state_readback", "calendar_readback", "observed_scheduled_firing", "managed-source-write-readback-unavailable", 'decision = "blocked"'), "provider capability router lacks fail-closed readiness gates", errors)
    require(isinstance(install_flow, dict) and install_flow.get("version") == 2, "browser install-flow schema is stale", errors)
    require(set(install_flow.get("deployment_lanes", {})) == {"personal_browser", "enterprise_managed", "portable_manual"}, "browser install flow lacks exact deployment lanes", errors)
    require(all(field in install_flow.get("assistant_readback_fields", []) for field in ("deployment_lane", "ai_runtime", "data_classification", "source_mode", "organization_approval", "organization_approval_reference")), "browser install flow lacks provider/approval readback", errors)

    config = load_json("starter/config.example.json")
    require(isinstance(config, dict) and all(isinstance(k, str) and k.isupper() for k in config), "starter config keys must be uppercase", errors)
    require(config.get("TIMEZONE") == "REQUIRED_IANA_TIMEZONE", "starter config ships a production timezone", errors)
    require(config.get("STATE_STORE") == "GOOGLE_SHEETS_DEFAULT_OR_SUPPORTED_DATABASE", "starter config does not default mutable state to Sheets/supported DB", errors)
    require(config.get("AUTHORITY_REGISTRY") == "REQUIRED_IN_STRUCTURED_STATE_STORE", "starter config lacks Authority Registry", errors)
    require(config.get("INTERVIEW_LEDGER") == "REQUIRED_IN_STRUCTURED_STATE_STORE", "starter config lacks Interview Ledger", errors)
    require(config.get("CANONICAL_CLOCK_POLICY") == "IANA_TIMEZONE_CONVERSION_NEVER_DEVICE_TIME_OR_STATIC_OFFSET", "starter config lacks canonical-clock policy", errors)
    require(config.get("DEPLOYMENT_LANE") == "PERSONAL_BROWSER_ENTERPRISE_MANAGED_OR_PORTABLE_MANUAL", "starter config lacks deployment-lane selection", errors)
    require(config.get("AI_RUNTIME") == "OBSERVED_RUNTIME_AND_DEPLOYMENT", "starter config lacks observed AI runtime", errors)
    require(config.get("SOURCE_CONTROL_MODE") == "USER_GIT_ORGANIZATION_GIT_MANAGED_CENTRAL_OR_NONE", "starter config lacks portable source modes", errors)
    require(config.get("GITHUB_REPO") == "SELECT_PERSONAL_ORGANIZATION_GIT_OR_MANAGED_SOURCE", "starter config hardcodes personal GitHub", errors)
    require("PRIVATE_GIT_REPOSITORY/state" not in json.dumps(config), "starter config still uses Git as mutable state store", errors)
    require("02:45" not in json.dumps(config) and "14:45" not in json.dumps(config), "starter config ships reference schedule times", errors)
    template_tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", generic))
    require(template_tokens <= set(config), "starter config does not cover template tokens", errors)

    # Durable fail-forward interview coverage.
    require(all_terms(interview_ledger, "unresolved", "asked", "answered", "resolved from evidence", "not applicable", "deferred"), "Interview Ledger lacks status model", errors)
    require(all_terms(interview_ledger, "answer the user's immediate request normally", "end with", "question-bank upgrades", "every question"), "Interview Ledger lacks fail-forward/upgrade behavior", errors)
    require("Preferences and consent are not silently inferred" in interview_ledger, "Interview Ledger permits inferred consent", errors)

    questions = load_json("starter/questions.json")
    rows = [q for section in questions.get("sections", []) if isinstance(section, dict) for q in section.get("questions", []) if isinstance(q, dict)]
    ids = [q.get("id") for q in rows]
    require(isinstance(questions, dict) and int(questions.get("version", 0)) >= 6, "starter questionnaire version is stale", errors)
    require(len(rows) >= 100 and len(ids) == len(set(ids)), "starter questionnaire lacks depth or has duplicate IDs", errors)
    for qid in (
        "works_away_from_home", "accountability_domains", "routine_progression",
        "education_active", "study_home_away", "study_next_action_rule",
        "scheduler_timezone_integrity", "repository_visibility", "public_source_policy",
        "employment_status", "retired_support", "hiking_outdoors", "vacation_planning",
        "meal_planning_help", "existing_meal_plans", "fitness_wearable",
        "medical_event_tracking", "appointment_email_auto_update", "git_state_commit_policy",
        "canonical_clock_guard", "authority_registry", "interview_ledger",
        "interview_resume_policy", "shared_authority", "appointment_provider_type_research",
        "appointment_reminder_day_before", "appointment_reminder_morning_of",
        "appointment_reminder_relative", "medication_reminders",
        "medication_schedule_evidence", "caregiver_reminder_sharing",
        "asset_identifier_capture", "manual_discovery", "technical_specifications",
        "deployment_lane", "ai_runtime", "data_classification", "organization_approval",
        "source_control_mode", "provider_capability_readback",
    ):
        require(qid in ids, f"starter questionnaire lacks field: {qid}", errors)

    require(len(start) < MAX_START_HERE_CHARS, f"START_HERE exceeds {MAX_START_HERE_CHARS} characters: {len(start)}", errors)
    for term in (
        "non-technical user", "Minimum Useful Setup", "Start now by asking only the four kickoff questions",
        "mark HOME/ROAD bypassed", "Driving/trucking", "active shopping list",
        "partial cancellation", "true replacement", "Calendar Projection", "immutable UUID",
        "Awaiting Settlement", "Module Circuit Breaker Report", "Do you want me to send this email?",
        "old chats are deleted", "automatically update validation, commit, and push",
        "Interview Ledger", "Google Sheets", "Google Drive", "Do you want help with meal planning?",
        "ZoneInfo", "provider type", "morning-of", "one hour before",
    ):
        require(term.lower() in start.lower(), f"START_HERE lacks behavior: {term}", errors)
    require(all_terms(interview, "Do you regularly work away from home", "minimum viable version", "home versus away/on the road", "Exercise / fitness", "School / study", "what to do next", "conversation detour"), "whole-life interview incomplete", errors)

    # Portable feature state boundaries.
    meal_manifest = load_json("starter/features/meal-planning/feature.json")
    appointment_manifest = load_json("starter/features/appointment-reconciliation/feature.json")
    for name, manifest in (("meal planning", meal_manifest), ("appointment reconciliation", appointment_manifest)):
        boundary = manifest.get("data_boundary", {}) if isinstance(manifest, dict) else {}
        require(boundary.get("source_contains_personal_data") is False, f"{name} portable source contains personal data", errors)
        require(boundary.get("runtime_state") == "external-authority", f"{name} does not declare external authority runtime state", errors)
    require(all_terms(meal_feature, "google sheets", "drive", "do you want help with meal planning?", "shopping intent is not purchase history", "readback"), "meal planning feature lacks external-state/import contract", errors)
    require(all_terms(appointment_feature, "official clinic/provider pages", "cardiology", "morning-of", "60 minutes before", "iana timezone", "read the calendar event back", "canonical state back"), "appointment feature lacks provider/reminder/readback contract", errors)

    # Public release gates.
    require("MIT License" in license_text and "Permission is hereby granted" in license_text, "public source lacks MIT reuse permission", errors)
    for pattern in (".env", "config.local.json", "*.sqlite"):
        require(pattern in gitignore, f".gitignore lacks safety pattern: {pattern}", errors)
    require(all_terms(public_audit, "audit_history", "scan_exempt_paths", "card_candidate", "blocked_filenames"), "public-source auditor lacks history/credential/card gates", errors)
    require("fetch-depth: 0" in ci and "audit_public_source.py . --history" in ci, "CI does not audit reachable Git history", errors)
    for term in (
        "audit_starter_privacy.py starter", "validate_repo.py .",
        "unittest discover -s tests", "unittest discover -s skill/ops-brief-policy/scripts",
        "validate_feature_manifest.py", "unittest discover -s starter/tests",
    ):
        require(term in ci, f"CI release gate lacks: {term}", errors)

    # Scheduler evidence chain plus runtime IANA clock.
    scheduler_surfaces = {
        "skill": skill, "maintenance": maintenance, "automation docs": automation,
        "starter dependencies": deps, "starter first boot": start,
        "starter interview": interview, "starter template": generic,
    }
    for label, surface in scheduler_surfaces.items():
        require(all_terms(surface, "notification", "duplicate", "canonical"), f"{label} lacks scheduler readback evidence", errors)
        require(any_term(surface, "actual firing", "actual scheduled firing", "observed firing", "observed execution"), f"{label} lacks observed scheduler execution evidence", errors)
        require(any_term(surface, "provider contract", "provider/tool contract"), f"{label} does not condition provider metadata on documented semantics", errors)
        require("iana" in surface.lower(), f"{label} lacks IANA canonical-time semantics", errors)
    require(all_terms(runtime, "ZoneInfo", "canonical_slot_evidence", "live_slot_evidence", "runtime_system_clock", "America/New_York", "slot-check"), "runtime lacks owned-clock canonical IANA slot guard", errors)
    require(all_terms(brief, "slot-check", "without `--now`", "runtime_system_clock", "canonical runtime clock gate", "12:45:00-06:00", "Before Gmail", "deterministic Run ID"), "brief run does not enforce owned-clock slot entry and fresh output identity", errors)
    require(all_terms(maintenance, "12:45-06:00", "14:45-04:00", "iana", "static utc offset"), "state maintenance lacks travel/DST canonical-clock proof", errors)
    require("default_timezone" in skill and "default_timezone" in automation and "default_timezone" in deps, "scheduler policy does not neutralize ambiguous default_timezone metadata", errors)
    require(all_terms(skill, "first external", "`Running`", "Run Log"), "skill does not require early Run Log entry", errors)
    require(all_terms(skill, "standalone", "runtime_system_clock", "without `--now`", "Never quote", "OPS-YYYY-MM-DD"), "skill lacks stale-delivery and model-clock containment", errors)
    require(all_terms(brief, "`Running`", "Run Log"), "brief workflow does not enter Run Log before downstream work", errors)
    require(all_terms(breaker, "subsequent actual run/Run Log timestamp"), "failure policy cannot prove scheduler recovery", errors)

    # Reference deployment invariants.
    require(all_terms(skill, "Keep mutable operational state in canonical Sheets", "retained files/evidence in canonical Drive"), "reference skill lost Sheets/Drive state authority", errors)
    require(all_terms(skill, "paid terminal mileage", "symmetric", "explicit", "exception"), "skill lacks symmetric paid-mile policy", errors)
    require(all_terms(maintenance, "same paid-mile value", "both", "unless"), "state maintenance lacks symmetric paid-mile upsert", errors)
    require(all_terms(brief, "symmetric", "terminal pair"), "brief workflow lacks pair-symmetric paid-mile semantics", errors)
    require(all_terms(runtime, '"paidmilesab": "paid_miles_ab"', '"paidmilesba": "paid_miles_ba"'), "runtime lacks both paid-mile route columns", errors)
    require("terminal_paid_miles_symmetric_by_pair: true" in compatibility and "terminal_paid_miles_directional: false" in compatibility, "legacy compatibility snapshot contradicts symmetric paid miles", errors)
    require(all_terms(data_platform, "symmetric", "terminal") and "never mirrors automatically" not in data_platform.lower(), "future data model contradicts current pair-mile policy", errors)

    require(all_terms(skill, "Retry is not mandatory", "Module Circuit Breaker Report", "never create hidden retry jobs"), "skill lacks bounded failure policy", errors)
    require(all_terms(breaker, "same external operation fails twice", "Stop writes for the affected module", "Continue unrelated modules", "never blind-rerun"), "module circuit-breaker policy is incomplete", errors)
    require(all_terms(skill, "Exactly one active **standalone** `LyfeOS Control Cycle`", "No separate active Ops/lifecycle/job-watch"), "skill lacks single-dispatcher invariant", errors)
    require(all_terms(cycle, "one newly generated user-facing Ops Brief", "PM qualified-job watch", "module isolation", "Job Watch"), "consolidated control-cycle contract is incomplete", errors)
    require(all_terms(jobs, "Job Watch Settings", "private deployment state", "max_required_relevant_years", "preferred qualification", "Never apply, reply, contact anyone, send email"), "qualified-job contract is incomplete", errors)

    # Purchase, evidence, identity, finance, and communication contracts.
    require(all_terms(receipt, "active shopping list", "remove the fulfilled shopping row", "explicit owner statement", "separate reconciliation task", "cancellation with no supported replacement"), "receipt/shopping contract incomplete", errors)
    require(all_terms(fitment, "Investigation before queue", "Unique resolution may be established by exclusion", "card last-four"), "fitment evidence contract incomplete", errors)
    require(all_terms(photo, "UPC/EAN/GTIN", "chat-local shadow receipt database"), "photo intake contract incomplete", errors)
    require(all_terms(email, "Orders/History/<vendor-slug>/<order-number>", "FedEx, UPS, DHL and USPS", "90 calendar days", "open return, claim, dispute"), "email retention/reconciliation contract incomplete", errors)
    require(all_terms(asset, "immutable RFC 4122 UUID", "collision-resistant across deployments/family members", "manufacturer/OEM"), "asset identity contract incomplete", errors)
    require(all_terms(manual, "Manuals & Reference", "Knowledge Index", "canonical Drive link", "immutable RFC 4122 UUID"), "knowledge/manual contract incomplete", errors)
    require(all_terms(life, "Next-action planner", "Routine accountability", "Exercise / fitness organization", "School / study workflow"), "whole-life planning contract incomplete", errors)
    require(all_terms(reimbursement, "A reimbursement is not a merchant refund", "Net Household Cost"), "reimbursement contract incomplete", errors)
    require(all_terms(payment, "Awaiting Settlement", "Overcharged", "unmatched"), "payment reconciliation contract incomplete", errors)
    require(all_terms(contact, "do not reply", "Do you want me to send this email?"), "vendor contact safety incomplete", errors)
    require("deleting the originating ChatGPT conversation" in chat, "chat portability contract incomplete", errors)
    require(all_terms(calendar, "Google Calendar event ID", "update the linked event in place", "order delivery dates/windows"), "Calendar Projection contract incomplete", errors)
    require(all_terms(automation_design, "not a per-order automation", "never creates per-order scheduled tasks"), "automation design conflates Calendar Projection with task fanout", errors)

    # Identity/history/import boundaries.
    require(all_terms(household, "Entity UUID", "immutable", "Friendly"), "household schema lacks UUID/friendly-ID separation", errors)
    require("Status: superseded" in historical and "TRIP-" not in historical and "MILE-" not in historical and "live canonical" in historical.lower(), "historical audit can be mistaken for live mutable state", errors)
    require("historical_occurrences_imported" in importer and "False" in importer, "run-sheet importer may create historical occurrences", errors)
    require(all_terms(importer, "normalize_aliases", "--aliases", "public importer deliberately carries no employer-specific corrections"), "run-sheet importer lacks explicit private alias configuration", errors)
    require("route_pair_count" in importer and '"occurrences"' not in importer, "run-sheet importer exports occurrence rows", errors)
    require(all_terms(feature_ledger, "retired/retiree profile", "parent/guardian profile", "contract-only", "spec-only", "conversation-audit limitations"), "forensic feature ledger is incomplete", errors)
    require(all_terms(feature_ledger, "provider-neutral ai runtime capability routing", "google workspace and microsoft 365 state/evidence portability", "apple/icloud and portable-file manual bridge", "locked-down and regulated enterprise/va pilot lane"), "forensic feature ledger lacks current portability requirements", errors)
    require(
        all_terms(
            beta_audit,
            "root cause",
            "failure matrix",
            "clean-history release: pass",
            "clean reachable-history privacy audit passes",
            "no longer reachable from a named branch",
            "next real 2:45",
        ),
        "beta hardening audit lacks clean-release evidence/blockers",
        errors,
    )
    require(all_terms(portability_audit, "root cause found", "provider-neutral", "claude", "microsoft 365", "apple/icloud", "va pilot", "live microsoft/onedrive/sharepoint writes", "remain external"), "platform portability audit lacks honest implementation/external-gate status", errors)

    # Starter privacy contamination blocklist.
    markers = [line.strip() for line in text("privacy/starter-blocklist.txt").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    starter_surface = "\n".join((start, interview, catalog, deps, starter_readme, versioning, lifecycle, discovery, portability, enterprise, state_model, interview_ledger, shared, generic, json.dumps(questions), json.dumps(platform_manifest), json.dumps(install_flow)))
    for marker in markers:
        require(marker not in starter_surface, f"portable starter leaks reference marker: {marker}", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Repository contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Combine verified integration capabilities with behavior dependency readiness.

This module consumes a portable snapshot of the deployment Integration Registry. It
counts only capabilities that were actually verified on connected integrations,
feeds those capabilities into the behavior dependency checker, produces a bounded
plain-language remediation contract for missing dependencies, and suggests useful
workflows only when they match explicit user goals. It never connects providers,
enables workflows, changes goals, or mutates external state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


STARTER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = STARTER_ROOT.parent
DEFAULT_CONTRACTS = STARTER_ROOT / "behavior-dependencies.json"
DEFAULT_CATALOG = REPO_ROOT / "docs" / "feature-catalog.json"
DEFAULT_WORKFLOWS = STARTER_ROOT / "integration-workflow-catalog.json"
CONNECTION_STATES = {"connected", "disconnected", "unknown", "blocked"}
MAX_SETUP_STEPS = 5

PROVIDER_HINTS = {
    "barcode_scan": "a phone or companion app with barcode/QR scanning",
    "calendar_read": "Google Calendar, Outlook Calendar, or another approved calendar",
    "calendar_write": "Google Calendar, Outlook Calendar, or another approved writable calendar",
    "email_read": "Gmail, Outlook, or another approved mailbox",
    "evidence_read": "Google Drive, OneDrive, SharePoint, or another approved document store",
    "evidence_write": "Google Drive, OneDrive, SharePoint, or another approved document store",
    "finance_read": "an approved connected financial account or financial-data provider",
    "home_assistant_read": "an approved Home Assistant connection",
    "location_read": "an approved device or route-location source",
    "notification_delivery": "a notification path on the user's phone, computer, wearable, or approved device",
    "source_read": "GitHub, GitLab, Azure Repos, or another approved source provider",
    "source_write": "GitHub, GitLab, Azure Repos, or another approved writable source provider",
    "wearable_read": "an approved wearable or health-data bridge",
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _checker_module():
    path = STARTER_ROOT / "tools" / "behavior_dependency_check.py"
    spec = importlib.util.spec_from_file_location("behavior_dependency_check", path)
    if spec is None or spec.loader is None:
        raise ValueError("behavior dependency checker could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _checker_module()


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicates")
    return list(value)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _validate_goal(row: Any, index: int) -> dict[str, Any]:
    goal = _mapping(row, f"goals[{index}]")
    goal_id = str(goal.get("id", "")).strip()
    label = str(goal.get("label", "")).strip()
    active = goal.get("active")
    tags = _string_list(goal.get("tags", []), f"goals[{index}].tags")
    if not goal_id or not label:
        raise ValueError(f"goals[{index}] requires id and label")
    if not isinstance(active, bool):
        raise ValueError(f"goals[{index}].active must be boolean")
    return {"id": goal_id, "label": label, "active": active, "tags": tags}


def _validate_registry(registry: dict[str, Any], contracts: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != 1:
        raise ValueError("integration registry snapshot must use schema_version 1")
    capability_labels = _mapping(contracts.get("capability_labels"), "capability_labels")
    enabled_behaviors = _string_list(registry.get("enabled_behaviors", []), "enabled_behaviors")
    available_behaviors = _string_list(registry.get("available_behaviors", []), "available_behaviors")
    available_authorities = _string_list(registry.get("available_authorities", []), "available_authorities")
    direct_capabilities = _string_list(
        registry.get("direct_verified_capabilities", []), "direct_verified_capabilities"
    )
    unknown_direct = sorted(set(direct_capabilities) - set(capability_labels))
    if unknown_direct:
        raise ValueError("unknown direct verified capabilities: " + ", ".join(unknown_direct))

    integrations_raw = registry.get("integrations", [])
    if not isinstance(integrations_raw, list):
        raise ValueError("integrations must be a list")
    integrations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(integrations_raw):
        row = _mapping(raw, f"integrations[{index}]")
        integration_id = str(row.get("id", "")).strip()
        display_name = str(row.get("display_name", "")).strip()
        connection_state = str(row.get("connection_state", "")).strip()
        verified = _string_list(
            row.get("verified_capabilities", []), f"integrations[{index}].verified_capabilities"
        )
        advertised = _string_list(
            row.get("advertised_capabilities", []), f"integrations[{index}].advertised_capabilities"
        )
        if not integration_id or not display_name:
            raise ValueError(f"integrations[{index}] requires id and display_name")
        if integration_id in seen_ids:
            raise ValueError(f"duplicate integration id: {integration_id}")
        seen_ids.add(integration_id)
        if connection_state not in CONNECTION_STATES:
            raise ValueError(f"unsupported connection_state for {integration_id}: {connection_state}")
        unknown = sorted((set(verified) | set(advertised)) - set(capability_labels))
        if unknown:
            raise ValueError(
                f"integration {integration_id} references unknown capabilities: {', '.join(unknown)}"
            )
        integrations.append(
            {
                "id": integration_id,
                "display_name": display_name,
                "connection_state": connection_state,
                "verified_capabilities": verified,
                "advertised_capabilities": advertised,
            }
        )

    goals_raw = registry.get("goals", [])
    if not isinstance(goals_raw, list):
        raise ValueError("goals must be a list")
    goals = [_validate_goal(row, index) for index, row in enumerate(goals_raw)]
    active_workflow_ids = _string_list(registry.get("active_workflow_ids", []), "active_workflow_ids")
    dismissed_workflow_ids = _string_list(
        registry.get("dismissed_workflow_ids", []), "dismissed_workflow_ids"
    )
    overlap = set(active_workflow_ids) & set(dismissed_workflow_ids)
    if overlap:
        raise ValueError("workflow ids cannot be both active and dismissed: " + ", ".join(sorted(overlap)))

    return {
        "enabled_behaviors": enabled_behaviors,
        "available_behaviors": available_behaviors,
        "available_authorities": available_authorities,
        "direct_verified_capabilities": direct_capabilities,
        "integrations": integrations,
        "goals": goals,
        "active_workflow_ids": active_workflow_ids,
        "dismissed_workflow_ids": dismissed_workflow_ids,
    }


def build_environment(registry: dict[str, Any], contracts: dict[str, Any]) -> dict[str, Any]:
    """Build dependency-check input from verified connected integration capabilities."""

    observed = _validate_registry(registry, contracts)
    capabilities = set(observed["direct_verified_capabilities"])
    for integration in observed["integrations"]:
        if integration["connection_state"] == "connected":
            capabilities.update(integration["verified_capabilities"])
    return {
        "schema_version": 1,
        "enabled_behaviors": observed["enabled_behaviors"],
        "available_behaviors": observed["available_behaviors"],
        "available_capabilities": sorted(capabilities),
        "available_authorities": observed["available_authorities"],
    }


def _provider_hint(dependency_id: str, label: str) -> str:
    return PROVIDER_HINTS.get(dependency_id, label)


def _remediation_card(behavior_title: str, dependency_id: str, label: str, kind: str) -> dict[str, Any]:
    target = _provider_hint(dependency_id, label)
    return {
        "dependency_kind": kind,
        "dependency_id": dependency_id,
        "dependency_label": label,
        "help_question": "Do you need help setting this up?",
        "guided_setup": [
            f"Use the provider or integration that can supply {target}.",
            "If a suitable provider is already connected, use that one instead of creating a duplicate connection.",
            "Approve only the access this feature actually needs.",
            "Return to MIRA when the connection is complete so MIRA can verify the required capability and readback.",
        ],
        "max_visible_steps": MAX_SETUP_STEPS,
        "decline_message": (
            f"No problem. {behavior_title} will stay unavailable until {label} is connected or configured. "
            "Tell me when it is ready and I will check it again."
        ),
        "verification_required": True,
        "automatic_install": False,
        "automatic_enablement": False,
    }


def add_remediation(readiness: dict[str, Any], contracts: dict[str, Any]) -> dict[str, Any]:
    """Attach bounded plain-language remediation to blocked behavior results."""

    capability_labels = contracts["capability_labels"]
    authority_labels = contracts["authority_labels"]
    behaviors = readiness.get("behaviors", {})
    if not isinstance(behaviors, dict):
        raise ValueError("readiness.behaviors must be an object")
    for behavior_id, result in behaviors.items():
        row = _mapping(result, f"readiness.behaviors.{behavior_id}")
        title = str(row.get("title", behavior_id))
        cards: list[dict[str, Any]] = []
        for capability in row.get("missing_required_capabilities", []):
            cards.append(_remediation_card(title, capability, capability_labels[capability], "capability"))
        for authority in row.get("missing_required_authorities", []):
            cards.append(_remediation_card(title, authority, authority_labels[authority], "authority"))
        for dependency in row.get("missing_required_behaviors", []):
            cards.append(
                _remediation_card(title, dependency, f"the required {dependency} workflow", "behavior")
            )
        row["remediation"] = cards
        if cards:
            row["prompt"] = f"{row['prompt']} {cards[0]['help_question']}"
    return readiness


def _validate_workflow_catalog(catalog: dict[str, Any], contracts: dict[str, Any]) -> list[dict[str, Any]]:
    if catalog.get("schema_version") != 1:
        raise ValueError("integration workflow catalog must use schema_version 1")
    policy = _mapping(catalog.get("policy"), "workflow catalog policy")
    required_policy = {
        "automatic_enablement": False,
        "automatic_goal_inference": False,
        "connected_provider_is_not_capability_proof": True,
        "verified_capabilities_only": True,
        "user_confirmation_required": True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise ValueError(f"workflow catalog policy.{key} must be {expected!r}")
    workflows = catalog.get("workflows")
    if not isinstance(workflows, list):
        raise ValueError("workflow catalog workflows must be a list")
    capability_labels = _mapping(contracts.get("capability_labels"), "capability_labels")
    known_behaviors = set(_mapping(contracts.get("assignments"), "assignments"))
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(workflows):
        row = _mapping(raw, f"workflows[{index}]")
        workflow_id = str(row.get("id", "")).strip()
        title = str(row.get("title", "")).strip()
        why = str(row.get("why", "")).strip()
        prompt = str(row.get("prompt", "")).strip()
        required = _string_list(row.get("required_capabilities", []), f"workflows[{index}].required_capabilities")
        optional = _string_list(row.get("optional_capabilities", []), f"workflows[{index}].optional_capabilities")
        goal_tags = _string_list(row.get("goal_tags", []), f"workflows[{index}].goal_tags")
        behavior_ids = _string_list(row.get("behavior_ids", []), f"workflows[{index}].behavior_ids")
        if not workflow_id or not title or not why or not prompt:
            raise ValueError(f"workflows[{index}] requires id, title, why, and prompt")
        if workflow_id in seen:
            raise ValueError(f"duplicate workflow id: {workflow_id}")
        seen.add(workflow_id)
        unknown_capabilities = sorted((set(required) | set(optional)) - set(capability_labels))
        if unknown_capabilities:
            raise ValueError(
                f"workflow {workflow_id} references unknown capabilities: {', '.join(unknown_capabilities)}"
            )
        unknown_behaviors = sorted(set(behavior_ids) - known_behaviors)
        if unknown_behaviors:
            raise ValueError(
                f"workflow {workflow_id} references unknown behaviors: {', '.join(unknown_behaviors)}"
            )
        result.append(
            {
                "id": workflow_id,
                "title": title,
                "why": why,
                "prompt": prompt,
                "required_capabilities": required,
                "optional_capabilities": optional,
                "goal_tags": goal_tags,
                "behavior_ids": behavior_ids,
            }
        )
    return result


def recommend_workflows(
    registry: dict[str, Any], contracts: dict[str, Any], workflow_catalog: dict[str, Any]
) -> list[dict[str, Any]]:
    """Recommend workflows only from verified capabilities and explicit active goals."""

    observed = _validate_registry(registry, contracts)
    workflows = _validate_workflow_catalog(workflow_catalog, contracts)
    available_capabilities: set[str] = set(observed["direct_verified_capabilities"])
    capability_integrations: dict[str, set[str]] = {}
    for integration in observed["integrations"]:
        if integration["connection_state"] != "connected":
            continue
        for capability in integration["verified_capabilities"]:
            available_capabilities.add(capability)
            capability_integrations.setdefault(capability, set()).add(integration["display_name"])

    active_ids = set(observed["active_workflow_ids"])
    dismissed_ids = set(observed["dismissed_workflow_ids"])
    active_goals = [goal for goal in observed["goals"] if goal["active"]]
    recommendations: list[dict[str, Any]] = []
    for workflow in workflows:
        if workflow["id"] in active_ids or workflow["id"] in dismissed_ids:
            continue
        required = set(workflow["required_capabilities"])
        if not required.issubset(available_capabilities):
            continue
        matching_goals = [
            goal for goal in active_goals if set(goal["tags"]) & set(workflow["goal_tags"])
        ]
        if not matching_goals:
            continue
        integrations = sorted(
            {
                name
                for capability in required
                for name in capability_integrations.get(capability, set())
            }
        )
        integration_text = ", ".join(integrations) if integrations else "your verified integration"
        goal = matching_goals[0]
        missing_optional = sorted(set(workflow["optional_capabilities"]) - available_capabilities)
        recommendations.append(
            {
                "id": workflow["id"],
                "title": workflow["title"],
                "goal_id": goal["id"],
                "goal_label": goal["label"],
                "integrations": integrations,
                "required_capabilities": workflow["required_capabilities"],
                "missing_optional_capabilities": missing_optional,
                "behavior_ids": workflow["behavior_ids"],
                "why": workflow["why"],
                "prompt": workflow["prompt"].format(
                    integrations=integration_text,
                    goal=goal["label"],
                ),
                "requires_confirmation": True,
                "automatic_enablement": False,
            }
        )

    limit = workflow_catalog.get("policy", {}).get("max_recommendations_per_review", 5)
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("workflow catalog max_recommendations_per_review must be a positive integer")
    return recommendations[:limit]


def review(
    registry: dict[str, Any],
    contracts: dict[str, Any],
    workflow_catalog: dict[str, Any],
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return dependency readiness plus non-mutating integration workflow recommendations."""

    CHECKER.validate_contracts(contracts)
    if catalog is not None:
        CHECKER.audit_catalog(contracts, catalog)
    environment = build_environment(registry, contracts)
    readiness = CHECKER.evaluate(contracts, environment, catalog)
    add_remediation(readiness, contracts)
    return {
        "schema_version": 1,
        "dependency_environment": environment,
        "dependency_readiness": readiness,
        "workflow_recommendations": recommend_workflows(registry, contracts, workflow_catalog),
        "policy": {
            "verified_capabilities_only": True,
            "provider_name_is_not_capability_proof": True,
            "automatic_dependency_install": False,
            "automatic_workflow_enablement": False,
            "explicit_user_goals_only": True,
            "user_confirmation_required": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path, help="JSON snapshot of the deployment Integration Registry")
    parser.add_argument("--contracts", type=Path, default=DEFAULT_CONTRACTS)
    parser.add_argument("--workflows", type=Path, default=DEFAULT_WORKFLOWS)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()
    try:
        catalog = _load_json(args.catalog) if args.catalog.is_file() else None
        result = review(
            _load_json(args.registry),
            _load_json(args.contracts),
            _load_json(args.workflows),
            catalog,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError, CHECKER.DependencyContractError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

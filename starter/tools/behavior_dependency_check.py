#!/usr/bin/env python3
"""Validate and evaluate dependencies for every cataloged M.I.R.R.O.R. behavior.

The dependency database is deliberately separate from the installable feature-package
graph. This module covers every operational behavior/gesture in the forensic feature
catalog, including receipts, scheduling, reminders, shipments, assets, onboarding,
provider portability, and infrastructure contracts. It never installs dependencies
or enables behavior; it only validates the map and reports readiness.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STARTER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = STARTER_ROOT.parent
DEFAULT_CONTRACTS = STARTER_ROOT / "behavior-dependencies.json"
DEFAULT_CATALOG = REPO_ROOT / "docs" / "feature-catalog.json"


class DependencyContractError(ValueError):
    """Raised when the dependency database or environment is inconsistent."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise DependencyContractError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise DependencyContractError(f"{label} contains duplicates")
    return list(value)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DependencyContractError(f"{label} must be an object")
    return value


def _validate_profile(name: str, profile: Any) -> tuple[set[str], set[str]]:
    row = _mapping(profile, f"profile {name}")
    allowed = {
        "required_capabilities",
        "optional_capabilities",
        "required_authorities",
        "optional_authorities",
    }
    unknown = sorted(set(row) - allowed)
    if unknown:
        raise DependencyContractError(f"profile {name} has unsupported fields: {', '.join(unknown)}")
    required_capabilities = set(
        _string_list(row.get("required_capabilities", []), f"profile {name}.required_capabilities")
    )
    optional_capabilities = set(
        _string_list(row.get("optional_capabilities", []), f"profile {name}.optional_capabilities")
    )
    required_authorities = set(
        _string_list(row.get("required_authorities", []), f"profile {name}.required_authorities")
    )
    optional_authorities = set(
        _string_list(row.get("optional_authorities", []), f"profile {name}.optional_authorities")
    )
    overlap = required_capabilities & optional_capabilities
    if overlap:
        raise DependencyContractError(
            f"profile {name} marks capabilities both required and optional: {', '.join(sorted(overlap))}"
        )
    overlap = required_authorities & optional_authorities
    if overlap:
        raise DependencyContractError(
            f"profile {name} marks authorities both required and optional: {', '.join(sorted(overlap))}"
        )
    return required_capabilities | optional_capabilities, required_authorities | optional_authorities


def _resolve_profile_reference(contracts: dict[str, Any], name: str) -> dict[str, Any]:
    """Resolve a reusable profile or one unambiguous direct capability selector."""

    profiles = _mapping(contracts.get("profiles"), "profiles")
    if name in profiles:
        return _mapping(profiles[name], f"profile {name}")

    capability_labels = _mapping(contracts.get("capability_labels"), "capability_labels")
    selector = name.replace("-", "_")
    candidates = [
        capability
        for capability in capability_labels
        if capability == selector or capability.startswith(selector + "_")
    ]
    if len(candidates) == 1:
        return {
            "required_capabilities": [candidates[0]],
            "optional_capabilities": [],
            "required_authorities": [],
            "optional_authorities": [],
        }
    if len(candidates) > 1:
        raise DependencyContractError(
            f"ambiguous capability selector {name}: {', '.join(sorted(candidates))}"
        )
    raise DependencyContractError(f"unknown dependency profile or capability selector: {name}")


def validate_contracts(contracts: dict[str, Any]) -> None:
    """Validate the dependency database without requiring the canonical feature catalog."""

    if contracts.get("schema_version") != 1:
        raise DependencyContractError("behavior-dependencies.json must use schema_version 1")

    policy = _mapping(contracts.get("policy"), "policy")
    required_policy = {
        "automatic_behavior_enablement": False,
        "automatic_dependency_install": False,
        "default_dependency_failure": "block-only-affected-behavior",
        "optional_dependency_failure": "degrade-only-affected-behavior",
        "missing_dependency_prompt_required": True,
        "user_in_the_loop": True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise DependencyContractError(f"policy.{key} must be {expected!r}")

    capability_labels = _mapping(contracts.get("capability_labels"), "capability_labels")
    authority_labels = _mapping(contracts.get("authority_labels"), "authority_labels")
    if any(
        not isinstance(key, str) or not isinstance(value, str) or not value
        for key, value in capability_labels.items()
    ):
        raise DependencyContractError("capability_labels must map strings to non-empty strings")
    if any(
        not isinstance(key, str) or not isinstance(value, str) or not value
        for key, value in authority_labels.items()
    ):
        raise DependencyContractError("authority_labels must map strings to non-empty strings")

    profiles = _mapping(contracts.get("profiles"), "profiles")
    assignments = _mapping(contracts.get("assignments"), "assignments")
    if not profiles or not assignments:
        raise DependencyContractError("profiles and assignments must not be empty")

    referenced_capabilities: set[str] = set()
    referenced_authorities: set[str] = set()
    for name, profile in sorted(profiles.items()):
        if not isinstance(name, str) or not name:
            raise DependencyContractError("profile names must be non-empty strings")
        capabilities, authorities = _validate_profile(name, profile)
        referenced_capabilities.update(capabilities)
        referenced_authorities.update(authorities)

    unlabeled_capabilities = sorted(referenced_capabilities - set(capability_labels))
    unlabeled_authorities = sorted(referenced_authorities - set(authority_labels))
    if unlabeled_capabilities:
        raise DependencyContractError(
            "capabilities missing user-facing labels: " + ", ".join(unlabeled_capabilities)
        )
    if unlabeled_authorities:
        raise DependencyContractError(
            "authorities missing user-facing labels: " + ", ".join(unlabeled_authorities)
        )

    known_behaviors = set(assignments)
    required_graph: dict[str, list[str]] = {}
    for behavior_id, assignment in sorted(assignments.items()):
        if not isinstance(behavior_id, str) or not behavior_id:
            raise DependencyContractError("behavior ids must be non-empty strings")
        row = _mapping(assignment, f"assignment {behavior_id}")
        allowed = {"profiles", "requires_behaviors", "optional_behaviors"}
        unknown = sorted(set(row) - allowed)
        if unknown:
            raise DependencyContractError(
                f"assignment {behavior_id} has unsupported fields: {', '.join(unknown)}"
            )
        selected_profiles = _string_list(row.get("profiles"), f"assignment {behavior_id}.profiles")
        if not selected_profiles:
            raise DependencyContractError(f"assignment {behavior_id} must select at least one profile")
        for profile_name in selected_profiles:
            _resolve_profile_reference(contracts, profile_name)
        required = _string_list(
            row.get("requires_behaviors", []), f"assignment {behavior_id}.requires_behaviors"
        )
        optional = _string_list(
            row.get("optional_behaviors", []), f"assignment {behavior_id}.optional_behaviors"
        )
        if behavior_id in required or behavior_id in optional:
            raise DependencyContractError(f"assignment {behavior_id} cannot depend on itself")
        unknown_dependencies = sorted((set(required) | set(optional)) - known_behaviors)
        if unknown_dependencies:
            raise DependencyContractError(
                f"assignment {behavior_id} references unknown behaviors: {', '.join(unknown_dependencies)}"
            )
        overlap = set(required) & set(optional)
        if overlap:
            raise DependencyContractError(
                f"assignment {behavior_id} marks behaviors both required and optional: "
                + ", ".join(sorted(overlap))
            )
        required_graph[behavior_id] = required

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(behavior_id: str) -> None:
        if behavior_id in visiting:
            raise DependencyContractError(f"required behavior dependency cycle detected at {behavior_id}")
        if behavior_id in visited:
            return
        visiting.add(behavior_id)
        for dependency in required_graph[behavior_id]:
            visit(dependency)
        visiting.remove(behavior_id)
        visited.add(behavior_id)

    for behavior_id in sorted(known_behaviors):
        visit(behavior_id)


def _flatten_catalog(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if catalog.get("schema_version") != 1:
        raise DependencyContractError("feature catalog must use schema_version 1")
    categories = catalog.get("categories")
    if not isinstance(categories, list):
        raise DependencyContractError("feature catalog categories must be a list")

    features: dict[str, dict[str, Any]] = {}
    for category in categories:
        category_row = _mapping(category, "feature catalog category")
        category_id = category_row.get("id")
        category_title = category_row.get("title")
        if not isinstance(category_id, str) or not isinstance(category_title, str):
            raise DependencyContractError("feature catalog category id/title must be strings")
        category_features = category_row.get("features")
        if not isinstance(category_features, list):
            raise DependencyContractError(f"feature catalog category {category_id} features must be a list")
        for feature in category_features:
            feature_row = _mapping(feature, f"feature catalog category {category_id} row")
            feature_id = feature_row.get("id")
            title = feature_row.get("title")
            if not isinstance(feature_id, str) or not isinstance(title, str):
                raise DependencyContractError("feature catalog feature id/title must be strings")
            if feature_id in features:
                raise DependencyContractError(f"duplicate feature catalog id: {feature_id}")
            features[feature_id] = {
                "id": feature_id,
                "title": title,
                "category_id": category_id,
                "category_title": category_title,
                "delivery": feature_row.get("delivery"),
                "verification": feature_row.get("verification"),
                "evidence_paths": feature_row.get("evidence_paths", []),
            }
    return features


def audit_catalog(contracts: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    """Require every cataloged behavior to have exactly one dependency assignment."""

    validate_contracts(contracts)
    catalog_features = _flatten_catalog(catalog)
    assignment_ids = set(contracts["assignments"])
    catalog_ids = set(catalog_features)
    missing = sorted(catalog_ids - assignment_ids)
    extra = sorted(assignment_ids - catalog_ids)
    if missing or extra:
        parts: list[str] = []
        if missing:
            parts.append("catalog behaviors missing dependency assignments: " + ", ".join(missing))
        if extra:
            parts.append("dependency assignments absent from catalog: " + ", ".join(extra))
        raise DependencyContractError("; ".join(parts))

    return {
        "schema_version": 1,
        "catalog_version": catalog.get("catalog_version"),
        "behavior_count": len(catalog_features),
        "dependency_assignment_count": len(assignment_ids),
        "complete": True,
    }


def resolve_behavior(
    behavior_id: str,
    contracts: dict[str, Any],
    catalog_features: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Expand named profiles/direct capability selectors into concrete dependency sets."""

    assignments = contracts["assignments"]
    if behavior_id not in assignments:
        raise DependencyContractError(f"unknown behavior: {behavior_id}")
    row = assignments[behavior_id]
    required_capabilities: set[str] = set()
    optional_capabilities: set[str] = set()
    required_authorities: set[str] = set()
    optional_authorities: set[str] = set()

    for profile_name in row["profiles"]:
        profile = _resolve_profile_reference(contracts, profile_name)
        required_capabilities.update(profile.get("required_capabilities", []))
        optional_capabilities.update(profile.get("optional_capabilities", []))
        required_authorities.update(profile.get("required_authorities", []))
        optional_authorities.update(profile.get("optional_authorities", []))

    optional_capabilities -= required_capabilities
    optional_authorities -= required_authorities
    catalog_row = (catalog_features or {}).get(behavior_id, {})
    return {
        "id": behavior_id,
        "title": catalog_row.get("title", behavior_id),
        "category_id": catalog_row.get("category_id"),
        "category_title": catalog_row.get("category_title"),
        "delivery": catalog_row.get("delivery"),
        "verification": catalog_row.get("verification"),
        "evidence_paths": catalog_row.get("evidence_paths", []),
        "profiles": list(row["profiles"]),
        "required_capabilities": sorted(required_capabilities),
        "optional_capabilities": sorted(optional_capabilities),
        "required_authorities": sorted(required_authorities),
        "optional_authorities": sorted(optional_authorities),
        "requires_behaviors": sorted(row.get("requires_behaviors", [])),
        "optional_behaviors": sorted(row.get("optional_behaviors", [])),
    }


def _environment(value: Any) -> dict[str, set[str] | list[str]]:
    row = _mapping(value, "environment")
    if row.get("schema_version") != 1:
        raise DependencyContractError("environment must use schema_version 1")
    allowed = {
        "schema_version",
        "enabled_behaviors",
        "available_behaviors",
        "available_capabilities",
        "available_authorities",
    }
    unknown = sorted(set(row) - allowed)
    if unknown:
        raise DependencyContractError("environment has unsupported fields: " + ", ".join(unknown))
    enabled = _string_list(row.get("enabled_behaviors"), "environment.enabled_behaviors")
    available_behaviors = set(
        _string_list(row.get("available_behaviors"), "environment.available_behaviors")
    )
    available_capabilities = set(
        _string_list(row.get("available_capabilities"), "environment.available_capabilities")
    )
    available_authorities = set(
        _string_list(row.get("available_authorities"), "environment.available_authorities")
    )
    return {
        "enabled_behaviors": enabled,
        "available_behaviors": available_behaviors,
        "available_capabilities": available_capabilities,
        "available_authorities": available_authorities,
    }


def evaluate(
    contracts: dict[str, Any],
    environment: dict[str, Any],
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate only enabled behavior and keep failures isolated to affected behavior."""

    validate_contracts(contracts)
    catalog_features = _flatten_catalog(catalog) if catalog is not None else {}
    observed = _environment(environment)
    enabled = observed["enabled_behaviors"]
    available_behaviors = observed["available_behaviors"]
    available_capabilities = observed["available_capabilities"]
    available_authorities = observed["available_authorities"]

    assert isinstance(enabled, list)
    assert isinstance(available_behaviors, set)
    assert isinstance(available_capabilities, set)
    assert isinstance(available_authorities, set)

    unknown_enabled = sorted(set(enabled) - set(contracts["assignments"]))
    unknown_available = sorted(available_behaviors - set(contracts["assignments"]))
    if unknown_enabled:
        raise DependencyContractError("enabled_behaviors contains unknown ids: " + ", ".join(unknown_enabled))
    if unknown_available:
        raise DependencyContractError(
            "available_behaviors contains unknown ids: " + ", ".join(unknown_available)
        )

    memo: dict[str, dict[str, Any]] = {}

    def status_for(behavior_id: str) -> dict[str, Any]:
        if behavior_id in memo:
            return memo[behavior_id]

        resolved = resolve_behavior(behavior_id, contracts, catalog_features)
        missing_required_capabilities = sorted(
            set(resolved["required_capabilities"]) - available_capabilities
        )
        missing_optional_capabilities = sorted(
            set(resolved["optional_capabilities"]) - available_capabilities
        )
        missing_required_authorities = sorted(
            set(resolved["required_authorities"]) - available_authorities
        )
        missing_optional_authorities = sorted(
            set(resolved["optional_authorities"]) - available_authorities
        )

        missing_required_behaviors = sorted(
            set(resolved["requires_behaviors"]) - available_behaviors
        )
        missing_optional_behaviors = sorted(
            set(resolved["optional_behaviors"]) - available_behaviors
        )
        blocked_by_behavior: list[str] = []
        degraded_by_behavior: list[str] = []

        for dependency in resolved["requires_behaviors"]:
            if dependency not in available_behaviors:
                continue
            dependency_status = status_for(dependency)
            if dependency_status["status"] == "blocked":
                blocked_by_behavior.append(dependency)
            elif dependency_status["status"] == "degraded":
                degraded_by_behavior.append(dependency)

        for dependency in resolved["optional_behaviors"]:
            if dependency not in available_behaviors:
                continue
            dependency_status = status_for(dependency)
            if dependency_status["status"] != "ready":
                degraded_by_behavior.append(dependency)

        behavior_missing = behavior_id not in available_behaviors
        blocked = (
            behavior_missing
            or bool(missing_required_capabilities)
            or bool(missing_required_authorities)
            or bool(missing_required_behaviors)
            or bool(blocked_by_behavior)
        )
        degraded = (
            not blocked
            and (
                bool(missing_optional_capabilities)
                or bool(missing_optional_authorities)
                or bool(missing_optional_behaviors)
                or bool(degraded_by_behavior)
            )
        )
        status = "blocked" if blocked else "degraded" if degraded else "ready"

        capability_labels = contracts["capability_labels"]
        authority_labels = contracts["authority_labels"]
        missing_required_labels = [
            capability_labels[item] for item in missing_required_capabilities
        ] + [authority_labels[item] for item in missing_required_authorities]
        missing_optional_labels = [
            capability_labels[item] for item in missing_optional_capabilities
        ] + [authority_labels[item] for item in missing_optional_authorities]

        if behavior_missing:
            missing_required_labels.insert(0, "the installed implementation of this behavior")
        if missing_required_behaviors:
            missing_required_labels.extend(f"behavior {item}" for item in missing_required_behaviors)
        if blocked_by_behavior:
            missing_required_labels.extend(
                f"working dependency behavior {item}" for item in blocked_by_behavior
            )
        if missing_optional_behaviors:
            missing_optional_labels.extend(f"optional behavior {item}" for item in missing_optional_behaviors)
        if degraded_by_behavior:
            missing_optional_labels.extend(
                f"fully ready optional dependency behavior {item}" for item in degraded_by_behavior
            )

        if status == "blocked":
            prompt = (
                f"{resolved['title']} is not ready yet. It needs "
                + "; ".join(missing_required_labels)
                + ". Nothing will be changed automatically, and unrelated workflows stay as they are."
            )
        elif status == "degraded":
            prompt = (
                f"{resolved['title']} can run, but some optional parts are unavailable: "
                + "; ".join(missing_optional_labels)
                + ". The rest of the workflow stays available."
            )
        else:
            prompt = f"{resolved['title']} has all declared dependencies available."

        result = {
            **resolved,
            "status": status,
            "missing_required_capabilities": missing_required_capabilities,
            "missing_optional_capabilities": missing_optional_capabilities,
            "missing_required_authorities": missing_required_authorities,
            "missing_optional_authorities": missing_optional_authorities,
            "missing_required_behaviors": missing_required_behaviors,
            "missing_optional_behaviors": missing_optional_behaviors,
            "blocked_by_behavior": sorted(set(blocked_by_behavior)),
            "degraded_by_behavior": sorted(set(degraded_by_behavior)),
            "prompt": prompt,
        }
        memo[behavior_id] = result
        return result

    results = {behavior_id: status_for(behavior_id) for behavior_id in enabled}
    blocked = sorted(
        behavior_id for behavior_id, result in results.items() if result["status"] == "blocked"
    )
    degraded = sorted(
        behavior_id for behavior_id, result in results.items() if result["status"] == "degraded"
    )
    return {
        "schema_version": 1,
        "ready": not blocked,
        "policy": {
            "automatic_dependency_install": False,
            "automatic_behavior_enablement": False,
            "failure_isolation": "block-only-affected-behavior",
            "user_in_the_loop": True,
        },
        "blocked_behaviors": blocked,
        "degraded_behaviors": degraded,
        "behaviors": results,
    }


def _catalog_if_present(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = _read_json(path)
    return _mapping(value, "feature catalog")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, default=DEFAULT_CONTRACTS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate the portable dependency database")

    audit_parser = subparsers.add_parser(
        "audit", help="prove every canonical feature-catalog behavior has a dependency assignment"
    )
    audit_parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    check_parser = subparsers.add_parser(
        "check", help="evaluate enabled behavior against observed capabilities and authorities"
    )
    check_parser.add_argument("environment", type=Path)
    check_parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    args = parser.parse_args()
    try:
        contracts = _mapping(_read_json(args.contracts), "dependency contracts")
        if args.command == "validate":
            validate_contracts(contracts)
            print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "valid": True,
                        "behavior_count": len(contracts["assignments"]),
                        "profile_count": len(contracts["profiles"]),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "audit":
            catalog = _mapping(_read_json(args.catalog), "feature catalog")
            print(json.dumps(audit_catalog(contracts, catalog), indent=2, sort_keys=True))
            return 0

        environment = _mapping(_read_json(args.environment), "environment")
        catalog = _catalog_if_present(args.catalog)
        result = evaluate(contracts, environment, catalog)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] else 3
    except (OSError, json.JSONDecodeError, DependencyContractError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

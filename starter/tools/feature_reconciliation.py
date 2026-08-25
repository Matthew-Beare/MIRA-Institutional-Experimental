#!/usr/bin/env python3
"""Maintain feature ownership/dependencies and plan user-in-the-loop upgrades.

The durable rule is conservative: local behavior is preserved by default.
This module may register metadata and produce proposals, but it never applies an
upstream behavior change or deletes a local feature.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


LOCK_NAME = "features.lock.json"
MAP_NAME = "feature-dependency-map.json"
FEATURE_ROOT = Path("features")
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
OWNERS = {"mirror", "user", "organization"}
CONFLICT_POLICIES = {"preserve-local-and-ask"}
ROLLBACK_POLICIES = {"checkpoint-before-change"}


class ReconciliationError(ValueError):
    """Raised when feature ownership or dependency state is unsafe."""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_manifests(starter_root: Path) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    feature_root = starter_root / FEATURE_ROOT
    if not feature_root.is_dir():
        raise ReconciliationError(f"feature root is missing: {feature_root}")
    for path in sorted(feature_root.glob("*/feature.json")):
        value = _read_json(path)
        feature_id = value.get("id") if isinstance(value, dict) else None
        if not isinstance(feature_id, str) or not ID_RE.fullmatch(feature_id):
            raise ReconciliationError(f"invalid feature id in {path}")
        if feature_id in manifests:
            raise ReconciliationError(f"duplicate feature id: {feature_id}")
        if path.parent.name != feature_id:
            raise ReconciliationError(
                f"feature directory {path.parent.name!r} does not match id {feature_id!r}"
            )
        manifests[feature_id] = value
    return manifests


def _load_lock(starter_root: Path) -> dict[str, Any]:
    path = starter_root / LOCK_NAME
    value = _read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ReconciliationError(f"{LOCK_NAME} must use schema_version 1")
    if not isinstance(value.get("features"), dict):
        raise ReconciliationError(f"{LOCK_NAME}.features must be an object")
    return value


def _validate_lock(lock: dict[str, Any], manifests: dict[str, dict[str, Any]]) -> None:
    if lock.get("default_conflict_policy") != "preserve-local-and-ask":
        raise ReconciliationError("default conflict policy must preserve local behavior and ask")
    if lock.get("default_rollback_policy") != "checkpoint-before-change":
        raise ReconciliationError("default rollback policy must checkpoint before change")

    rows = lock["features"]
    missing = sorted(set(manifests) - set(rows))
    extra = sorted(set(rows) - set(manifests))
    if missing:
        raise ReconciliationError(f"features missing ownership records: {', '.join(missing)}")
    if extra:
        raise ReconciliationError(f"ownership records without manifests: {', '.join(extra)}")

    owned_patterns: dict[str, str] = {}
    for feature_id, row in sorted(rows.items()):
        if not isinstance(row, dict):
            raise ReconciliationError(f"lock entry {feature_id} must be an object")
        owner = row.get("owner")
        origin = row.get("origin")
        if owner not in OWNERS or origin not in OWNERS:
            raise ReconciliationError(f"{feature_id} has invalid owner/origin")
        if row.get("conflict_policy") not in CONFLICT_POLICIES:
            raise ReconciliationError(f"{feature_id} must preserve local behavior on conflict")
        if row.get("rollback_policy") not in ROLLBACK_POLICIES:
            raise ReconciliationError(f"{feature_id} must require a rollback checkpoint")
        if row.get("installed_version") != manifests[feature_id].get("version"):
            raise ReconciliationError(f"{feature_id} lock version does not match its manifest")
        local_revision = row.get("local_revision")
        if not isinstance(local_revision, int) or isinstance(local_revision, bool) or local_revision < 0:
            raise ReconciliationError(f"{feature_id}.local_revision must be a nonnegative integer")
        for field in ("upstream_feature_id", "upstream_base_version", "upstream_base_revision"):
            if field not in row or not (row[field] is None or isinstance(row[field], str)):
                raise ReconciliationError(f"{feature_id}.{field} must be string or null")
        paths = row.get("owned_paths")
        if not isinstance(paths, list) or not paths or any(
            not isinstance(item, str) or not item.strip() for item in paths
        ):
            raise ReconciliationError(f"{feature_id}.owned_paths must contain paths")
        expected_prefix = f"starter/features/{feature_id}/"
        if not any(item.startswith(expected_prefix) for item in paths):
            raise ReconciliationError(f"{feature_id} must own its feature directory")
        for pattern in paths:
            previous = owned_patterns.get(pattern)
            if previous and previous != feature_id:
                raise ReconciliationError(
                    f"owned path {pattern!r} is claimed by both {previous} and {feature_id}"
                )
            owned_patterns[pattern] = feature_id


def register_feature(starter_root: Path, feature_id: str, owner: str) -> dict[str, Any]:
    """Register one manifest and refresh the dependency map without changing ownership silently."""
    if not ID_RE.fullmatch(feature_id):
        raise ReconciliationError("feature id must be lowercase hyphen-case")
    if owner not in OWNERS:
        raise ReconciliationError(f"owner must be one of: {', '.join(sorted(OWNERS))}")
    manifests = _load_manifests(starter_root)
    if feature_id not in manifests:
        raise ReconciliationError(f"feature manifest does not exist: {feature_id}")
    lock = _load_lock(starter_root)
    existing = lock["features"].get(feature_id)
    manifest = manifests[feature_id]
    if existing is not None:
        if existing.get("owner") != owner:
            raise ReconciliationError(
                f"refusing to change {feature_id} ownership from {existing.get('owner')} to {owner}"
            )
        existing["installed_version"] = manifest.get("version")
        if owner == "mirror" and existing.get("upstream_feature_id") is None:
            existing["upstream_feature_id"] = feature_id
    else:
        upstream = owner == "mirror"
        lock["features"][feature_id] = {
            "owner": owner,
            "origin": owner,
            "installed_version": manifest.get("version"),
            "upstream_feature_id": feature_id if upstream else None,
            "upstream_base_version": manifest.get("version") if upstream else None,
            "upstream_base_revision": "template" if upstream else None,
            "local_revision": 0,
            "owned_paths": [f"starter/features/{feature_id}/**"],
            "conflict_policy": "preserve-local-and-ask",
            "rollback_policy": "checkpoint-before-change",
        }
    _write_json(starter_root / LOCK_NAME, lock)
    return sync_dependency_map(starter_root, check=False)


def build_dependency_map(starter_root: Path) -> dict[str, Any]:
    manifests = _load_manifests(starter_root)
    lock = _load_lock(starter_root)
    _validate_lock(lock, manifests)

    features: dict[str, Any] = {}
    edges: list[dict[str, str]] = []
    for feature_id in sorted(manifests):
        manifest = manifests[feature_id]
        locked = lock["features"][feature_id]
        runtime = manifest.get("runtime_contract", {})
        dependencies = manifest.get("dependencies", [])
        feature_dependencies: list[dict[str, str]] = []
        for dependency in dependencies if isinstance(dependencies, list) else []:
            if not isinstance(dependency, dict):
                continue
            dependency_id = dependency.get("id")
            version_range = dependency.get("version_range")
            if isinstance(dependency_id, str) and isinstance(version_range, str):
                feature_dependencies.append({"id": dependency_id, "version_range": version_range})
                edges.append(
                    {"from": feature_id, "to": dependency_id, "kind": "feature-required"}
                )

        required = sorted(set(runtime.get("required_capabilities", [])))
        optional = sorted(set(runtime.get("optional_capabilities", [])))
        conditional = runtime.get("conditional_capabilities", {})
        if not isinstance(conditional, dict):
            conditional = {}
        for capability in required:
            edges.append(
                {"from": feature_id, "to": capability, "kind": "capability-required"}
            )
        for capability in optional:
            edges.append(
                {"from": feature_id, "to": capability, "kind": "capability-optional"}
            )

        features[feature_id] = {
            "id": feature_id,
            "version": manifest.get("version"),
            "summary": manifest.get("summary"),
            "owner": locked.get("owner"),
            "origin": locked.get("origin"),
            "upstream_feature_id": locked.get("upstream_feature_id"),
            "upstream_base_version": locked.get("upstream_base_version"),
            "upstream_base_revision": locked.get("upstream_base_revision"),
            "local_revision": locked.get("local_revision"),
            "owned_paths": sorted(locked.get("owned_paths", [])),
            "conflict_policy": locked.get("conflict_policy"),
            "rollback_policy": locked.get("rollback_policy"),
            "feature_dependencies": sorted(feature_dependencies, key=lambda item: item["id"]),
            "required_capabilities": required,
            "optional_capabilities": optional,
            "conditional_capabilities": dict(sorted(conditional.items())),
            "failure_domain": runtime.get("failure_domain"),
        }

    unknown_feature_dependencies = sorted(
        {
            edge["to"]
            for edge in edges
            if edge["kind"] == "feature-required" and edge["to"] not in features
        }
    )
    if unknown_feature_dependencies:
        raise ReconciliationError(
            "unknown feature dependencies: " + ", ".join(unknown_feature_dependencies)
        )

    return {
        "schema_version": 1,
        "policy": {
            "local_behavior_default": "keep-current",
            "user_in_the_loop": True,
            "rollback_before_change": True,
            "automatic_local_feature_deletion": False,
        },
        "features": features,
        "edges": sorted(edges, key=lambda item: (item["from"], item["kind"], item["to"])),
    }


def sync_dependency_map(starter_root: Path, *, check: bool) -> dict[str, Any]:
    generated = build_dependency_map(starter_root)
    path = starter_root / MAP_NAME
    if check:
        if not path.is_file():
            raise ReconciliationError(f"{MAP_NAME} is missing; run sync before committing")
        current = _read_json(path)
        if current != generated:
            raise ReconciliationError(
                f"{MAP_NAME} is stale; update the dependency map whenever a feature changes"
            )
    else:
        _write_json(path, generated)
    return generated


def _load_capability_inventory(path: Path) -> tuple[set[str], dict[str, str]]:
    value = _read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ReconciliationError("capability inventory must use schema_version 1")
    observed = value.get("observed_capabilities")
    if not isinstance(observed, list) or any(not isinstance(item, str) for item in observed):
        raise ReconciliationError("observed_capabilities must be a list of strings")
    sources = value.get("capability_sources", {})
    if not isinstance(sources, dict) or any(
        not isinstance(key, str) or not isinstance(label, str) for key, label in sources.items()
    ):
        raise ReconciliationError("capability_sources must be a string map")
    return set(observed), sources


def audit_capabilities(
    dependency_map: dict[str, Any],
    observed: Iterable[str],
    capability_sources: dict[str, str] | None = None,
) -> dict[str, Any]:
    observed_set = set(observed)
    labels = capability_sources or {}
    rows: dict[str, Any] = {}
    blocked: list[str] = []
    degraded: list[str] = []
    for feature_id, feature in sorted(dependency_map.get("features", {}).items()):
        required = set(feature.get("required_capabilities", []))
        optional = set(feature.get("optional_capabilities", []))
        missing_required = sorted(required - observed_set)
        missing_optional = sorted(optional - observed_set)
        status = "ready"
        if missing_required:
            status = "blocked"
            blocked.append(feature_id)
        elif missing_optional:
            status = "degraded"
            degraded.append(feature_id)
        rows[feature_id] = {
            "status": status,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "missing_required_help": [labels.get(item, item) for item in missing_required],
            "missing_optional_help": [labels.get(item, item) for item in missing_optional],
        }
    return {
        "schema_version": 1,
        "ready": not blocked,
        "blocked_features": blocked,
        "degraded_features": degraded,
        "features": rows,
    }


def _tokens(feature: dict[str, Any]) -> set[str]:
    words = set(TOKEN_RE.findall(str(feature.get("summary", "")).lower()))
    words -= {"and", "the", "with", "for", "from", "when", "using", "into", "plus"}
    words |= set(feature.get("required_capabilities", []))
    words |= set(feature.get("optional_capabilities", []))
    return words


def _overlap(left: dict[str, Any], right: dict[str, Any]) -> float:
    a = _tokens(left)
    b = _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_consolidation_candidates(
    current: dict[str, Any], candidate: dict[str, Any], *, threshold: float = 0.35
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    current_features = current.get("features", {})
    candidate_features = candidate.get("features", {})
    for local_id, local in sorted(current_features.items()):
        if local.get("owner") not in {"user", "organization"}:
            continue
        for upstream_id, upstream in sorted(candidate_features.items()):
            if local_id == upstream_id:
                continue
            score = _overlap(local, upstream)
            if score >= threshold:
                results.append(
                    {
                        "local_feature": local_id,
                        "upstream_feature": upstream_id,
                        "overlap_score": round(score, 3),
                        "default": "keep-local",
                        "requires_user_decision": True,
                    }
                )
    return sorted(
        results,
        key=lambda row: (-row["overlap_score"], row["local_feature"], row["upstream_feature"]),
    )


def _dependency_signature(feature: dict[str, Any]) -> dict[str, Any]:
    return {
        "feature_dependencies": feature.get("feature_dependencies", []),
        "required_capabilities": feature.get("required_capabilities", []),
        "optional_capabilities": feature.get("optional_capabilities", []),
    }


def _readiness_fields(readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "missing_required": readiness.get("missing_required", []),
        "missing_optional": readiness.get("missing_optional", []),
        "missing_required_help": readiness.get("missing_required_help", []),
        "missing_optional_help": readiness.get("missing_optional_help", []),
    }


def plan_upgrade(
    base: dict[str, Any],
    current: dict[str, Any],
    candidate: dict[str, Any],
    *,
    observed_capabilities: Iterable[str] = (),
    capability_sources: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a proposal only. Nothing in this function mutates source or state."""
    current_features = current.get("features", {})
    candidate_features = candidate.get("features", {})
    base_features = base.get("features", {})
    capability_audit = audit_capabilities(candidate, observed_capabilities, capability_sources)
    changes: list[dict[str, Any]] = []

    for feature_id in sorted(set(current_features) | set(candidate_features)):
        old = current_features.get(feature_id)
        new = candidate_features.get(feature_id)
        original = base_features.get(feature_id)
        readiness = capability_audit["features"].get(feature_id, {})
        blocked = readiness.get("status") == "blocked"

        if old is None and new is not None:
            changes.append(
                {
                    "feature": feature_id,
                    "kind": "dependency-blocked" if blocked else "new-upstream-feature",
                    "current_version": None,
                    "candidate_version": new.get("version"),
                    "default_action": "keep-current",
                    "offered_action": "connect-required-dependency" if blocked else "install",
                    "requires_user_decision": True,
                    "rollback_checkpoint_required": True,
                    "reason": (
                        "The proposed feature needs a capability that is not currently available."
                        if blocked
                        else "A new feature is available; it is not installed automatically."
                    ),
                    **_readiness_fields(readiness),
                }
            )
            continue

        if old is not None and new is None:
            changes.append(
                {
                    "feature": feature_id,
                    "kind": "upstream-removed-or-unavailable",
                    "current_version": old.get("version"),
                    "candidate_version": None,
                    "default_action": "keep-current",
                    "offered_action": "review-removal",
                    "requires_user_decision": True,
                    "rollback_checkpoint_required": True,
                    "reason": "Your existing feature stays in place unless you approve a safe replacement or removal.",
                    "missing_required": [],
                    "missing_optional": [],
                    "missing_required_help": [],
                    "missing_optional_help": [],
                }
            )
            continue

        assert old is not None and new is not None
        changed = (
            old.get("version") != new.get("version")
            or old.get("summary") != new.get("summary")
            or _dependency_signature(old) != _dependency_signature(new)
        )
        locally_owned = old.get("owner") in {"user", "organization"}
        locally_modified = bool(old.get("local_revision", 0))

        if not changed:
            continue

        if locally_owned or locally_modified:
            kind = "local-feature-overlap"
            offered = "compare-and-reconcile"
            reason = "This feature contains local behavior, so the local version is protected by default."
        else:
            kind = "upstream-update-available"
            offered = "use-upstream-update"
            reason = "An upstream update is available, but your current behavior remains the default until you approve it."
        if blocked:
            kind = "dependency-blocked"
            offered = "connect-required-dependency"
            reason = "The proposed version needs a capability that is not currently available."

        changes.append(
            {
                "feature": feature_id,
                "kind": kind,
                "current_version": old.get("version"),
                "base_version": original.get("version") if isinstance(original, dict) else None,
                "candidate_version": new.get("version"),
                "default_action": "keep-current",
                "offered_action": offered,
                "requires_user_decision": True,
                "rollback_checkpoint_required": True,
                "reason": reason,
                **_readiness_fields(readiness),
            }
        )

    return {
        "schema_version": 1,
        "status": "proposal-only",
        "default_action": "keep-current",
        "user_in_the_loop": True,
        "automatic_apply": False,
        "automatic_local_feature_deletion": False,
        "rollback": {
            "required_before_any_change": True,
            "message": "A rollback checkpoint must be created before applying an approved change.",
        },
        "capability_audit": capability_audit,
        "changes": changes,
        "consolidation_candidates": find_consolidation_candidates(current, candidate),
    }


def render_boomer(plan: dict[str, Any]) -> str:
    lines = [
        "MIRA update review",
        "Nothing has been changed yet. Your current setup is the default.",
        "Before any approved change, MIRA creates a rollback checkpoint so you can go back.",
    ]
    changes = plan.get("changes", [])
    if not changes:
        lines.append("There are no feature changes that need your decision.")
    for change in changes:
        feature = change.get("feature", "feature")
        current = change.get("current_version") or "not installed"
        candidate = change.get("candidate_version") or "not included in the new release"
        lines.extend(
            [
                "",
                f"Feature: {feature}",
                f"What you have now: {current}.",
                f"What the new release offers: {candidate}.",
                "What MIRA recommends by default: keep what you have until you choose otherwise.",
                f"Why you are being asked: {change.get('reason', 'The behavior may change.')}",
            ]
        )
        missing_required = change.get("missing_required_help") or change.get("missing_required", [])
        missing_optional = change.get("missing_optional_help") or change.get("missing_optional", [])
        if missing_required:
            lines.append(
                "This cannot be enabled yet because a required connection or capability is missing: "
                + ", ".join(missing_required)
                + "."
            )
        if missing_optional:
            lines.append(
                "It can still work, but these optional connections are unavailable: "
                + ", ".join(missing_optional)
                + "."
            )
        lines.append("Your choices: keep mine, use the new version, or show me more detail.")

    candidates = plan.get("consolidation_candidates", [])
    if candidates:
        lines.extend(
            [
                "",
                "MIRA also found features that may overlap. Nothing will be combined or deleted automatically.",
            ]
        )
        for row in candidates:
            lines.append(
                f"{row['local_feature']} may overlap with {row['upstream_feature']}. "
                "Your existing feature remains in place unless you approve a consolidation plan."
            )
    return "\n".join(lines) + "\n"


def _snapshot(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ReconciliationError(f"invalid dependency-map snapshot: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="build or verify the durable dependency map")
    sync.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sync.add_argument("--check", action="store_true")

    register = sub.add_parser("register", help="register a new/changed feature and refresh the map")
    register.add_argument("feature_id")
    register.add_argument("--owner", choices=sorted(OWNERS), required=True)
    register.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])

    capability = sub.add_parser(
        "capability-audit", help="check required and optional runtime dependencies"
    )
    capability.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    capability.add_argument("--capabilities", required=True, type=Path)
    capability.add_argument("--boomer", action="store_true")

    plan = sub.add_parser("plan", help="produce a non-mutating three-way upgrade proposal")
    plan.add_argument("--base", required=True, type=Path)
    plan.add_argument("--current", required=True, type=Path)
    plan.add_argument("--candidate", required=True, type=Path)
    plan.add_argument("--capabilities", type=Path)
    plan.add_argument("--boomer", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "sync":
            sync_dependency_map(args.root, check=args.check)
            if args.check:
                print("Feature dependency map is current.")
            else:
                print(f"Wrote {args.root / MAP_NAME}")
            return 0

        if args.command == "register":
            register_feature(args.root, args.feature_id, args.owner)
            print(
                f"Registered {args.feature_id} as {args.owner}; refreshed {args.root / MAP_NAME}."
            )
            return 0

        if args.command == "capability-audit":
            dependency_map = build_dependency_map(args.root)
            observed, labels = _load_capability_inventory(args.capabilities)
            result = audit_capabilities(dependency_map, observed, labels)
            if args.boomer:
                pseudo_plan = {
                    "changes": [
                        {
                            "feature": feature_id,
                            "current_version": dependency_map["features"][feature_id].get("version"),
                            "candidate_version": dependency_map["features"][feature_id].get("version"),
                            "reason": "A required or optional connection is unavailable.",
                            "missing_required": row["missing_required"],
                            "missing_optional": row["missing_optional"],
                            "missing_required_help": row["missing_required_help"],
                            "missing_optional_help": row["missing_optional_help"],
                        }
                        for feature_id, row in result["features"].items()
                        if row["status"] != "ready"
                    ],
                    "consolidation_candidates": [],
                }
                print(render_boomer(pseudo_plan), end="")
            else:
                print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["ready"] else 2

        observed: set[str] = set()
        labels: dict[str, str] = {}
        if args.capabilities:
            observed, labels = _load_capability_inventory(args.capabilities)
        result = plan_upgrade(
            _snapshot(args.base),
            _snapshot(args.current),
            _snapshot(args.candidate),
            observed_capabilities=observed,
            capability_sources=labels,
        )
        if args.boomer:
            print(render_boomer(result), end="")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ReconciliationError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

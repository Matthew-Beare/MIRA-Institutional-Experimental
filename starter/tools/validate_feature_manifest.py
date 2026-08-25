#!/usr/bin/env python3
"""Validate portable Personal Ops Planner feature manifests without third-party packages."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
CROSS_WRITE_RE = re.compile(r"^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$")
SEMVER = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
VERSION_RE = re.compile(rf"^{SEMVER}$")
RANGE_TERM_RE = re.compile(rf"^(?:>=|<=|>|<|=|\^|~)?{SEMVER}$")
CONFIG_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_FIELDS = {
    "manifest_version",
    "id",
    "version",
    "summary",
    "portable",
    "delivery_status",
    "compatibility",
    "dependencies",
    "entrypoints",
    "permissions",
    "data_boundary",
    "runtime_contract",
    "config_schema",
    "tests",
}
ENTRYPOINT_FIELDS = {"references", "scripts", "schemas", "migrations"}
PERMISSION_FIELDS = {"connectors", "network_domains", "writes", "approval_required"}
RUNTIME_STATES = {"none", "deployment-local", "external-authority"}
DELIVERY_STATES = {"contract-only", "implemented"}
RUNTIME_CONTRACT_FIELDS = {
    "failure_domain",
    "required_capabilities",
    "optional_capabilities",
    "conditional_capabilities",
    "canonical_state_classes",
    "idempotency_scope",
    "on_required_failure",
    "on_optional_failure",
    "cross_module_writes",
}


def _string_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{field} must be a list of nonempty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{field} must not contain duplicates")
    return value


def _id_list(value: Any, field: str, errors: list[str], *, allow_empty: bool = True) -> list[str]:
    items = _string_list(value, field, errors)
    if not allow_empty and not items:
        errors.append(f"{field} must not be empty")
    for item in items:
        if not ID_RE.fullmatch(item):
            errors.append(f"{field} contains invalid id: {item}")
    return items


def _safe_path(value: str) -> bool:
    if "\\" in value or not value or value.startswith("/"):
        return False
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return False
    return PurePosixPath(value).as_posix() == value


def _valid_version_range(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or ",," in value:
        return False
    chunks = value.split(",")
    if any(not chunk.strip() for chunk in chunks):
        return False
    terms = [term for chunk in chunks for term in chunk.split()]
    return bool(terms) and all(RANGE_TERM_RE.fullmatch(term) for term in terms)


def _semver_key(value: str) -> tuple[tuple[int, int, int], tuple[Any, ...]]:
    without_build = value.split("+", 1)[0]
    core, separator, prerelease = without_build.partition("-")
    numbers = tuple(int(part) for part in core.split("."))
    if not separator:
        pre_key: tuple[Any, ...] = (1,)
    else:
        identifiers = tuple(
            (0, int(part)) if part.isdigit() else (1, part)
            for part in prerelease.split(".")
        )
        pre_key = (0, *identifiers)
    return numbers, pre_key


def _version_satisfies(version: str, version_range: str) -> bool:
    if not VERSION_RE.fullmatch(version) or not _valid_version_range(version_range):
        return False
    candidate = _semver_key(version)
    terms = [term for chunk in version_range.split(",") for term in chunk.split()]
    for term in terms:
        match = re.fullmatch(rf"(>=|<=|>|<|=|\^|~)?({SEMVER})", term)
        if match is None:
            return False
        operator = match.group(1) or "="
        expected_text = match.group(2)
        expected = _semver_key(expected_text)
        if operator == "=" and candidate != expected:
            return False
        if operator == ">" and not candidate > expected:
            return False
        if operator == ">=" and not candidate >= expected:
            return False
        if operator == "<" and not candidate < expected:
            return False
        if operator == "<=" and not candidate <= expected:
            return False
        if operator in {"^", "~"}:
            major, minor, patch = expected[0]
            if operator == "~":
                upper = ((major, minor + 1, 0), (1,))
            elif major:
                upper = ((major + 1, 0, 0), (1,))
            elif minor:
                upper = ((0, minor + 1, 0), (1,))
            else:
                upper = ((0, 0, patch + 1), (1,))
            if not expected <= candidate < upper:
                return False
    return True


def _schema_value_matches_type(value: Any, expected: str) -> bool:
    return {
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(float(value)),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "null": value is None,
    }.get(expected, False)


def _schema_scalar_satisfies(value: Any, node: dict[str, Any], expected: str) -> bool:
    if not _schema_value_matches_type(value, expected):
        return False
    if expected in {"integer", "number"}:
        if isinstance(node.get("minimum"), (int, float)) and value < node["minimum"]:
            return False
        if isinstance(node.get("maximum"), (int, float)) and value > node["maximum"]:
            return False
    if expected == "string":
        if isinstance(node.get("minLength"), int) and len(value) < node["minLength"]:
            return False
        if isinstance(node.get("maxLength"), int) and len(value) > node["maxLength"]:
            return False
        if isinstance(node.get("pattern"), str):
            try:
                if re.search(node["pattern"], value) is None:
                    return False
            except re.error:
                pass
    return True


def _validate_config_schema_node(node: Any, field: str, errors: list[str]) -> None:
    allowed = {
        "type", "description", "default", "enum", "const", "minimum", "maximum",
        "minLength", "maxLength", "pattern", "items", "properties", "required",
        "additionalProperties",
    }
    if not isinstance(node, dict):
        errors.append(f"{field} must be an object")
        return
    unknown = sorted(set(node) - allowed)
    if unknown:
        errors.append(f"{field} contains unsupported schema keywords: {', '.join(unknown)}")
    expected = node.get("type")
    if expected not in {"boolean", "integer", "number", "string", "array", "object", "null"}:
        errors.append(f"{field}.type is invalid")
        return
    if "description" in node and not isinstance(node["description"], str):
        errors.append(f"{field}.description must be a string")
    if "default" in node and not _schema_value_matches_type(node["default"], expected):
        errors.append(f"{field}.default does not match type {expected}")
    if "const" in node and not _schema_value_matches_type(node["const"], expected):
        errors.append(f"{field}.const does not match type {expected}")
    if "enum" in node:
        enum = node["enum"]
        if not isinstance(enum, list) or not enum:
            errors.append(f"{field}.enum must be a nonempty list")
        elif any(not _schema_value_matches_type(item, expected) for item in enum):
            errors.append(f"{field}.enum contains a value outside type {expected}")
        elif len({json.dumps(item, sort_keys=True) for item in enum}) != len(enum):
            errors.append(f"{field}.enum must not contain duplicates")
    for bound in ("minimum", "maximum"):
        if bound in node and (
            not isinstance(node[bound], (int, float))
            or isinstance(node[bound], bool)
            or not math.isfinite(float(node[bound]))
        ):
            errors.append(f"{field}.{bound} must be finite numeric")
        elif bound in node and expected not in {"integer", "number"}:
            errors.append(f"{field}.{bound} is valid only for numeric schemas")
    for bound in ("minLength", "maxLength"):
        if bound in node and (
            not isinstance(node[bound], int) or isinstance(node[bound], bool) or node[bound] < 0
        ):
            errors.append(f"{field}.{bound} must be a nonnegative integer")
        elif bound in node and expected != "string":
            errors.append(f"{field}.{bound} is valid only for string schemas")
    if (
        isinstance(node.get("minimum"), (int, float))
        and not isinstance(node.get("minimum"), bool)
        and isinstance(node.get("maximum"), (int, float))
        and not isinstance(node.get("maximum"), bool)
        and node["minimum"] > node["maximum"]
    ):
        errors.append(f"{field}.minimum must not exceed maximum")
    if (
        isinstance(node.get("minLength"), int)
        and not isinstance(node.get("minLength"), bool)
        and isinstance(node.get("maxLength"), int)
        and not isinstance(node.get("maxLength"), bool)
        and node["minLength"] > node["maxLength"]
    ):
        errors.append(f"{field}.minLength must not exceed maxLength")
    if "pattern" in node:
        try:
            re.compile(node["pattern"])
        except (TypeError, re.error):
            errors.append(f"{field}.pattern must be a valid regular expression")
        if expected != "string":
            errors.append(f"{field}.pattern is valid only for string schemas")
    for keyword in ("default", "const"):
        if (
            keyword in node
            and _schema_value_matches_type(node[keyword], expected)
            and not _schema_scalar_satisfies(node[keyword], node, expected)
        ):
            errors.append(f"{field}.{keyword} violates its declared constraints")
    if isinstance(node.get("enum"), list):
        for item in node["enum"]:
            if _schema_value_matches_type(item, expected) and not _schema_scalar_satisfies(
                item, node, expected
            ):
                errors.append(f"{field}.enum contains a value outside declared constraints")
                break
        if "const" in node and node["const"] not in node["enum"]:
            errors.append(f"{field}.const must appear in enum")
        if "default" in node and node["default"] not in node["enum"]:
            errors.append(f"{field}.default must appear in enum")
    if expected == "array":
        if "items" not in node:
            errors.append(f"{field}.items is required for array schemas")
        else:
            _validate_config_schema_node(node["items"], f"{field}.items", errors)
    elif "items" in node:
        errors.append(f"{field}.items is valid only for array schemas")
    if expected == "object":
        properties = node.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"{field}.properties must be an object")
            properties = {}
        for key, child in properties.items():
            if not isinstance(key, str) or not CONFIG_KEY_RE.fullmatch(key):
                errors.append(f"{field}.properties contains invalid key: {key!r}")
            _validate_config_schema_node(child, f"{field}.properties.{key}", errors)
        required = _string_list(node.get("required", []), f"{field}.required", errors)
        missing = sorted(set(required) - set(properties))
        if missing:
            errors.append(f"{field}.required names missing properties: {', '.join(missing)}")
        if node.get("additionalProperties") is not False:
            errors.append(f"{field}.additionalProperties must be false")
    else:
        for keyword in ("properties", "required", "additionalProperties"):
            if keyword in node:
                errors.append(f"{field}.{keyword} is valid only for object schemas")


def _is_fixture(path: Path) -> bool:
    return "fixtures" in path.parts


def validate_manifest(value: Any, check_files_from: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["manifest root must be an object"]
    missing = sorted(REQUIRED_FIELDS - set(value))
    extra = sorted(set(value) - REQUIRED_FIELDS)
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if extra:
        errors.append(f"unknown fields: {', '.join(extra)}")
    if missing:
        return errors
    if value["manifest_version"] != 3:
        errors.append("manifest_version must equal 3")
    if not isinstance(value["id"], str) or not ID_RE.fullmatch(value["id"]):
        errors.append("id must be lowercase hyphen-case")
    if not isinstance(value["version"], str) or not VERSION_RE.fullmatch(value["version"]):
        errors.append("version must be semantic version syntax")
    if (
        not isinstance(value["summary"], str)
        or not 1 <= len(value["summary"]) <= 200
        or not value["summary"].strip()
    ):
        errors.append("summary must contain 1 to 200 characters")
    if value["portable"] is not True:
        errors.append("portable must be true")
    if (
        not isinstance(value["delivery_status"], str)
        or value["delivery_status"] not in DELIVERY_STATES
    ):
        errors.append("delivery_status must be contract-only or implemented")

    compatibility = value["compatibility"]
    if not isinstance(compatibility, dict) or set(compatibility) != {"core"}:
        errors.append("compatibility must contain only a core range")
    elif not _valid_version_range(compatibility.get("core")):
        errors.append("compatibility.core must be a valid semantic-version range")

    dependencies = value["dependencies"]
    seen_dependency_ids: set[str] = set()
    if not isinstance(dependencies, list):
        errors.append("dependencies must be a list")
    else:
        for index, dependency in enumerate(dependencies):
            if not isinstance(dependency, dict) or set(dependency) != {"id", "version_range"}:
                errors.append(f"dependencies[{index}] must contain id and version_range only")
                continue
            dep_id = dependency.get("id")
            if not isinstance(dep_id, str) or not ID_RE.fullmatch(dep_id):
                errors.append(f"dependencies[{index}].id is invalid")
            elif dep_id == value.get("id"):
                errors.append("feature cannot depend on itself")
            elif dep_id in seen_dependency_ids:
                errors.append(f"duplicate feature dependency: {dep_id}")
            else:
                seen_dependency_ids.add(dep_id)
            if not _valid_version_range(dependency.get("version_range")):
                errors.append(f"dependencies[{index}].version_range is invalid")

    entrypoints = value["entrypoints"]
    referenced_paths: list[tuple[str, str]] = []
    if not isinstance(entrypoints, dict) or set(entrypoints) != ENTRYPOINT_FIELDS:
        errors.append("entrypoints must contain references, scripts, schemas, and migrations")
    else:
        for field in sorted(ENTRYPOINT_FIELDS):
            for path in _string_list(entrypoints[field], f"entrypoints.{field}", errors):
                if not _safe_path(path):
                    errors.append(f"entrypoints.{field} contains unsafe path: {path}")
                else:
                    referenced_paths.append((f"entrypoints.{field}", path))

    permissions = value["permissions"]
    if not isinstance(permissions, dict) or set(permissions) != PERMISSION_FIELDS:
        errors.append("permissions must contain connectors, network_domains, writes, and approval_required")
    else:
        for field in sorted(PERMISSION_FIELDS):
            items = _string_list(permissions[field], f"permissions.{field}", errors)
            if field == "network_domains" and any("://" in item for item in items):
                errors.append("permissions.network_domains must contain domains, not URLs")

    boundary = value["data_boundary"]
    runtime_state: str | None = None
    boundary_fields = {"source_contains_personal_data", "shared_logs_contain_personal_data", "runtime_state", "forbidden_source_data"}
    if not isinstance(boundary, dict) or set(boundary) != boundary_fields:
        errors.append("data_boundary fields do not match the portable contract")
    else:
        runtime_state = boundary.get("runtime_state") if isinstance(boundary.get("runtime_state"), str) else None
        if boundary["source_contains_personal_data"] is not False:
            errors.append("source_contains_personal_data must be false")
        if boundary["shared_logs_contain_personal_data"] is not False:
            errors.append("shared_logs_contain_personal_data must be false")
        if runtime_state not in RUNTIME_STATES:
            errors.append("data_boundary.runtime_state is invalid")
        forbidden = _string_list(boundary["forbidden_source_data"], "data_boundary.forbidden_source_data", errors)
        if not forbidden:
            errors.append("data_boundary.forbidden_source_data must not be empty")

    runtime = value["runtime_contract"]
    if not isinstance(runtime, dict) or set(runtime) != RUNTIME_CONTRACT_FIELDS:
        errors.append("runtime_contract fields do not match the isolation contract")
    else:
        domain = runtime.get("failure_domain")
        if not isinstance(domain, str) or not ID_RE.fullmatch(domain):
            errors.append("runtime_contract.failure_domain must be lowercase hyphen-case")

        required = _id_list(
            runtime.get("required_capabilities"),
            "runtime_contract.required_capabilities",
            errors,
            allow_empty=False,
        )
        optional = _id_list(
            runtime.get("optional_capabilities"),
            "runtime_contract.optional_capabilities",
            errors,
        )
        overlap = sorted(set(required) & set(optional))
        if overlap:
            errors.append(f"capabilities cannot be both required and optional: {', '.join(overlap)}")

        conditional = runtime.get("conditional_capabilities")
        if not isinstance(conditional, dict) or any(
            not isinstance(key, str)
            or not ID_RE.fullmatch(key)
            or not isinstance(rule, str)
            or not rule.strip()
            for key, rule in (conditional.items() if isinstance(conditional, dict) else [])
        ):
            errors.append("runtime_contract.conditional_capabilities must map capability ids to nonempty string rules")
        elif not set(conditional) <= set(optional):
            errors.append("conditional capabilities must be declared optional capabilities")

        state_classes = _id_list(
            runtime.get("canonical_state_classes"),
            "runtime_contract.canonical_state_classes",
            errors,
        )
        if runtime_state == "external-authority" and "structured-state-authority" not in required:
            errors.append("external-authority features must require structured-state-authority")
        if runtime_state not in {None, "none"} and not state_classes:
            errors.append("stateful features must declare canonical_state_classes")

        idempotency = runtime.get("idempotency_scope")
        if not isinstance(idempotency, str) or not idempotency.strip() or len(idempotency) > 160:
            errors.append("runtime_contract.idempotency_scope must be a nonempty string <= 160 characters")
        if runtime.get("on_required_failure") != "block-module-only":
            errors.append("runtime_contract.on_required_failure must equal block-module-only")
        if runtime.get("on_optional_failure") != "degrade-capability-and-continue":
            errors.append("runtime_contract.on_optional_failure must equal degrade-capability-and-continue")
        cross_writes = _string_list(runtime.get("cross_module_writes"), "runtime_contract.cross_module_writes", errors)
        for write in cross_writes:
            if not CROSS_WRITE_RE.fullmatch(write):
                errors.append(f"runtime_contract.cross_module_writes contains invalid target: {write}")

    config_schema = value["config_schema"]
    _validate_config_schema_node(config_schema, "config_schema", errors)
    if isinstance(config_schema, dict) and config_schema.get("type") != "object":
        errors.append("config_schema.type must be object")

    tests = _string_list(value["tests"], "tests", errors)
    if not tests:
        errors.append("tests must not be empty")
    for path in tests:
        if not _safe_path(path):
            errors.append(f"tests contains unsafe path: {path}")
        else:
            referenced_paths.append(("tests", path))
    if value.get("delivery_status") == "implemented" and not any(
        PurePosixPath(path).suffix in {".py", ".sh", ".js", ".ts"} for path in tests
    ):
        errors.append("implemented features must declare at least one executable test")
    if (
        value.get("delivery_status") == "implemented"
        and isinstance(entrypoints, dict)
        and not entrypoints.get("scripts")
    ):
        errors.append("implemented features must declare at least one script entrypoint")

    if check_files_from is not None:
        try:
            base = check_files_from.resolve(strict=True)
        except OSError as exc:
            errors.append(f"feature root cannot be resolved: {exc}")
            return errors
        for field, relative in referenced_paths:
            candidate = check_files_from / relative
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(base)
            except ValueError:
                errors.append(f"{field} path escapes feature root: {relative}")
                continue
            except OSError:
                errors.append(f"{field} references missing file: {relative}")
                continue
            if not resolved.is_file():
                errors.append(f"{field} references non-file path: {relative}")
    return errors


def validate_dependency_graph(entries: list[tuple[Path, dict[str, Any]]]) -> list[str]:
    """Validate live feature-to-feature dependencies as one acyclic install bundle."""
    errors: list[str] = []
    by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, value in entries:
        feature_id = value.get("id")
        if not isinstance(feature_id, str):
            continue
        if feature_id in by_id:
            errors.append(f"duplicate live feature id: {feature_id}")
        else:
            by_id[feature_id] = (path, value)

    graph: dict[str, list[str]] = {feature_id: [] for feature_id in by_id}
    for feature_id, (_, value) in by_id.items():
        dependencies = value.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not isinstance(dependency, dict):
                continue
            dep_id = dependency.get("id")
            if not isinstance(dep_id, str):
                continue
            if dep_id not in by_id:
                errors.append(f"feature {feature_id} depends on missing bundled feature {dep_id}")
            else:
                graph[feature_id].append(dep_id)
                dependency_version = by_id[dep_id][1].get("version")
                version_range = dependency.get("version_range")
                if (
                    isinstance(dependency_version, str)
                    and isinstance(version_range, str)
                    and not _version_satisfies(dependency_version, version_range)
                ):
                    errors.append(
                        f"feature {feature_id} requires {dep_id} {version_range}, "
                        f"but bundle provides {dependency_version}"
                    )

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle_start = stack.index(node) if node in stack else 0
            cycle = stack[cycle_start:] + [node]
            errors.append("feature dependency cycle: " + " -> ".join(cycle))
            return
        visiting.add(node)
        stack.append(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for feature_id in sorted(graph):
        visit(feature_id)
    return errors


def default_manifests() -> list[Path]:
    return sorted([*ROOT.glob("features/*/feature.json"), *ROOT.glob("fixtures/features/*.feature.json")])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="*", type=Path)
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Require every declared live-feature entrypoint and test path to exist beside the manifest. Synthetic fixtures are schema-checked only.",
    )
    args = parser.parse_args()
    manifests = args.manifests or default_manifests()
    if not manifests:
        parser.error("no feature manifests found")

    failed = False
    parsed: list[tuple[Path, dict[str, Any]]] = []
    for path in manifests:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR {path}: {exc}")
            failed = True
            continue
        parsed.append((path, value))
        check_from = path.parent if args.check_files and not _is_fixture(path) else None
        errors = validate_manifest(value, check_from)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR {path}: {error}")
        else:
            print(f"OK {path}")

    live_entries = [(path, value) for path, value in parsed if not _is_fixture(path)]
    graph_errors = validate_dependency_graph(live_entries)
    if graph_errors:
        failed = True
        for error in graph_errors:
            print(f"ERROR feature graph: {error}")
    elif live_entries:
        print("OK live feature dependency graph")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

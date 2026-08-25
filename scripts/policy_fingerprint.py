#!/usr/bin/env python3
"""Compute the stable deployed-skill fingerprint stored inside Git.

Fingerprint v5 hashes every deployable skill file except executable tests, bytecode,
and the explicitly deployment-local private authority map. Each relative path and
deterministic Git blob identity is included. Agent metadata is reduced to its supported
semantic fields before hashing because the installer rewrites YAML quoting, line folds,
asset-path prefixes, and provider-owned product declarations during materialization.
The source icon digest is pinned separately because the installer replaces the SVG with
a provider-rendered asset; source validation remains strict while deployed comparison
uses that retained source digest instead of the rewritten SVG bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DEPLOYMENT_LOCAL_FILES = {"references/deployment-authorities.md"}
AGENT_METADATA_PATH = "agents/openai.yaml"
AGENT_ICON_PATH = "assets/icon.svg"
AGENT_ICON_DIGEST_PATH = "assets/icon.source.sha256"
AGENT_INTERFACE_KEYS = (
    "display_name",
    "short_description",
    "icon_small",
    "icon_large",
    "brand_color",
    "default_prompt",
)


def policy_files(skill_root: Path) -> list[Path]:
    if skill_root.is_symlink():
        raise ValueError(f"skill root must not be a symlink: {skill_root}")
    skill_root = skill_root.resolve(strict=True)
    if not skill_root.is_dir():
        raise NotADirectoryError(f"skill root is not a directory: {skill_root}")
    if not (skill_root / "SKILL.md").is_file():
        raise FileNotFoundError(f"missing policy source: {skill_root / 'SKILL.md'}")
    files: list[Path] = []
    for path in skill_root.rglob("*"):
        relative = path.relative_to(skill_root).as_posix()
        if path.is_symlink():
            raise ValueError(f"policy source must not be a symlink: {path}")
        if not path.is_file():
            continue
        if (
            "__pycache__" in path.parts
            or path.suffix == ".pyc"
            or relative in DEPLOYMENT_LOCAL_FILES
            or (path.suffix == ".py" and path.name.startswith("test_"))
        ):
            continue
        try:
            path.resolve(strict=True).relative_to(skill_root)
        except ValueError as exc:
            raise ValueError(f"policy source escapes skill root: {path}") from exc
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(skill_root).as_posix())


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _yaml_section_scalars(text: str, section: str) -> dict[str, str]:
    lines = text.splitlines()
    try:
        start = lines.index(f"{section}:") + 1
    except ValueError as exc:
        raise ValueError(f"agent metadata lacks {section!r} section") from exc
    values: dict[str, str] = {}
    current: str | None = None
    for line in lines[start:]:
        if line and not line[0].isspace():
            break
        match = re.match(r"^  ([a-z][a-z0-9_]*):(?:\s*(.*))?$", line)
        if match:
            current = match.group(1)
            values[current] = (match.group(2) or "").strip()
            continue
        continuation = re.match(r"^\s{4,}(\S.*)$", line)
        if current and continuation and not continuation.group(1).startswith("-"):
            values[current] = f"{values[current]} {continuation.group(1).strip()}".strip()
    return values


def _yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid double-quoted agent metadata scalar") from exc
        if not isinstance(decoded, str):
            raise ValueError("agent metadata scalar must be text")
        return decoded
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def canonical_agent_metadata(content: bytes) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("agent metadata must be UTF-8") from exc
    interface = _yaml_section_scalars(text, "interface")
    missing = [key for key in AGENT_INTERFACE_KEYS if not interface.get(key)]
    if missing:
        raise ValueError(f"agent metadata lacks interface fields: {', '.join(missing)}")
    policy = _yaml_section_scalars(text, "policy")
    allow = _yaml_scalar(policy.get("allow_implicit_invocation", "")).lower()
    if allow not in {"true", "false"}:
        raise ValueError("agent metadata has invalid allow_implicit_invocation")
    canonical_interface = {
        key: " ".join(_yaml_scalar(interface[key]).split())
        for key in AGENT_INTERFACE_KEYS
    }
    for key in ("icon_small", "icon_large"):
        canonical_interface[key] = canonical_interface[key].removeprefix("./")
    payload = {
        "interface": canonical_interface,
        "policy": {"allow_implicit_invocation": allow == "true"},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _is_materialized_agent_metadata(content: bytes) -> bool:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("agent metadata must be UTF-8") from exc
    policy = _yaml_section_scalars(text, "policy")
    return "products" in policy


def _icon_source_digest(skill_root: Path) -> str:
    path = skill_root / AGENT_ICON_DIGEST_PATH
    value = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"invalid source icon digest: {path}")
    return value


def compute(skill_root: Path) -> str:
    if skill_root.is_symlink():
        raise ValueError(f"skill root must not be a symlink: {skill_root}")
    normalized_root = skill_root.resolve(strict=True)
    metadata_content = (normalized_root / AGENT_METADATA_PATH).read_bytes()
    canonical_metadata = canonical_agent_metadata(metadata_content)
    materialized = _is_materialized_agent_metadata(metadata_content)
    source_icon_digest = _icon_source_digest(normalized_root)
    digest = hashlib.sha256()
    for path in policy_files(normalized_root):
        relative_text = path.relative_to(normalized_root).as_posix()
        relative = relative_text.encode("utf-8")
        content = path.read_bytes()
        if relative_text == AGENT_METADATA_PATH:
            content = canonical_metadata
        elif relative_text == AGENT_ICON_PATH:
            actual = hashlib.sha256(content).hexdigest()
            if not materialized and actual != source_icon_digest:
                raise ValueError(
                    f"source icon digest mismatch: expected {source_icon_digest}, got {actual}"
                )
            content = f"source-icon-sha256:{source_icon_digest}\n".encode("ascii")
        blob_identity = git_blob_sha(content).encode("ascii")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(blob_identity)
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path)
    args = parser.parse_args()
    try:
        print(compute(args.skill_root))
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

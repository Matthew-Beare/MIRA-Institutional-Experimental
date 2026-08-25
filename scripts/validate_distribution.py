#!/usr/bin/env python3
"""Validate an immutable generated M.I.R.R.O.R. distribution tree and its channel contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path("DEPLOYMENT_CHANNEL.json")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
CHANNELS: dict[str, dict[str, Any]] = {
    "public-experimental": {
        "repository": "Matthew-Beare/MIRA-Public-Experimental",
        "visibility": "public",
        "template": True,
        "title": "M.I.R.R.O.R. Personal-Experimental",
    },
    "institutional-experimental": {
        "repository": "Matthew-Beare/MIRA-Institutional-Experimental",
        "visibility": "public",
        "template": True,
        "title": "M.I.R.R.O.R. Institutional-Experimental",
    },
}
REQUIRED_FILES = {
    ".github/workflows/ci.yml",
    ".gitignore",
    "DEPLOYMENT_CHANNEL.json",
    "LICENSE",
    "README.md",
    "docs/BRANDING.md",
    "privacy/starter-blocklist.txt",
    "scripts/audit_public_source.py",
    "scripts/audit_starter_privacy.py",
    "scripts/validate_distribution.py",
    "starter/QUICK_START.md",
    "starter/SHARED_FEATURE_WORKFLOW.md",
    "starter/INSTALL.md",
    "starter/PROVIDER_ONBOARDING.md",
    "starter/ENTERPRISE_PILOT.md",
    "starter/platform-capabilities.json",
    "starter/tools/provider_capability_router.py",
}
FORBIDDEN_ROOTS = {"distribution", "policy", "project", "skill", "tests"}


def _ignored_worktree_path(relative: Path) -> bool:
    return (
        bool(relative.parts)
        and relative.parts[0] == ".git"
        or "__pycache__" in relative.parts
        or relative.suffix == ".pyc"
    )


def _load_manifest(root: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid {MANIFEST_PATH}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{MANIFEST_PATH} must contain an object")
        return {}
    return value


def _payload_hashes(root: Path, errors: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if _ignored_worktree_path(relative):
            continue
        if path.is_symlink():
            errors.append(f"symlink is forbidden: {relative.as_posix()}")
        elif path.is_file() and relative != MANIFEST_PATH:
            hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def validate(
    root: Path,
    *,
    expected_repository: str | None = None,
    expected_channel: str | None = None,
    expected_source_revision: str | None = None,
) -> list[str]:
    """Return deterministic validation errors for one generated distribution."""
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f"distribution root is not a directory: {root}"]

    manifest = _load_manifest(root, errors)
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not _ignored_worktree_path(path.relative_to(root))
    }
    for relative in sorted(REQUIRED_FILES - actual_files):
        errors.append(f"missing required distribution file: {relative}")

    present_roots = {Path(relative).parts[0] for relative in actual_files}
    for name in sorted(FORBIDDEN_ROOTS & present_roots):
        errors.append(f"forbidden canonical root present: {name}")

    channel_id = manifest.get("channel_id")
    contract = CHANNELS.get(channel_id)
    if contract is None:
        errors.append(f"unsupported channel_id: {channel_id!r}")
        contract = {}
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must equal 1")
    if manifest.get("product_name") != "M.I.R.R.O.R.":
        errors.append("manifest product_name must equal M.I.R.R.O.R.")
    if manifest.get("repository") != contract.get("repository"):
        errors.append("manifest repository does not match channel")
    if manifest.get("required_visibility") != contract.get("visibility"):
        errors.append("manifest visibility does not match channel")
    if manifest.get("template_repository") is not contract.get("template"):
        errors.append("manifest template flag does not match channel")
    if manifest.get("canonical_source_repository") != "Matthew-Beare/MIRA-Personal-Production":
        errors.append("manifest canonical source repository is incorrect")
    if not REVISION_RE.fullmatch(str(manifest.get("canonical_source_revision", ""))):
        errors.append("manifest canonical source revision is not a full lowercase commit SHA")
    if manifest.get("generated_distribution") is not True:
        errors.append("distribution must declare generated_distribution=true")
    if manifest.get("manual_edits_allowed") is not False:
        errors.append("distribution must forbid manual drift")
    if manifest.get("contains_runtime_state") is not False:
        errors.append("distribution must declare contains_runtime_state=false")
    if manifest.get("regulated_data_allowed_in_git") is not False:
        errors.append("distribution must forbid regulated data in Git")

    if expected_repository is not None and manifest.get("repository") != expected_repository:
        errors.append(
            f"repository readback mismatch: expected {expected_repository}, got {manifest.get('repository')}"
        )
    if expected_channel is not None and channel_id != expected_channel:
        errors.append(f"channel readback mismatch: expected {expected_channel}, got {channel_id}")
    if (
        expected_source_revision is not None
        and manifest.get("canonical_source_revision") != expected_source_revision
    ):
        errors.append("canonical source revision readback mismatch")

    expected_hashes = manifest.get("payload_sha256")
    actual_hashes = _payload_hashes(root, errors)
    if not isinstance(expected_hashes, dict):
        errors.append("manifest payload_sha256 must be an object")
    elif expected_hashes != actual_hashes:
        errors.append("distribution payload differs from its immutable hash manifest")

    readme_path = root / "README.md"
    provider_path = root / "starter/PROVIDER_ONBOARDING.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    providers = provider_path.read_text(encoding="utf-8") if provider_path.is_file() else ""
    expected_title = contract.get("title")
    if expected_title and expected_title not in readme:
        errors.append("channel README title is incorrect")
    for term in ("Google Workspace", "Microsoft 365", "OneDrive", "Apple/iCloud", "Claude"):
        if term.lower() not in providers.lower():
            errors.append(f"provider onboarding lacks: {term}")
    if channel_id == "institutional-experimental":
        for term in ("no PHI/PII", "ATO", "approved runtime", "Do **not** put PHI", "generic or synthetic personas"):
            if term.lower() not in readme.lower():
                errors.append(f"institutional boundary lacks: {term}")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--repository")
    parser.add_argument("--channel")
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    errors = validate(
        args.root,
        expected_repository=args.repository,
        expected_channel=args.channel,
        expected_source_revision=args.source_revision,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Distribution contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

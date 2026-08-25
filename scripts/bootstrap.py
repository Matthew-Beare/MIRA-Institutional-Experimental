#!/usr/bin/env python3
"""Render a generic Project instructions template from a flat JSON config."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Mapping


TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
CONFIG_KEYS = frozenset({
    "AI_RUNTIME", "APPOINTMENT_RECONCILIATION", "APPOINTMENT_REMINDER_PROFILE",
    "ASSET_ACQUISITION", "AUTHORITY_REGISTRY", "AUTO_VERSIONING",
    "BRIEF_NOTIFICATION_MODE", "BRIEF_SERVICE", "BRIEF_SLOTS",
    "CALENDAR_PROJECTION", "CALENDAR_PROVIDER", "CANONICAL_CLOCK_POLICY",
    "CAPABILITY_DISCOVERY", "CHAT_INTAKE_SCOPE", "CONTEXT_MODE_NAMES",
    "DATA_CLASSIFICATION", "DEPLOYMENT_LANE", "DRIVE_ROOT", "EMAIL_PROVIDER", "EMAIL_RETENTION_POLICY",
    "ESCALATION_STYLE", "FAILURE_DOMAIN_POLICY", "FEATURE_SHARING_POLICY",
    "GITHUB_REPO", "HOME_MODE_RULE", "HOUSEHOLD_MODEL", "INTEGRATION_REGISTRY",
    "INTERVIEW_LEDGER", "MEAL_PLANNING", "MERGE_POLICY", "MODE_MODEL",
    "ORDER_LIFECYCLE_SERVICE", "ORDER_NOTIFICATION_MODE", "ORDER_UPDATE_SLOTS",
    "ORGANIZATION_APPROVAL",
    "OUTPUT_STYLE", "PAYMENT_RECONCILIATION", "PERSONAL_BRANCH_MODEL",
    "PROFILE_MODEL", "PROVIDER_CAPABILITY_PROFILE", "PROVIDER_SPECIALTY_ENRICHMENT", "RECEIPT_SCOPE",
    "RECOVERY_SNAPSHOT_POLICY",
    "RECIPE_LIBRARY_MODE", "RECIPE_LIBRARY_SERVICE", "REIMBURSEMENT_TRACKING",
    "REPOSITORY_VISIBILITY", "ROAD_MODE_RULE", "ROUTE_MILEAGE_MODEL",
    "SECONDARY_STATE_STORE", "SHARED_STATE_SCOPE", "SKILL_NAME", "STATE_STORE",
    "SOURCE_CONTROL_MODE", "SYSTEM_NAME", "TIMEZONE", "UPSTREAM_PROVENANCE",
})


def load_config(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration must be a JSON object")
    config: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Z0-9_]+", key):
            raise ValueError(f"invalid configuration key: {key!r}")
        if isinstance(value, (dict, list)) or value is None:
            raise ValueError(f"configuration value for {key} must be a scalar")
        config[key] = str(value)
    missing = sorted(CONFIG_KEYS - set(config))
    unexpected = sorted(set(config) - CONFIG_KEYS)
    if missing:
        raise ValueError("configuration is missing supported keys: " + ", ".join(missing))
    if unexpected:
        raise ValueError("configuration has unsupported keys: " + ", ".join(unexpected))
    return config


def render(template: str, config: Mapping[str, str]) -> str:
    required = set(TOKEN_RE.findall(template))
    missing = sorted(key for key in required if key not in config or not config[key].strip())
    if missing:
        raise ValueError("missing configuration keys: " + ", ".join(missing))

    rendered = TOKEN_RE.sub(lambda match: config[match.group(1)], template)
    leftovers = sorted(set(TOKEN_RE.findall(rendered)))
    if leftovers:
        raise ValueError("unresolved template keys: " + ", ".join(leftovers))
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="validate rendering without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    temp_path: Path | None = None
    try:
        config = load_config(args.config)
        rendered = render(args.template.read_text(encoding="utf-8"), config)

        if args.check:
            print("Starter configuration and template are valid.")
            return 0
        if args.output is None:
            raise ValueError("--output is required unless --check is used")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=args.output.parent,
            prefix=f".{args.output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, args.output)
        temp_path = None
        print(f"Rendered {args.output}")
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())

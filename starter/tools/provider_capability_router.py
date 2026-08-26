#!/usr/bin/env python3
"""Resolve onboarding readiness from observed capabilities without assuming provider parity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SOURCE_MODES = {"user-git", "organization-git", "managed-central", "none"}
ENVIRONMENTS = {"personal", "enterprise", "regulated"}
DATA_CLASSIFICATIONS = {"public", "personal", "non-sensitive-work", "regulated-sensitive"}
CAPABILITY_KEYS = {
    "source_read",
    "source_write",
    "source_remote_readback",
    "managed_release_read",
    "structured_state_read",
    "structured_state_write",
    "structured_state_readback",
    "structured_state_transactions",
    "structured_state_migration_export",
    "evidence_read",
    "evidence_write",
    "evidence_readback",
    "evidence_content_hash",
    "email_read",
    "calendar_read",
    "calendar_write",
    "calendar_readback",
    "scheduled_dispatch",
    "canonical_clock_gate",
    "observed_scheduled_firing",
    "client_api_read",
    "client_api_command",
    "client_sync",
    "local_agent",
    "visual_notification",
    "spoken_notification",
    "barcode_decode",
    "camera_capture",
    "local_model",
    "hosted_model",
    "strong_hosted_model",
    "private_overlay_network",
    "authenticated_https_api",
}
REQUEST_KEYS = {
    "stateful_modules",
    "retained_evidence",
    "email_evidence",
    "calendar_projection",
    "scheduled_dispatch",
}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_bool(mapping: dict[str, Any], key: str) -> bool:
    value = mapping.get(key, False)
    if not isinstance(value, bool):
        raise ValueError(f"capability {key} must be boolean")
    return value


def evaluate(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic readiness decision for one observed deployment plan."""

    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    runtime_id = str(plan.get("runtime_id", "")).strip()
    storage_id = str(plan.get("storage_id", "")).strip()
    source_mode = str(plan.get("source_mode", "")).strip()
    environment = str(plan.get("environment", "")).strip()
    classification = str(plan.get("data_classification", "")).strip()
    if not runtime_id or not storage_id:
        raise ValueError("runtime_id and storage_id are required")
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"unsupported source_mode: {source_mode}")
    if environment not in ENVIRONMENTS:
        raise ValueError(f"unsupported environment: {environment}")
    if classification not in DATA_CLASSIFICATIONS:
        raise ValueError(f"unsupported data_classification: {classification}")

    requested = _require_mapping(plan.get("requested", {}), "requested")
    unknown_requests = sorted(set(requested) - REQUEST_KEYS)
    if unknown_requests:
        raise ValueError("unsupported requested capabilities: " + ", ".join(unknown_requests))
    capabilities = _require_mapping(plan.get("capabilities", {}), "capabilities")
    unknown = sorted(set(capabilities) - CAPABILITY_KEYS)
    if unknown:
        raise ValueError("unsupported capabilities: " + ", ".join(unknown))
    observed = {key: _require_bool(capabilities, key) for key in CAPABILITY_KEYS}
    approved = plan.get("organization_approved_for_data", False)
    if not isinstance(approved, bool):
        raise ValueError("organization_approved_for_data must be boolean")
    approval_reference = str(plan.get("organization_approval_reference", "")).strip()

    blocks: list[str] = []
    degradations: list[str] = []
    next_actions: list[str] = []

    if classification == "regulated-sensitive" and not approved:
        blocks.append("runtime-or-storage-not-approved-for-regulated-sensitive-data")
        next_actions.append("obtain-and-record-organization-approval-for-the-exact-runtime-storage-data-class-and-actions")
    elif classification == "regulated-sensitive" and not approval_reference:
        blocks.append("organization-approval-evidence-missing")
        next_actions.append("record-current-organization-approval-evidence-reference")

    if source_mode in {"user-git", "organization-git"}:
        missing_source = [
            key for key in ("source_read", "source_write", "source_remote_readback")
            if not observed[key]
        ]
        if missing_source:
            degradations.append("durable-personal-source-mutation-unavailable")
            next_actions.append("verify-source-read-write-and-remote-readback")
    elif source_mode == "managed-central":
        if not observed["managed_release_read"]:
            blocks.append("managed-release-not-readable")
            next_actions.append("grant-read-access-to-an-approved-pinned-release")
        if not observed["source_write"]:
            degradations.append("personal-policy-changes-require-managed-change-process")
        elif not observed["source_remote_readback"]:
            degradations.append("managed-source-write-readback-unavailable")
            next_actions.append("verify-managed-source-remote-readback")
    else:
        degradations.append("no-durable-source-lineage-for-personal-changes")
        next_actions.append("select-approved-source-or-accept-manual-portable-mode")

    stateful = requested.get("stateful_modules", True)
    if not isinstance(stateful, bool):
        raise ValueError("requested.stateful_modules must be boolean")
    if stateful:
        missing_state = [
            key for key in (
                "structured_state_read",
                "structured_state_write",
                "structured_state_readback",
            )
            if not observed[key]
        ]
        if missing_state:
            blocks.append("canonical-structured-state-contract-incomplete")
            next_actions.append("verify-structured-state-read-write-and-readback")

    evidence = requested.get("retained_evidence", False)
    if not isinstance(evidence, bool):
        raise ValueError("requested.retained_evidence must be boolean")
    if evidence:
        missing_evidence = [
            key for key in ("evidence_read", "evidence_write", "evidence_readback")
            if not observed[key]
        ]
        if missing_evidence:
            degradations.append("retained-evidence-path-unavailable")
            next_actions.append("verify-evidence-read-write-and-readback-or-disable-retained-evidence-modules")

    email_evidence = requested.get("email_evidence", False)
    if not isinstance(email_evidence, bool):
        raise ValueError("requested.email_evidence must be boolean")
    if email_evidence and not observed["email_read"]:
        degradations.append("email-evidence-adapter-unavailable")
        next_actions.append("verify-approved-email-read-or-disable-email-evidence-modules")

    calendar_projection = requested.get("calendar_projection", False)
    if not isinstance(calendar_projection, bool):
        raise ValueError("requested.calendar_projection must be boolean")
    if calendar_projection and not all(
        observed[key] for key in ("calendar_read", "calendar_write", "calendar_readback")
    ):
        degradations.append("calendar-projection-contract-incomplete")
        next_actions.append("verify-calendar-read-write-and-readback-or-disable-calendar-projection")

    scheduling = requested.get("scheduled_dispatch", False)
    if not isinstance(scheduling, bool):
        raise ValueError("requested.scheduled_dispatch must be boolean")
    if scheduling:
        if not observed["scheduled_dispatch"] or not observed["canonical_clock_gate"]:
            blocks.append("scheduled-dispatch-contract-incomplete")
            next_actions.append("verify-scheduler-and-canonical-clock-gate")
        elif not observed["observed_scheduled_firing"]:
            degradations.append("scheduled-dispatch-awaiting-observed-firing")
            next_actions.append("observe-one-real-scheduled-firing-and-read-back-the-run-record")

    blocks = list(dict.fromkeys(blocks))
    degradations = list(dict.fromkeys(degradations))
    next_actions = list(dict.fromkeys(next_actions))
    decision = "blocked" if blocks else "degraded" if degradations else "ready"
    return {
        "decision": decision,
        "runtime_id": runtime_id,
        "storage_id": storage_id,
        "source_mode": source_mode,
        "environment": environment,
        "data_classification": classification,
        "provider_name_used_as_proof": False,
        "organization_approval_reference_present": bool(approval_reference),
        "blocks": blocks,
        "degradations": degradations,
        "next_actions": next_actions,
        "verified_claims": {
            "regulated_data_allowed": classification != "regulated-sensitive" or approved,
            "durable_source_write": (
                source_mode in {"user-git", "organization-git"}
                and all(observed[key] for key in ("source_read", "source_write", "source_remote_readback"))
            ) or (
                source_mode == "managed-central"
                and all(observed[key] for key in ("managed_release_read", "source_write", "source_remote_readback"))
            ),
            "structured_state_write": not stateful
            or all(observed[key] for key in (
                "structured_state_read",
                "structured_state_write",
                "structured_state_readback",
            )),
            "retained_evidence_write": not evidence
            or all(observed[key] for key in ("evidence_read", "evidence_write", "evidence_readback")),
            "email_evidence_read": not email_evidence or observed["email_read"],
            "calendar_projection_write": not calendar_projection
            or all(observed[key] for key in ("calendar_read", "calendar_write", "calendar_readback")),
            "scheduled_delivery": not scheduling
            or all(observed[key] for key in (
                "scheduled_dispatch",
                "canonical_clock_gate",
                "observed_scheduled_firing",
            )),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="JSON file containing observed onboarding capabilities")
    args = parser.parse_args()
    try:
        raw = json.loads(args.plan.read_text(encoding="utf-8"))
        print(json.dumps(evaluate(raw), indent=2, sort_keys=True))
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

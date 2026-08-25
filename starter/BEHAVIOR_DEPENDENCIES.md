# M.I.R.R.O.R. Behavior Dependency Model

M.I.R.R.O.R. maintains two related dependency graphs because a packaged feature and an operational behavior are not the same thing.

- `features.lock.json` plus `feature-dependency-map.json` track installable/customizable feature packages, ownership, upstream lineage, local revisions, and package capabilities.
- `behavior-dependencies.json` tracks **every cataloged operational behavior or gesture**, including behavior that predates the portable feature-package model.

The canonical repository currently has 123 entries in the forensic feature catalog. Canonical CI requires exactly 123 corresponding behavior dependency assignments. Adding a new cataloged behavior without adding its dependency assignment is a release failure.

## What one behavior dependency record means

Each behavior selects one or more reusable dependency profiles. A profile can declare:

- required capabilities;
- optional capabilities;
- required canonical authorities;
- optional authorities;
- required behavior-to-behavior dependencies; and
- optional behavior-to-behavior dependencies.

Required dependency failure blocks **only that behavior and anything that explicitly depends on it**. Optional dependency failure degrades only the optional path. The checker never installs a connector, creates an authority, enables a behavior, or changes source.

## Behavior requirements versus user integrations

The dependency database describes what a behavior requires. A deployment's Integration Registry describes what that particular user currently has.

Connecting or disconnecting an integration does not normally rewrite `behavior-dependencies.json`. Instead MIRA refreshes the Integration Registry and recalculates behavior readiness. Only **verified capabilities** count. An app can be connected while still lacking the permission, action, history coverage, or readback needed by the behavior.

`tools/integration_dependency_router.py` bridges those two layers. It accepts an observed Integration Registry snapshot, contributes verified capabilities from connected integrations to the dependency environment, runs the existing behavior checker, attaches user-facing remediation for missing required dependencies, and proposes goal-matched workflows from `integration-workflow-catalog.json`.

Provider labels are never proof. A Google connection does not automatically prove Drive creation or Sheets write/readback. A smartwatch connection does not automatically prove wearable data can be read. A financial connection does not prove complete transaction history or a requested account scope.

## Receipt example

Catalog behavior `c-06`, receipt intake from email, files, photos/screenshots, and manual entry, explicitly depends on:

- the Purchase & Receipt Archive;
- structured-state read, write, and readback;
- an evidence/document store with read, write, and readback; and
- the installed policy source.

Email intake, file import, image intake, and OCR candidate extraction are optional ingestion paths. Therefore a user can retain the receipt workflow while losing only the unavailable adapter. Missing Gmail should not destroy manual receipt entry. Missing the canonical Purchase & Receipt Archive, however, blocks the receipt mutation because there is nowhere authoritative to write it.

## Scheduling example

Catalog behavior `a-01`, recurring brief scheduling, explicitly depends on:

- Ops Status Register;
- Run Log;
- the deployment scheduler;
- structured-state read, write, and readback;
- scheduled-dispatch capability;
- the canonical timezone-aware clock gate; and
- the installed source/policy lineage.

Observed evidence from a real scheduled firing is an additional optional readiness signal. It can keep the behavior in a degraded/unproven state without pretending the scheduler never existed.

## Runtime preflight

Before an enabled behavior executes, MIRA builds an observed environment containing:

- enabled behavior IDs;
- behavior implementations actually available in this deployment;
- verified capabilities; and
- observed canonical authorities.

`tools/behavior_dependency_check.py` resolves the provider-neutral dependency graph and returns `ready`, `degraded`, or `blocked` per enabled behavior. When Integration Registry evidence is available, `tools/integration_dependency_router.py` constructs that environment from verified integrations and adds the nontechnical setup/recommendation layer.

A required dependency failure produces a user-facing explanation such as:

> Receipt intake is not ready yet. It needs the selected evidence/document store. Nothing will be changed automatically, and unrelated workflows stay as they are. Do you need help setting this up?

An optional dependency failure produces a narrower explanation such as:

> Order tracking can still run, but automatic mailbox evidence is unavailable. The rest of the workflow stays available.

Do not expose internal graph terminology unless the user requests technical detail.

## Boomer-safe dependency remediation

A dependency check is diagnostic, not permission to repair the environment automatically. When a feature the user wants is blocked:

1. identify the affected feature and missing dependency in ordinary language;
2. state that unrelated features still work and nothing changes automatically;
3. ask exactly **Do you need help setting this up?**;
4. if yes, provide no more than five visible setup steps, prefer an already connected suitable provider, request only the minimum necessary permission, and stop when the user must complete an external action;
5. after setup, verify the exact required read/write/readback or other capability proof, update the Integration Registry, and rerun dependency readiness for the affected behavior and its dependents only.

If the user declines help, use a short closure rather than repeatedly prompting:

> No problem. This feature will stay unavailable until the required dependency is connected or configured. Tell me when it is ready and I will check it again.

Never mark the dependency fixed merely because a provider appears in a connected-app list. Never silently select a different account or create a duplicate provider resource just to clear a dependency check.

If the user approves a lasting source change, use the normal feature-reconciliation checkpoint and rollback contract before changing anything. If the user approves a provider/account setup action, use the provider's normal bounded permission and readback gate.

## Integration-to-goal workflow discovery

Connected integrations can reveal useful capabilities, but they do not define the user's goals. MIRA may suggest a workflow only when a verified capability intersects with an explicit active user goal.

Examples:

- verified wearable data + stated fitness/activity goal → offer evidence-backed routine/accountability support;
- verified financial read access + stated budget/saving goal → offer spending/reconciliation support;
- verified mailbox read + stated receipt/order/admin goal → offer evidence-assisted intake and reconciliation;
- verified Calendar access + stated appointment/scheduling goal → offer reconciliation and reminder projection;
- verified Drive/OneDrive/SharePoint evidence write/readback + stated document/receipt/manual goal → offer evidence retention;
- barcode/QR scan capability + stated asset/inventory goal → offer scan-to-identify/manual-link workflow.

A recommendation is an offer, not activation. `integration-workflow-catalog.json` limits each review to a small set of high-value suggestions, records required versus optional capabilities, and leaves activation behind explicit user confirmation. If the runtime cannot enumerate all connected plugins, MIRA uses the existing Integration Registry plus bounded relevant probes and must not claim a global scan occurred.

## Behavior-to-behavior dependencies

Higher-level services can depend on lower-level behaviors. Examples include:

- receipt archive service → receipt intake + searchable purchase history + receipt taxonomy;
- orders/shipments service → evidence ingestion + lifecycle reconciliation + exception states + active-shipment output;
- briefs/action digest → scheduling + canonical clock + Run Log + failure isolation;
- assets/maintenance/manuals → stable asset identity + purchase evidence + bidirectional queries + identifiers + evidence + manuals + verified specifications.

This lets MIRA determine whether a service is blocked because a provider is unavailable or because one of its own required behaviors is absent/broken.

## Forward-development contract

Every durable new behavior must follow this order:

1. define the behavior in the feature catalog or portable feature manifest;
2. assign dependency profiles and any behavior-to-behavior edges;
3. declare required versus optional dependencies deliberately;
4. add/update direct tests;
5. run the behavior dependency audit;
6. run feature/package dependency checks when the behavior belongs to an installable feature;
7. run repository/privacy/distribution CI; and
8. only then merge and promote.

A newly connected integration normally updates runtime capability state, not source. If it exposes a reusable capability or workflow contract that is not yet represented in source, that new source behavior must go through the same branch, test, dependency, privacy, CI, and promotion gates.

Canonical CI cross-checks the forensic feature catalog against `behavior-dependencies.json`. Distribution CI validates the portable dependency database even though the private/reference forensic catalog is not shipped as a distribution authority.

## Standalone application use

A standalone MIRA application can use the same dependency checker without GitHub-specific UI logic. The app supplies its observed capabilities, authorities, installed behaviors, and enabled behaviors; the checker returns the readiness graph. A Linux agent, desktop app, cloud runtime, or institutional deployment can therefore share one dependency contract while exposing different actual capabilities.

The checker and integration router remain non-mutating. UI layers may offer approved setup actions, but dependency detection and workflow recommendation themselves never grant permission to perform them.

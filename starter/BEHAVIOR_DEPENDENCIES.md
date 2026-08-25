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

Before an enabled behavior executes, MIRA should build an observed environment containing:

- enabled behavior IDs;
- behavior implementations actually available in this deployment;
- observed capabilities; and
- observed canonical authorities.

`tools/behavior_dependency_check.py` resolves the dependency graph and returns `ready`, `degraded`, or `blocked` per enabled behavior.

A required dependency failure produces a user-facing explanation such as:

> Receipt intake is not ready yet. It needs the selected evidence/document store. Nothing will be changed automatically, and unrelated workflows stay as they are.

An optional dependency failure produces a narrower explanation such as:

> Order tracking can still run, but automatic mailbox evidence is unavailable. The rest of the workflow stays available.

Do not expose internal graph terminology unless the user requests technical detail.

## User-in-the-loop dependency remediation

A dependency check is diagnostic, not permission to repair the environment automatically.

When a missing dependency could be added, MIRA should explain:

1. what behavior is affected;
2. what is missing in plain language;
3. what still works without it;
4. what connecting or creating the dependency would change; and
5. whether the remediation changes durable source or mutable provider state.

If the user approves a lasting source change, use the normal feature-reconciliation checkpoint and rollback contract before changing anything. If the user declines, preserve the existing behavior and state.

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

Canonical CI cross-checks the forensic feature catalog against `behavior-dependencies.json`. Distribution CI validates the portable dependency database even though the private/reference forensic catalog is not shipped as a distribution authority.

## Standalone application use

A standalone MIRA application can use the same dependency checker without GitHub-specific UI logic. The app supplies its observed capabilities, authorities, installed behaviors, and enabled behaviors; the checker returns the readiness graph. A Linux agent, desktop app, cloud runtime, or institutional deployment can therefore share one dependency contract while exposing different actual capabilities.

The checker remains non-mutating. UI layers may offer approved setup actions, but dependency detection itself never grants permission to perform them.

# MIRA Feature Ownership, Dependencies, and Upgrade Reconciliation

## Purpose

A M.I.R.R.O.R. deployment must be able to receive upstream improvements without destroying behavior created or customized by its owner. Upstream releases are proposals against a deployment, never replacement images for a user's repository.

MIRA is the control plane for reasoning, planning, dependency analysis, user approval, and approved execution. M.I.R.R.O.R. is the reality/data plane plus the durable policy, schema, provenance, dependency, and evidence structures that describe reality. The networking analogy is intentionally approximate: M.I.R.R.O.R. is broader than a classic packet-forwarding data plane.

## Two dependency layers

Package reconciliation and runtime behavior readiness are separate problems.

`features.lock.json` is the deployment-owned feature ownership and lineage registry. Every installable/customizable feature must have exactly one ownership record. The registry records owner/origin, installed version, upstream lineage when present, local revision, owned source paths, conflict policy, and rollback policy.

`feature-dependency-map.json` is generated from `features.lock.json` plus every `features/<feature-id>/feature.json`. It records feature-to-feature dependencies and required/optional capability edges. CI compares the committed map to a freshly generated map. Adding or changing a feature without updating its ownership/dependency graph is therefore a release failure.

`behavior-dependencies.json` covers the finer-grained operational layer. Every behavior in the canonical forensic feature catalog has one dependency assignment, whether or not that behavior is packaged as an installable feature. This includes receipts, scheduling, briefs, reminders, orders, shipments, assets, mileage, onboarding, provider portability, household workflows, and infrastructure contracts. Canonical CI cross-checks behavior coverage; the portable releases validate the dependency database itself.

New user-created features use `owner: user` and `origin: user`. Organization-specific features use `owner: organization`. Stock portable features use `owner: mirror`. A customized stock feature increments `local_revision`; the upstream base remains recorded so MIRA can reason about what changed locally and what changed upstream.

## Dependency availability

Dependencies are not assumed from brand names. A feature or behavior declares required and optional capabilities/authorities. Runtime onboarding, execution preflight, and upgrade planning compare those declarations with observed capabilities.

A missing required dependency blocks only the affected behavior or feature and anything that explicitly depends on it. MIRA explains the missing connection in ordinary language. A missing optional dependency degrades only that optional path and MIRA explains what will not work yet. Gmail, Outlook, Drive, OneDrive, Calendar, finance, maps, wearables, and other providers are adapters to capabilities rather than hard-coded product dependencies.

Dependency detection never grants permission to repair a missing dependency. Connecting an account, creating an authority, enabling a service, or changing source remains a separate user-approved action.

See [`BEHAVIOR_DEPENDENCIES.md`](BEHAVIOR_DEPENDENCIES.md) for the every-gesture runtime dependency contract.

## Upgrade algorithm

For each upgrade MIRA constructs three views:

1. the upstream feature state the deployment originally adopted;
2. the deployment's current feature state, including user-owned and locally modified behavior; and
3. the candidate upstream release.

MIRA then builds the package dependency graph, evaluates the behavior dependency preflight for affected enabled behaviors, and identifies unchanged features, upstream changes, local modifications, missing capabilities/authorities, removed features, new features, and possible semantic overlap between local and upstream features.

No feature change is applied during planning. The plan is `proposal-only` and the default action is always `keep-current`.

User-owned or locally modified features are never deleted, overwritten, consolidated, or silently replaced by upstream. If an upstream feature overlaps a local feature, MIRA may propose a consolidation or adapter plan, but the local feature remains the default until the user explicitly approves something else.

## Boomer-mode decision contract

Technical merge mechanics stay behind MIRA. The user-facing review should answer four questions:

- What do I have now?
- What does the new version change?
- Is anything I use missing or incompatible?
- Do I want to keep mine, use the new version, or see more detail?

The first screen must say that nothing has changed yet and that keeping the current workflow is the default.

Before any approved change, MIRA creates a rollback checkpoint and reminds the user that they can return to the previous working setup if they prefer it. The user must not need to understand branches, rebases, dependency graphs, manifests, migration hashes, or merge-base terminology to make the decision.

For a simple update MIRA can say:

> MIRA found an update for Meal Planning. You currently use version 1.0. The new version changes how leftovers are carried into the next plan. Nothing has changed yet. Keeping your current version is the default. If you choose the new version, MIRA will save a rollback point first. Do you want to keep yours, use the new version, or see the differences in more detail?

For a dependency problem MIRA can say:

> Receipt intake is missing access to the selected document store. Your other workflows are unchanged. Nothing will be connected or changed automatically. You can keep the current setup, review how to enable that dependency, or see more detail.

## Apply gate

An approved upgrade is performed on an upgrade branch/checkpoint, never directly over the known-good deployment. Before promotion MIRA must:

1. create and verify a rollback source checkpoint;
2. apply only user-approved feature decisions;
3. preserve all unapproved local/user-owned features;
4. apply schema migrations in an idempotent or reversible form where practical;
5. audit required/optional package dependencies and affected behavior dependencies;
6. run stock and local feature tests;
7. run feature dependency-map freshness validation;
8. run full behavior dependency coverage validation;
9. run privacy/source audits;
10. run behavioral regression checks;
11. run code-overlap/consolidation analysis as advisory evidence only;
12. commit and push the candidate;
13. require green CI;
14. read back the remote commit and changed feature/dependency registries; and
15. promote only after the user-approved candidate is verified.

If any required gate fails, the upgrade is blocked and the current deployment remains the active deployment.

## AI consolidation boundary

MIRA may use AI to identify duplicate behavior, analyze source/API/schema differences, propose adapters, generate migrations/tests, and recommend common-core extraction. Deterministic dependency/capability data is the starting evidence, not a substitute for tests.

AI analysis has no authority to delete or replace user-owned behavior. Consolidation remains a user-in-the-loop source change with rollback and full regression testing.

## Module architecture

Features are modular packages with explicit contracts and failure domains when packaging is useful. Smaller operational gestures do not need to become separate packages or network services merely to receive dependency metadata. The behavior dependency database provides that finer granularity without producing a zoo of tiny services.

A separate service/process is justified only when isolation, privilege separation, scaling, hardware access, or platform/runtime boundaries make it useful. Stable capability interfaces are preferred over direct imports into another feature's private internals.

## Standalone application boundary

This architecture is intentionally application-friendly. A standalone desktop/mobile/web app can place a UI over the same control-plane operations: feature inventory, behavior dependency readiness, plain-language update review, approval, rollback history, and provider connection status. The durable registries remain portable JSON/Git source, while mutable personal state remains in its selected authorities.

A native application should call the same reconciliation and behavior dependency engines rather than reimplement upgrade/runtime-readiness rules in the UI.

## Linux integration

Linux adds a useful local execution and integration plane without becoming the canonical source of truth. A Linux agent can provide filesystem watching, local file indexing, systemd timers/services, D-Bus/desktop notifications, secret-store integration, local command execution under constrained permissions, hardware/device access, local backups, container/process isolation, and optional offline/local-model execution.

Linux integration must advertise each capability separately and be least-privilege. Installing the Linux agent does not automatically authorize arbitrary shell execution, root access, or access to every file. MIRA should request and record only the capabilities an enabled behavior actually needs, then run the same behavior dependency preflight used by cloud or institutional deployments.

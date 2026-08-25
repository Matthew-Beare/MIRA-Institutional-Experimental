# Shared Personal Ops Planner Feature Workflow

## Decision

Personal Ops Planner is an ecosystem of personal deployments built from a stable **public upstream**. Git versions portable behavior/config/schema/tests/features. Mutable operational state stays in the deployment's selected canonical authorities, normally Sheets + Drive for the starter.

| Surface | Contents | Rule |
|---|---|---|
| Public upstream | portable core/starter/features/tests/reference implementation | no secrets or mutable personal data |
| User Git repository | policy/config/schema/tests/personal features/provenance | source/version lineage |
| Structured state authority | tasks, interview ledger, appointments, routines, meal plans, shopping, indexes | canonical mutable state |
| Drive/evidence authority | retained documents/images/receipt/manual/recipe bodies when selected | evidence/documents |
| Calendar/email/finance/wearable/maps | evidence/projection/action/current inputs | optional adapters |

## Non-compromise invariants

- Shared defaults never override a deployment owner's timezone, provider choices, schedules, goals, state authorities, sharing scopes, or local features.
- Adoption is explicit. Importing an upstream feature is a reviewed source/config/migration change.
- Public contributions contain no credentials, secrets, mutable Sheet/database exports, private Drive evidence, Calendar history, receipt/mail bodies, account/medical/school records, or unintended personal information.
- If portability extraction would destabilize a working deployment, preserve the deployment and extract reusable behavior separately.
- Dependencies and permissions are declared rather than assumed from the author's connected apps.

## Personal feature lifecycle

1. User identifies a problem or Personal Ops Planner discovers a useful workflow opportunity.
2. Create/modify the feature on a feature branch.
3. Add/update policy, configuration schema, state-store schema/migrations, and tests as needed.
4. Test against synthetic fixtures plus the deployment interfaces without copying live state into portable source.
5. Commit/push a coherent feature checkpoint under standing Git authorization.
6. Integrate with other experiments on `experimental` when useful.
7. When coherent, ask exactly: **Do you want to make this feature available to other people?**

If no, keep it personal. If yes, continue through the portability gate.

## Portability gate

Before an upstream contribution:
1. state the reusable problem/behavior without personal assumptions;
2. replace user identifiers, authority IDs, provider IDs, and deployment-specific constants with configuration;
3. remove real Sheet/database rows, Drive evidence, Calendar events, private provider references, and local configuration;
4. create synthetic fixtures;
5. minimize dependencies and declare optional/required connectors;
6. define permissions, authority/state schemas, migrations, and adapter boundaries;
7. make migrations idempotent and reversible when practical;
8. add feature version/manifest and compatibility range;
9. run feature tests, repository validation, starter privacy audit, and public-source history/current-tree audit;
10. show the exact public contribution diff and what becomes public;
11. under explicit publication authority, create or use a sanitized contribution branch in the upstream contribution network and open an upstream PR. A private template copy is not assumed to be a fork and cannot itself prove PR compatibility.

Never interpret permission to auto-version a personal source repository as permission to publish upstream.

## Portable feature boundary

Portable modules live under `starter/features/<feature-id>/` when useful. Their source describes behavior, schema/migrations, configuration, tests, and optional provider adapters. It never contains a real user's mutable authority data.

## Bidirectional exchange

```text
public upstream template/release
        ↓ private template copy + pinned provenance
personal source repository + selected state authorities
        ↓ customization
personal feature
        ↓ opt-in sanitization + contribution branch/fork + PR
public upstream
        ↓ review/release
other deployments
```

## Moving a feature between deployments

1. Pin a reviewed feature/core version.
2. Import only portable source plus declared dependencies.
3. Supply configuration/authority references from the receiving deployment.
4. Run synthetic tests and dependency checks before writes.
5. Apply state-store migrations transactionally/idempotently and verify readback.
6. Record installed version/commit/migration in `features.lock.json`.
7. Preserve local overrides and never silently overwrite canonical state with upstream defaults.

## Dependency minimization

Portable modules depend on the smallest state-authority interface and optional capabilities they actually need. Exercise accountability can work with the structured state authority and optionally consume wearable evidence. Appointment reconciliation can work with canonical appointment state, while email evidence and Calendar projection are optional adapters.

A missing optional dependency fails that adapter path only. Avoid central middleware whose failure disables unrelated life domains.

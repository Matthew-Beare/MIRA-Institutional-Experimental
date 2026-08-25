# Shared M.I.R.R.O.R. Skill and Feature Workflow

M.I.R.R.O.R. is designed to learn new repeatable behaviors without turning one person's private life into somebody else's source code. The normal path is **design privately → test → version → optionally sanitize → share**.

## For a non-technical user

You can ask MIRA to create a new skill in ordinary language. Describe the outcome, not the implementation.

Example:

`Design a skill that tracks maintenance for my equipment, links receipts and manuals, and reminds me when service is due.`

MIRA should then:

1. **Inspect before building.** Check the current feature catalog, installed skills, connected providers, schemas, and existing behavior so the new work does not duplicate or contradict something already present.
2. **Define the contract.** State what the skill does, what evidence it reads, which authority owns mutable state, what permissions/connectors it needs, what it may write, how failure is isolated, and what counts as success.
3. **Create a feature branch.** Implement the change away from `main`. Reusable modules normally live under `starter/features/<feature-id>/`; deployment-specific behavior stays in the private deployment boundary.
4. **Make the data boundary explicit.** Put behavior, schemas, migrations, non-secret configuration, and tests in Git. Keep credentials, live authority IDs, private email/receipt bodies, health records, and mutable personal state out of portable source.
5. **Record ownership and dependencies.** Add/update the feature in `features.lock.json`, declare feature and capability dependencies in its manifest, regenerate `feature-dependency-map.json`, and keep the user's feature owner/lineage intact. A new personal feature is `owner: user` and is never silently converted to upstream ownership.
6. **Add tests and synthetic fixtures.** A reusable skill must be testable without copying the user's real data into public or portable source.
7. **Verify the private version.** Run the relevant feature tests, dependency-map freshness check, capability audit, and provider readbacks, then commit and push a coherent checkpoint. A half-working experiment is not silently promoted.
8. **Keep it private by default.** Finishing a useful personal skill does not imply permission to publish it.
9. **Ask before sharing.** When coherent, ask exactly: **Do you want to make this feature available to other people?**

If the answer is **no**, stop at the private, versioned implementation.

If the answer is **yes**, continue through the portability gate below. A yes authorizes preparation for a public contribution, not publication of private data and not an automatic merge. **Publication authority** remains separate and requires explicit approval of the sanitized public diff.

## Source and state surfaces

| Surface | Contents | Rule |
|---|---|---|
| Public upstream | portable core, starter, features, tests, reference implementation | no secrets or mutable personal data |
| User Git repository | policy, config, schema, tests, personal features, provenance | source/version lineage |
| Structured state authority | tasks, interview ledger, appointments, routines, meal plans, shopping, indexes | canonical mutable state |
| Drive/evidence authority | retained documents, images, receipts, manuals, recipe bodies when selected | evidence/documents |
| Calendar/email/finance/wearable/maps | evidence, projection, action, current inputs | optional adapters |

## Non-compromise invariants

- Shared defaults never override a deployment owner's timezone, provider choices, schedules, goals, state authorities, sharing scopes, or local features.
- Adoption is explicit. Importing an upstream feature is a reviewed source/config/migration change.
- Public contributions contain no credentials, secrets, mutable Sheet/database exports, private Drive evidence, Calendar history, receipt/mail bodies, account/medical/school records, or unintended personal information.
- If portability extraction would destabilize a working deployment, preserve the deployment and extract reusable behavior separately.
- Dependencies and permissions are declared rather than assumed from the author's connected apps.
- Standing permission to commit and push a private deployment is never permission to publish upstream.
- User-owned behavior is preserved by default during upstream reconciliation. AI may propose consolidation but may not delete, replace, or re-own a local feature without explicit approval.
- Every approved upgrade creates a rollback checkpoint before source or state migrations are applied.

## Portability gate

Before an upstream contribution:

1. state the reusable problem and behavior without personal assumptions;
2. replace user identifiers, authority IDs, provider IDs, and deployment-specific constants with configuration;
3. remove real database rows, Drive evidence, Calendar events, private provider references, and local configuration;
4. create synthetic fixtures that demonstrate the behavior without exposing the user;
5. minimize dependencies and declare optional and required connectors;
6. define permissions, authority/state schemas, migrations, and adapter boundaries;
7. make migrations idempotent and reversible when practical;
8. add or update feature version, manifest, compatibility range, and tests;
9. run feature tests, repository validation, starter privacy audit, and public-source current-tree/history audit;
10. show the user the exact sanitized diff and clearly identify what becomes public;
11. obtain explicit publication approval; and
12. create or use a sanitized contribution branch in the upstream contribution network and open an upstream pull request.

Publication is complete only after the upstream review/merge process and required CI succeed. Never treat a private template copy as proof that a public PR is safe.

## Portable feature boundary

Portable modules live under `starter/features/<feature-id>/` when useful. Their source describes behavior, schema/migrations, configuration, tests, and optional provider adapters. It never contains a real user's mutable authority data.

If a new capability genuinely requires its own installable skill package instead of a feature module, use the same branch, authority, test, sanitization, permission, and publication rules.

## Bidirectional exchange

```text
public upstream template/release
        ↓ reviewed private adoption
personal source repository + selected state authorities
        ↓ customization on feature branch
personal skill/feature
        ↓ explicit opt-in + sanitization + synthetic fixtures
sanitized contribution branch
        ↓ reviewed pull request
public upstream
        ↓ release
other deployments
```

## Moving a feature between deployments

1. Pin a reviewed feature/core version.
2. Import only portable source plus declared dependencies.
3. Supply configuration/authority references from the receiving deployment.
4. Run synthetic tests and dependency checks before writes.
5. Apply state-store migrations transactionally/idempotently and verify readback.
6. Record installed version/commit/migration plus owner/origin/lineage in `features.lock.json`.
7. Regenerate and commit `feature-dependency-map.json`.
8. Preserve local overrides and never silently overwrite canonical state with upstream defaults.

## Dependency minimization

Portable modules depend on the smallest state-authority interface and optional capabilities they actually need. Exercise accountability can work with the structured state authority and optionally consume wearable evidence. Appointment reconciliation can work with canonical appointment state, while email evidence and Calendar projection are optional adapters.

A missing required dependency blocks only the affected feature and prompts the user to connect/configure it. A missing optional dependency fails that adapter path only and MIRA explains the degraded behavior. Avoid central middleware whose failure disables unrelated life domains.

For upstream update behavior and the plain-language user decision flow, see [`FEATURE_RECONCILIATION.md`](FEATURE_RECONCILIATION.md).

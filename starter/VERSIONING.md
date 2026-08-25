# Life Planner Starter Versioning and Personal Deployments

## Repository roles

- This repository is the public Life Planner upstream and reference implementation.
- `starter/` is the portable onboarding/distribution boundary.
- A personal, organization, or managed Git repository preserves source lineage: policy, non-secret configuration, schemas, migrations, enabled features, tests, onboarding, authority references, and custom feature work.
- Mutable operational state lives in selected canonical authorities, defaulting to Google Sheets/Google Drive for personal deployments or approved Microsoft Lists/Excel and OneDrive/SharePoint candidates in Microsoft 365 deployments.
- Git is not the routine recipe/appointment/task/routine/meal-history database.

Read `STATE_AUTHORITY_MODEL.md`, `INTERVIEW_LEDGER.md`, and `PERSONAL_FORK_LIFECYCLE.md`.

## Normal inheritance path

1. complete the browser-only `INSTALL.md` flow: create one private repository from the audited public GitHub template;
   or select approved organization Git/managed central source under `ENTERPRISE_PILOT.md`;
2. record observed upstream provenance and independently verify ChatGPT read plus Codex write capability;
3. run `START_HERE.md`; non-technical onboarding never falls back to Command Prompt, local Git, Codespaces, tokens, or SSH keys;
4. discover existing capabilities/evidence before creating duplicate systems;
5. create/select the structured state authority and evidence root;
6. create the Authority Registry and Interview Ledger;
7. generate the user's non-secret deployment configuration, schema/migrations, selected features, and policy;
8. validate, commit/push, and verify the first coherent Git source checkpoint, or verify the pinned managed release and approved change route;
9. verify canonical state authority writes/readback;
10. only then enable scheduled/provider writes whose gates pass.

## Branch model

Recommended convention:

```text
main            known-good deployment source
experimental    optional integration branch for concurrent experiments
feature/*       bounded feature work
fix/*           bounded defect work
```

Five features may be in flight at once without one undifferentiated branch. Mutable state continues in its canonical state store while source experiments are isolated in Git branches.

## Automatic personal versioning

After one-time standing Git authorization, lasting behavior/config/schema/migration/feature/onboarding changes automatically validate, commit, push, and receive remote readback.

Routine mutable state changes do not create Git commits. They use the state authority's own audit/history model and required readback.

Automatic versioning does not authorize force-push, visibility change, destructive history rewriting, release, merge, or public publication.

## Share-back gate

When a personal feature is coherent and tests pass, ask exactly:

`Do you want to make this feature available to other people?`

If yes, follow `SHARED_FEATURE_WORKFLOW.md`: extract portable behavior/schema/migrations/tests, replace personal examples with synthetic fixtures, declare dependencies/permissions, run privacy/public-source/feature tests, show the exact public diff, and publish/open an upstream PR only under publication authority.

Do not include mutable Sheet rows, Drive evidence, Calendar events, private provider IDs that expose personal state, or credentials.

## Deployment version record

Persist a non-secret record containing:
- core version or snapshot identifier;
- exact upstream commit/tag/tree;
- schema version;
- selected feature IDs/versions in `features.lock.json`;
- migration checksums/state;
- local policy version;
- repository visibility;
- configured authority types/IDs when safe;
- enabled connector capability identifiers without credentials;
- last verified source commit.

## Updating from upstream

1. compare the next audited upstream release with recorded provenance;
2. read release notes/migrations;
3. test against the user's configuration and state schemas;
4. apply idempotent state-store migrations only after bounded approval/policy authority;
5. review source/config delta and local-feature conflicts;
6. preserve canonical state and local overrides;
7. apply the audited source delta under the user's policy; a private template copy may not share a Git merge base with upstream;
8. verify remote source commit and any state migration readback.

Never assume template history is a fork, force unrelated histories together, reset a deployment to upstream, or overwrite personal state/features silently.

## Public release model

Use semantic versions for upstream releases. Feature branches are not installation targets. Public `main` remains the stable upstream only after coherent forensic CI and merge authority. User deployments may pin any known-good release and advance deliberately.

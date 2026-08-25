# Personal Fork Lifecycle

Life Planner is designed to be inherited, personalized, versioned, and optionally improved upstream without treating Git as the user's live database.

## Repository lineage

```text
public upstream GitHub template
        ↓ personal template copy OR approved organization/managed release
user-owned, organization-owned, or managed Life Planner source
        ↓ first-boot source/config checkpoint
feature/fix branches + optional experimental integration
        ↓ tested personal release
        ↓ optional sanitized feature extraction
public upstream PR
```

The user's Git repository is the durable source of truth for **behavior and structure**: policy, schemas, migrations, module selection, authority references, non-secret configuration, tests, feature code, onboarding, provenance, recovery instructions, and user-selected recurring brief schedules.

Mutable personal operational state lives in canonical authorities described in `STATE_AUTHORITY_MODEL.md`, normally Google Sheets plus Google Drive evidence for the personal starter or Microsoft Lists/Excel plus OneDrive/SharePoint in an approved Microsoft 365 lane.

Despite this file's historical name, the non-technical default is a GitHub **template copy**, not a Git fork or local clone. Complete `INSTALL.md`: the user creates the first private repository once on GitHub's website, the ChatGPT GitHub app receives read access, and Codex separately receives write access. No command line is part of default onboarding.

That is the personal default, not a corporate bypass. `ENTERPRISE_PILOT.md` also permits approved GitHub Enterprise, GitLab, Azure Repos, or managed central source. In the managed lane the end user does not need a Git account; lasting personal policy changes enter the approved change process. Claude and other AI runtimes use the same source contract only after their exact read/write/readback capabilities are observed.

## First boot

After the browser setup and repository capability readback in `INSTALL.md`, then capability discovery and bounded provisioning approval:

1. resolve the exact upstream tag/commit/tree used;
2. verify the selected personal, organization, or managed source mode and record visibility/provenance;
3. verify source read, source write and remote readback independently when user-level source mutations are allowed;
4. create/select the structured state authority and evidence root;
5. create and verify the `Authority Registry` and `Interview Ledger`;
6. ask whether recurring briefs are wanted and, if so, record only the user's exact local slots, notification mode, and canonical IANA timezone; the product supplies no default brief time;
7. write non-secret deployment configuration, selected feature IDs/versions, schemas/migrations, policy, and any selected brief schedule;
8. import approved accessible existing information into the selected canonical state/evidence authorities with provenance;
9. run applicable validation/privacy/source tests;
10. commit and push one coherent Git source/config checkpoint;
11. read back the remote source commit;
12. project any selected recurring brief schedule into the verified scheduler and read the exact definition back;
13. read back canonical state/evidence writes before calling initialization complete.

Credentials, OAuth tokens, passwords, raw authentication material, full payment credentials, mutable Sheet/List/Excel exports, and private Drive/OneDrive/SharePoint evidence do not belong in portable Git source.

## Continuous state

Routine state changes happen in the canonical mutable authority, not Git. Each state-changing action follows the module contract:

- read canonical state/evidence;
- correlate/dedupe using stable IDs;
- write the smallest mutation;
- read back the canonical authority;
- verify material fields;
- retain required event/history rows;
- report success only after verification.

Examples include accepting a meal plan, recording a workout, adding/revising an appointment, marking a task complete, or reconciling an email-derived appointment with Calendar.

## Continuous personal development

After standing Git authorization, lasting behavior/configuration/schema/migration/onboarding changes automatically validate, commit, push, and receive remote readback. Several experiments may exist at once on separate feature branches. The stable personal branch stays known-good; incomplete work belongs on feature/experimental branches.

A recurring brief schedule is one of those durable configuration changes. When the user moves, adds, disables, renames, or removes a brief, update the version-controlled schedule first, validate/commit/push/read it back, then reconcile the provider scheduler and verify the live definition. Never leave the live scheduler and Git describing different schedules.

Examples:
- a new meal-planning rule;
- an appointment reconciliation policy;
- a hiking/travel module;
- a custom work-mode transition;
- a changed recurring brief time or notification mode;
- a state-store schema migration;
- a reusable fitness evidence adapter;
- a household workflow.

## Portable feature candidate gate

When a custom feature reaches a coherent tested checkpoint, Life Planner asks exactly:

`Do you want to make this feature available to other people?`

If no, keep it in the user's repository.

If yes:
1. identify reusable behavior separately from deployment state;
2. replace personal identifiers/authority references with configuration placeholders;
3. exclude live Sheet rows, Drive evidence, Calendar events, private provider IDs, local config, and secrets;
4. create synthetic fixtures;
5. declare dependencies and permissions;
6. add migrations/rollback behavior when needed;
7. run feature tests, starter privacy audit, and public-source audit;
8. generate a portable feature manifest/version;
9. show the exact public contribution diff;
10. publish/open the upstream PR only under configured publication authority.

## Upstream synchronization

User deployments pin known-good upstream versions. Updating is deliberate:
- compare the next release with recorded provenance;
- review migrations and feature conflicts;
- test against the user's configuration/state schemas;
- apply compatible source and bounded state-store migrations;
- preserve canonical state and local features;
- apply the audited source delta under the user's policy; a private template copy may not share a Git merge base with upstream;
- verify remote source commit and state migration readback.

Never assume template history is a fork, force unrelated histories together, reset a user's deployment to upstream, or discard local state/features merely because public upstream advanced.

## Failure isolation

A Git/managed-source failure blocks only the durable source mutation that depends on it. A Sheets/Lists/Excel/Drive/OneDrive/SharePoint selected-state failure blocks only the state-changing module that depends on that authority. Preserve and read back known-good state, continue unrelated healthy modules, and never fall back to chat memory, a personal account workaround, or a shadow database.

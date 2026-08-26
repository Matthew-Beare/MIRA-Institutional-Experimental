# M.I.R.R.O.R. State Authority Model

M.I.R.R.O.R. separates **portable source** from **mutable life state** and treats runtime modules as independent failure domains wherever practical. Storage providers are adapters. Canonical identities, schemas, event semantics, provenance and business rules belong to M.I.R.R.O.R., not to a Sheet, Drive folder, SQL table layout, or client application.

## Authority stack

A deployment selects one verified implementation for each required role:

- **Git or managed central repository:** code, policy, schemas, migrations, feature manifests, non-secret configuration, tests, onboarding, provenance, and recovery/version history.
- **Structured-state adapter:** mutable operational state. Current candidates include Google Sheets, Microsoft Lists/Excel tables, PostgreSQL, or another implementation satisfying `runtime-interface-contract.json`.
- **Evidence adapter:** retained documents, images, receipts, manuals, recipe bodies, photos and other bulky evidence. Current candidates include Google Drive, OneDrive/SharePoint, S3-compatible object storage, or another verified implementation.
- **Calendar adapter:** optional appointment/event projection and reminder surface. Calendar is not the sole state authority.
- **Scheduler adapter:** deployment-owned recurring execution. Hosted tasks, Linux `systemd` timers, managed cloud schedulers, or another verified implementation may satisfy the same contract.
- **Notification adapter:** visual/spoken/in-app delivery intents. Native clients may implement device-specific delivery without changing canonical reminder state.

Another supported backend can replace a current provider if its adapter satisfies the same read/write/dedupe/audit/readback/migration contract. Do not require a second live state database merely because one is available.

Git is never the default database for recipes, appointments, routines, meal history, shopping rows, medical-event scheduling, receipt bodies, or similar changing personal records.

## Service/API boundary

Web, Windows/Linux desktop, Android, AI runtimes, and local agents must not write canonical storage directly. Normal mutation flows through the bounded M.I.R.R.O.R. service/API contract, which performs dependency preflight, authorization, schema validation, stable identity/idempotency checks, transaction/compensation handling, write, readback, and audit.

A browser/connector deployment may implement that boundary through provider adapters without a separately hosted server. A self-hosted or cloud deployment should make the service boundary explicit. The behavior contract is the same in both cases.

## Failure-domain architecture

**One canonical authority per data class does not mean one giant workbook or database transaction for the entire system.** Canonical identity and physical resource isolation are separate decisions.

Every enabled module declares a runtime isolation contract containing:

- its `failure_domain`;
- baseline required capabilities;
- optional/conditional capabilities;
- canonical state classes;
- idempotency scope;
- required-failure behavior;
- optional-failure behavior;
- any deliberate cross-module writes;
- client-only capabilities if any;
- model-routing class if semantic inference is required.

The normal rule is:

- a missing **required** capability blocks that module only;
- a missing **optional** capability degrades only that capability/path;
- a module must not write directly into another module's canonical state unless the cross-module mutation is explicitly declared and verified at both authority boundaries;
- feature-to-feature dependencies must be acyclic and resolve to bundled/installed features;
- retries, failure state and recovery remain module-scoped;
- no module may silently substitute chat, Git, a stale export, a different provider, or another module's store for its canonical state.

### Recommended production resource boundaries

A small deployment may begin with one structured state workbook when simplicity is more important than availability, but production use should split independent high-value/high-churn domains so one resource failure does not unnecessarily take unrelated workflows with it.

A practical default is:

1. **Core Ops authority** — Authority Registry, Interview Ledger, tasks/projects, controls, routines, trips/routes, lightweight run/audit state.
2. **Commerce authority** — orders, receipts, payment reconciliation, shopping/procurement, purchase allocations.
3. **Mileage/Pay authority** — only when work/pay mileage exists.
4. **Scoped authorities when useful** — appointments, household/shared state, meal planning, school, or another domain may be separated when privacy, sharing, volume, or failure isolation justifies it.

In PostgreSQL these may be schemas/tables within one database while retaining domain transaction boundaries. In Sheets/List-style deployments they may be separate workbooks/resources. Physical layout is adapter-specific; canonical domain semantics are not.

## Authority Registry

First boot creates an `Authority Registry` in the selected core structured state store. Each row has at minimum:

- Authority UUID
- Data Class
- Capability Contract
- Adapter/provider type
- Provider resource ID/URL or database namespace reference
- Failure Domain
- Owner person UUID
- Scope (`personal`, `household`, `shared`, or another configured scope)
- Read/write/readback capability status
- Schema/migration version
- Sharing policy
- Last verified timestamp
- Recovery/backup policy reference
- Notes

Every mutable data class has exactly one canonical authority. Evidence files can be linked from canonical rows by stable Evidence UUID/provider locator without becoming a second database.

## Structured state and evidence layout

A starter deployment may expose logical tables/entities such as:

- `Authority Registry`
- `Interview Ledger`
- `People`
- `Provider / Organization Directory`
- `Tasks & Projects`
- `Routines & Accountability`
- `Appointments`
- `Calendar Projection`
- `Recipes`
- `Meal Plans`
- `Pantry & Freezer`
- `Shopping & Procurement`
- `Orders / Receipts / Payment Reconciliation`
- `Assets`
- `Asset Identifiers`
- `Locations`
- `Asset Location Events`
- `Knowledge Index`
- `Integration Registry`
- `Run Log`

The exact physical workbook/database/table boundaries depend on the adapter and failure-domain needs. Logical entity names and UUID relationships survive backend migration.

Evidence storage may contain receipts, manuals/reference, recipes, appointment/admin evidence, photos, or other selected classes. Canonical rows retain Evidence UUID, content hash, provider locator, source identity and provenance so the underlying evidence object can later move from Drive-style storage to object storage without changing its identity.

## Integration Registry and health

The deployment persists a compact `Integration Registry` or equivalent capability registry with:

- module/feature ID;
- capability/adapter ID;
- required / optional / conditional role;
- failure domain;
- provider/resource reference;
- current health (`Healthy`, `Degraded`, `Blocked`, `Unknown`);
- circuit-breaker state;
- last verified timestamp;
- last material error/next action.

This registry is observability/configuration, not a second mutable business-state database. Connecting or disconnecting an app changes observed capability health; it does not normally rewrite behavior dependency source.

## Recovery snapshots

A recovery copy is not a second live authority and is **never a second writable master**.

Where the selected backend supports version history/export/snapshots, first boot should offer a recovery policy appropriate to that adapter. PostgreSQL deployments should use database-native backup/WAL strategies plus restore tests; object storage should use versioning/backup where supported. Provider migration snapshots remain nonauthoritative until an explicit verified cutover.

## Sharing and collaboration

Sharing state and sharing a feature are different operations.

A deployment can support:

1. **Personal authority:** only the owner/service identities explicitly authorized by the owner.
2. **Whole-authority sharing:** the owner deliberately grants another person access to the selected resource/API scope.
3. **Scoped shared authority:** create/select a separate shared scope for household, travel, meal planning, projects, or another domain when the owner does not want to expose the entire personal authority.

Never infer that a family member should receive access. Record grants in the Authority Registry and verify provider/API access after the owner changes sharing.

## Mutation contract

For every state-changing workflow:

1. read the module's canonical row/object and relevant evidence through the selected adapter/service interface;
2. correlate/dedupe with stable IDs and source identities;
3. verify required behavior/integration dependencies for that module/path only;
4. validate authorization and idempotency key;
5. write the smallest required mutation through the canonical service boundary;
6. read the canonical authority back;
7. verify identifiers and material fields;
8. only then report completion or trigger declared dependent projections;
9. retain append-only event/history rows where the module contract requires history.

If the canonical state authority is unavailable, stop that state-changing module and report `Action Required — <authority> unavailable`. Do not substitute chat memory or Git files as mutable state. Unrelated modules with healthy independent authorities may continue.

## Backend migration contract

Backend migration is staged and reversible until cutover:

1. provision the candidate adapter and schema migrations;
2. one-way mirror canonical IDs, rows/events, evidence metadata and hashes;
3. compare counts, identifiers, financial totals, relationship edges and material read models;
4. dual-write or verification-write a bounded test subset when appropriate;
5. perform backup/restore tests;
6. stop writes or use a bounded cutover transaction;
7. switch Authority Registry references only after parity/readback passes;
8. preserve rollback to the last verified old authority until the migration window closes.

Never renumber canonical UUIDs because the database changed.

## Git lineage

Each deployment inherits the public M.I.R.R.O.R. foundation and has one durable source lineage from first boot. Git records exact upstream version/provenance, enabled modules/features, schemas/migrations, adapter contracts, authority types/failure domains, generated deployment policy/configuration, integration contracts, custom feature code/policy/tests, and release/recovery history. Git never stores live secrets or database dumps.

After standing Git authorization, lasting behavior/config/schema/feature changes validate, commit, push, and receive remote readback automatically. Routine mutable state changes do not create Git commits.

## Portability boundary

When a personal feature becomes reusable, MIRA asks exactly:

`Do you want to make this feature available to other people?`

A yes exports behavior/schema/migrations/tests with synthetic fixtures and configuration placeholders. It never exports the user's mutable rows, evidence, Calendar events, database credentials, provider IDs that expose private state, client device tokens, or secrets.

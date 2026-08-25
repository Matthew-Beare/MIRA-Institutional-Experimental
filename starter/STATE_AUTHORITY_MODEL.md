# Life Planner State Authority Model

Life Planner separates **portable source** from **mutable life state** and treats runtime modules as independent failure domains wherever practical.

## Default authority stack

For new-user deployments the default is intentionally boring and inspectable:

- **Git or managed central repository:** code, policy, schemas, migrations, feature manifests, non-secret configuration, tests, onboarding, provenance, and recovery/version history. An enterprise user may consume this without a personal Git account.
- **Google Sheets, Microsoft Lists/Excel, or another selected database:** structured mutable operational state.
- **Google Drive, OneDrive/SharePoint, or another verified evidence store:** retained documents, images, receipts, manuals, recipe bodies or other bulky evidence that does not belong in table cells.
- **Google Calendar, Outlook Calendar, or another verified calendar:** optional projection/reminder surface. Calendar is not the sole state authority.

Another supported database can replace Sheets or Lists/Excel if its adapter satisfies the same read/write/dedupe/audit/readback contract. Do not require a second live state database merely because one is available.

Git is never the default database for recipes, appointments, routines, meal history, shopping rows, medical-event scheduling, receipt bodies, or similar changing personal records.

## Failure-domain architecture

**One canonical authority per data class does not mean one giant workbook for the entire system.** Canonical identity and physical resource isolation are separate decisions.

Every enabled module declares a runtime isolation contract containing:

- its `failure_domain`;
- baseline required capabilities;
- optional/conditional capabilities;
- canonical state classes;
- idempotency scope;
- required-failure behavior;
- optional-failure behavior;
- any deliberate cross-module writes.

The normal rule is:

- a missing **required** capability blocks that module only;
- a missing **optional** capability degrades only that capability/path;
- a module must not write directly into another module's canonical state unless the cross-module mutation is explicitly declared and verified at both authority boundaries;
- feature-to-feature dependencies must be acyclic and must resolve to bundled/installed features;
- retries, failure state and recovery remain module-scoped;
- no module may silently substitute chat, Git, a stale export, or another module's store for its canonical state.

### Recommended production resource boundaries

A small deployment may begin with one structured state workbook when simplicity is more important than availability, but production use should split independent high-value/high-churn domains so one resource failure does not unnecessarily take unrelated workflows with it.

A practical default is:

1. **Core Ops authority** — Authority Registry, Interview Ledger, tasks/projects, controls, routines, trips/routes, lightweight run/audit state.
2. **Commerce authority** — orders, receipts, payment reconciliation, shopping/procurement, purchase allocations.
3. **Mileage/Pay authority** — only when work/pay mileage exists.
4. **Scoped authorities when useful** — appointments, household/shared state, meal planning, school, or another domain may be separated when privacy, sharing, volume, or failure isolation justifies it.

This is a failure-domain recommendation, not a demand for database sprawl. Two data classes may share one resource when their coupling is intentional and the user accepts the shared failure domain.

A provider-wide outage can still affect multiple authorities hosted by that provider. Life Planner treats that as an infrastructure failure, not permission to create shadow state. Unaffected providers/modules may continue, and recovery begins from the canonical authorities plus verified recovery snapshots/provider history.

## Authority Registry

First boot creates an `Authority Registry` in the selected core structured state store. Each row has at minimum:

- Authority UUID
- Data Class
- Provider/type
- Provider resource ID or URL
- Failure Domain
- Owner person UUID
- Scope (`personal`, `household`, `shared`, or another configured scope)
- Read/write capability status
- Sharing policy
- Last verified timestamp
- Recovery/backup policy reference
- Notes

Every mutable data class has exactly one canonical authority. Drive evidence can be linked from canonical rows by stable IDs/URLs without becoming a second database.

## Structured state / evidence layout

A starter deployment may use tables such as:

- `Authority Registry`
- `Interview Ledger`
- `People`
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
- `Knowledge Index`
- `Integration Registry`
- `Run Log`

The exact enabled tables and physical workbook/database boundaries depend on selected modules and failure domains. Do not create unused databases for sport, but do not collapse unrelated high-value domains merely to save one resource.

Google Drive, OneDrive, or SharePoint may contain folders/libraries such as `Receipts`, `Manuals & Reference`, `Recipes`, `Appointments & Admin`, or another selected evidence class. Canonical rows retain the provider file ID/link and provenance.

Apple/iCloud can participate through deliberate browser/Files-app import and export, but it is not advertised as a general automatic authority. CloudKit app containers are not equivalent to arbitrary iCloud Drive access. A manual evidence file remains manual until a verified adapter writes and reads it back.

## Integration Registry and health

The deployment should persist a compact `Integration Registry` or equivalent capability registry with:

- module/feature ID;
- capability/adapter ID;
- required / optional / conditional role;
- failure domain;
- provider/resource reference;
- current health (`Healthy`, `Degraded`, `Blocked`, `Unknown`);
- circuit-breaker state;
- last verified timestamp;
- last material error/next action.

This registry is observability/configuration, not a second mutable business-state database. A module decides whether it can proceed from its own declared contract plus current dependency health, not from another module's incidental success.

## Recovery snapshots

A recovery copy is not a second live authority and is **never a second writable master**.

Where the provider supports version history/export/snapshots, first boot should offer a recovery policy appropriate to the selected state store. A recovery snapshot:

- is immutable or timestamped;
- is not read as live state during normal operation;
- is never silently promoted after an outage;
- is restored/promoted only through an explicit disaster-recovery transaction with validation and readback;
- does not create two writable masters.

This gives recoverability without inventing split-brain state.

## Sharing and collaboration

Sharing state and sharing a feature are different operations.

A deployment can support:

1. **Personal authority:** only the owner/service accounts explicitly authorized by the owner.
2. **Whole-authority sharing:** the owner deliberately grants another person access to the workbook/folder.
3. **Scoped shared authority:** create/select a separate shared workbook/folder for household, travel, meal planning, projects, or another domain when the owner does not want to expose the entire personal authority.

Never infer that a family member should receive access. Record grants in the Authority Registry and verify provider read/write access after the owner changes sharing.

The system should be able to explain which data would become visible before a broad share.

## Mutation contract

For every state-changing workflow:

1. read the module's canonical row/object and relevant evidence;
2. correlate/dedupe with stable IDs;
3. verify required dependencies for that module/path only;
4. write the smallest required mutation;
5. read the canonical authority back;
6. verify identifiers and material fields;
7. only then report completion or trigger declared dependent projections;
8. retain append-only event/history rows where the module contract requires history.

If the canonical state authority is unavailable, stop that state-changing module and report `Action Required — <authority> unavailable`. Do not substitute chat memory or Git files as mutable state. Unrelated modules with healthy independent authorities may continue.

## Git lineage

Each deployment inherits the public Life Planner foundation and has one durable source lineage from first boot. That lineage may be a user repository, an approved organization repository, or a managed central source. Git records:

- exact upstream version/provenance;
- enabled modules/features;
- schemas and migrations for the selected state store;
- authority *references/types/failure domains*, never credentials;
- generated deployment policy and configuration;
- integration contracts;
- custom feature code/policy/tests;
- release/recovery history.

After standing Git authorization, lasting behavior/config/schema changes validate, commit, push, and receive remote readback automatically. In a managed-source enterprise lane, those changes use the approved change process rather than an end-user push. Routine mutable state changes do not create Git commits.

## Portability boundary

When a personal feature becomes reusable, Life Planner asks exactly:

`Do you want to make this feature available to other people?`

A yes exports behavior/schema/migrations/tests with synthetic fixtures and configuration placeholders. It never exports the user's Sheet/List/Excel rows, Drive/OneDrive/SharePoint evidence, Calendar events, provider IDs that expose private state, or credentials.

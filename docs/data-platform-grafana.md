# LyfeOS Data Platform and Grafana Migration

## Goal

Move from Google Sheets as the long-term mutable operational store to a normalized database without losing the working Gmail/brief/receipt workflows, auditability, or easy recovery. Grafana is the read-only dashboard layer, not the source of truth.

## Target architecture

```text
Gmail / Calendar / Finances / user statements / carrier evidence
                         |
                         v
               LyfeOS ingestion/policy service
                 (validation + idempotency)
                         |
                         v
                    PostgreSQL
                         |
              +----------+----------+
              |                     |
              v                     v
         Grafana read-only     small admin/API UI
          dashboards/alerts    bounded corrections
```

### PostgreSQL

PostgreSQL becomes the canonical mutable state only after a staged parity migration. Use normal relational constraints, foreign keys, unique/idempotency keys, append-only event tables, and migration tooling. Do not put secrets in ordinary data tables.

Suggested domains/tables:

- `receipts`
- `receipt_items`
- `receipt_tags`
- `order_events`
- `expense_allocations`
- `financial_resolution_events`
- `shipments`
- `classification_queue`
- `assets`
- `asset_specs`
- `fitment_evidence`
- `tool_inventory`
- `terminals`
- `route_pairs`
- `route_direction_facts`
- `trips`
- `trip_legs`
- `mileage_entries`
- `mode_overrides`
- `tasks`
- `run_logs`
- `system_config`

For terminal pairs, route geometry and runtime may keep A → B and B → A learned facts independently. Company-paid terminal mileage is a policy-controlled pair fact: for the current deployment it is symmetric, so a verified A↔B paid-mile value is stored/used both directions unless an explicit exception is recorded for that pair. A future generic deployment may choose a directional paid-mile policy only through explicit configuration rather than accidental reverse-fallback behavior.

### Write API / policy service

Use a small service such as FastAPI (or equivalent) as the sole normal writer to PostgreSQL. Responsibilities:

- validate schemas and enums;
- create stable IDs;
- enforce idempotency/deduplication;
- apply receipt allocation balance checks;
- preserve append-only events;
- perform fitment/evidence gates;
- enforce cancellation/refund state transitions;
- enforce HOME/ROAD and trip-leg transitions;
- expose bounded endpoints to ChatGPT/connectors and a future companion app;
- record actor/source/provenance and audit timestamps.

Do not give Grafana or ChatGPT unrestricted SQL write credentials.

### Grafana

Grafana gets a dedicated read-only database user and views/materialized views designed for dashboards. Good first dashboards:

1. **Ops Now** — HOME/ROAD, active trip leg, location age, ETA, action-required count, upcoming appointments, active shipments.
2. **Mileage & Pay** — current closed/open work cycle, paid miles by leg, gross estimate, final vs estimated, terminal-pair history.
3. **Purchases & Receipts** — rolling spend, monthly/YTD/rolling-year, category/asset breakdown, recent receipts, classification backlog.
4. **Orders & Refunds** — active shipments, delayed/no-progress orders, cancellations awaiting money resolution, five-business-day exceptions.
5. **Assets & Fitment** — vehicles/assets, purchased parts, exact part numbers, fitment evidence, unresolved assignments, maintenance/inventory views.
6. **System Health** — ingestion runs, failed audits, stale connectors, policy/runtime version, backup age.

Grafana alerts may surface database conditions, but user-facing ChatGPT notifications should still flow through the bounded Ops policy rather than creating random per-record scheduled jobs.

## Migration stages

### Stage 0 — keep Sheets authoritative

Current production remains unchanged while schemas and tests stabilize.

### Stage 1 — build PostgreSQL schema

- create migrations and synthetic fixtures;
- map every current Sheet column to normalized fields;
- preserve stable existing IDs and immutable UUIDs;
- create read-only views matching current Sheet outputs.

### Stage 2 — one-way mirror

Mirror Sheets → PostgreSQL. PostgreSQL is not authoritative yet. Compare counts, totals, allocations, active shipments, route/trip state, mileage/pay, and event history after every sync.

### Stage 3 — Grafana on mirrored data

Deploy Grafana read-only while Sheets still own writes. This gives dashboard value with minimal migration risk.

### Stage 4 — dual-write validation

The policy service writes a bounded test subset to both Sheet and PostgreSQL or writes PostgreSQL plus a verification mirror. Compare every transaction. Any mismatch blocks cutover.

### Stage 5 — authority cutover

Only after parity/restore tests pass:

- PostgreSQL becomes canonical mutable authority;
- Sheets become exported views/recovery artifacts or are retired from operational writes;
- Project/skill authority IDs are updated in one versioned release;
- rollback remains available to the last verified Sheet snapshot until the migration window closes.

## Deployment choices

### Homelab

A Docker/Podman stack is sufficient:

- PostgreSQL
- LyfeOS API/policy service
- Grafana
- backup job
- reverse proxy only if needed

Prefer VPN/private access instead of exposing PostgreSQL or Grafana directly to the public Internet. Local availability depends on the user's homelab, so ChatGPT cloud workflows require an explicit authenticated bridge/API.

### Managed

Managed PostgreSQL + hosted Grafana reduces infrastructure maintenance but adds recurring cost and places more personal operational data in external services. The same API/data-boundary rules apply.

## Backups

Before PostgreSQL becomes authoritative, implement and restore-test the requested backup contract:

- frequent incremental/WAL-capable backup where appropriate;
- daily encrypted off-host/cloud backup;
- weekly full/base backup;
- automatic retention/rotation;
- periodic restore test into an isolated database;
- Git stores schema/migrations/config examples only, never live database dumps or secrets.

## Difficulty

The technology is ordinary. The hard part is migration correctness, not PostgreSQL or Grafana themselves. A useful read-only Grafana mirror is a moderate project. Making PostgreSQL the trusted write authority is a larger release because receipt identity, allocations, financial resolution, mode overrides, trips, mileage, and recovery all need parity and rollback tests first.
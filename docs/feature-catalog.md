# Personal Ops Planner hierarchical feature catalog

Generated from `docs/feature-ledger-2026-08-24.md`. Edit the forensic ledger, then run `python3 scripts/feature_catalog.py --write`. CI rejects drift. Delivery status and verification are separate: repository tests do not prove a live connector or scheduled firing.

## A. Brief engine, time, tasking, and operational state

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `a-01` | Exactly two briefs at 2:45 AM and 2:45 PM `America/New_York` | REQUIRED | `unproven` | `ci_evidence` |
| `a-02` | No UTC-shifted, relative, duplicate, 3:00, noon/midnight, or extra diagnostic schedules | REQUIRED / supersedes old states | `documented` | `documented` |
| `a-03` | Canonical-clock guard with DST-safe slot matching and bounded dispatch grace | REQUIRED by failure evidence | `executable` | `ci_evidence` |
| `a-04` | Standalone scheduled delivery with deterministic Run ID header | REQUIRED by stale-response incident | `executable` | `ci_evidence` |
| `a-05` | Deterministic HOME/ROAD context with explicit overrides | REQUIRED | `executable` | `ci_evidence` |
| `a-06` | Generic context pairs: HOME/ROAD, HOME/TRUCK, HOME/FIELD, HOME/CAMPUS, HOME/OFFICE, HOME/AWAY, custom | ACCEPTED direction | `rejected` | `documented` |
| `a-07` | Job title/duties inform context recommendation but never silently enable it | REQUIRED | `mixed` | `documented` |
| `a-08` | Active trip tracking separate from context and paid-work tracking | REQUIRED | `executable` | `ci_evidence` |
| `a-09` | Multi-leg routes, learned runtime, current location, ETA, ahead/behind inference | REQUIRED | `executable` | `ci_evidence` |
| `a-10` | ROAD severe-weather/route-condition watch; HOME local weather only | REQUIRED | `workflow` | `documented` |
| `a-11` | Company-paid mileage and estimated gross pay; both Thursday briefs | REQUIRED | `executable` | `ci_evidence` |
| `a-12` | Separate accessible Miles & Pay tracker | REQUIRED | `live_external` | `live_readback_required` |
| `a-13` | Task hierarchy High/Medium/Low → classification → subsystem → one task per bullet | REQUIRED | `documented` | `documented` |
| `a-14` | Next-action coaching and honest completion evidence | ACCEPTED | `workflow` | `documented` |
| `a-15` | Phase-aware Run Log, last-good checkpoint, resumable recovery, circuit breaker | REQUIRED by repeated stalls | `executable` | `ci_evidence` |
| `a-16` | Optional module failure isolation | REQUIRED | `executable` | `ci_evidence` |

## B. Calendar, appointments, mail, and communication safety

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `b-01` | Saturday 2:45 AM ROAD appointment lookahead for the next week | REQUIRED | `workflow` | `documented` |
| `b-02` | Appointment reminder day before and morning of | REQUIRED | `executable` | `ci_evidence` |
| `b-03` | Appointment reminder one hour before | REQUIRED | `executable` | `ci_evidence` |
| `b-04` | Medication reminders from explicit owner, prescription-label, pharmacy, or clinician evidence | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `b-05` | Caregiver reminder sharing | REQUIRED safety boundary | `executable` | `ci_evidence` |
| `b-06` | Context-aware appointment windows without exposing misleading confirmation state | REQUIRED | `mixed` | `documented` |
| `b-07` | Important email triage across school, employer, jobs, financial, medical, vendors, fraud/security | REQUIRED | `workflow` | `documented` |
| `b-08` | No automatic outbound email or vendor contact | REQUIRED safety invariant | `documented` | `documented` |
| `b-09` | Archive-approval prompt using exact user-facing question and repeat-on-silence behavior | REQUIRED | `workflow` | `documented` |
| `b-10` | Career/VA job watch with realistic qualification filtering | REQUIRED personal service | `documented` | `documented` |

## C. Orders, shipments, receipts, payments, and spending

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `c-01` | Gmail evidence ingestion and carrier/vendor correlation | REQUIRED | `executable` | `documented` |
| `c-02` | Ordered→shipped→delivered lifecycle with dedupe | REQUIRED | `executable` | `ci_evidence` |
| `c-03` | Cancelled, replaced, returned, refunded, and no-settlement states | REQUIRED | `mixed` | `documented` |
| `c-04` | Replacement updates superseded purchase state without duplicate spend | REQUIRED | `mixed` | `documented` |
| `c-05` | Active undelivered-only brief output; five-business-day no-progress action | REQUIRED | `workflow` | `ci_evidence` |
| `c-06` | Receipt intake from email, files, photos/screenshots, and manual entry | REQUIRED/ACCEPTED | `executable` | `ci_evidence` |
| `c-07` | Searchable expandable receipt/purchase history | REQUIRED | `executable` | `ci_evidence` |
| `c-08` | Monthly email-detected spending sheet with dedupe/category totals | REQUIRED | `workflow` | `documented` |
| `c-09` | General receipt taxonomy: automotive, tools, house, bills, education, personal/medical records, warranties, etc. | ACCEPTED backlog | `specification` | `documented` |
| `c-10` | Expected-charge, refund, reimbursement, and household-beneficiary reconciliation | ACCEPTED | `executable` | `ci_evidence` |
| `c-11` | Subscription/free-trial tracking | PROPOSED/previous automation | `not_present` | `documented` |
| `c-12` | Credit-card linkage/complete financial ingestion | PROPOSED/INFRA | `not_present` | `documented` |

## D. Assets, fitment, inventory, shopping, and household storage

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `d-01` | Stable asset identity and item-to-vehicle/equipment fitment | REQUIRED | `executable` | `ci_evidence` |
| `d-02` | Asset purchase evidence, manuals, warranties, maintenance, and verified specifications | ACCEPTED | `executable` | `ci_evidence` |
| `d-03` | Bidirectional receipt/order ↔ asset/vehicle/tool queries | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `d-04` | Namespaced UPC/GTIN, merchant SKU, manufacturer part/model, serial, IMEI, and MAC identities | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `d-05` | Product/serial/barcode photo and Gmail evidence enrichment | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `d-06` | Manual discovery, canonical Drive retention, and asset linkage | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `d-07` | Vehicle/equipment technical specifications with exact applicability and provenance | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `d-08` | Shopping intent separate from purchase history | ACCEPTED | `mixed` | `documented` |
| `d-09` | Immutable inventory/item IDs | ACCEPTED backlog | `specification` | `ci_evidence` |
| `d-10` | Hierarchical locations and intended-location versus last-moved-location | REQUIRED/under exploration | `specification` | `documented` |
| `d-11` | QR/barcode scan-in and scan-out | ACCEPTED backlog | `specification` | `documented` |
| `d-12` | Queryable household/loft/shop inventory | REQUIRED direction | `specification` | `documented` |
| `d-13` | Consumable/grocery par levels and under-level notification | REQUIRED | `specification` | `documented` |
| `d-14` | Scale-based par sensing | PROPOSED | `specification` | `documented` |
| `d-15` | Grocery list/pantry/freezer flows | PROPOSED/ACCEPTED direction | `specification` | `documented` |
| `d-16` | Recipes, meal planning, shopping linkage | CURRENT REQUIRED | `contract` | `documented` |

## E. Profiles, onboarding, family, and per-user customization

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `e-01` | Generic quarantined starter with no inherited personal data | REQUIRED | `mixed` | `ci_evidence` |
| `e-02` | Adaptive first boot: four kickoff questions, then bounded follow-ups | REQUIRED | `documented` | `ci_evidence` |
| `e-03` | Ask AI use, pain points, job/duties, desired automation, apps/services, and constraints | REQUIRED | `documented` | `documented` |
| `e-04` | Ask preferred brief cadence/timezone for new users | REQUIRED | `documented` | `documented` |
| `e-05` | Explicit service activation states: unresolved/enabled/disabled/not-applicable/deferred | REQUIRED for honest onboarding | `rejected` | `ci_evidence` |
| `e-06` | Working and self-employed profiles | ACCEPTED | `executable` | `ci_evidence` |
| `e-07` | Retired/retiree profile distinct from nonworking/between-jobs | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `e-08` | Nonworking/between-jobs profile | ACCEPTED | `executable` | `ci_evidence` |
| `e-09` | Parent/guardian profile | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `e-10` | Child/dependent profiles and family-school coordination | ACCEPTED direction | `documented` | `ci_evidence` |
| `e-11` | Caregiver and household-manager profiles | PROPOSED/ACCEPTED direction | `documented` | `ci_evidence` |
| `e-12` | Student profile and HOME/CAMPUS option | ACCEPTED | `mixed` | `ci_evidence` |
| `e-13` | Mixed/custom roles | REQUIRED for generality | `documented` | `ci_evidence` |
| `e-14` | Older-adult usability/profile recommendations | ACCEPTED direction | `executable` | `ci_evidence` |
| `e-15` | “Boomer mode” | PROPOSED nickname; exact older wording only partly recoverable | `documented` | `documented` |
| `e-16` | Per-person identity, household/beneficiary relationships, and permission scopes | ACCEPTED | `workflow` | `documented` |
| `e-17` | Personal fork plus reviewed upstream feature sharing | REQUIRED | `documented` | `ci_evidence` |
| `e-18` | Standalone clean starter repository | ACCEPTED release boundary | `mixed` | `ci_evidence` |
| `e-19` | Self-improving/custom skill builder from repeated friction | PROPOSED/ACCEPTED direction | `mixed` | `documented` |
| `e-20` | Automatic instruction updates | USER ASKED; technically constrained | `mixed` | `documented` |
| `e-21` | Browser-only non-technical installation with no terminal fallback | CURRENT REQUIRED | `documented` | `ci_evidence` |
| `e-22` | Independent ChatGPT GitHub read and Codex GitHub write gates | CURRENT REQUIRED | `documented` | `ci_evidence` |
| `e-23` | Provider-neutral AI runtime capability routing | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `e-24` | Personal Git, organization Git, managed-central source, and explicit no-Git lanes | CURRENT REQUIRED | `executable` | `ci_evidence` |

## F. Life-service modules discussed or catalogued

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `f-01` | Briefs/action digest | REQUIRED | `executable` | `ci_evidence` |
| `f-02` | Next-action planner | REQUIRED/ACCEPTED | `workflow` | `documented` |
| `f-03` | Email triage | REQUIRED | `workflow` | `documented` |
| `f-04` | Orders/shipments | REQUIRED | `executable` | `documented` |
| `f-05` | Receipt archive | REQUIRED | `executable` | `documented` |
| `f-06` | Personal finance organization | ACCEPTED direction | `specification` | `ci_evidence` |
| `f-07` | Appointments/calendar/reminders | REQUIRED | `executable` | `ci_evidence` |
| `f-08` | Administrative health organization | PROPOSED/ACCEPTED direction | `executable` | `ci_evidence` |
| `f-09` | Shopping/procurement | ACCEPTED direction | `specification` | `documented` |
| `f-10` | Recipes/meals/groceries | CURRENT REQUIRED | `contract` | `documented` |
| `f-11` | Household/errands/admin/maintenance | CURRENT REQUIRED direction | `documented` | `documented` |
| `f-12` | Laundry stages and drop-off/pickup reminders | CURRENT REQUIRED | `documented` | `ci_evidence` |
| `f-13` | Routines/fitness/accountability | REQUIRED for user; optional stock service | `workflow` | `documented` |
| `f-14` | Education/study/deadlines/offline road preparation | REQUIRED for user; optional stock service | `workflow` | `documented` |
| `f-15` | Parent/child school coordination | CURRENT REQUIRED direction | `documented` | `documented` |
| `f-16` | Travel/vacation/outdoor planning | ACCEPTED direction | `workflow` | `documented` |
| `f-17` | Work-trip/route/paid-work tracking | REQUIRED | `executable` | `ci_evidence` |
| `f-18` | Assets/maintenance/warranties/manuals | ACCEPTED | `workflow` | `documented` |
| `f-19` | Personal knowledge/reference library | ACCEPTED | `workflow` | `documented` |
| `f-20` | Backup/disaster recovery | REQUIRED backlog | `specification` | `documented` |
| `f-21` | Custom skill/automation builder | PROPOSED/ACCEPTED direction | `documented` | `documented` |
| `f-22` | Activity trackers/wearable data | PROPOSED | `not_present` | `documented` |

## G. Data platform, integrations, recovery, and future infrastructure

| ID | Feature | Decision | Delivery | Verification |
|---|---|---|---|---|
| `g-01` | Sheets/Drive as current mutable authority with Git for policy/schema/tests | REQUIRED current architecture | `live_external` | `live_readback_required` |
| `g-02` | Google Workspace and Microsoft 365 state/evidence portability | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `g-03` | Apple/iCloud and portable-file manual bridge | CURRENT REQUIRED portability boundary | `contract` | `ci_evidence` |
| `g-04` | Locked-down and regulated enterprise/VA pilot lane | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `g-05` | Eventual PostgreSQL/private SQL canonical service | USER DIRECTION / INFRA | `infrastructure` | `documented` |
| `g-06` | Policy/data API | PROPOSED/INFRA | `infrastructure` | `documented` |
| `g-07` | Grafana/observability dashboards | PROPOSED/INFRA | `infrastructure` | `documented` |
| `g-08` | Object storage/NAS for evidence and attachments | PROPOSED/INFRA | `infrastructure` | `documented` |
| `g-09` | Companion/mobile app with scanning and queries | USER DIRECTION / INFRA | `not_present` | `documented` |
| `g-10` | Home Assistant bridge | PROPOSED/INFRA | `not_present` | `documented` |
| `g-11` | Plex bridge | PROPOSED/INFRA | `not_present` | `documented` |
| `g-12` | Voice queries/commands | PROPOSED/INFRA | `not_present` | `documented` |
| `g-13` | NAS/LAN/private-service bridge and VPN access | PROPOSED/INFRA | `not_present` | `documented` |
| `g-14` | Family site-to-site VPN/redundancy/failover | PROPOSED | `not_present` | `documented` |
| `g-15` | Twice-daily incremental, daily cloud, weekly full, rotation, encryption, restore tests | REQUIRED backlog | `specification` | `documented` |
| `g-16` | Knowledge ingestion with relevant excerpts, timestamps, URL/title/metadata, provenance, relationships, optional full pin | REQUIRED/ACCEPTED | `executable` | `ci_evidence` |
| `g-17` | Drive organization by domain and searchable metadata | ACCEPTED personal behavior | `workflow` | `documented` |
| `g-18` | Hierarchical machine-readable feature catalog with CI drift enforcement | CURRENT REQUIRED | `executable` | `ci_evidence` |
| `g-19` | Machine-enforced production-code inventory and anti-bloat ownership gate | CURRENT REQUIRED | `executable` | `ci_evidence` |

# Personal Ops Planner / Daily Ops Brief feature ledger — 2026-08-24 forensic audit

This ledger aggregates feature evidence from the available project-conversation set, current direct instructions, continuity/search evidence, the audited legacy `main` baseline, open GitHub backlog, and the rejected universal-onboarding experiment. It deliberately separates a user requirement from an assistant proposal and from an implementation claim. “Current status” records this repaired clean-history candidate where stated; live scheduler and provider gates remain independent of code release.

## Evidence/status vocabulary

- **REQUIRED** — directly ordered or reaffirmed by the user.
- **ACCEPTED** — proposed earlier and subsequently treated as an agreed requirement.
- **PROPOSED** — discussed/speculated, but no reliable acceptance evidence.
- **INFRA/DEFERRED** — desired direction requiring infrastructure or a later phase.
- **REJECTED/SUPERSEDED** — explicitly prohibited or replaced.
- **UNRESOLVED** — evidence exists, but the exact decision or wording is unavailable.

Implementation states are independent: **executable**, **skill workflow**, **contract-only**, **spec-only**, **broken**, or **not present**.

## Project-conversation coverage

| Conversation | Feature evidence recovered |
| --- | --- |
| 2026-08-25 — cross-platform and VA service-chief portability | Personal users may create GitHub in the browser; Claude and other capable AI runtimes must be supported without assuming feature parity. Add Google Workspace, Microsoft 365/OneDrive/SharePoint, Apple/manual portability, organization Git or managed source, and a browser-only locked-down/regulated pilot lane. Never use a personal account to bypass corporate or VA policy. |
| 2026-08-25 — Foodie onboarding failure | Default onboarding must be browser-only for non-technical users; it must create a private personal repository through GitHub's template UI, distinguish ChatGPT read access from Codex write access, and never fall back to Command Prompt. Meal planning is a current requirement. Laundry stages and clothing/other drop-off pickup reminders must be explicit household-routine choices. |
| 2026-08-21 — Action required for FL5 tire availability | Cancellation/replacement must update the canonical purchase record rather than create contradictory duplicates; vehicle/asset fitment must remain correct; absolutely no automatic email; user approval may be requested. |
| 2026-08-15 — Platform Failure Explanation | Work-credit exhaustion and stalled runs are operational failure evidence; long work needs resumability, phase evidence, and an honest recovery path. Model/credit purchase discussion is not a LyfeOS end-user feature. |
| 2026-08-23 — Continue Repo Changes | Forensic release gate; test failure modes; push verified main; install into production and verify; correct active-trip and paid-mileage state from canonical evidence; include Boomer/retiree/parent and other profile modes. |
| 2026-08-22 — Fix ROAD Brief Failure | Deterministic ROAD/HOME resolution must remain correct in the Saturday PM brief and must not depend on optional mileage success. |
| 2026-08-20 — AM ops brief with urgent account alerts | Active trip/route/location/ETA; ROAD context; order/vehicle-fitment reconciliation; Saturday 2:45 AM appointment lookahead; day-before and morning-of appointment reminders; Git-backed policy/source-of-truth changes. |
| 2026-08-20/21 — Pony online | Gmail-driven ordered→shipped→delivered lifecycle; cancellations/replacements; searchable database; item-to-vehicle association; stock receipt/order/brief behavior for new users; first boot asks cadence/timezone; job-aware but user-confirmed context modes; durable Git updates. |
| 2026-08-15/16 — Automation Overhaul Completed | Quarantined generic starter; extensive/adaptive first boot; GitHub + Drive authority model; job/lifestyle/AI-use discovery; automation suggestions; private-device/work-integration caveats; progressive improvement; appointments/meals/hiking/training branches; portable fork/PR feature sharing. |
| 2026-08-15 — Operational Fixes Acknowledged | Stuck/spinning work must expose recovery state instead of silently hanging; circuit-breaker/checkpoint behavior is a product-quality requirement. |
| 2026-08-15 — Password Strength Evaluation | GitHub was offered as the durable engineering surface and the user asked the assistant to implement every supported part; this is authorization/context, not a standalone feature. |
| 2026-08-12 — Archive Old Chats | Canonical Eastern schedule; weekly work/travel timing; location-based schedule inference; company-paid miles and Thursday gross estimate; separate Miles & Pay tracker; eventual self-hosted SQL; full copy-ready instruction updates; expanded LyfeOS feature exploration. |
| 2026-08-10 — Brief Task Scheduling Fix | Schedule history proves several superseded schedules; the only accepted schedule is exactly 2:45 AM and 2:45 PM `America/New_York`. |

## Consolidated feature ledger

### A. Brief engine, time, tasking, and operational state

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Exactly two briefs at 2:45 AM and 2:45 PM `America/New_York` | REQUIRED | One schedule remains; chat-bound delivery and model-supplied entry time were diagnosed after the PM run; replacement firing still unproven | Keep one standalone schedule, named TZID, provider readback, runtime-owned clock, Run Log proof. |
| No UTC-shifted, relative, duplicate, 3:00, noon/midnight, or extra diagnostic schedules | REQUIRED / supersedes old states | Historical paused jobs exist | Keep prohibited; diagnostics must not become permanent schedules. |
| Canonical-clock guard with DST-safe slot matching and bounded dispatch grace | REQUIRED by failure evidence | Executable now owns the production system clock, waits out at most 60 seconds of early handoff, and tests Eastern/Central/Mountain/Pacific/UTC summer+winter equivalence | Never accept a model-guessed production timestamp; retain actual-firing proof as a separate live scheduler gate. |
| Standalone scheduled delivery with deterministic Run ID header | REQUIRED by stale-response incident | Policy/runtime contract repaired; provider migration and first live firing remain evidence gates | Each run starts from saved prompt, never a long-lived chat; first line identifies `OPS-YYYY-MM-DD-AM|PM`. |
| Deterministic HOME/ROAD context with explicit overrides | REQUIRED | Repaired single executable engine; installed private copy fingerprint-matched and retested | Keep config-driven transitions and authority readback. |
| Generic context pairs: HOME/ROAD, HOME/TRUCK, HOME/FIELD, HOME/CAMPUS, HOME/OFFICE, HOME/AWAY, custom | ACCEPTED direction | Candidate router supports safe custom labels and explicit activation state; v2 branch remains rejected | Keep lean, opt-in, user-confirmed context routing. |
| Job title/duties inform context recommendation but never silently enable it | REQUIRED | Candidate router recommends with word-boundary matching and never auto-enables | Ask confirmation; permit bypass/rename. |
| Active trip tracking separate from context and paid-work tracking | REQUIRED | Executable | Preserve independent states/history and validate trip identity. |
| Multi-leg routes, learned runtime, current location, ETA, ahead/behind inference | REQUIRED | Executable/skill workflow, partly personal-hardcoded | Keep; move mutable route/schedule facts out of public source. |
| ROAD severe-weather/route-condition watch; HOME local weather only | REQUIRED | Skill workflow | Keep optional and failure-isolated. |
| Company-paid mileage and estimated gross pay; both Thursday briefs | REQUIRED | Repaired executable with section-scoped failure isolation | Retain finite/nonnegative validation and deterministic totals. |
| Separate accessible Miles & Pay tracker | REQUIRED | Live external authority | Keep as mutable authority, never duplicate live rows in Git. |
| Task hierarchy High/Medium/Low → classification → subsystem → one task per bullet | REQUIRED | Skill/state contract | Keep; ask only for materially missing classification. |
| Next-action coaching and honest completion evidence | ACCEPTED | Skill workflow | Keep; never mark completion from weak inference. |
| Phase-aware Run Log, last-good checkpoint, resumable recovery, circuit breaker | REQUIRED by repeated stalls | Run Log schema/phase evidence repaired; professional Module Circuit Breaker artifact installed and private deployment synced | Prove the next live Run Log entry at an actual scheduled firing. |
| Optional module failure isolation | REQUIRED | Repaired and adversarially tested for mileage, appointments, routes/settings, and unavailable adapters | Preserve core/optional failure boundaries in every new module. |

### B. Calendar, appointments, mail, and communication safety

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Saturday 2:45 AM ROAD appointment lookahead for the next week | REQUIRED | Policy/skill behavior | Keep and test calendar boundary. |
| Appointment reminder day before and morning of | REQUIRED | Executable deterministic planner + skill behavior | Project through the single control cycle, dedupe deterministic reminder identities, and require provider readback. |
| Appointment reminder one hour before | REQUIRED | Executable deterministic planner + skill behavior | Keep the relative interval configurable; suppress rather than emit a reminder at/after event start. |
| Medication reminders from explicit owner, prescription-label, pharmacy, or clinician evidence | CURRENT REQUIRED | Executable deterministic planner | Never infer dose/schedule or give missed-dose advice; activation remains explicit and mutable. |
| Caregiver reminder sharing | REQUIRED safety boundary | Executable opt-in gate | Default to the user only; require explicit sharing consent and an exact private recipient identity. |
| Context-aware appointment windows without exposing misleading confirmation state | REQUIRED | Partial code/contract | Keep; isolate malformed/unavailable appointment data. |
| Important email triage across school, employer, jobs, financial, medical, vendors, fraud/security | REQUIRED | Skill workflow | Keep, evidence-grounded, compact. |
| No automatic outbound email or vendor contact | REQUIRED safety invariant | Skill contract | Hard gate: draft/prompt only until explicit per-action approval. |
| Archive-approval prompt using exact user-facing question and repeat-on-silence behavior | REQUIRED | Skill workflow | Keep; no silent archive. |
| Career/VA job watch with realistic qualification filtering | REQUIRED personal service | Consolidated PM control-cycle phase with canonical `Job Watch` dedupe/report state; no separate active task | Treat as optional per-user service, not universal default; reject senior/developer roles that exceed the configured baseline. |

### C. Orders, shipments, receipts, payments, and spending

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Gmail evidence ingestion and carrier/vendor correlation | REQUIRED | Skill workflow + shipment executable | Keep; newer carrier evidence outranks stale vendor state. |
| Ordered→shipped→delivered lifecycle with dedupe | REQUIRED | Executable/skill workflow | Keep; validate deterministic timestamps and output invariants. |
| Cancelled, replaced, returned, refunded, and no-settlement states | REQUIRED | Partial/broken | Fix replacement linking and payment/refund contradictions. |
| Replacement updates superseded purchase state without duplicate spend | REQUIRED | Partial workflow | Stable purchase/case IDs; append-only events; canonical current record. |
| Active undelivered-only brief output; five-business-day no-progress action | REQUIRED | Skill workflow | Keep and regression-test. |
| Receipt intake from email, files, photos/screenshots, and manual entry | REQUIRED/ACCEPTED | Executable normalized evidence core + skill/provider workflow | OCR/connector adapters collect evidence; validate source identity, provenance, entity/receipt/line links, and provider readback. |
| Searchable expandable receipt/purchase history | REQUIRED | Live external state + executable receipt/asset graph query | Preserve provenance and return the same connected purchase/asset records from either direction. |
| Monthly email-detected spending sheet with dedupe/category totals | REQUIRED | Skill workflow | Keep clearly labelled incomplete/email-grounded spending. |
| General receipt taxonomy: automotive, tools, house, bills, education, personal/medical records, warranties, etc. | ACCEPTED backlog | Spec-only | Implement generic taxonomy without current-user defaults. |
| Expected-charge, refund, reimbursement, and household-beneficiary reconciliation | ACCEPTED | Executable + skill workflow, defects found | Harden IDs, money validation, settlement semantics, and audit evidence. |
| Subscription/free-trial tracking | PROPOSED/previous automation | Paused historical automation | Offer as optional service; do not resurrect silently. |
| Credit-card linkage/complete financial ingestion | PROPOSED/INFRA | Not present | Requires explicit connector, scope, privacy, and reconciliation design. |

### D. Assets, fitment, inventory, shopping, and household storage

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Stable asset identity and item-to-vehicle/equipment fitment | REQUIRED | Executable + skill workflow/data model | Receipt-line reconciler enforces immutable asset/relationship UUIDs, exact source identity, explicit endpoints, set/lot quantity and idempotent replay; provider adapters still require target readback. |
| Asset purchase evidence, manuals, warranties, maintenance, and verified specifications | ACCEPTED | Executable normalized evidence/knowledge/specification core + skill/provider workflows | Keep provenance and exact model/part/revision/applicability evidence; live adapter writes require readback. |
| Bidirectional receipt/order ↔ asset/vehicle/tool queries | CURRENT REQUIRED | Executable graph query core | Traverse explicit assignment/installation/use relationships but exclude household ownership edges that would contaminate results with unrelated assets. |
| Namespaced UPC/GTIN, merchant SKU, manufacturer part/model, serial, IMEI, and MAC identities | CURRENT REQUIRED | Executable normalized identifier core | Preserve exact values and leading zeroes, validate global check digits, namespace local identifiers, and reject serial-level collisions. |
| Product/serial/barcode photo and Gmail evidence enrichment | CURRENT REQUIRED | Executable evidence core + skill/provider workflow | Treat OCR as candidate extraction, retain the source, corroborate identity, and enrich the same UUID rather than duplicating the asset. |
| Manual discovery, canonical Drive retention, and asset linkage | CURRENT REQUIRED | Executable knowledge/index core + skill/provider workflow | Search authoritative manufacturer/OEM sources first, record blocked/no-match states honestly, retain the file in Drive, and link it with a Knowledge UUID. |
| Vehicle/equipment technical specifications with exact applicability and provenance | CURRENT REQUIRED | Executable specification core | Verified torque, pressure, capacity, alignment, and load values require authoritative source tier plus page/section and exact subject UUID; never promote owner memory to verified. |
| Shopping intent separate from purchase history | ACCEPTED | Branch/catalog proposal | Implement only as distinct state to prevent duplicate spend/history. |
| Immutable inventory/item IDs | ACCEPTED backlog | Executable beta core | UUID-backed asset and relationship reconciliation is implemented/tested; live specialized inventory migration is deployment state, while QR/mobile events remain later work. |
| Hierarchical locations and intended-location versus last-moved-location | REQUIRED/under exploration | Spec-only | Implement minimally; avoid burdensome per-cut lumber tracking. |
| QR/barcode scan-in and scan-out | ACCEPTED backlog | Spec-only | Defer until stable IDs/location/event schema exists. |
| Queryable household/loft/shop inventory | REQUIRED direction | Spec-only | Generic location/category/search model; no personal inventory in public source. |
| Consumable/grocery par levels and under-level notification | REQUIRED | Spec-only | Support manual counts first; notifications opt-in. |
| Scale-based par sensing | PROPOSED | Spec-only | Optional Home Assistant hardware integration; not beta-core. |
| Grocery list/pantry/freezer flows | PROPOSED/ACCEPTED direction | Contract/spec-only | Keep separate from receipt history and par state. |
| Recipes, meal planning, shopping linkage | CURRENT REQUIRED | Contract-only manifest | Keep onboarding/configuration available, but do not call the planner implemented until executable behavior and tests exist. |

### E. Profiles, onboarding, family, and per-user customization

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Generic quarantined starter with no inherited personal data | REQUIRED | Candidate tree and clean reachable history are sanitized; scanners strengthened; legacy history was not imported | Release only from this clean lineage; handle the separate legacy repository under explicit owner authority. |
| Adaptive first boot: four kickoff questions, then bounded follow-ups | REQUIRED | Starter present | Preserve ≤4 initial questions and Minimum Useful Setup. |
| Ask AI use, pain points, job/duties, desired automation, apps/services, and constraints | REQUIRED | Starter present | Keep capability-aware and avoid promising unavailable integrations. |
| Ask preferred brief cadence/timezone for new users | REQUIRED | Starter present | Store named IANA TZ; user’s personal deployment remains fixed Eastern/twice daily. |
| Explicit service activation states: unresolved/enabled/disabled/not-applicable/deferred | REQUIRED for honest onboarding | Implemented and tested in candidate; unsafe branch implementation rejected | Keep finite-state activation and exclude disabled/not-applicable services from recommendations. |
| Working and self-employed profiles | ACCEPTED | Implemented as composable candidate roles | Keep as composable roles. |
| Retired/retiree profile distinct from nonworking/between-jobs | CURRENT REQUIRED | Executable first-class composable role with appointment/medication reminder recommendations | Public label is `Retired`; use the respectful `Personal Schedule & Wellbeing` support template, keep retirement distinct from employment status, and never infer age/ability. |
| Nonworking/between-jobs profile | ACCEPTED | Implemented as a composable candidate role | Keep distinct from retirement. |
| Parent/guardian profile | CURRENT REQUIRED | Implemented as first-class composable role; recommendations never auto-enable services | Keep family/calendar/household modules explicit and permission-scoped. |
| Child/dependent profiles and family-school coordination | ACCEPTED direction | Dependent-minor role/router implemented; dedicated family-school service remains spec/skill-level | Minimum necessary private data; explicit calendar/school/activity/sharing scopes. |
| Caregiver and household-manager profiles | PROPOSED/ACCEPTED direction | Composable router roles implemented; dedicated services remain spec/skill-level | No capability or permission assumptions. |
| Student profile and HOME/CAMPUS option | ACCEPTED | Student role and safe custom context are implemented in the candidate | Keep context separate from role. |
| Mixed/custom roles | REQUIRED for generality | Composable/custom roles implemented; underlying roles preserved | Preserve underlying roles; `mixed` only a summary. |
| Older-adult usability/profile recommendations | ACCEPTED direction | Executable role/template core; broader accessibility preferences remain discovery-driven | Never use an insulting public label or infer disability, medication, finance, age, or competence; services remain opt-in. |
| “Boomer mode” | PROPOSED nickname; exact older wording only partly recoverable | Deliberately not a public mode | Map supported needs to retired/older-adult/accessibility configuration; allow only an optional private alias. |
| Per-person identity, household/beneficiary relationships, and permission scopes | ACCEPTED | Data model/skill workflow | Private immutable IDs; relationship labels do not grant custody/health/finance access. |
| Personal fork plus reviewed upstream feature sharing | REQUIRED | Starter workflow present | Keep isolation tests and controlled propagation. |
| Standalone clean starter repository | ACCEPTED release boundary | Clean-history distribution lineage created from the audited candidate tree | Keep one sanitized root history and reject imports from the contaminated legacy lineage. |
| Self-improving/custom skill builder from repeated friction | PROPOSED/ACCEPTED direction | Branch spec + generic starter workflow | Only create versioned private modules with declared capabilities, permissions, state, failures, and tests. |
| Automatic instruction updates | USER ASKED; technically constrained | Partial template/process | Move durable behavior to policy-as-code; emit copy-ready instruction changes where UI cannot be mutated safely. |
| Browser-only non-technical installation with no terminal fallback | CURRENT REQUIRED | Machine-readable browser workflow + CI contract; upstream template setting still requires live GitHub readback | Create a private repository from the web template, block on missing capability, and never substitute Command Prompt, PowerShell, local Git, GitHub CLI, Codespaces, tokens, or SSH keys. |
| Independent ChatGPT GitHub read and Codex GitHub write gates | CURRENT REQUIRED | Machine-readable capability/readback contract with CI coverage | Never infer write access from the read-only ChatGPT GitHub app; verify the exact personal repository and remote commit readback. |
| Provider-neutral AI runtime capability routing | CURRENT REQUIRED | Executable fail-closed onboarding router + machine-readable contract/tests | Support ChatGPT, Claude, approved Microsoft/VA AI, Gemini, and generic MCP-capable runtimes only from observed actions and readback; never infer feature parity from brand. |
| Personal Git, organization Git, managed-central source, and explicit no-Git lanes | CURRENT REQUIRED | Executable capability routing + browser/managed-source contracts/tests | Personal users may create GitHub in the browser; enterprise users may use approved GitHub Enterprise/GitLab/Azure Repos or a pinned managed release without a personal account. |

### F. Life-service modules discussed or catalogued

| Service | Decision/evidence | Current status |
| --- | --- | --- |
| Briefs/action digest | REQUIRED | Executable + skill workflow. |
| Next-action planner | REQUIRED/ACCEPTED | Skill workflow. |
| Email triage | REQUIRED | Skill workflow. |
| Orders/shipments | REQUIRED | Executable + skill workflow. |
| Receipt archive | REQUIRED | Skill workflow + partial executables. |
| Personal finance organization | ACCEPTED direction | Partial reconciliation executables; broader service spec-only. |
| Appointments/calendar/reminders | REQUIRED | Executable reminder planner + calendar/skill workflow; provider projection requires readback. |
| Administrative health organization | PROPOSED/ACCEPTED direction | Medication-reminder safety core executable; broader service remains specification-only and must exclude diagnosis/dosing. |
| Shopping/procurement | ACCEPTED direction | Spec-only. |
| Recipes/meals/groceries | CURRENT REQUIRED | Contract-only; onboarding selection and storage/projection contracts exist, executable planner remains absent. |
| Household/errands/admin/maintenance | CURRENT REQUIRED direction | Generic task system plus machine-readable household-routine service/onboarding contract; live reminder projection remains capability-gated. |
| Laundry stages and drop-off/pickup reminders | CURRENT REQUIRED | Machine-readable router/reminder contract with tests; live brief/Calendar delivery requires provider capability and readback. |
| Routines/fitness/accountability | REQUIRED for user; optional stock service | Skill workflow. |
| Education/study/deadlines/offline road preparation | REQUIRED for user; optional stock service | Skill workflow. |
| Parent/child school coordination | CURRENT REQUIRED direction | Parent/dependent role routing implemented; dedicated service remains spec/skill-level. |
| Travel/vacation/outdoor planning | ACCEPTED direction | Partial trip/route skill workflows. |
| Work-trip/route/paid-work tracking | REQUIRED | Executable + skill workflow. |
| Assets/maintenance/warranties/manuals | ACCEPTED | Skill workflow/contracts. |
| Personal knowledge/reference library | ACCEPTED | Skill workflow/spec. |
| Backup/disaster recovery | REQUIRED backlog | Spec-only. |
| Custom skill/automation builder | PROPOSED/ACCEPTED direction | Workflow/spec only. |
| Activity trackers/wearable data | PROPOSED | Not present; connector/infrastructure dependent. |

### G. Data platform, integrations, recovery, and future infrastructure

| Feature | Decision | Current status | Required disposition |
| --- | --- | --- | --- |
| Sheets/Drive as current mutable authority with Git for policy/schema/tests | REQUIRED current architecture | In use | Clarify authority registry; query live authority before memory/chat. |
| Google Workspace and Microsoft 365 state/evidence portability | CURRENT REQUIRED | Executable capability contract/router + documentation/tests; live tenant adapters remain capability- and readback-gated | Permit Sheets/Drive or Lists/Excel plus OneDrive/SharePoint only after exact identity, scope, bounded write, and provider readback. |
| Apple/iCloud and portable-file manual bridge | CURRENT REQUIRED portability boundary | Contract-only, machine-validated manual lane | Support deliberate browser/mobile CSV/JSON/ICS/document import/export; do not advertise arbitrary automated iCloud Drive access. |
| Locked-down and regulated enterprise/VA pilot lane | CURRENT REQUIRED | Executable fail-closed approval/capability gate + tested pilot contract; live tenant authorization remains unproven | Use synthetic/public data first, forbid personal-account workarounds, pin approved source, verify least-privilege read/write/readback, and require exact current organization approval for regulated-sensitive data. |
| Eventual PostgreSQL/private SQL canonical service | USER DIRECTION / INFRA | Architecture docs only | Stage migration behind API/schema/tests; no pretend bridge. |
| Policy/data API | PROPOSED/INFRA | Architecture spec | Needed before companion app/remote consumers; authenticated and scoped. |
| Grafana/observability dashboards | PROPOSED/INFRA | Architecture doc | Operational telemetry only; not beta-core. |
| Object storage/NAS for evidence and attachments | PROPOSED/INFRA | Architecture spec | Define provenance, retention, backup, encryption. |
| Companion/mobile app with scanning and queries | USER DIRECTION / INFRA | Not present | Depends on stable API, identity, events, auth, offline handling. |
| Home Assistant bridge | PROPOSED/INFRA | Not present | Explicit local bridge and permissions; no cloud-reachability assumption. |
| Plex bridge | PROPOSED/INFRA | Not present | Optional local module. |
| Voice queries/commands | PROPOSED/INFRA | Not present | Explicit confirmation for consequential actions. |
| NAS/LAN/private-service bridge and VPN access | PROPOSED/INFRA | Not present | Threat model and explicit network boundary first. |
| Family site-to-site VPN/redundancy/failover | PROPOSED | Not present | Separate infrastructure project, not beta-core Personal Ops Planner. |
| Twice-daily incremental, daily cloud, weekly full, rotation, encryption, restore tests | REQUIRED backlog | Spec-only | Define actual data set/RPO/RTO and prove restores before claiming backup. |
| Knowledge ingestion with relevant excerpts, timestamps, URL/title/metadata, provenance, relationships, optional full pin | REQUIRED/ACCEPTED | Executable knowledge/provenance core + skill/provider workflow | Keep raw source temporary unless pinned; test retrieval/provenance and verify retained Drive objects by readback. |
| Drive organization by domain and searchable metadata | ACCEPTED personal behavior | Skill workflow | User-specific layout stays private/configurable. |
| Hierarchical machine-readable feature catalog with CI drift enforcement | CURRENT REQUIRED | Executable repository release gate | Update the forensic ledger, regenerate JSON/Markdown, attach code/test evidence to executable claims, then commit and push every durable feature change. |
| Machine-enforced production-code inventory and anti-bloat ownership gate | CURRENT REQUIRED | Executable repository release gate | Every production Python file declares one bounded responsibility, why it is separate, and direct test evidence; unlisted code, debug execution, bare exceptions, wildcard imports, and `shell=True` fail CI. |

## Explicit exclusions and non-negotiable safety boundaries

- Never send email, contact vendors, make purchases, or create consequential commitments without explicit per-action approval.
- Never use conversation memory as a substitute for the configured canonical database/authority when mutable state matters.
- Never put live IDs, email addresses, aliases, routes, vehicles, schedules, or other personal deployment state in the public portable source.
- Never infer HOME/ROAD solely from a job-title keyword.
- Never equate retired, nonworking, parent/guardian, caregiver, household manager, student, or dependent-minor roles.
- Never infer health, financial, custody, or sharing authority from age or relationship labels.
- Never call a Markdown contract, stub, branch experiment, or catalog entry “implemented” or “provisioned.”
- Never resurrect superseded schedules or merge the four-UTC-candidate scheduler design.
- Never automatically merge a PR merely because standing commit/push authority exists.

## Conversation-audit limitations

The available project context contains eleven named conversations, but some bodies are summarized or truncated rather than verbatim. Personal-context retrieval and the dated continuity snapshot were used only as corroboration. The current conversation makes retiree and parent/guardian support explicit requirements, so those are not unresolved. Only the exact older wording and acceptance state of the “Boomer mode” nickname remains partly unrecoverable; the ledger does not invent it.

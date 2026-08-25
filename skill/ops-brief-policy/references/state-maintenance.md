# Ops State and Automation Maintenance

Load this reference completely before changing task, control, mode, mileage, automation, calendar-projection, or other persistent Ops state. Preserve Sheet identity, headers, validation, row formatting, provenance and history.

## Global capture from supported conversations

- A clear request to add/update/complete/pause/remove something from the named Daily/Ops system is a command to update the canonical Ops Status Register immediately when that authority is reachable from the current surface.
- Chat is an intake surface, not an authority. Never leave a durable Ops change only in chat memory, a project-local note, prompt, or second database.
- If a required connected Sheet/app cannot be reached or written from the current conversation, say the change was not persisted. Never claim account-wide interception of every ChatGPT conversation.
- For guaranteed LifeOS receipt/state ingestion, use a conversation where the configured project/skill and write-capable authorities are actually available. Global Custom Instructions may identify intent across chats but do not manufacture missing connector/tool access.

## Tasks

- Apply additions, completions, removals, pauses, renames, tier/classification changes, scheduling and visibility directly to the existing Ops Status Register.
- Mark completion `Done` and removal `Removed`; never delete task history or infer completion from silence.
- Ask only for a genuinely missing required field.

## Mode overrides

Use Control type `Mode Override`; Vacation and Home early are `Item` values.

- For an unambiguous “got home early” statement, run `python3 scripts/ops_policy.py home-early --now <current-offset-aware-ISO> --pretty`, then upsert the returned Home early control row.
- Home early starts immediately, closes the current work-cycle mileage accrual at supported HOME arrival, and remains HOME through the next Friday 2:45 PM brief; runtime uses exclusive Friday 3:00 PM Eastern expiry.
- Mark a final active leg Arrived only when the user's statement/evidence supports it. Never fabricate arrival time or miles.
- Expired overrides are ignored by the engine rather than manually erased.

## Mileage and pay

- Log only company-paid miles stated by the user or credible company/settlement/run-sheet evidence. Never substitute map, odometer or estimated distance.
- A work cycle is the actual sequence of paid dispatch legs from work departure through confirmed HOME arrival. It normally closes Wednesday PM or earlier; Thursday is reporting-only unless a real paid leg is explicitly recorded after HOME.
- Every real dispatch leg gets its own Trip ID and Mileage Log occurrence when trip tracking is enabled. Never assume the first outbound destination returns directly home.
- A reusable route pair may be learned even when the user does not want a current Trip occurrence created. Do not create a Trip merely because a Route was updated.
- Use stable `MILE-###` rows and preserve corrections/voids in place. Settlement evidence outranks estimates.
- Freeze the applicable rate on each historical mileage row so future rate changes do not rewrite prior gross estimates.

## Routes, terminal pairs, trips and imported run sheets

Read `references/route-weather.md` before changing route/trip/runtime/departure/ETA/location/arrival/watch state.

- `Routes` is the learned reusable terminal-pair database; `Trips` and Mileage Log are occurrence history. Never create a parallel route database for an employer/shared run sheet.
- **Standing paid-mile rule:** company-paid terminal mileage is symmetric by terminal pair. Once A↔B is reconciled, write/use the same paid-mile value in both `Paid Miles A → B` and `Paid Miles B → A`, unless the user later gives an explicit exception for that pair.
- Route geometry/runtime may remain directional even when paid miles are symmetric.
- A shared/employer run sheet is an evidence source. Reconcile/upsert into existing Routes/Trips/Mileage using the strongest stable source/date/terminal/run identifiers; do not duplicate an occurrence already represented.
- Historical source variants and obvious human-entry errors remain provenance. For a reusable Route value, prefer explicit user/company corrections, then current/latest consistent evidence, then a strong repeated/modal value. Material conflicts that cannot be reconciled must be surfaced rather than silently averaged.
- When a paid-mile pair is learned, update the reusable Route record. Record an actual Trip/Mileage occurrence only when that leg happened and occurrence tracking is enabled/supported.
- Preserve terminal codes when location identity is unknown; enrich later rather than guessing a city from a similar code.

## Calendar projection state

- `Calendar Projection` is the dedupe/link table for optional projections from canonical LifeOS state to Google Calendar.
- Calendar projection is opt-in by event type. Never assume that enabling appointments also enables deliveries, work travel, trials, bills, deadlines, routines, study sessions or tasks.
- Each projected event stores source type/source ID plus Google Calendar event ID so revisions update the existing event instead of creating duplicates.
- If source state changes, update/cancel the linked event according to that user's selected policy. Calendar is a presentation/scheduling surface; the underlying Sheet remains authoritative.
- Do not create a new automation per calendar event.

## Inbox and shipment maintenance

Read `references/email-reconciliation.md` before order-mail processing, shipment mutations, Gmail filing, archive approval or deletion. The standing 90-day FedEx/UPS/DHL/USPS carrier-retention exception lives there; all other Gmail deletion still requires explicit bounded authority.

## Automation maintenance

- Keep the scheduled prompt a thin dispatcher, not a policy copy.
- Keep exactly one active **standalone** `LyfeOS Control Cycle` schedule at 2:45 AM/PM Eastern. Each run starts from the saved prompt, not a long-lived operational chat. It runs receipt/order lifecycle work, the PM qualified-job watch, and the brief as module-isolated phases and returns one fresh user-facing brief identified by its deterministic Run ID.
- Keep no separate active Ops Brief, Receipt & Order Lifecycle, or Qualified IT Job Watch task after consolidation readback succeeds.
- Scheduled runs never inspect/mutate automation definitions.
- The canonical timezone is scheduling authority. Current device/location/travel timezone and HOME/ROAD mode are context only.
- Runtime execution must invoke `scripts/ops_policy.py slot-check` without `--now`. The executable captures its own current offset-aware UTC instant, converts it into the canonical IANA timezone, and compares that canonical local clock with the intended slot. Never let the model/prompt construct a timestamp or use the device/travel clock, a static UTC offset, or a hand-maintained UTC offset as the execution gate.
- Do not delete a chat that currently anchors an active Scheduled Task. Durable operational content still lives outside chat, but the active task anchor is a platform dependency until retired or deliberately migrated.

### Canonical runtime clock

For the reference deployment, the authoritative clock is `America/New_York`.

Use the standard-library IANA timezone database, conceptually:

```python
canonical_now = now.astimezone(ZoneInfo("America/New_York"))
```

The consolidated control-cycle scheduled entry is valid only when the canonical local clock is `02:45` or `14:45`.

The same instant may be displayed as 2:45 Eastern, 1:45 Central, 12:45 Mountain, 11:45 Pacific, or the equivalent UTC time. For example, an August instant expressed as `12:45-06:00` in Denver converts to `14:45-04:00` in New York and matches the PM Ops slot. `12:40-06:00` converts to `14:40-04:00` and does not. Winter offsets change automatically through IANA DST rules.

Do not encode “Denver is two hours behind” or similar seasonal assumptions. Do not mutate the canonical schedule because the user travels.

A scheduled canonical-slot mismatch is a scheduler integrity failure. Stop downstream state-changing modules, read back/preserve known-good state, and apply the Module Circuit Breaker Report scheduler boundary. A manual brief is not rejected merely because it is invoked outside a scheduled slot.

### Scheduler integrity gate

A visible `TZID=America/New_York` or correct RRULE is necessary but not sufficient. A connector field merely named `default_timezone` is not automatically authoritative. Scheduler health is an evidence chain.

Before any automation create/update/consolidation:
1. read the canonical IANA timezone from policy/state;
2. snapshot each affected job's title, prompt, schedule, enabled state, timing mode, notification state, last-run metadata, and any provider field whose contract explicitly defines persistent task execution state;
3. inspect current provider/task capability and prefer editing the existing notification-capable canonical dispatcher unless its chat-bound delivery context is the diagnosed fault; production target state is a standalone task whose runs start from the saved prompt;
4. perform only the smallest required mutation.

After every automation create/update:
1. read the task back from the provider;
2. verify exact title, enabled state, cadence/local clock time/RRULE, intended TZID, timing mode, required notification state, and duplicate count;
3. treat `default_timezone` or similar metadata as execution authority only when the provider/tool contract explicitly says it is persistent task execution state. Travel/device/session location is diagnostic context, not proof;
4. require exactly one active standalone canonical control-cycle job and no active Ops/lifecycle/job-watch/child/retry/legacy duplicates;
5. require the entered runtime to pass the IANA canonical-clock gate;
6. require the next actual firing or canonical Run Log evidence to land in the intended canonical local slot before declaring a scheduler incident cleared.

For the Ops Brief dispatcher, the first external mutation after deterministic scheduled entry should upsert its canonical Run Log row as `Running` with Started (ET) before other state-changing module work. At completion, update that same row. This separates “scheduler never entered” from “scheduler entered and downstream work failed.”

Do not report a timezone/scheduler repair successful from VEVENT text, a `default_timezone` label, notification configuration, or a local/device clock alone.

If the intended slot is missed despite correct task readback:
- stop further scheduler mutation after the bounded diagnostic attempt;
- preserve the safest known canonical dispatcher and manual workflows;
- generate `Module Circuit Breaker Report — automation scheduler`;
- diagnose platform pause/deletion/inactivity, notification delivery, usage limits, task-anchor chat deletion, canonical-clock mismatch, and scheduler/runtime failure as separate possibilities;
- do not compensate with UTC/Pacific aliases, hidden hourly checks, AM/PM child tasks, or travel-location-specific schedules.

If the provider contract explicitly exposes a persistent execution-timezone field and that authoritative field disagrees with canonical time, treat it as a real integrity failure. If the field's semantics are undocumented/ambiguous, do not repeatedly recreate tasks merely to chase it; require observed execution evidence instead.

### Healthy consolidation transaction

For ordinary changes, update the existing notification-capable Ops job in place when possible. Replace it only when a diagnosed chat-bound delivery context can resurface stale responses; the replacement must be a standalone task and must be verified before the old anchor is paused.

To consolidate existing Ops, lifecycle, and qualified-job jobs without burning another active task slot:
1. snapshot exact job IDs/prompts/schedules/titles/timing/notification states and last-run metadata;
2. harmlessly verify required authorities and scheduler capability;
3. convert the notification-capable Ops job into the canonical standalone `LyfeOS Control Cycle` at 02:45/14:45 Eastern, or create a verified standalone replacement when the old chat anchor is the fault;
4. read it back and verify title, schedule, timing, timezone, enabled state, and notification state;
5. only then pause the separate lifecycle and qualified-job jobs;
6. re-inspect and require exactly one active canonical job;
7. on deterministic mutation/readback failure, restore the verified snapshot once and read it back;
8. do not clear a prior scheduler incident until the next actual canonical firing is proven.

Never create AM/PM child jobs, hidden retries, per-order jobs or support schedules.

## Repository and Project-instruction synchronization

- Treat the configured Git repository as the **sole source of truth** for lasting policy, code, tests, onboarding, schemas and recovery contracts. The installed skill is a deployed runtime copy, never a competing authority.
- Repository visibility is an explicit owner choice verified from provider metadata. Public source requires the public-source audit to pass; private source follows the same no-secrets rule.
- Standing authorization covers scoped commits/pushes of non-secret durable changes without asking for a separate Git confirmation. Mutable Sheets/Gmail/calendar/account data never belongs in source control.
- Never change repository visibility, merge/release outside configured authority, force-push, commit secrets, or export mutable personal state by implication.
- The ChatGPT Project-instructions field is not writable from every surface. Repository code must never claim it silently changed that UI field.
- Prefer a stable bootstrap contract in Project instructions: fixed authorities, safety boundaries and repo/skill indirection. Routine policy/feature changes should update Git/skill without changing the Project field. Change the bootstrap only when its authority/safety/recovery contract changes.
- When the Project bootstrap genuinely changes and no direct Project-instructions write tool exists, return the full replacement under `PROJECT INSTRUCTIONS UPDATE`; never make the user splice a patch.
- If Git write/verification is unavailable, report `Action Required — repository synchronization unavailable` and do not claim the lasting change is fully saved.

## Continuation and recovery

Clear equivalents of “continue Daily Briefs,” “old chat is gone,” or “pick this up here” are bootstrap commands. Re-read canonical authorities and continue without requiring prior chat history.

When a newly available capability would materially improve reliability or maintenance, surface one concise `OPTIONAL UPGRADE` with benefit/tradeoff. Never install/connect/migrate a new external service without approval.

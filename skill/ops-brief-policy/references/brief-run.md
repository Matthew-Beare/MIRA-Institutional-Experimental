# Scheduled and Manual Brief Run

Load this reference completely for one AM or PM Ops Brief. Do not inspect automations, repositories, personal context, broad web results, skill registries, or state-maintenance instructions during the run. Browse only the explicit weather sources when the engine opens a weather gate.

## Fixed inputs

Read these exact Ops Status Register core ranges once:

- `Tasks!A1:L500`
- `Control!A1:I200`
- `Routes!A1:P500`
- `Trips!A1:O1000`
- `'Travel Settings'!A1:F100`
- `'Run Log'!A1:U1000`

Read `Shipments!A1:N500` before Gmail reconciliation. After all required shipment mutations, read `Shipments!A1:N500` exactly once more; that second read is authoritative for the rendered shipment section. Do not render from the pre-reconciliation read.

Read these Purchase & Receipt Archive ranges once:

- `Order Events!A1:Q1000`
- `Classification Queue!A1:L500`

Use the latest prior successful `Completed (ET)` value from Run Log as the delivery-event cutoff. If the receipt workbook is unavailable, mark the brief `Degraded`, skip delivery-once, financial-resolution exceptions, and classification rendering, and continue with the active shipment queue.

From `Order Events`, also resolve the latest financial-correction state per Receipt ID. A latest unresolved `Financial Resolution Overdue` / equivalent `financial_resolution_overdue` event remains an `ACTION REQUIRED` item until a later `Financial Resolution Verified`, `Refunded`, `Revised Before Settlement`, or `No Refund Required` event resolves it. Never infer resolution merely because the order was cancelled.

Read these exact Mileage & Pay Tracker ranges once:

- `'Mileage Log'!A4:O504`
- `Settings!A3:B8`

Mileage/pay is section-scoped, not a global prerequisite. If either mileage range is unreadable or unavailable on a non-Thursday run, skip the mileage section and continue without turning the whole run into `Error`. If either is unavailable on Thursday, continue all other valid sections, mark the completed run `Degraded`, and emit exactly `Action Required — mileage/pay Sheet unavailable`. HOME/ROAD mode never suppresses a Thursday mileage summary. Thursday reports the closed work-cycle total; operational mileage accrual normally closed on Wednesday HOME arrival or earlier Home early.

Read connected Google Calendar far enough ahead to cover the next seven days. Calendar is non-authoritative evidence: after one failed or unavailable call, use an empty appointments list, mark the run `Degraded`, and continue.

Appointment rendering is slot-based and independent of HOME/ROAD mode: the Saturday 2:45 AM brief shows appointments from Saturday through Friday (a half-open seven-calendar-day window); every other 2:45 AM brief shows appointments occurring that calendar day; every 2:45 PM brief shows appointments occurring the following calendar day. This produces the requested day-before and morning-of reminders without exposing confirmation state.

## Canonical runtime clock gate

The scheduled dispatcher is defined in `America/New_York`. Travel, device, session, or caller timezone is context only and **never** changes the scheduled slot.

For every entered scheduled brief:

1. immediately run `python3 scripts/ops_policy.py slot-check --timezone America/New_York --pretty` **without `--now`**;
2. require `clock_source: runtime_system_clock`; never let the model, prompt, device, session, or travel location construct or guess the production timestamp;
3. the executable captures its own offset-aware UTC instant, converts it with `ZoneInfo("America/New_York")`, and returns `canonical_now`, `canonical_clock`, and slot evidence for `02:45` / `14:45`;
4. if the provider hands control to the runtime up to 60 seconds early, the executable waits once until the slot and recaptures its own clock; it never waits out an earlier dispatch or creates a retry task;
5. derive AM/PM from the **canonical New York clock**, not from travel/device time or a hard-coded UTC offset;
6. proceed only when `entry_allowed` is true. Outside the bounded window, do not perform Gmail/Calendar/Drive/mileage or other downstream mutations; preserve/read back known-good state and apply the Module Circuit Breaker Report scheduler boundary.

A manual brief is not rejected merely because it is invoked outside a scheduled slot. Manual invocations still use `America/New_York` for all canonical date/slot semantics.

This guard intentionally makes an instant such as `2026-08-23T12:45:00-06:00` evaluate as `14:45` in New York, while `12:40-06:00` evaluates as `14:40` and does not match. DST comes from IANA timezone rules, never hand-maintained offset math.

## Deterministic pass and entry log

1. Use the `canonical_now` returned by the live system-clock gate as the exact `now` input and derive AM/PM from its logical slot. Never recapture, round, or invent a second start timestamp.
2. Build UTF-8 JSON with the raw range arrays and Calendar evidence:

```json
{
  "now": "current offset-aware ISO-8601 instant",
  "brief_slot": "AM or PM derived from canonical America/New_York clock",
  "strict_inputs": true,
  "tasks_values": [["Task ID", "..."], ["TASK-001", "..."]],
  "control_values": [["Record ID", "..."], ["CTRL-001", "..."]],
  "routes_values": [["Route ID", "..."], ["ROUTE-001", "..."]],
  "trips_values": [["Trip ID", "..."], ["TRIP-001", "..."]],
  "travel_settings_values": [["Setting ID", "..."], ["TRAVEL-001", "..."]],
  "mileage_values": [["Entry ID", "..."], ["MILE-001", "..."]],
  "mileage_settings_values": [["Setting", "Value"], ["Rate per mile", "<verified live rate>"]],
  "appointments": [{"id": "...", "title": "...", "start": "ISO-8601", "end": "ISO-8601", "preparation": "optional"}]
}
```

When mileage/pay is unavailable, omit or pass the failed mileage datasets as unavailable input to the hardened runtime; do not manufacture a readable-looking fake range.

3. Run `python3 scripts/ops_policy.py resolve --input <json-file> --pretty` from the skill directory.
4. Treat the result as authoritative for mode, input health, weather gates, mowing focus, route-watch eligibility, trip status, mileage/pay summary, actions, appointment items, task rendering, Run ID, Run Log base fields, and `canonical_clock_evidence`. Mode precedence is live unexpired explicit override, then an active trip, then the weekly default. Company-paid terminal mileage is symmetric by canonical terminal pair unless an explicit exception is recorded; route geometry/runtime may remain directional.
5. For a scheduled brief, require `canonical_clock_evidence.slot_match: true` before downstream mutations. For a manual brief, record the evidence but do not use slot mismatch as a rejection condition.
6. Accept `status: ok` or `status: degraded` as completed deterministic results. If execution fails or returns `status: error`, render its error compactly under `ACTION REQUIRED`; never improvise the failed policy.
7. **Before Gmail, Calendar-projection, shipment, weather-state or other downstream mutations**, locate the deterministic Run ID in the loaded Run Log and upsert that exact row as `Running`, mapping engine fields by exact header name rather than dictionary order. Set `Started (ET)` to the actual canonical Eastern start time and preserve policy/mode/input/action plus logical slot, effective scheduled instant, dispatch delay/state and DST adjustment. If the Run Log itself cannot be written, do not continue state-changing downstream modules; report the blocker. A retry updates the same Run ID and never creates a second row.
8. Set `Weather Watch` to `Off` for every returned `expired_watch_trip_ids` value while retaining the trip row.

Loss of the Ops Status Register as a whole, deterministic policy failure unrelated to an isolated section, a scheduled canonical-slot mismatch, or a required mutation failure makes the run `Error`. A mileage/pay read failure alone is never a global `Error`; Thursday becomes `Degraded` with the explicit mileage action, and other days simply continue without that section.

## Bounded evidence pass

Perform one bounded pass per applicable external source. Run only the planned queries and never recursively delegate or block completion on Gmail, Calendar, NWS, or DOT/511. A failed non-authoritative source makes the run `Degraded`; finish with the evidence that succeeded. Retry only when the failure is plausibly transient/idempotent and the Module Circuit Breaker policy permits the one bounded retry.

### Gmail

- Load and follow `references/email-reconciliation.md`.
- Search new material since the latest completed brief, or the prior 24 hours if none exists.
- Separately inspect each active shipment by exact order number and tracking number, then inspect carrier/vendor delivery evidence first received since the latest completed brief. Search USPS, FedEx, UPS, and DHL evidence when applicable; absence of one carrier is not evidence of delivery.
- Cap each search at 50 results and read at most 20 materially relevant complete threads total.
- Surface only material medical, financial, employment, school, vendor, appointment, subscription, fraud, or security changes relevant to the deployment.
- Normalize materially relevant order/carrier facts and run `python3 scripts/reconcile_shipments.py reconcile --input <json-file> --pretty` with the pre-reconciliation `Shipments` values. Apply its active-row upserts and delivered-row deletions to the Sheet, then perform the Gmail filing transaction in the email-reconciliation workflow.
- Explicit user delivery statements outrank carrier evidence; carrier delivery/progress evidence outranks vendor status. Never infer delivery from age, an ETA, or a vendor's shipped notice.
- Re-read `Shipments!A1:N500` after mutations. Show active rows as `Item — ETA <date>` or `Item — No ETA`; add status only for a material exception.
- From `Order Events`, show each credible delivery observed after the previous successful brief exactly once as `Delivered — <item>`. Do not retain it in the active queue or show it on later briefs.
- From `Classification Queue`, render unresolved rows under `ACTION REQUIRED` as compact questions with exact vendor/order/item and the smallest useful choices. Do not infer an answer from silence.
- From current unresolved financial-resolution events, render one compact `ACTION REQUIRED` line per overdue Receipt ID after the five-business-day gate. Do not create a new reminder job or send a vendor email automatically.
- Search `in:inbox label:"Ops/Archive Approval"` after filing. Group related messages into concise decisions under `IMPORTANT EMAIL`, retain them in Inbox, and end that section with the exact line `Is it OK to archive these emails?`. If the user did not answer the prior brief, repeat the queue unchanged. Do not treat silence as approval.
- Never send email automatically. Do not delete Gmail outside the standing audited carrier-retention rule or an explicit bounded user request.
- Do not search promotions, calculate discounts, or monitor sales.

### Weather

- When `home_weather_allowed` is true, check the configured home location only if weather materially affects a HOME decision.
- When `mowing_weather_focus` is true, prioritize recent/forecast rain, drying, wetness, and realistic mowing windows. Use the deployment's configured mowing season.
- Never render HOME weather in ROAD mode unless deployment policy explicitly allows it.
- When `route_weather_allowed` is true or a travel action requires input, load and follow `references/route-weather.md`. Otherwise do not mention or inspect route weather.

## Finalize Run Log

After evidence and required mutations finish, update the **same** deterministic Run ID row created as `Running` at entry. Never create two rows for one Run ID.

- Keep the original `Started (ET)` and set `Completed (ET)` to the actual canonical Eastern completion timestamp.
- Preserve engine policy version, mode, input health, action count, canonical clock evidence, and error notes.
- Use `OK` when all requested checks complete, `Degraded` for a completed brief with a non-authoritative or isolated section failure including Thursday mileage/pay unavailability, and `Error` only for core policy/authority, scheduled canonical-slot integrity, or required-mutation failure.
- In `External Evidence`, write only concise tokens such as `Calendar: OK; Gmail: 2 material threads; NWS: clear`.
- In `Mutations`, write only stable IDs or `None`; never copy message bodies, secrets, or the full brief.
- If final logging fails after downstream work, preserve the known-good mutations, do not create a second Run ID, and surface the incomplete final-log state under the Module Circuit Breaker recovery boundary.

## Output contract

The first line is exactly the deterministic Run ID returned by the engine, such as `OPS-2026-08-24-PM`. This makes every delivered notification self-identifying and prevents an old chat response from passing as a current brief. Generate the response only from the current run; never quote, summarize, or reuse prior chat output.

Render only nonempty sections in this order:

1. `WEATHER`
2. `ROUTE WEATHER`
3. `SHIPMENTS` (active shipments plus newly observed deliveries exactly once)
4. `UPCOMING APPOINTMENTS`
5. `IMPORTANT EMAIL`
6. `OPS STATUS`
7. `MILES & PAY`, only when `mileage_summary_due` is true and a summary is available
8. `IMPORTANT` or `ACTION REQUIRED`, only when necessary
9. `TRIP STATUS`, always last when returned

Insert `ops_status_markdown` and `mileage_summary_markdown` verbatim. Render only `appointments_due`, chronologically, and never expose confirmation state. Render `IMPORTANT EMAIL` only from the current `Ops/Archive Approval` Inbox queue and always include its exact archive question. Keep the brief brutally compact: no empty headings, `None`, `Nothing new`, delivery history, or combined task bullets.

# Automation Contracts

Scheduled prompts are dispatchers, not policy databases. Durable behavior lives in the skill/repository and mutable state lives in canonical authorities.

## Scheduling timezone integrity

Every deployment has one canonical IANA timezone. A scheduled job is healthy only when both the provider definition and the runtime canonical clock agree with that timezone.

Required evidence:

1. the normalized VEVENT/RRULE contains the intended local clock time and explicit canonical `TZID` when the scheduler supports it;
2. exactly one intended dispatcher is enabled with the expected `timing_mode`;
3. notification channels required by the user are enabled;
4. at execution, the policy executable captures its own system UTC instant, converts it through the IANA timezone database into the canonical timezone, and that canonical local clock matches the intended slot;
5. after creation or repair, an actual firing and canonical Run Log entry land in the intended local slot.

Do not infer scheduler health from a field merely named `default_timezone`. Connector/tool readbacks may expose current session, device, or travel timezone rather than persistent scheduler execution state. Treat such a field as authoritative only when the provider/tool contract explicitly defines it as the task's stored execution timezone.

### Canonical runtime clock

Execution-time comparisons never use a model-constructed timestamp, the user's current travel/device timezone, or a hand-maintained UTC offset. The scheduled entry invokes `slot-check` without `--now`; the executable captures its own offset-aware UTC instant and converts it with the configured IANA timezone, conceptually:

```python
canonical_now = now.astimezone(ZoneInfo(canonical_timezone))
```

Then compare `canonical_now.hour` / `canonical_now.minute` to the configured local slot. This makes DST an IANA database concern rather than a pile of seasonal arithmetic.

For the reference Ops Brief in summer, `14:45-04:00` Eastern, `13:45-05:00` Central, `12:45-06:00` Mountain, `11:45-07:00` Pacific, and `18:45Z` are the same instant and all resolve to the valid 14:45 New York PM slot. `12:40-06:00` resolves to 14:40 New York and is not valid. Winter offsets change automatically through the IANA database.

For every create/update/consolidation:
- snapshot existing jobs before mutation;
- prefer editing the existing notification-capable canonical dispatcher over replacing it;
- write the smallest required change;
- read the task back;
- verify title, enabled state, exact recurrence, intended local time, visible TZID, timing mode, required notification state, and duplicate count;
- if replacement is unavoidable, verify replacement notification state before disabling the known-good dispatcher;
- verify the next actual firing or canonical Run Log entry before declaring a scheduler incident cleared.

For every entered scheduled run:
- run the deployment's canonical-clock guard without `--now` before downstream state-changing modules and require `clock_source: runtime_system_clock`;
- if the canonical slot evidence does not permit entry, do not reinterpret travel/device time, do not proceed as if the intended slot fired, and apply the scheduler Module Circuit Breaker Report boundary;
- preserve the known-good scheduler definition and canonical state rather than manufacturing compensating UTC/Pacific/local jobs.

Leaving ChatGPT Work, closing the app, changing HOME/ROAD mode, or being physically away from home does not redefine the canonical schedule. Platform-level task pause/deletion/inactivity behavior is a separate condition.

## Cross-authority transaction isolation

Independent authorities are not treated as one distributed database transaction.

For every declared cross-authority projection or side effect:

1. identify the canonical source authority and stable source identity;
2. commit the canonical source mutation first and read it back;
3. derive desired target state from the verified source plus current target state;
4. write the target projection using stable correlation identity;
5. read the target back before marking that projection healthy;
6. if the target fails, preserve the canonical source record and mark only the target projection/module `Degraded` or `Pending`;
7. on a later run, reconcile source-to-target from current canonical state instead of replaying a blind mutation or creating a hidden retry job.

Never roll back, clone, renumber, or delete canonical source identity merely because an unrelated target is unavailable. Do not create active-active shadow state as an outage workaround. A provider-wide outage may affect several resources hosted by that provider, but unrelated providers/modules continue when their own invariants remain healthy.

## Consolidated LyfeOS Control Cycle

Title: `LyfeOS Control Cycle`

Delivery context: standalone scheduled task; every run starts from the saved prompt instead of returning to a long-lived chat.

Schedule: `RRULE:FREQ=DAILY;BYHOUR=2,14;BYMINUTE=45;BYSECOND=0` with `TZID=America/New_York`.

The dispatcher invokes `$ops-brief-policy` for the current **canonical Eastern** slot. Runtime uses `scripts/ops_policy.py slot-check` with no `--now`; the executable captures its own clock and verifies that the instant falls within the bounded dispatch window around 02:45 or 14:45 in New York before downstream module mutations. If execution is handed off up to 60 seconds early, it waits once until the slot and recaptures the system clock; anything earlier is rejected. The post-slot grace remains 15 minutes, and the deterministic Run ID prevents a later retry from becoming a second run.

On the spring-forward date, a configured local time inside the nonexistent clock gap resolves to the first valid local instant after the gap. On fall-back, an ambiguous local slot uses only its first occurrence. The Run Log records the logical slot, effective instant, delay and DST adjustment so one logical slot cannot enter twice.

The dispatcher must not contain mutable task/route/order/routine/job data or inspect/mutate automations during a scheduled run. It runs receipt/order lifecycle reconciliation, the PM qualified-job watch, and the Ops Brief as module-isolated phases, then emits one fresh brief whose first line is the deterministic Run ID. It never quotes or reuses an earlier chat response. Context such as HOME/ROAD may change brief contents; it does not change dispatcher timezone.

The first external mutation after deterministic entry should upsert the canonical Run Log row as `Running`; completion updates that same row. Missing Run Log evidence after an intended slot is a scheduler/runtime incident, not silent success.

Within the control-cycle service, a writable core Ops Run Log is an intentional entry barrier for downstream state-changing modules. This is a service-local safety dependency, not a distributed transaction: a failed Ops Brief phase does not roll back a successful receipt/order lifecycle or qualified-job phase, and a failed lifecycle/job phase does not block a safe brief.

### Receipt & Order Lifecycle phase

Phase responsibilities:
- invoke `$ops-brief-policy` against live canonical authorities;
- apply receipt ingestion/photo intake, classification/fitment, email reconciliation, payment reconciliation, beneficiary/reimbursement, active Shopping & Procurement reconciliation, and vendor-contact approval policy as applicable;
- commit/read back the canonical Purchase & Receipt Archive transaction before reconciling downstream Ops `Shipments`, shopping, or asset/inventory projections;
- if a downstream projection is unavailable, preserve the canonical Receipt ID/order/event/allocation/evidence and report only that projection `Degraded/Pending`;
- later retries re-derive desired target state from canonical purchase state and current target state rather than cloning/replaying the purchase;
- reconcile same-order revisions before matching account charges;
- keep expected charges open until settlement/no-settlement resolution;
- investigate unmatched/over/undercharges rather than guess;
- keep reimbursements separate from merchant refunds;
- dedupe evidence arriving from multiple conversations/sources;
- remove a fulfilled active shopping intent only after durable purchase/owner-confirmation evidence and verification; missing receipt/product identity remains a separate reconciliation task;
- if external contact is needed, validate the recipient/no-reply state and official support channel, then notify with recipient, subject, full proposed message, and `Do you want me to send this email?`;
- never send external email in the scheduled run;
- never create per-order/child/retry automations;
- never inspect or mutate automation schedules during a scheduled run.

Only meaningful lifecycle/payment/reimbursement/shopping changes, exceptions, classification questions, and contact-approval proposals are folded into the one brief.

### Qualified IT Job Watch phase

The PM logical slot scans connected Gmail using the candidate baseline and exclusion rules in `qualified-job-watch.md`, deduplicates through the canonical `Job Watch` table, and folds only new likely fits or one specific blocker into the brief. It never applies, replies, contacts anyone, or sends email. Failure is scoped to the job-watch module.

## Accountability / study scheduling

Starter deployments may opt into recurring routine or study check-ins. These use the fewest scheduled dispatchers practical, preserve mutable routine/study state in canonical authorities, and obey the same scheduler evidence chain and IANA canonical-clock guard. Do not create one permanent automation per exercise, assignment, course, project, or session when a consolidated dispatcher can resolve due items from state.

# Automation Design

One standalone recurring control-cycle task dispatches both daily briefs and owns the lifecycle/job phases. Every run starts from the saved prompt rather than returning to a long-lived chat:

```text
BEGIN:VEVENT
DTSTART;TZID=America/New_York:<next local 02:45 or 14:45>
RRULE:FREQ=DAILY;BYHOUR=2,14;BYMINUTE=45;BYSECOND=0
END:VEVENT
```

The dispatcher immediately runs the installed `ops_policy.py slot-check` without `--now`; the executable owns the production clock and derives AM/PM from New York time. Each run first performs module-isolated receipt/order lifecycle work, the PM run performs the qualified-job scan, and then it renders one freshly generated brief beginning with the deterministic Run ID. This retains two brief deliveries while consuming one active task slot.

Scheduler verification is an evidence chain. After create/update, verify title, enabled state, recurrence/local time/TZID, timing mode, required notification state, and duplicate count. A field merely named `default_timezone` is not authoritative unless the provider contract explicitly defines it as persistent task execution state. Do not clear a scheduler incident until a subsequent actual firing or canonical Run Log entry lands in the intended New York slot.

## Legacy-task migration

1. Snapshot the active Ops, lifecycle, and qualified-job jobs, including notification state and last-run metadata.
2. Verify the Ops Sheets, Gmail, Calendar and scheduler dependencies with harmless reads.
3. Update one healthy notification-capable legacy job in place to the combined title, prompt and schedule unless its long-lived chat anchor is the diagnosed stale-delivery fault; in that case create a standalone replacement.
4. Re-inspect and verify that job's schedule, timing mode and notification state.
5. Pause the separate lifecycle and qualified-job jobs—or the contaminated chat-bound dispatcher—only after the standalone surviving dispatcher is verified.
6. Re-inspect and verify exactly one active canonical `LyfeOS Control Cycle` job.
7. Require the next actual canonical firing before declaring a prior scheduler incident cleared.
8. Restore the snapshot if a deterministic mutation/readback fails and rollback can be proven.

Updating in place avoids needing a temporary extra task when the account is already at its active-task limit and avoids accidentally replacing a notification-capable dispatcher with a silent one.

## Receipt, order, and job phases

The receipt/order phase scans direct merchant/carrier mail and authorized forwarded evidence, updates the normalized receipt tables, synchronizes active Ops shipments and Gmail labels, refreshes Drive filing and inventory side effects, and rebuilds the Audit gate. It never creates per-order scheduled tasks, reminders, retry jobs, or child automations.

If the deployment opted into Calendar Projection for order deliveries, the lifecycle may create or update the one source-linked Google Calendar event through the canonical `Calendar Projection` dedupe table. That is a calendar projection, not a per-order automation, and ETA revisions update the existing event rather than creating another one.

The lifecycle phase commits only when Gmail, Drive, Orders, Details, Order Events, Expense Ledger, Classification Queue, Audit, and any required Shipment/Tool Inventory/shopping side effect agree. A failed check leaves the source thread unarchived and produces one actionable failure in the brief.

The PM qualified-job phase uses the canonical `Job Watch` table for dedupe and scans only realistic entry/junior IT families. It never creates a second monitor task and never applies, replies, or sends email.

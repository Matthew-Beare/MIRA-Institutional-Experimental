# Consolidated LyfeOS Control Cycle

Load this reference completely for the single scheduled `LyfeOS Control Cycle`. Its purpose is one scheduler with module isolation, not one giant all-or-nothing transaction.

## Entry and output contract

- The only scheduled entries are 02:45 and 14:45 `America/New_York`. The standalone dispatcher immediately runs `scripts/ops_policy.py slot-check` without `--now`; the executable owns the production clock, converts it through the IANA canonical timezone, and absorbs at most the bounded early-dispatch jitter before entry.
- The first external mutation is the deterministic Ops Run Log upsert to `Running` with Started (ET). Completion updates the same row.
- Return exactly one newly generated user-facing Ops Brief beginning with its deterministic `OPS-YYYY-MM-DD-AM|PM` Run ID. Lifecycle, job-watch, and module-failure findings are folded into that brief; do not emit separate scheduled notifications, quote old responses, or reuse chat output.
- A manual control-cycle run may occur outside the scheduled slot when the owner explicitly requests it.
- Scheduled runs never inspect or mutate automation definitions.

## Fixed phase order

1. **Entry:** run the live system-clock slot guard with no caller-supplied timestamp and upsert the Run Log.
2. **Receipt/order lifecycle:** run the applicable email, receipt, classification/fitment, asset-identity/relationship, shopping, payment, reimbursement, shipment, evidence, and contact-proposal workflows. Commit/read back canonical commerce state before downstream projections. After core receipt PASS, use `scripts/inventory_reconciliation.py` for supported receipt-line inventory effects and verify the exact receipt line → asset UUID → relationship targets before reporting the asset projection healthy. Run `scripts/asset_evidence.py` before identifier/evidence/manual/specification writes; write and read back each normalized target independently. Its receipt, UUID, and identifier query paths must converge on the same connected graph.
3. **Reminder reconciliation:** for explicitly enabled profiles, run `scripts/reminder_policy.py` and reconcile day-before, morning-of, and configured relative appointment reminders into the linked Calendar event. Medication reminder schedules require explicit supported evidence and activation. Read back provider projection state; do not create per-event ChatGPT automations and do not infer medical instructions.
4. **PM qualified-job watch:** only in the PM logical slot, run `qualified-job-watch.md`. The AM slot skips this phase unless canonical state proves the previous PM scan never completed and a bounded catch-up is safe.
5. **Ops Brief:** run `brief-run.md` from current canonical state and include only meaningful lifecycle/job/failure actions.
6. **Completion:** update the same Run Log row with phase outcomes and completion state.

## Failure isolation

- Each phase keeps its declared authority and failure domain. A receipt, Gmail, job-watch, mileage, Calendar, or Drive failure does not erase successful canonical work from another phase.
- Stop writes only in the failed module, preserve/read back verified state, record one concise phase failure, continue safe unrelated phases, and render one Module Circuit Breaker Report action in the brief when required.
- Never use distributed rollback, duplicate IDs, shadow state, hidden retries, child automations, or a second user-facing task to compensate.

## Idempotency

- Receipt/order work uses canonical Receipt IDs, lifecycle events, and projection identities.
- Job monitoring deduplicates against the canonical `Job Watch` table using stable Gmail message/thread identity plus normalized job URL or employer/title/location key.
- Re-entering the same deterministic Run ID cannot create another logical run, duplicate purchase, duplicate reminder projection, duplicate job report, or second brief.

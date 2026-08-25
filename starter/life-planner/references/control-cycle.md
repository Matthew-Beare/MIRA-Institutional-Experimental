# Control cycle and briefs

The user chooses cadence, local slots, IANA timezone, notification mode, sections, and anti-noise rules during onboarding. **There is no product-default brief time.** Do not inherit another deployment's schedule.

The version-controlled deployment schedule described in `brief-schedule.md` is the durable source of truth for recurring brief timing. The live scheduler is only a projection of that configuration. When the user changes a brief time, name, notification mode, timezone, or enabled state, update and validate their source configuration, commit/push/read it back, then reconcile and read back the scheduler definition.

## Scheduled entry

1. Capture the runtime's current offset-aware instant.
2. Convert it through the deployment's configured canonical IANA timezone.
3. Match it against the configured enabled local slot and bounded provider grace window.
4. Derive one deterministic Run ID from deployment UUID, canonical date, and slot.
5. Upsert the Run Log as `Running` before downstream provider mutations.
6. Run enabled modules independently from current canonical state and connected evidence.
7. Update the same Run Log row to `Complete`, `Degraded`, or `Blocked`, with module evidence.
8. Return only the current run's brief. Never reuse an earlier chat response.

A provider may need more than one physical scheduler object to represent arbitrary user-selected local times. Use the fewest objects needed without creating unintended extra firings, but treat them as one logical M.I.R.R.O.R. control-cycle service and keep the exact desired slots in version-controlled configuration.

## Manual smoke entry

A manual smoke test may exercise the actual brief pipeline at any wall-clock time. It bypasses recurring-slot eligibility only for that manual invocation, uses a distinct manual Run ID, and records that it is **not** scheduled-firing evidence. It never changes or substitutes for the user's configured schedule.

## Normal module order

1. Current context, tasks, routines, projects, and appointments.
2. Receipt/order/shipment/payment reconciliation when enabled.
3. Calendar reminder reconciliation when enabled.
4. Qualified-job monitoring when enabled.
5. Weather, travel, mileage/pay, meal planning, and other selected sections.
6. Compact next actions and exact blocked dependencies.

Each module declares its own authority and optional adapters. Continue healthy modules when another failure domain is unavailable.

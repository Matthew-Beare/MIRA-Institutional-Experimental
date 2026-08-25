# Receipt Ingestion and Inventory Side Effects

Load this reference completely before ingesting purchase receipts, filing receipt evidence in Drive, updating the receipt index, producing a receipt-based spending rollup, reconciling a shopping/procurement item, or applying an inventory side effect.

## Authorities

- Purchase evidence may come from complete Gmail/forwarded merchant mail, retained Drive evidence, authoritative carrier/vendor/account evidence when the selected workflow permits it, or explicit owner screenshot/chat confirmation. Gmail is an evidence adapter, not a mandatory ingestion gate; unavailable merchant email must not make a known purchase disappear.
- The Drive archive is `LyfeOS/02 Receipts & Purchases/Receipt Archive` with `00 Index & Database`, `01 Receipt Backups`, and `02 Receipts by Category`.
- `Purchase & Receipt Archive` is resolved through the private Authority Registry. Preserve its verified identity, validation, formulas, formatting, stable Receipt IDs, and foreign-key relationships.
- `Orders - Database` stores one row per underlying transaction; `Receipt Details - Expandable` stores searchable line items; `Order Events` stores append-only lifecycle transitions and related Receipt IDs; `Expense Ledger` stores cost allocations; `Classification Queue` stores unresolved user choices; `Financial Dashboard` is a derived email/receipt-detected view.
- `Shopping & Procurement` is an **active shopping list**, not purchase history or a second purchase ledger. It contains only open shopping intent. Durable fulfilled-purchase evidence belongs in the canonical Purchase & Receipt Archive/Drive history and any separate unresolved reconciliation queue/task.
- `Legacy - Purchase Receipts Full Text Archive - Search Backup` is backup text only. Never use it as the user-facing receipt view.
- User-facing Drive navigation must be a native Google Doc, native Sheet view, or supported Drive shortcut with a readable title. Never place raw HTML, JSON, Markdown, or source-code link cards in an active vehicle/tool hub; retain any such artifact only under backups.
- Enabled asset authorities are resolved through the private Authority Registry. `People & Assets` plus `Asset Relationships` hold canonical physical-asset identity/edges; Tool Inventory keeps detailed tool fields and exposes the same immutable-UUID contract. A receipt may update either only after the base receipt record is safely stored. They are downstream asset projections, not part of the purchase ledger's atomic commit.

## Failure-domain boundary

The canonical purchase transaction must not depend on unrelated projection targets being healthy.

- **Core purchase domain:** Purchase & Receipt Archive plus required retained receipt evidence in Drive.
- **Shipment projection:** active fulfillment projected into the Ops `Shipments` queue when that authority is healthy.
- **Shopping reconciliation:** active intent reconciliation after durable purchase/owner-confirmation evidence exists.
- **Asset/inventory projection:** Tool Inventory or another asset authority after the purchase is durable.

Commit canonical purchase state first. Then reconcile each downstream projection independently using stable Receipt/Order/line-item identities and target readback. A failed projection leaves the purchase committed and that projection unresolved/degraded; it must not roll back or duplicate the Receipt ID. On later runs, derive the desired projection again from canonical purchase state plus current target state. Do not create a second outbox database or hidden retry automation.

## Evidence and classification

- Include purchase receipts, paid invoices, order confirmations, or explicit owner evidence that establishes a transaction. Exclude shipping-only, delivery-only, marketing, quotation, cart, and abandoned-checkout messages unless another source supplies the purchase evidence.
- Extract only evidence-backed vendor, order or invoice number, purchase date, item description, quantity, subtotal, tax, shipping, discounts, total, payment suffix when present, and source-message/evidence identifiers.
- If merchant/order email is unavailable, not delivered to the connected mailbox, or otherwise missing from the connector, explicit owner screenshot/chat confirmation is sufficient to create the canonical purchase/lifecycle identity. Leave unavailable order number, tax, supported total, carrier, tracking and ETA blank; project unresolved fulfillment as `Awaiting Shipment` when applicable; mark spend/allocation unresolved when the supported total is incomplete; and enrich the same Receipt ID when later evidence appears. Never wait for Gmail and never invent missing fields.
- Deduplicate using the strongest available combination of vendor, order or invoice number, transaction date, amount, item identity, Gmail message/thread ID, owner-evidence identity, and attachment identity. Enrich the existing record when it is the same transaction.
- Search direct merchant/carrier mail and messages forwarded by user-approved mailbox aliases recorded in private configuration. For forwarded evidence, parse the embedded merchant sender, order number, items, amount, status, and tracking facts from the complete forwarded body; the outer sender alone does not invalidate the evidence.
- An explicit user correction outranks stale email. Preserve both in `Order Events` and annotate the correction source instead of erasing the earlier evidence.
- File into the narrowest supported category under `02 Receipts by Category`: Automotive, Bills & Utilities, Education, Electronics & Computer, Food & Dining, Health, House, Subscriptions & Services, Tools, Travel, or General. Do not invent a category from weak semantics.
- A transaction may have multiple non-exclusive categories, search tags, and related assets. Count it once by Receipt ID. Expense allocations may split the total across cost owners, but their sum must equal the single order total.
- Automotive canonical folders come from the live asset registry and Drive authority; never hard-code a deployment's vehicles in portable policy. Multi-vehicle orders use one configured shared folder plus link/reference cards. Tool receipts use the configured tools area; a tool may reference a vehicle without becoming a vehicle part.
- If classification, vehicle, cost owner, or product identity is materially ambiguous, do not guess. Add one unresolved `Classification Queue` row, apply `Shopping/Needs Classification`, exclude it from verified allocations, and let the next brief ask the smallest useful question.

## Shopping & Procurement reconciliation

- After a receipt/order is identified, compare its line items and intended use against open rows in `Shopping & Procurement` before creating any new shopping row.
- Match by strongest available evidence: explicit user intent/correction, exact product/part/SKU/model, vehicle/asset and purpose, merchant/order history, category, and timing. Do not close a vaguely similar shopping item merely because a purchase shares a category.
- A supported fulfilled match does **not** become a `Purchased` tombstone. First preserve the durable purchase/order/reconciliation evidence in the canonical Purchase & Receipt Archive, then remove the fulfilled shopping row from the active list after verification/readback.
- An explicit owner statement that a shopping intent was bought is sufficient to close/remove that active shopping intent even when exact receipt/product identity remains unresolved. Preserve the owner statement as provenance and keep the missing receipt/product identification as a **separate reconciliation task/queue item**; do not keep a known-bought item on the shopping list merely to remember the evidence gap.
- Same-order revisions and true replacement orders satisfy the same underlying shopping intent. Reconcile to the surviving product/order and remove the one fulfilled intent only after the replacement/purchase evidence is durable. Do not create duplicate shopping rows for the original, revision and replacement.
- A confirmed cancellation with no supported replacement does **not** fulfill the shopping intent unless the owner explicitly abandons/removes that intent. Leave it open (or clearly needing replacement when the active-list schema supports that distinction).
- Partial fulfillment closes only a specifically divisible supported portion. If the active-list row represents one indivisible intent and anything remains unfulfilled, keep the intent open with the smallest useful note rather than fabricating completion.
- `Shopping & Procurement` is not a spending ledger. Never add financial totals there in a way that can be summed as duplicate spend; Receipt IDs and the Purchase Archive remain financial truth.
- When an already-purchased item is discovered on a stale shopping row, reconcile it retroactively from canonical evidence or explicit owner confirmation, then remove the stale active row after verification.
- Row removal is a state mutation: target by the verified shopping intent/row identity, account for row-index shifts in batch operations, and read back the list after deletion so unrelated rows were not removed. If deletion/readback is ambiguous, stop shopping writes and invoke the Module Circuit Breaker Report rather than issuing blind compensating deletes.
- A shopping reconciliation failure after the core receipt commit is module-scoped. Preserve the receipt and leave only the shopping mutation unresolved; never delete/recreate the Receipt ID to retry shopping state.

## Cancellation, return, and refund transitions

- Treat a request as pending until the merchant or an explicit authoritative source confirms the financial/fulfillment result. Append `Cancellation Requested` or `Partial Cancellation Requested`, keep the active shipment in `Exception`, and do not change totals or spend flags while the revised charge/refund is unknown.
- For a confirmed full cancellation before shipment and before a settled charge, append `Cancelled`, retain the original order and searchable details, set the order/details/allocations to cancelled and `Include in Spend = FALSE`, and remove every matching active fulfillment only after the event is durable.
- For a confirmed partial cancellation, append `Partial Cancellation Confirmed`; retain the cancelled detail/allocation as history with `Include in Spend = FALSE`; update the surviving lines and order financial fields only from the merchant's confirmed revised totals; make included allocations sum to that revised total; and rewrite the active shipment to contain only the surviving fulfillment. If the revised total or surviving item is missing, keep `Exception` and surface one action instead of inventing a tax, fee, refund, or item split.
- A physical return does not erase spend. Append `Returned` and keep the original financial effect until exact refund evidence arrives. On `Refunded`, record the confirmed amount as a linked negative expense adjustment or confirmed revised net total, preserve gross purchase/refund evidence in `Order Events`, and make dashboards report the net effect exactly once.
- Never delete an order, detail line, allocation, or prior event because it was cancelled, returned, or refunded. Lifecycle state and spend inclusion change; identity and provenance remain.
- If the Ops `Shipments` authority is unavailable after a cancellation/revision is durably committed, keep the canonical purchase event authoritative and report the shipment projection as pending/degraded. Reconcile the target from canonical state when Ops recovers; do not undo the purchase event.

## Replacement and supersession

- First decide whether the merchant revised the same underlying order or created a new order. The same vendor/order number remains one Receipt ID and uses the cancellation/revision rules above. A distinct merchant order number or independently charged transaction gets a distinct Receipt ID.
- For a true replacement, preserve both transactions. Append `Replaced By` to the original and `Replacement For` to the new Receipt ID. Each event must carry the reciprocal `Related Receipt ID`, one shared `Replacement Group ID`, the source, and the observed time. Never mutate the old Receipt ID into the new one.
- A user statement that explicitly identifies the old and replacement orders is authoritative relationship evidence, but it does not prove a refund amount or revised charge. Preserve any earlier merchant evidence beside the user correction.
- Apply cancellation and refund accounting to the original independently. If cancellation is only requested or the old charge/refund is unresolved, keep the original active fulfillment as `Exception` and keep its supported financial effect. Never net, copy, or transfer totals between orders without exact evidence.
- Upsert the replacement as its own active fulfillment when Ops `Shipments` is reachable. When original cancellation is confirmed, canonical replacement/cancellation events commit first; the active fulfillment projection is then reconciled independently. If the projection target is unavailable, preserve both Receipt IDs/events and report the shipment projection pending rather than blocking the purchase records.
- Copy vehicle/category attribution only when the replacement item is proven equivalent or the user explicitly assigns it. Otherwise queue the new item for classification rather than inheriting a potentially wrong fitment.
- The core purchase Audit gate must verify that both Receipt IDs exist, reciprocal links agree, the shared group ID agrees, the original financial state follows cancellation/refund evidence, and the replacement has its own balanced allocation. Shipment projection consistency is a separate projection-health check and may be Degraded without invalidating the canonical receipt records.

## Core commit and downstream projections

Use this order so canonical purchase state is durable before any unrelated authority is touched and Gmail is never cleared before durable evidence exists:

1. Read and classify the complete available purchase evidence. Do not block a proven owner-confirmed purchase merely because merchant Gmail evidence is unavailable.
2. Check the canonical index and destination folder for duplicates.
3. Save the original receipt attachment when one exists. For email-only or owner-only evidence, create or update one concise, mobile-readable receipt record with a brief summary and expandable full details. Any vehicle/tool navigation record must be native and human-readable, never a raw source file.
4. Upsert one `Orders - Database` row and the searchable line items. Point the Receipt Browser's `Show details` link at that receipt's expandable range, never the legacy Doc.
5. Append each new Ordered/Awaiting Shipment, Shipped, Delivered, Exception, Cancellation Requested, Partial Cancellation Confirmed, Cancelled, Returned, Refunded, Replaced By, or Replacement For transition to `Order Events`. Link true replacements with reciprocal Related Receipt IDs and one Replacement Group ID. Idempotency is event ID plus Receipt ID, event type, event time, tracking/package or related Receipt ID, and source.
6. Upsert `Expense Ledger` allocations only when the supported transaction total is known and verify that allocations for one Receipt ID sum to the one counted transaction total. If only an item price is known and tax/shipping/fees/order total are unresolved, keep `Include in Spend = FALSE`/financial reconciliation pending rather than treating the partial item price as a complete transaction total.
7. Rebuild/refresh the **core receipt Audit** integrity gate. Require PASS for one order row per Receipt ID, at least one detail row, compact detail link, canonical Drive archive link when required/available, verified-or-queued classification, exact expense-allocation sum for financially complete included transactions, known vehicle mappings, vehicle-specific Drive placement/link when required, and reciprocal replacement links when present. The core receipt PASS does not depend on Ops Shipments, Tool Inventory, Calendar, or another module's authority being reachable.
8. After core PASS, reconcile the active Ops `Shipments` projection when reachable: Awaiting Shipment and Shipped remain active; Exception remains actionable; Delivered is removed after the canonical event is durably recorded. Read back the target. If Ops is unavailable or target readback disagrees, preserve the core receipt, mark only shipment projection Degraded/Pending, and stop writes to that target.
9. Reconcile `Shopping & Procurement` when applicable. Preserve any separate reconciliation task needed for missing identity/evidence, then remove only the fulfilled active-list row after purchase/owner-confirmation evidence is durable. Read back the shopping list and prove unrelated rows remain intact. Failure here does not roll back the core receipt.
10. Apply supported inventory/asset side effects only after core PASS through `scripts/inventory_reconciliation.py`. Deduplicate by immutable UUID and stable source identity; link the exact Receipt ID and exact receipt-line coordinate to the acquired asset UUID; then write explicit `owned_by`, `assigned_to`, `installed_on`, or other supported relationship edges and read back every target. A multi-quantity set/lot gets one UUID plus quantity unless individual serial tracking is actually useful. `assigned_to` must not be promoted to `installed_on` without installation evidence. Cancelled/excluded lines create no owned asset. For a tool, create/enrich the Tool Inventory row using evidence-backed attributes and its Entity UUID. Never guess brand, model, power source, platform, ownership, condition, classification, or relationship. If an asset authority is unavailable, preserve the receipt and report only the asset projection pending/degraded.
11. Verify each downstream projection independently. Projection success requires target readback. A projection failure trips only that projection/module under the Module Circuit Breaker Report; later reconciliation re-derives desired target state from canonical purchase records instead of replaying a blind write.
12. Gmail filing may occur after the core receipt/evidence transaction is verified. If a still-unresolved projection depends on the originating thread as the only convenient operational cue, retain that thread until the projection is reconciled; otherwise canonical Receipt ID/source IDs/Drive evidence are sufficient for replay. Never claim a pending projection succeeded merely because the receipt core passed.

If a core purchase/Drive write fails, leave any available Gmail message unarchived and report the exact incomplete stage. Do not claim the receipt was processed merely because one partial artifact exists.
If the core Audit fails, write the Receipt ID and remediation, leave affected Gmail threads unarchived when they exist, and surface one compact `Action Required` summary. A correct Sheet tag with a missing required evidence record is still a core failure.
If only a downstream projection fails, report the receipt as durably ingested with that projection explicitly `Degraded/Pending`; do not roll back, clone, or renumber the Receipt ID.

## Monthly receipt rollups

- A monthly rollup is an email/receipt-evidence-detected spending report, not a complete financial ledger or bank statement.
- Deduplicate confirmation, shipment, delivery, attachment, owner-evidence, and later-enrichment variants of the same purchase.
- Preserve the shared-Amazon rule: exclude only items strongly evidenced as another household member's purchase. Put ambiguous ownership or classification in `Classification Queue` instead of silently including, excluding, or guessing.
- Show the covered month, evidence boundary, category totals, monthly total, and any unresolved ambiguous transactions.

## Safety

- Do not expose or reproduce full payment-card numbers, account credentials, access tokens, or unrelated private message content.
- Do not overwrite an original attachment. Preserve originals and make corrections in the index or a clearly versioned native record.
- Keep receipt history separate from the active shipment queue. Durable lifecycle history belongs in `Order Events`; delivered shipments must not remain in active `Shipments`.
- Do not create one automation, calendar event, reminder, or permanent task per order. One lifecycle phase maintains all purchases and the consolidated control-cycle dispatcher reports active and newly delivered state.

# Email and Shipment Reconciliation

Load this reference completely for order mail, active shipments, Gmail filing, archive approval, approved carrier-retention deletion, and the Gmail pass of every brief/lifecycle run.

## Authoritative state

- `Order Events!A1:Q1000` in the Purchase & Receipt Archive is the canonical append-only lifecycle history. `Classification Queue!A1:L500` is unresolved purchase input.
- `Shipments!A1:N500` in the Ops Status Register is the active fulfillment **projection/working queue**, not purchase history. It is derived from current supported fulfillment state and may temporarily be `Degraded/Pending` if Ops is unavailable while canonical commerce history remains valid.
- Keep one active shipment row per fulfillment/tracking number. Split packages may create multiple rows for one order.
- Gmail is evidence and a searchable archive, but canonical order/tracking history lives in Sheets/Drive. Never make Gmail folder residence the only record of a lifecycle fact.
- Stable Receipt ID/order/tracking/package identities are the reconciliation keys between commerce history, active shipment projection, and Gmail evidence.

## Failure-domain boundary

Commerce lifecycle history and the active Ops shipment queue are separate authority boundaries.

- Commit/read back a supported lifecycle event in the Purchase & Receipt Archive **before** applying its corresponding `Shipments` projection.
- If the commerce event cannot be committed, do not mutate the shipment projection from that event.
- If the lifecycle event commits but the Ops shipment projection fails/unavailable, preserve the canonical event, mark only shipment projection `Degraded/Pending`, and reconcile the target later from current canonical events plus current target state.
- Never delete/rewrite/replay a canonical Order Event merely to retry `Shipments`.
- Gmail labels/archive are downstream filing projections. Apply them only after the canonical event/state needed to survive message archival is verified. A Gmail filing failure does not invalidate already-committed Sheets/Drive state.
- Do not create a shadow shipment database or hidden retry automation.

## Read and match evidence

1. Read the active queue when reachable before searching Gmail; if Ops is unavailable, continue commerce-history/Gmail evidence work that does not require a shipment projection and report the projection dependency degraded.
2. Search new material since the previous successful lifecycle pass, plus exact order/tracking searches for every reachable active fulfillment.
3. Inspect USPS, FedEx, UPS, DHL and vendor mail as applicable, but read every materially relevant message/thread in full before final state.
4. Normalize evidence using vendor, order number, Receipt ID when known, item, carrier, tracking/package, event time, observed time, ETA, and source.
5. For cancellation evidence include scope, removed/surviving items, original/revised total, and financial facts actually stated. For replacements include both merchant order numbers, both Receipt IDs when resolved, replacement group and cancellation state.
6. Match in this order: exact tracking; exact vendor+order; exact order+item/package; only then a unique combination of vendor/item/date/recipient/package facts.
7. More than one plausible match is unresolved. Do not overwrite or invent a relationship.

## Revisions, cancellations and replacements

- Reconcile same-merchant-order revisions before shipment or payment matching. The strongest current revision under the same merchant order remains one Receipt ID and becomes the expected settlement source.
- `Cancellation Requested` and `Partial Cancellation Requested` are non-terminal until authoritative evidence establishes the fulfillment/financial result.
- A confirmed full cancellation appends/verifies the canonical event first, then removes matching active fulfillment from the Ops projection when reachable.
- A confirmed partial cancellation commits the canonical surviving/cancelled state first, then rewrites active fulfillment to only the surviving supported item(s) when the target is reachable.
- Cancellation, return and refund accounting is committed through receipt/payment policy; shipment logic never invents totals, tax, fees or refunds.
- A true replacement with a different merchant order/transaction gets a different Receipt ID and reciprocal relationship events. Never mutate the original into the replacement.
- Projection failure after a canonical cancellation/replacement event leaves only the active shipment projection stale/degraded; it does not undo the commerce event.

## Evidence precedence

Use strongest evidence, not newest text blindly:

1. explicit user correction;
2. carrier delivery event;
3. carrier exception/progress event;
4. vendor fulfillment/status event.

Within a class, newer credible evidence wins. Never infer delivery from age, ETA expiry or an invoice.

## Gmail filing model

Use/create these labels as applicable:

- `Receipts`
- `Receipts/Automotive`
- `Receipts/Tools`
- `Orders/Awaiting Shipment`
- `Orders/Shipped`
- `Orders/History`
- `Orders/Carrier Retention/90d`
- `Shopping/Needs Classification`
- `Ops/Archive Approval`

For every verified order with a merchant order number, create/use an order-history label `Orders/History/<vendor-slug>/<order-number>`. If the merchant order number is unavailable or unsafe as a Gmail label component, use `Orders/History/<Receipt-ID>`. Apply the same order-history label to the merchant confirmation/invoice, shipment notices, delivery messages and correlated carrier messages. This is the Gmail folder-like grouping layer; canonical Sheets/Drive state remains authoritative.

For an active order:

- use `Orders/Awaiting Shipment` until credible shipment evidence and `Orders/Shipped` afterward;
- remove the opposite active label;
- apply `Orders/History` plus the specific order-history label;
- archive routine confirmation/progress mail only after the canonical commerce state needed to reconstruct the active shipment projection is committed/read back.

For a delivered order:

- append/verify Delivered in `Order Events` first;
- reconcile removal from active `Shipments` when Ops is reachable and report delivery once from durable event history;
- apply `Receipts` and the narrow receipt category where appropriate;
- apply `Orders/History` plus the specific order-history label to all correlated merchant/carrier evidence;
- remove active order labels;
- archive routine correlated mail after the canonical receipt/order Audit gate passes. If shipment projection is still degraded and the message contains the only evidence needed to resolve that projection, retain it until reconciliation; otherwise the canonical event/source IDs are sufficient for later projection repair;
- additionally label carrier-originated FedEx/UPS/DHL/USPS tracking/progress/delivery messages `Orders/Carrier Retention/90d` so they can be purged later without touching merchant evidence.

Never place a merchant order confirmation, invoice/receipt, cancellation/refund notice, warranty/support message, payment evidence, user correspondence, or mixed merchant/carrier thread in the carrier-purge class merely because it mentions tracking.

## 90-day carrier-email retention exception

The user has explicitly authorized automatic deletion-to-Trash of qualifying **FedEx, UPS, DHL and USPS carrier-originated logistics messages** beginning 90 calendar days after the related canonical delivery time. This is a narrow standing exception to the normal no-auto-delete rule.

A message may be deleted only when all are true:

1. it is carrier-originated FedEx/UPS/DHL/USPS logistics mail, not merchant/support/user correspondence;
2. exact tracking/order correlation resolves to a canonical Delivered event;
3. at least 90 calendar days have elapsed since that Delivered event;
4. carrier, tracking number, delivery timestamp/status and needed shipment history are already durable in canonical Sheets/Drive;
5. the relevant receipt/order Audit gate passes;
6. no open return, claim, dispute, damage case, chargeback, warranty/shipping investigation or other reason requires the carrier email;
7. the message does not contain unique receipt/payment/order-revision evidence not stored elsewhere.

When eligible, move the message to Gmail Trash, remove it from active retention labels as appropriate, and append/log a concise `Carrier Email Purged` audit fact without preserving Gmail message IDs in Git. Gmail Trash behavior is the deletion mechanism; do not attempt permanent provider-side purge.

Any carrier not named above remains retention-only unless the user later extends this rule. Any deletion outside this exact 90-day carrier class still requires an explicit bounded user request.

## Important and unknown mail

- Important or decision-bearing mail stays in Inbox under `Ops/Archive Approval`; silence is never archive approval and the 90-day carrier rule never overrides this label.
- Unknown purchases receive `Shopping/Needs Classification` plus one canonical queue case and are not guessed into verified filing/allocation.
- After classification is resolved, update canonical state first, then filing/labels.

## Contact safety

Before any proposed vendor reply/contact, load `vendor-contact.md`: inspect From/Reply-To/body/footer for no-reply or unmonitored instructions, research a current official contact path when needed, and show recipient/channel + subject + complete draft followed by `Do you want me to send this email?`. Never send automatically.

## Source-first transaction order

1. build normalized evidence from complete messages and live reachable canonical state;
2. reconcile revisions/cancellations/replacements and determine the desired canonical lifecycle event(s);
3. append/update/read back canonical Purchase & Receipt Archive state first, including receipt/payment/allocation facts required by the event;
4. reconcile the Ops `Shipments` projection from canonical commerce state when reachable, then read the target back. If it fails, preserve commerce state and mark only shipment projection `Degraded/Pending`;
5. reconcile other declared receipt/asset/shopping projections independently under their own policies;
6. rebuild/verify the canonical receipt/order Audit gate and record projection-health exceptions separately from core purchase integrity;
7. apply Gmail labels/order-history filing and archive routine evidence only after enough canonical state exists to survive archival;
8. run the bounded 90-day carrier-purge check;
9. re-read reachable active state and report only meaningful changes/actions.

A required mutation failure is scoped to the authority/module it belongs to. Canonical commerce failure blocks the commerce lifecycle mutation. A shipment projection failure does not roll back commerce. Gmail filing failure leaves already-verified canonical state intact and leaves filing pending. Never claim a failed projection succeeded, and never use cross-authority rollback as compensation.

## Excluded scope

- Do not search Promotions for discounts/sales unless explicitly reinstated.
- Do not calculate sale percentages or create promotion alerts by default.

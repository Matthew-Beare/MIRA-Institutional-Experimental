# Receipt Pipeline

Receipt ingestion and lifecycle reconciliation are one transaction:

1. Read the complete Gmail evidence and classify the transaction.
2. Deduplicate against the canonical receipt index and Drive destination.
3. Save or update one canonical, mobile-readable receipt with a compact summary and expandable details.
4. Upsert one transaction row and searchable line items under a stable Receipt ID.
5. Append the lifecycle event instead of overwriting history.
6. Allocate the single transaction total across cost owners without double counting.
7. After core receipt PASS, reconcile supported inventory side effects through the immutable asset graph: exact receipt line → acquired asset UUID → explicit relationship target UUID(s). Normalize Gmail/photo/label/manual evidence, namespaced identifiers, Knowledge relationships and verified specifications through `asset_evidence.py`; confirm receipt, asset/vehicle/tool UUID and identifier queries converge on the same graph. Then synchronize the active shipment queue, Gmail labels, Drive links, Asset Browser and specialized inventories such as Tool Inventory.
8. Queue unknown classifications for the next brief instead of guessing.
9. Rebuild the Audit gate and require every applicable check to pass.
10. Only then archive routine Gmail source threads.

If a downstream step fails, the source email remains unarchived and the exact Receipt ID/remediation is written to Audit. Shipping and delivery messages enrich the transaction's Order Events; they do not create duplicate receipts.

Cancellation is a lifecycle transition, not deletion. A request remains `Exception` with unchanged financials until confirmation. A confirmed full cancellation leaves the receipt searchable, excludes supported financial rows from spend, and removes its active fulfillment. A confirmed partial cancellation retains the cancelled line as excluded history, applies only merchant-confirmed revised totals to the surviving allocation, and rewrites `Shipments` to the surviving item. Returns do not reduce spend until exact refund evidence exists; refunds are linked negative adjustments or confirmed revised net totals and are counted once.

A same-order revision stays under one Receipt ID. A true replacement creates a new Receipt ID and reciprocal `Replaced By`/`Replacement For` events with one Replacement Group ID. The original is removed from active fulfillment only when cancellation is confirmed; otherwise it remains `Exception` beside the new active order. The Audit gate verifies reciprocal links, independent totals/allocations, and the shipment handoff.

The monthly spending report is bounded to email-detected purchases. It is not represented as a complete bank, card, or household ledger.

The user-facing front end is the Receipt Browser plus expandable detail ranges, not the legacy full-text Doc. Search tags remain visible and searchable while the long line-item body stays minimized.

Receipt Browser and Asset Browser are two views over one graph. A receipt query returns its acquired assets and their explicit vehicle/tool/manual/specification links; an asset or vehicle query returns the connected receipt lines and purchase dates. Neither view owns data, and `owned_by` is never used as a broad join that contaminates one asset with the rest of the household.

For a multi-quantity set/lot, preserve quantity under one UUID unless individual serial tracking is useful. `assigned_to` is not `installed_on`. Cancelled or otherwise excluded receipt lines remain searchable financial/lifecycle history and create no owned inventory asset.

Drive navigation must remain native and readable. Vehicle/tool folders may point at the same canonical evidence through a native Google Doc, native Sheet view, or supported shortcut, but never through a raw HTML/JSON/Markdown source card that Drive renders like code.

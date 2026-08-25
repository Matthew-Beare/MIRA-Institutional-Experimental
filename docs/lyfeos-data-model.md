# LyfeOS Data Model

LyfeOS keeps stable transaction/asset/trip/knowledge identities while allowing many evidence sources, tags, beneficiaries, events and allocations. Google Sheets/Drive are the current mutable implementation; keys and relationships are designed to migrate to PostgreSQL/object storage without rewriting history.

## Identity rule

People, physical assets and retained knowledge objects use immutable collision-resistant RFC 4122 UUIDs as canonical cross-database identities. Friendly IDs such as `ASSET-FL5-2025`, names, tool numbers, model names and Knowledge IDs are aliases for humans. A UUID is never recycled or changed because a record is renamed, reclassified, transferred, moved to another database, or later shared across a family deployment.

## Core entities

| Entity | Current authority/tab | Primary key | Purpose |
|---|---|---|---|
| Transaction | Purchase Archive `Orders - Database` | `Receipt ID` | One counted merchant transaction |
| Transaction item | `Receipt Details - Expandable` | Receipt ID + item/SKU/position | Searchable line items, category, fitment |
| Order event | `Order Events` | `Event ID` | Append-only lifecycle/revision/replacement history |
| Expense allocation | `Expense Ledger` | `Allocation ID` | Balanced cost-owner/asset/project allocation |
| Classification case | `Classification Queue` | `Queue ID` | Last-resort unresolved identity/ownership/fitment |
| Payment case | `Payment Reconciliation` | `Payment Case ID` | Expected charge vs pending/posted settlement |
| Person/asset registry | `People & Assets` | `Entity UUID` | People, beneficiaries, aliases, owned/external physical assets |
| Asset relationship | `Asset Relationships` | `Relationship UUID` | Explicit UUID-to-UUID ownership, assignment, installation, storage and replacement edges |
| Asset identifier | `Asset Identifiers` | `Identifier UUID` | Namespaced UPC/GTIN, SKU, manufacturer part/model, serial, IMEI, MAC and other exact identifiers |
| Evidence object | `Evidence Index` + Drive/Gmail/source | `Evidence UUID` | Photo, receipt, label, message, manufacturer page, manual and owner-confirmation provenance |
| Specialized inventory | Tool Inventory or configured domain source | `Entity UUID` | Detailed tool/collection fields without replacing global identity |
| Knowledge/reference | `Knowledge Index` + Drive | `Entity UUID` | Manuals/datasheets/reference metadata and canonical file link |
| Knowledge relationship | `Knowledge Relationships` | `Relationship UUID` | Explicit Knowledge UUID ↔ asset/vehicle/tool applicability |
| Technical specification | `Technical Specifications` | `Specification UUID` | Value/unit, exact subject/applicability, source tier, revision and page/section provenance |
| Asset query projection | `Asset Browser` | Entity/Receipt query | Human-facing bidirectional receipt ↔ asset/manual/specification view; not an authority |
| Reimbursement | `Reimbursements` | `Reimbursement ID` | Expected/received payback separate from merchant refund |
| Active fulfillment | Ops `Shipments` | `Shipment ID` | Undelivered/exception work queue only |
| Calendar projection | Ops `Calendar Projection` | `Projection ID` | Source entity ↔ Google Calendar event dedupe/link |
| Route knowledge | Ops `Routes` | `Route ID` | Reusable terminal-pair geometry/runtime/paid-mile facts |
| Trip occurrence | Ops `Trips` | `Trip ID` | One real work leg/travel occurrence |
| Mileage occurrence | Mileage `Mileage Log` | `Mileage ID` | Auditable paid mileage/pay occurrence |
| Integrity result | `Audit` | `Check ID` | Commit gate/remediation |

## Purchase, asset and knowledge invariants

1. A Receipt ID occurs once in the transaction table and its supported total is counted once.
2. A receipt may contain line items with different categories/assets/beneficiaries; included allocations reconcile exactly to the supported merchant total.
3. Email, photographed receipt, screenshot, account transaction and shipment evidence enrich the same transaction when they describe the same purchase.
4. A same-order merchant revision keeps one Receipt ID; a true new replacement order gets a separate Receipt ID and reciprocal relationship events.
5. Lifecycle events append idempotently; corrections supersede earlier interpretations without erasing them.
6. Product/asset identity may be enriched from model, serial, UPC/GTIN, SKU, part number, product photo, receipt, manual and manufacturer evidence. One physical asset uses one immutable Entity UUID.
7. A receipt-created asset stores the exact Receipt ID and receipt-line coordinate/source identity. Each cross-asset edge stores its own immutable Relationship UUID and both endpoint Entity UUIDs. A descriptive fitment note is not a relationship record.
8. A multi-quantity set/lot uses one Entity UUID plus quantity unless individual serial-level tracking is useful. `assigned_to` does not claim physical installation; only evidence may create `installed_on`. Cancelled/excluded receipt lines create no owned asset.
9. Retained product/service manuals and technical references use one immutable Knowledge UUID, live as files in canonical Drive, and are indexed by manufacturer/model/part/revision/asset relationships. Multiple upload/email/URL paths to the same document enrich one record rather than duplicating it.
10. Exact identifier values preserve leading zeroes. Global check-digit identifiers are validated; merchant/manufacturer-local SKU/part/model/serial values carry a namespace; unique serial/IMEI/MAC values cannot silently bind to two assets.
11. Verified safety-critical torque, tire-pressure, fluid, alignment, and load specifications require an authoritative source tier, exact subject UUID/applicability, revision, and page/section locator. Owner memory may be retained as candidate evidence but never promoted to verified.
12. Receipt, Entity UUID, and namespaced-identifier queries traverse the same explicit asset graph and return the same connected receipts, evidence, manuals and specifications. General `owned_by` traversal is excluded so one vehicle query does not return every household asset.
13. Unknown classification/fitment is queued only after reachable evidence and asset-registry exclusion checks are exhausted.
14. Reimbursement is not merchant refund. Gross merchant purchase remains auditable while verified reimbursements reduce net household cost separately.
15. Payment cases remain open until expected settlement is matched, split-matched, resolved as no-settlement or otherwise financially resolved. Actual posted amounts are compared with the latest supported same-order revision.
16. Gmail/archive success requires the applicable Audit gate to pass.

## Fulfillment and Gmail retention

`Shipments` contains only active `Awaiting Shipment`, `Shipped`, or `Exception` fulfillment. Delivered state is durable in `Order Events` and reported once.

Correlated merchant/carrier mail may be grouped by order-history labels. The narrow deployment retention rule may move only carrier-originated FedEx/UPS/DHL/USPS logistics messages to Trash after 90 days from durable delivery when tracking evidence is saved, Audit passes, and no claim/return/dispute/investigation requires the message. Merchant receipts/order/payment/support evidence is retained.

## Routes, trips and external run-sheet evidence

`Routes` is reusable terminal-pair knowledge; `Trips` and Mileage Log are actual occurrences. A historical employer/shared run sheet used to teach route mileage is normalized into **unique canonical terminal pairs only by default**. Repeated source occurrences become provenance counts/variants and do not create hundreds of historical Trip/Mileage rows unless historical-occurrence import is explicitly requested.

Normalize only proven aliases/typos before pair dedupe. For the current deployment, company-paid terminal mileage is symmetric by terminal pair unless an explicit exception is supplied. Historical source variants remain provenance; reusable route values prefer explicit corrections, then current/repeated evidence rather than silently averaging conflicting entries.

## Manual/reference library

Drive `Manuals & Reference` is the current durable file store. `Knowledge Index` stores Knowledge ID, immutable Entity UUID, title/type, manufacturer, model/part, source URL, Drive URL/ID, revision/date, tags, summary, source identity/hash and status. `Knowledge Relationships` carries explicit links to any number of asset/vehicle/tool UUIDs. Queries resolve by Knowledge UUID, asset UUID, model/part/title/tags, read the retained source when needed, and return the canonical Drive link plus page/section provenance when supported.

## Calendar projection

Google Calendar is an optional projection surface, not authoritative state. `Calendar Projection` stores source type/source ID, target calendar, Google event ID, event class, source revision and sync status. A revised delivery ETA/appointment/deadline updates the existing linked event rather than creating a duplicate. Inviting attendees is a separate action boundary.

## Lifecycle financial semantics

- Cancellation request preserves existing financial state until confirmed.
- Full cancellation before settlement excludes spend without inventing a refund.
- Partial cancellation keeps removed lines as excluded history and updates surviving totals only from authoritative merchant revision evidence.
- Return preserves spend until refund evidence exists.
- Refund is linked financial evidence and nets exactly once; it does not erase gross history.
- Replacement financial state is resolved independently for original and replacement orders.

## Self-hosting path

A future relational implementation maps naturally to `transactions`, `transaction_items`, `order_events`, `expense_allocations`, `payment_cases`, `people`, `assets`, `knowledge_objects`, `asset_knowledge`, `transaction_assets`, `reimbursements`, `shipments`, `routes`, `trips`, `mileage_entries`, `calendar_projections`, `evidence_objects`, and `audit_results`, with original files in S3-compatible object storage. Immutable UUIDs and append-only evidence/event history survive migration. Drive/Gmail/provider URLs remain provenance references during/after transition. Self-hosting changes storage/query/automation power; it does not weaken connector, approval or integrity rules.

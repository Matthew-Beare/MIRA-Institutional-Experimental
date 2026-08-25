# Household Financial Reconciliation Extension

This extends LyfeOS without changing the one-transaction/one-Receipt-ID invariant.

## New canonical mutable tables

### People & Assets

Stores people/entities, aliases, relationship, household financial scope, and optional asset rows. It is the canonical mutable identity/asset layer for household members and outside beneficiaries. External assets are allowed and remain distinguishable from household-owned assets.

Every person and physical asset uses one immutable collision-resistant RFC 4122 `Entity UUID` as canonical cross-database identity. Friendly IDs, display names, Asset IDs, tool IDs and aliases are human-facing attributes and must never replace, recycle, or mutate the UUID.

Suggested columns:

`Entity UUID`, `Friendly Entity ID`, `Display Name`, `Entity Type`, `Relationship`, `Aliases`, `Financial Scope`, `Friendly Asset ID`, `Asset Type`, `Asset Label`, `Year`, `Make`, `Model`, `Notes`, `Updated ET`, `Quantity`, `Tracking Mode`, `Lifecycle Status`, `Source Authority`, `Source Record ID`, `Receipt ID`, `Receipt Line ID`, `Evidence Link`, `Schema Version`.

When a person and an asset are modeled as distinct physical/logical entities, each receives its own Entity UUID and the ownership/beneficiary relationship links them. Do not stuff two independently addressable objects under one reused UUID merely because one row layout is convenient.

### Asset Relationships

Stores explicit graph edges between asset/person UUIDs. Suggested columns:

`Relationship UUID`, `From Entity UUID`, `Relationship Type`, `To Entity UUID`, `Status`, `Source Authority`, `Source Record ID`, `Receipt ID`, `Receipt Line ID`, `Evidence Link`, `Notes`, `Effective From ET`, `Effective To ET`, `Updated ET`, `Schema Version`.

Set/lot inventory uses one UUID plus quantity unless serial-level tracking is useful. `assigned_to` records allocation or intended fitment and never implies `installed_on`. A receipt-created asset must link the exact Receipt ID and exact receipt-line coordinate; excluded/cancelled lines do not create owned assets.

### Reimbursements

Stores expected/received money back from an outside beneficiary or other reimbursing party. This table is independent of merchant refund events.

Suggested columns:

`Reimbursement ID`, `Receipt ID`, `Beneficiary Entity UUID`, `Beneficiary / Cost Owner`, `Related Asset UUID(s)`, `Purchase Amount Allocated`, `Amount Expected Back`, `Amount Received`, `Status`, `Payment Evidence / Account Ref`, `Expected / Received Date`, `Net Household Cost`, `Source`, `Notes`, `Updated ET`.

### Payment Reconciliation

Tracks the merchant charge expected from the latest authoritative order/revision evidence until settlement is matched.

Suggested columns:

`Payment Case ID`, `Receipt ID`, `Vendor`, `Order Number`, `Expected Charge`, `Expected Evidence`, `Card Last Four / Account Hint`, `Status`, `Observed Posted Amount`, `Observed Pending Amount`, `Difference`, `First Expected ET`, `Last Checked ET`, `Resolved ET`, `Source`, `Notes`.

## Relationships

- `Orders - Database.Receipt ID` -> one merchant transaction.
- `Expense Ledger.Receipt ID` -> one or more cost allocations whose included rows reconcile to the merchant transaction total.
- `Reimbursements.Receipt ID` -> zero or more non-merchant paybacks reducing net household cost without mutating gross merchant spend.
- `Payment Reconciliation.Receipt ID` -> one or more settlement cases when a merchant legitimately settles separately; normally one case per current merchant order financial outcome.
- `People & Assets` supplies immutable beneficiary/asset UUIDs plus friendly aliases referenced by allocations/reimbursements.
- `Asset Relationships` supplies explicit UUID-to-UUID ownership/assignment/installation edges. Free-text fitment notes remain searchable context but are not the relationship authority.

## Financial views

Expose separate measures instead of collapsing unlike concepts:

- Gross Merchant Spend: supported vendor purchases after merchant cancellations/refunds are applied exactly once.
- Reimbursements Received: verified money returned by outside beneficiaries, not merchant refunds.
- Net Household Cost: Gross Merchant Spend attributable to the household minus verified outside reimbursements.
- Expected Unsettled Charges: supported merchant totals still awaiting account settlement.
- Merchant Charge Variance: posted charge minus latest supported expected merchant charge.
- Unmatched Account Charges: material account debits not yet linked to a supported Receipt ID/payment case.

## PostgreSQL path

Future relational tables map naturally to:

- `parties`
- `party_aliases`
- `assets`
- `asset_owners`
- `transactions`
- `transaction_items`
- `expense_allocations`
- `reimbursement_obligations`
- `reimbursement_events`
- `payment_cases`
- `payment_observations`
- `order_events`
- `evidence_objects`

Use immutable UUIDs and append-only events. The migration must preserve existing canonical Entity UUIDs exactly and must not reinterpret an outside-person reimbursement as revenue or a merchant refund.

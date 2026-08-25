# Household, Beneficiary, and Reimbursement Reconciliation

Use this workflow whenever the household buys something for another person, another person's asset, a shared project, an employer/client, or any case where some or all of the purchase is expected to be reimbursed.

## Canonical model

- `People & Assets` is the mutable identity/asset registry. It stores household people, outside beneficiaries, aliases used by speech recognition, and owned/external assets. It is not Git source data.
- `Expense Ledger` records the merchant purchase allocation by economic beneficiary/asset while preserving the one underlying Receipt ID and one merchant total.
- `Reimbursements` records money expected back and money actually received. A reimbursement is not a merchant refund and must never rewrite the merchant order lifecycle.
- Household dashboards expose both gross paid purchase cost and net household cost after verified reimbursements. Never erase the gross purchase merely because another person paid the household back.

## Identity and asset assignment

1. Normalize a person's alias through `People & Assets` before creating a new identity. Speech-recognition variants must not create duplicate people.
2. A receipt item may be assigned to an external person's vehicle/equipment when exact item evidence plus the live registry or an explicit user statement establishes the relationship.
3. External assets remain first-class searchable assets even though the household does not own them. Store owner/beneficiary separately from possession or payer.
4. Missing year/trim/details do not block creation of a minimally identified external asset when owner + make/model are explicit. Never invent the missing details; enrich later.
5. If an outside beneficiary has multiple plausible assets, perform the same UPC/SKU/part/fitment evidence pass used for household assets before asking the user.

## Purchase and reimbursement accounting

For every reimbursable purchase:

- keep the merchant transaction under its normal Receipt ID and full supported merchant total;
- allocate each relevant item/cost to the actual beneficiary and related asset in `Expense Ledger`;
- create one stable Reimbursement ID per reimbursement obligation, which may cover one or several allocation rows from the same Receipt ID;
- store `Amount Expected Back` only from an explicit agreement, user statement, invoice/split evidence, or clear full-reimbursement context; never assume a friend owes the entire receipt when mixed household items exist;
- set status to `Expected`, `Partially Received`, `Received`, `Waived`, or `Disputed` as evidence changes;
- when money arrives, reconcile the incoming account transaction by amount/date/counterparty/payment note when reachable and store only the needed account reference/provenance;
- compute Net Household Cost as purchase amount allocated minus verified reimbursement received, without changing the merchant purchase amount;
- do not classify a reimbursement inflow as wages, business revenue, or a vendor refund merely because it is money coming in.

If reimbursement is expected but not yet received, keep it open in the same lifecycle table. Do not create a separate reminder per person/purchase. The consolidated receipt/order lifecycle checks open reimbursement cases.

## Mixed receipts

One receipt may contain household and outside-person items. Split cost using line-item or evidence-backed allocation. The allocation rows across the transaction still reconcile to one merchant total. Reimbursement only offsets the external beneficiary portion actually repaid.

Example structure:

- merchant Receipt ID: one purchase for $600;
- household item allocation: $200;
- outside-beneficiary vehicle part allocation: $400;
- reimbursement expected: $400;
- reimbursement received: $400;
- gross merchant spend: $600;
- net household cost: $200.

This is preferable to deleting the external item, excluding the whole receipt, or pretending the incoming $400 was a merchant refund.

## Audit gate

A reimbursable purchase cannot pass final financial reconciliation unless:

- each external-beneficiary allocation has a stable beneficiary/asset relationship or an explicit unresolved queue entry;
- expected reimbursement amount has evidence or is intentionally blank;
- received reimbursement is backed by explicit user confirmation or credible payment/account evidence;
- gross purchase totals remain unchanged by reimbursement;
- reimbursement does not duplicate a merchant refund/credit;
- net household cost equals allocated purchase cost minus verified reimbursement exactly once.

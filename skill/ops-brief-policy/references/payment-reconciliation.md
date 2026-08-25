# Payment and Merchant-Charge Reconciliation

Use this workflow for every receipt/order whose expected merchant charge can be supported from order, invoice, revision, shipment, cancellation, or refund evidence and whenever connected account data is available.

## Goal

A purchase lifecycle is not financially complete merely because an order exists or shipped. Keep an explicit payment case until the merchant charge/reversal/refund is reconciled or credible evidence establishes that no settlement should occur.

`Payment Reconciliation` is the canonical mutable queue. One row represents one expected merchant financial outcome for one Receipt ID/order state. It is not a duplicate transaction ledger.

## Expected amount

1. Establish the current expected charge from the strongest merchant evidence.
2. Reconcile revisions by exact vendor + order number before comparing to account transactions. A later confirmed same-order revision supersedes an earlier confirmation amount for expected settlement while preserving the prior amount in lifecycle history.
3. A distinct merchant order number is a separate Receipt ID/payment case unless evidence proves it is merely a processor artifact for the same underlying transaction.
4. Include merchandise, shipping, tax, fees, discounts, and protection only as supported by the merchant's latest confirmed total. Never reconstruct an expected total from guessed tax or fees when a merchant total exists.

## Account matching

- When card/payment last-four is present in email/receipt evidence, first bind only to a linked account with the same last-four and plausible type, then search that account by amount/date/merchant.
- When last-four is absent, search all plausible connected payment accounts. Do not invent a card binding.
- Query both pending and posted transactions when useful. Pending authorization is evidence of an attempt, not final settlement.
- Use exact amount/date/order/merchant evidence first. If the merchant descriptor differs, widen to same account/date/amount and retain the descriptor mismatch in provenance.
- Never copy unrelated account transactions or balances into the receipt archive.

## Statuses

Use these normalized statuses:

- `Awaiting Settlement` — expected charge is supported but no matching pending/posted charge is yet visible;
- `Pending Match` — a plausible pending authorization exists at the expected amount;
- `Matched` — posted charge equals the latest expected amount within exact currency-cent comparison;
- `Overcharged` — posted merchant charge exceeds the latest supported expected amount without a newer merchant revision explaining the difference;
- `Undercharged` — posted merchant charge is less than the expected amount and no split-charge evidence explains the remainder;
- `Split Settlement` — multiple proven merchant charges sum exactly to the expected amount;
- `Pending Release` — merchant evidence says no settlement should remain, but a pending authorization or credit is still moving through the account;
- `Settlement Contradiction` — merchant evidence says no settlement occurred, but the current posted debit-minus-credit total is nonzero and requires investigation;
- `Refund/Reversal Expected` — a settled charge now has a supported expected merchant correction;
- `Resolved No Settlement` — merchant evidence establishes the order/revision was removed before settlement;
- `Ambiguous` — multiple account transactions remain plausible after investigation.

## Mismatch detection

When a posted charge is found, compare it against the latest confirmed expected amount.

- Difference = observed settled merchant debit minus expected charge.
- Pending projection = pending debits minus pending credits. Never drop a pending credit merely because the expected outcome started as a charge.
- If Difference > $0.00 without newer merchant evidence, surface `Action Required — possible merchant overcharge` with vendor/order, expected amount, observed amount, difference, and the account suffix if safely known.
- If Difference < $0.00, investigate split shipments/charges, discounts, revised invoices, partial cancellations, processor credits, and subsequent related charges before calling it an undercharge.
- Never silently accept a larger charge merely because the merchant name matches.
- A posted debit and posted credit that exactly net to zero can support `Resolved No Settlement`; a nonzero posted net cannot. If a pending correction may still bring the net to zero, retain `Pending Release` until it posts or disappears.
- Never treat a charge from the same merchant as belonging to the order unless the date/amount/order context is plausible; unmatched merchant charges should themselves be investigated as possible duplicate/unrecognized charges.

## Waiting for a charge

`Awaiting Settlement` is a valid open state, not an error. The receipt/order phase rechecks it on every control-cycle run using current account evidence. There is no per-order reminder or automation.

Do not start a five-business-day refund clock merely because a purchase has not posted yet. A merchant charge may settle after shipment or in multiple parts. Keep checking until one of these occurs:

- exact/split settlement matches;
- merchant confirms no settlement is due;
- a newer same-order revision changes the expected amount;
- cancellation/return creates a real expected refund/reversal;
- a mismatch becomes actionable.

## Unmatched charges

During account reconciliation, inspect material card charges that cannot be tied to any known Receipt ID/order/invoice. Before calling them unknown, search Gmail/receipt photos/Drive evidence by merchant, amount, date, order identifiers and likely aliases. If no supported purchase is found, surface the charge as an unmatched financial exception rather than fabricating a receipt.

## Audit requirements

The financial audit gate verifies, where applicable:

- the latest merchant revision is the expected amount source;
- every posted matched charge is linked to one supported payment case and not counted twice;
- a split settlement has exact component references and sums to expected total;
- any over/undercharge has been investigated against newer merchant evidence before escalation;
- cancellations before settlement do not create fictional refunds;
- actual settled cancellations/returns retain their refund/reversal expectation until resolved;
- `Awaiting Settlement` cases remain open and continue to be checked after shipping/delivery until financially resolved.

# Receipt Line Classification, Fitment, and Financial Resolution

Load this reference together with `receipt-ingestion.md` for every purchase/receipt ingestion, cancellation/refund reconciliation, or inventory side effect.

## Line-item classification is authoritative

- One Receipt ID represents one underlying transaction, but its individual line items may belong to different categories, subcategories, cost owners, vehicles/assets, projects, and inventory destinations.
- Classify each identifiable line item independently. Never force every item on a mixed receipt into the receipt-level `Primary Category` or `Vehicle / Project` value.
- `Orders - Database.Primary Category` is a navigation summary only. Use the single dominant category when truly representative; use `Mixed / Multi-category` when no single category represents the receipt. `Search Categories` is the union of all line-item categories/tags.
- `Receipt Details - Expandable` holds the item-level category/asset identity. `Expense Ledger` holds the financial allocation. The included allocation rows for one Receipt ID must sum exactly to that transaction's one supported net total.
- One line item may itself serve multiple assets/projects. Split its cost through balanced allocations rather than duplicating the line or counting its full value more than once.
- A category or asset correction changes classification/allocation, never Receipt ID or source evidence.

## Part number and fitment evidence pass

When a purchased item has a manufacturer part number, vendor SKU, model, UPC/GTIN, exact wheel/tire size, or another sufficiently specific identity, perform a fitment/identity evidence pass before final vehicle/asset assignment.

Evidence priority:

1. manufacturer or OEM catalog/specification;
2. vehicle/OEM parts catalog or manufacturer application guide;
3. merchant/vendor product page tied to the exact SKU;
4. reputable specialist catalog with an exact part-number match;
5. explicit user correction/assignment, which controls the user's intended asset relationship while preserving conflicting earlier evidence.

For automotive items, compare all material attributes that the evidence exposes rather than one convenient dimension:

- wheels: diameter, width, offset/inset, bolt pattern/PCD, center bore, load rating when available, brake/caliper clearance or application notes when available, and lug-seat/thread requirements when relevant;
- tires: exact size, load/speed specification, intended wheel setup, and proven vehicle/project context;
- OEM/replacement parts: exact part number and supersession chain, model year, trim, engine, transmission/drivetrain, axle/front-rear/left-right position, and other catalog qualifiers;
- studs/lugs/hubs: thread pitch, knurl/diameter, seat style, length, hub/application compatibility, and any known conversion already applied to the vehicle;
- electrical/electronic accessories: connector/interface, voltage/platform, model/application, and any required controller/ecosystem.

Assignment rules:

- If exact evidence plus the owned-asset registry uniquely resolves one asset and no material spec conflicts, auto-assign that asset and store a concise fitment note with the exact part/SKU and evidence source.
- Unique resolution may be established by exclusion as well as an explicit application listing. Example: when an exact 5x120 wheel is materially compatible and only one owned vehicle has that bolt pattern, the system should assign that vehicle rather than ask a question merely because the receipt omitted the vehicle name.
- If two or more owned assets remain plausible, evidence is incomplete after investigation, or any material fitment field conflicts, do not guess. Put the line in `Classification Queue` and ask the smallest useful question.
- Do not assign merely because a merchant page says `universal`, because one bolt pattern happens to match when other material dimensions conflict, or because a product title resembles a prior purchase.
- When no part/SKU is printed but exact manufacturer dimensions uniquely identify a catalog entry, enrich the receipt with that manufacturer part number and provenance.
- Preserve user-confirmed intended use even when the item is not a catalog-standard fitment, but record the distinction as `owner-assigned / custom fitment` rather than pretending the manufacturer application guide confirmed it.

### Investigation before queue

`Unknown` is a conclusion after evidence work, not a shortcut around it. Before asking the user which asset an identifiable item belongs to:

1. normalize/search its UPC, GTIN, SKU, model and part number, including manufacturer supersessions;
2. derive material compatibility attributes from authoritative sources;
3. compare against every relevant owned asset and known modification/conversion in the live asset registry;
4. eliminate assets with material conflicts and record the exclusion reason;
5. cross-reference same-receipt items, order application selections, replacement relationships, prior verified wheel/tire or part associations, inventory records, shipment data and merchant correspondence;
6. if the result uniquely resolves, assign it with provenance and confidence rather than asking the user to repeat information the system already possesses;
7. queue only when multiple plausible assignments or a real material conflict remains, and write the exact unresolved dimension/question into the queue.

Example: an Enkei GTC02 listed as `18x9.5 5x120 +45 Matte Black` resolves in Enkei's catalog to part `534-895-1245`. That evidence can enrich the line and be compared against the user's owned vehicles before asset assignment.

## Cancellation versus financial resolution

Cancellation state and money state are related but separate facts.

- A merchant-confirmed cancellation proves fulfillment/lifecycle cancellation. It does not by itself prove that a settled charge was refunded.
- Determine whether the cancelled amount ever settled. If the merchant revises the order before a charge settles and exact revised-order evidence shows the surviving amount, no fictional refund event is required; record the revised supported total and retain the cancelled line as excluded history.
- Merchant charge-timing policy is valid supporting evidence when tied to the actual lifecycle. If a merchant charges only at shipment and the order was revised before shipment, a removed line normally becomes `revised before settlement / no refund expected` unless later account evidence contradicts it.
- If the original/full amount settled, require credible reversal/refund evidence before marking the financial correction complete. Accept merchant refund confirmation, processor/card/bank posted credit/reversal, or another authoritative financial record.
- When email/receipt evidence exposes payment-network and card last-four, map it only to a connected account with the same last-four and plausible type, then query that exact account for merchant/amount/date evidence. Never store or request a full card number.
- If no last-four is exposed, investigate all plausible connected payment accounts by merchant, amount, authorization/posted date and nearby exact amounts before concluding that the account evidence is unavailable.
- When connected account data is available, store only normalized proof needed for audit: resolution state, confirmed amount, date, account last-four when already exposed/linked, and source class/reference. Do not copy account balances, account IDs, full account numbers, or unrelated transactions into the receipt archive.
- A pending authorization or pending credit is not a settled refund. Preserve pending state and re-check through the normal lifecycle process.
- Absence of a matching financial transaction is not proof of refund/non-charge when account freshness/coverage is incomplete or unknown. It is one evidence result to combine with merchant timing, revised invoices, shipment totals and later statements.

## Five-business-day unresolved-money rule

- Start the clock only when merchant cancellation/refund eligibility or an accepted return creates an expected financial correction. Do not start a refund timer for an amount proven to have been removed before settlement.
- Normalize each unresolved case with Receipt ID, vendor/order, expected amount when known, financial-resolution status, start time, and the missing evidence.
- Run `python3 scripts/financial_resolution.py resolve --input <json-file> --pretty` through the lifecycle workflow. Its five-business-day deadline preserves the local clock time and counts Monday through Friday; never replace this with a separate reminder job.
- If an expected refund/reversal or confirmed revised charge is still not proven when the deterministic gate becomes due, surface its compact `financial_resolution_overdue` action in the next brief: vendor/order, unresolved amount if known, and the missing proof.
- Continue checking the existing receipt/order record; never create a separate reminder automation, duplicate receipt, or replacement financial transaction just to track the deadline.
- Clear the action once exact merchant or financial-account evidence resolves the money state. Append the resolution/reclassification event; never erase the earlier exception or earlier provisional interpretation.

## Audit requirements

A receipt cannot pass final Audit when any required item-level classification, fitment assignment, or expected financial correction remains falsely represented as verified.

The Audit gate must verify, where applicable:

- every line item has a verified or investigated-and-queued category and asset/cost-owner state;
- exact UPC/SKU/part/model evidence and provenance are retained when used to determine identity/fitment;
- no item or allocation is double-counted across categories/assets;
- included allocations equal the one supported transaction total;
- a cancelled line is absent from active fulfillment and spend while preserved as history;
- any settled cancelled/returned amount has a resolved refund/reversal state or a visible five-business-day exception;
- amounts removed before settlement are not mislabeled as refunds owed;
- replacement relationships remain separate from refund accounting.

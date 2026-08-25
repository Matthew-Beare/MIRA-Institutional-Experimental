# Receipt Photo / Screenshot Intake

Use this workflow when a receipt, invoice, packing slip, order screenshot, product-label photo, barcode image, or other purchase evidence is supplied directly in any supported Chat, Work, Project, voice/dictation follow-up, or connected-file context where this skill and the canonical authorities are available.

The conversation that receives the image is only the intake surface. The canonical result must flow through the same Purchase & Receipt Archive, Drive evidence, order lifecycle, classification, allocation, fitment, inventory, and Audit-gate workflow used for email receipts. Never create a chat-local shadow receipt database.

## Evidence extraction

Inspect the supplied image directly before resorting to OCR. Extract every legible identifier that can materially improve reconciliation, including:

- vendor/merchant, transaction/order/invoice number, date/time, subtotal, tax, fees, discounts, total, payment-method hint or last four when visible;
- item description, quantity, unit/extended price;
- UPC/EAN/GTIN, SKU, manufacturer part number, model, serial number, IMEI or other stable product identifier when present;
- vehicle/application text, size, dimensions, color/variant and other configuration qualifiers;
- barcode digits that are visibly printed with the barcode. Do not invent a barcode value from an unreadable image.

Preserve the image as source evidence when the user has authorized normal receipt ingestion. Use image hash/source metadata when available to prevent the same photographed receipt from becoming a second transaction after its email copy is later discovered.

Before provider writes, normalize the image/evidence and extracted identifiers through `scripts/asset_evidence.py`. OCR text alone never silently overwrites a verified identifier or serial.

## Reconciliation-first lookup

For every identifiable line item, investigate before returning `unknown`:

1. Preserve the printed identifier exactly, including leading zeroes. Validate UPC/EAN/GTIN check digits, distinguish merchant SKU from manufacturer part/model/serial namespaces, then search exact identities first.
2. Prefer manufacturer/OEM evidence, then exact vendor SKU/product evidence, then reputable specialist catalogs.
3. Expand the product identity into relevant compatibility attributes. For automotive parts, this includes application, dimensions, bolt pattern/PCD, center bore, offset, thread/seat, trim, engine/drivetrain and position as applicable.
4. Compare those attributes against the complete live owned-asset registry and known modifications, not merely the asset named on the receipt.
5. Use exclusion evidence aggressively. If a wheel is 5x120 and only one owned vehicle accepts 5x120 with the remaining material dimensions consistent, that is positive unique-assignment evidence, not an excuse to ask the user which car it belongs to.
6. Cross-reference surrounding evidence: other items on the same receipt, replacement links, prior wheel/tire setup associations, order email, shipment evidence, merchant application selections, existing inventory and earlier verified part associations.
7. If one asset uniquely survives all material checks, auto-assign it and record the evidence/provenance. If the intended use is explicit but fitment is custom/non-catalog, preserve `owner-assigned / custom fitment` rather than fabricating OEM fitment.
8. Use manufacturer/OEM sources first for product identity and manuals, then exact merchant/specialist sources. Queue `blocked`, `no_match`, or unresolved identity honestly; a web result is not evidence until its URL, identity match, and source tier are retained.
9. Only after reachable evidence has been exhausted may the item enter `Classification Queue`. The queue note must say what was checked and the exact ambiguity that remains, so the user is never asked a question the system could have answered itself.

Do not use generic web similarity, one matching dimension, or model-name resemblance when a material compatibility conflict exists.

## Transaction reconciliation

Before creating a new Receipt ID, search existing receipt/order evidence for the same vendor, date, total, order number, payment hint and matching line items. A photograph and an email are often two sources for one transaction, not two purchases.

If an email or account record later supplies better evidence, enrich/supersede the existing receipt and append the lifecycle event. Never delete the photograph-backed history merely because a cleaner source later appears.

When card last-four is visible in the receipt/email, map it only to a currently linked account with the same last-four and plausible account type. Then reconcile exact amount/date/merchant evidence on that account. If the last-four is absent, do not invent a card binding; search all plausible connected payment accounts and retain the lack of binding as provenance.

## Completion gate

A photo receipt is complete only after the same normal Audit gate passes: transaction identity, canonical evidence, line-item classification, balanced allocation, part/fitment assignment or explicit queue, order/shipment mapping when applicable, financial-resolution state when applicable, and inventory side effects when required.

Never send an email as a side effect of receipt intake. If investigation suggests contacting a merchant, draft the proposed action and obtain explicit pre-send confirmation before any send.

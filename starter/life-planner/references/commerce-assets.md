# Commerce, assets, and knowledge

## Purchase and fulfilment identities

- One merchant transaction has one Receipt UUID and supported total.
- Receipt lines, orders, packages, payments, shopping intent, refunds, and reimbursements are distinct linked records.
- A cancellation is not a refund. A revision is not automatically a replacement transaction.
- Active Shipments is a fulfilment projection; durable Order Events and receipt history do not resurrect completed fulfilment.
- Screenshot, photo, owner confirmation, Gmail, merchant, carrier, and payment evidence may enrich the same identity. Never wait for Gmail when explicit owner evidence is sufficient.

## Assets and identifiers

Every person, physical asset, and retained knowledge object uses an immutable RFC 4122 UUID. Friendly IDs are aliases.

Preserve identifier namespaces and exact printed values: GTIN/UPC, merchant SKU, manufacturer part/model, serial, IMEI, MAC, and other local IDs are not interchangeable. Retain leading zeroes and validate applicable check digits.

Create an owned asset only from included, supported purchase/evidence lines. A multi-quantity set may use one lot UUID unless serial-level tracking is useful. `assigned_to`, `installed_on`, `used_with`, storage, replacement, and ownership are different relationships.

## Evidence and specifications

Store retained originals/manuals in Drive, then record provider file ID/link, provenance, title, revision, and asset/receipt relationships. Technical specifications such as torque, pressure, capacity, alignment, or load require an authoritative source, exact subject UUID/applicability, revision, and page/section before status becomes `Verified`.

Commit and read back canonical purchase/asset state before optional downstream projections. If a projection fails, preserve the source record and mark only that projection `Degraded` or `Pending`.

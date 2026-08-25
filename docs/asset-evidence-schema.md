# Asset, evidence, manual, and specification schema

This is the provider-adapter contract for the normalized graph validated by
`skill/ops-brief-policy/scripts/asset_evidence.py`. Google Sheets/Drive are the
current mutable implementation. Column order is stable for the beta; PostgreSQL
may later replace the storage adapter without changing UUIDs or provenance.

## Canonical tables

### `Evidence Index`

`Evidence UUID` · `Evidence Type` · `Entity UUID` · `Receipt ID` ·
`Receipt Line ID` · `Source Authority` · `Source Record ID` · `Source URI` ·
`Drive File URL` · `Drive File ID` · `Content Hash` · `Captured ET` · `Status` ·
`Notes` · `Updated ET` · `Schema Version`

One source object may link to an entity, a receipt, an exact receipt line, or a
supported combination. Gmail message/thread identity, Drive file identity,
image hash, merchant-account record identity, or explicit owner-confirmation
identity prevents a photo and later email from becoming duplicate purchases or
assets. OCR output is extracted evidence, never an authority by itself.

### `Asset Identifiers`

`Identifier UUID` · `Entity UUID` · `Identifier Type` · `Value` ·
`Normalized Value` · `Namespace` · `Status` · `Evidence UUID` ·
`Source Authority` · `Source Record ID` · `Evidence Link` · `Notes` ·
`Updated ET` · `Schema Version`

Supported beta types are UPC-A, EAN-13, GTIN-8/12/13/14, manufacturer part
number, vendor SKU, model number, serial number, IMEI, and MAC address. `Value`
preserves the printed text and leading zeroes. `Normalized Value` is only the
search key. Merchant/manufacturer-local part, SKU, model, and serial values
require `Namespace`. GTIN and IMEI check digits are validated. A live serial,
IMEI, or MAC cannot bind to two Entity UUIDs.

### `Knowledge Index`

The existing columns remain compatible:

`Knowledge ID` · `Entity UUID` · `Title` · `Knowledge Type` · `Manufacturer` ·
`Model` · `Part/SKU` · `Related Asset UUID` · `Related Asset ID` · `Source URL` ·
`Drive File URL` · `Drive File ID` · `Version/Revision` · `Effective Date` ·
`Tags` · `Summary` · `Status` · `Updated ET`

Append: `Source Authority` · `Source Record ID` · `Content Hash` ·
`Schema Version`.

`Entity UUID` is the immutable Knowledge UUID. The two legacy Related Asset
columns remain a readable convenience only; multi-asset applicability belongs
in `Knowledge Relationships`. A `retained` manual/reference requires canonical
Drive file ID/URL and an explicit version, revision, or edition. Failed searches
remain `lookup_queued`, `download_blocked`, or `unavailable`.

### `Knowledge Relationships`

`Relationship UUID` · `Knowledge UUID` · `Entity UUID` · `Relationship Type` ·
`Status` · `Source Authority` · `Source Record ID` · `Evidence UUID` · `Notes` ·
`Updated ET` · `Schema Version`

This is the many-to-many manual/datasheet/bulletin/reference applicability
table. A link must use exact Knowledge and asset/vehicle/tool UUIDs and is not
permission to duplicate either object.

### `Technical Specifications`

`Specification UUID` · `Subject Entity UUID` · `Specification Type` · `Label` ·
`Value` · `Unit` · `Applicability` · `Source Tier` · `Source URL` ·
`Knowledge UUID` · `Source Locator` · `Version/Revision` · `Status` ·
`Source Authority` · `Source Record ID` · `Evidence UUID` · `Notes` ·
`Updated ET` · `Schema Version`

Torque, tire pressure, fluid capacity/specification, alignment, and load limits
are safety-critical. `verified` requires OEM/manufacturer/authoritative-regulatory
source tier, exact subject/applicability, and page/section plus revision. A value
from chat or owner memory may stay `candidate`; it never becomes `verified`.
Corrections append a new source identity and supersede the old row rather than
silently overwriting a verified value.

### `Asset Lookup Queue`

`Lookup UUID` · `Entity UUID` · `Lookup Type` · `Query` · `Status` ·
`Evidence UUID` · `Result URL` · `Notes` · `Source Authority` ·
`Source Record ID` · `Updated ET` · `Schema Version`

Lookup types include product identity, UPC product, manual, technical
specification, and part fitment. Search manufacturer/OEM sources first, then the
exact merchant or reputable specialist. `succeeded` requires a retained result
URL; `blocked`, `failed`, and `no_match` are honest terminal evidence, not silent
success. The queue is work state, not a second asset registry.

## User projection: `Asset Browser`

`Entity UUID` · `Asset Label` · `Asset Type` · `Lifecycle Status` ·
`Relationship Summary` · `Connected Receipt IDs` · `Connected Purchase Dates` · `Identifiers` ·
`Manual Links` · `Verified Specifications` · `Evidence Links` · `Updated ET`

The control cycle rebuilds this readable projection from canonical tables. It is
not manually authoritative. Receipt Browser and Asset Browser invoke the same
graph query: a Receipt ID, asset/vehicle/tool UUID, or namespaced identifier must
return the same connected receipts, evidence, manuals, and verified specs.
Traversal uses explicit assignment/installation/use/storage/replacement/alias
edges. It excludes broad `owned_by` traversal so one vehicle query does not
return every household asset.

## Adapter commit gate

1. Read current canonical rows and run the receipt-line identity reconciler when
   a purchase creates inventory.
2. Run `asset_evidence.py` on existing state plus proposed normalized intents.
3. Write only the returned changed rows, preserving immutable UUID/source fields.
4. Read back every target row and any Drive file.
5. Rebuild/read back Asset Browser and confirm receipt-, entity-, and identifier-
   initiated queries converge.
6. Record target health in Audit. A failed manual/spec/browser projection does not
   roll back a verified receipt or asset; it remains a precise degraded target.

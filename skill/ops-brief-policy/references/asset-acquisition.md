# Asset Acquisition and Evidence Enrichment

Load this reference when the user supplies a tool/equipment/product photo, model number, serial number, UPC/SKU/part number, receipt/invoice, warranty card, packaging label, manual, or other evidence that should create/enrich an owned or external asset.

## Intake sources

An asset may be established from one or several sources: receipt email, photographed receipt, product photo, barcode/label photo, model/serial plate, manual, invoice, merchant order, manufacturer lookup, explicit user statement, or an already verified inventory record. These are evidence sources for one asset, not separate assets.

Inspect images directly before OCR fallback. Preserve originals in canonical Drive evidence when normal ingestion is authorized.

## Failure-domain boundary

The asset registry owns physical-asset identity/state. Receipt, manual/knowledge and vehicle/project relationships are evidence/link projections around that identity; they are not permission to turn asset creation into a distributed all-or-nothing transaction.

- When evidence is sufficient to establish the physical asset, create/enrich the canonical asset UUID and read it back before mutating another authority.
- A receipt relationship uses an existing verified Receipt ID/line when reachable. If purchase evidence is temporarily unavailable but independent evidence sufficiently identifies the asset, preserve the asset and leave the receipt relationship unresolved rather than cloning/deleting the asset.
- Manual/Knowledge linkage is downstream: a failed knowledge/manual ingestion does not erase an already verified physical asset.
- Conversely, a manual can be durably ingested even when asset enrichment is temporarily unavailable; the Knowledge UUID remains canonical and the asset relationship can reconcile later.
- Any cross-authority linkage uses stable UUID/Receipt/Knowledge IDs plus target readback. Never use a hidden retry job or shadow registry.

## Immutable identity

Every person and physical asset in canonical LifeOS state gets one immutable RFC 4122 UUID (`Entity UUID`) at creation/import. The UUID is the durable cross-database identity and must be collision-resistant across deployments/family members, not merely unique inside one Sheet.

- Never recycle, renumber, or change an Entity UUID when a display name, owner, category, location, friendly Asset ID, project, or database backend changes.
- Friendly IDs such as `ASSET-...`, tool numbers, labels, nicknames, serials, and vehicle names are aliases/attributes, not primary identity.
- A later PostgreSQL/object-store migration preserves existing UUIDs exactly.
- Merging duplicate records retires/aliases the losing record to the surviving UUID with an audit relationship; it never silently reuses an old UUID for a different physical object.
- External/beneficiary assets use the same UUID identity rules as household-owned assets.

## Canonical asset and relationship records

`People & Assets` is the canonical general physical-asset registry. Specialized inventories such as Tool Inventory retain their domain-specific columns but expose one `Entity UUID` per physical record. `Asset Relationships` is the canonical graph for UUID-to-UUID ownership, assignment, installation, storage, replacement, alias/merge, and supported-use edges.

Normalized supporting tables are not optional free-text duplicates:

- `Evidence Index` retains Gmail/photo/receipt/label/manual/manufacturer evidence identity, source locator/hash, exact entity/Receipt ID/receipt-line links, and status;
- `Asset Identifiers` stores one namespaced identifier row per Entity UUID/value/type, preserving the printed value and a deterministic normalized search value;
- `Knowledge Index` plus `Knowledge Relationships` stores retained manuals/references and their explicit asset/vehicle/tool applicability;
- `Technical Specifications` stores one exact subject UUID, value/unit, applicability, revision, source tier, source URL or Knowledge UUID, and page/section locator;
- `Asset Browser` is a user-facing projection over those authorities, not an editable second registry.

- Receipt-created assets carry the exact `Receipt ID` and exact receipt-line coordinate/source key; never link only by a descriptive item string.
- Relationship rows carry their own immutable RFC 4122 UUID, both endpoint UUIDs, relationship type/status, source identity, timestamps, and receipt/evidence provenance when applicable.
- Use `assigned_to` for intended or canonical allocation and `installed_on` only for supported physical-installation evidence. Never silently upgrade one to the other.
- One set/lot may have quantity greater than one under one asset UUID. Use one UUID per item only when serial-level identity, warranty, maintenance, loss, or movement tracking is genuinely useful.
- Run `scripts/inventory_reconciliation.py` before provider writes. It rejects UUID replacement/collision, duplicate source identity, invalid quantity/tracking mode, unknown relationship endpoints, self-links, and inventory creation from excluded receipt lines.
- Run `scripts/asset_evidence.py` before identifier/evidence/knowledge/specification writes. It rejects invalid GTIN/IMEI check digits, missing namespaces, serial/IMEI/MAC collisions, cross-asset evidence misuse, unretained manual claims, unsafe specification provenance, and source-identity mutation.

## Identity resolution

1. Extract stable identifiers exactly when visible: manufacturer, product name, model, manufacturer part number, SKU, UPC/EAN/GTIN, serial number, IMEI/MAC or domain-specific identifiers.
2. Normalize formatting but preserve the source text/provenance.
3. Search manufacturer/OEM documentation first, then exact vendor SKU/product pages, then reputable specialist catalogs.
4. Enrich evidence-backed specifications useful for future matching: dimensions, platform/battery family, voltage, compatibility/application, capacities, warranty, included accessories, color/variant, etc.
5. Treat OCR and barcode decoding as extraction, not truth. Preserve the exact source, corroborate material identity, and keep unsupported candidates out of `verified` state.

UPC/GTIN lookup uses the printed digits including leading zeroes and validates the check digit before web research. A merchant SKU, manufacturer part number, model number, and serial number always carries its merchant/manufacturer namespace. Never relabel a merchant SKU as UPC merely because it is numeric.
5. Never invent a serial/model digit that is unreadable. Queue the missing value only when it is actually required.

## Dedupe and ownership

Before creating an asset, search existing canonical asset/tool/inventory records by Entity UUID when supplied, serial, model+purchase, part/SKU, receipt/order, photo/evidence hash and descriptive identity. Enrich an existing asset when evidence describes the same physical item.

- One physical asset gets one immutable Entity UUID and may also have one friendly Asset/Tool ID.
- Multiple receipts/evidence objects/manuals may link to the same asset.
- A multi-quantity purchase may create multiple physical asset UUIDs only when individual tracking is useful or unique serials exist; otherwise retain quantity at the line/inventory level.
- Owner/beneficiary and related vehicle/project are separate relationships. A tool used on a vehicle does not become a vehicle part.

## Automotive fitment

For automotive parts, load receipt-classification-fitment.md too. Resolve part identity/application against the complete owned/external vehicle registry and known modifications. Use exclusion evidence. Unique fitment may be auto-assigned; material ambiguity is queued only after reachable evidence is exhausted.

## Receipt, manual and warranty linkage

When purchase/reference evidence exists:

- link the asset UUID to the existing Receipt ID and exact receipt line rather than duplicating spend;
- preserve merchant/order/date/price evidence;
- route retained manuals/service documents through `knowledge-manual-ingestion.md` and link their Knowledge UUIDs to the asset UUID;
- capture warranty period/registration/support documentation only when supported;
- keep replacement/returned/disposed status as lifecycle state rather than deleting the original asset identity.

These relationships are independently reconcilable. A relationship is not considered healthy until its target readback agrees, but relationship failure does not invalidate the already verified source UUID. The exact receipt line must also read back its acquired asset UUID and assigned target UUID(s); a note or vehicle-name string alone is not an integrated relationship.

## Bidirectional query contract

Receipt Browser and Asset Browser use the same graph query. Starting from an exact Receipt ID, Entity UUID, or namespaced identifier must return the same connected receipt lines, assets, explicit relationships, evidence, manuals and verified specifications. Relationship traversal is bidirectional for `assigned_to`, `installed_on`, `used_with`, storage/replacement and alias edges. Do not traverse `owned_by` as a general join: doing so would make a WRX query return every tool and vehicle owned by the same person.

## Completion gate

Core asset acquisition is complete only when immutable UUID identity/dedupe, ownership/beneficiary, searchable evidence-backed identifiers, and any asset-local required fitment/classification are verified or precisely queued. Never mark acquisition complete because a photo was merely saved.

Receipt/manual/warranty relationships that cross another authority are separate projection-health checks. Report them `Degraded/Pending` when their target is unavailable or ambiguous, preserve the core asset, and reconcile later from the verified asset UUID plus target authority. Do not roll back or duplicate the physical asset to repair a relationship.

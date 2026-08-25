# Knowledge and Product-Manual Ingestion

Load this reference when the user supplies a product manual, service manual, datasheet, warranty guide, technical PDF, download URL, uploaded file, email attachment, or other durable reference that should remain queryable in LifeOS.

## Interim authority

Until the self-hosted LifeOS database/object store is deployed:

- keep the original manual/reference file in the canonical Google Drive `Manuals & Reference` hierarchy;
- index searchable metadata and relationships in the canonical `Knowledge Index` Sheet;
- treat Drive as the evidence/file store and the Sheet as the searchable index, not chat history;
- preserve identifiers so a later PostgreSQL/object-store migration can retain the same Knowledge UUID and asset relationships.

A chat, upload, email, URL, and Drive copy may be multiple evidence paths to one reference. Do not create duplicate knowledge records merely because the same manual arrives twice.

## Failure-domain boundary

Drive file retention plus the `Knowledge Index` are the required internal capabilities of the knowledge/manual module. Asset, receipt, project and other relationships are downstream links from the canonical Knowledge UUID.

- A knowledge object is not complete until its retained file and Knowledge Index row both exist and read back correctly.
- Once the Knowledge UUID/file/index are verified, failure to update an external asset/receipt/project relationship does not roll back or duplicate the knowledge object. Mark only that relationship `Degraded/Pending` and reconcile later by stable IDs.
- Conversely, an existing asset does not become invalid merely because its manual cannot yet be retained/indexed.
- Never create a second shadow knowledge database or hidden retry task to compensate for a Drive/Sheet outage.

## Identity and dedupe

Every canonical knowledge object gets one immutable RFC 4122 UUID (`Entity UUID`). Never recycle or mutate that UUID when a title, filename, folder, manufacturer, model, tags, or related asset changes. A readable `Knowledge ID` is an alias for humans, not the primary identity.

Before creating a record, search existing knowledge by:

1. exact Drive file ID or content hash when available;
2. source URL plus revision/version;
3. manufacturer + model/part number + document type/version;
4. normalized title/filename plus related asset when uniquely identifying.

If existing evidence identifies the same manual, enrich/update that record and preserve the UUID.

## Intake and filing

1. Inspect the supplied file/link and determine document type, manufacturer/publisher, title, model/part/SKU, revision/version, effective/publication date, language, and related asset(s) when supported.
2. Prefer the manufacturer's/OEM's official download/source when available. Preserve the original supplied source URL as provenance even when a stronger canonical source is found.
3. Save or copy the retained file into the canonical Drive `Manuals & Reference` hierarchy using a readable filename. Never place credentials or secrets in filenames/metadata.
4. Upsert one `Knowledge Index` row containing Knowledge ID, Entity UUID, title/type, manufacturer/model/part, source URL, Drive file URL/ID, version/date, tags, concise summary, status, and update timestamp.
5. Validate the proposed knowledge row and explicit `Knowledge Relationships` through `scripts/asset_evidence.py`. `retained` requires the canonical Drive file ID/URL and an explicit revision/edition; an attempted lookup that could not be downloaded remains `download_blocked`, `unavailable`, or `lookup_queued` rather than pretending the manual is retained.
6. Verify the Drive file and Sheet row by readback. These two steps establish the canonical knowledge object.
7. After core knowledge readback succeeds, reconcile related asset UUID(s), receipt IDs, part numbers, or projects when evidence supports the relationship. Do not create a duplicate asset merely because a manual exists. Read back each target relationship; a target failure leaves only that relationship pending.

## Search and answer behavior

When the user later asks for a manual, procedure, specification, torque value, setup instruction, or similar reference:

- search the Knowledge Index by asset UUID/ID when linked, manufacturer, model, part/SKU, title, tags, and aliases;
- read the relevant source content when needed rather than answering only from remembered chat context;
- answer with the evidence-backed result and surface the canonical Drive link to the manual/reference;
- cite page/section/revision when the source supports it;
- distinguish source facts from inference.

Preserve relevant extracted facts/provenance in the knowledge system when useful, but do not duplicate an entire copyrighted manual into Git or Sheet cells. The retained Drive file remains the canonical document.

Safety-critical extracted specifications—torque, tire pressure, fluid capacity/specification, alignment, or load limits—enter `Technical Specifications` only as `verified` when the source tier is OEM/manufacturer/authoritative regulatory, the exact subject UUID and applicability are recorded, and the page/section plus revision are retained. A value from chat or owner memory may be a candidate but is never promoted to verified. Never silently apply an STI, trim, engine, transmission, wheel/tire, model-year, or market specification to a different configuration.

## Asset acquisition interaction

A manual can enrich an existing asset with verified model/specification/warranty/application information, but asset identity remains governed by `asset-acquisition.md`. If the manual proves a previously ambiguous part/asset relationship, update that relationship using the existing immutable asset UUID rather than creating another physical asset.

This enrichment is source-first: preserve/read back the canonical Knowledge UUID first, then update the asset relationship. If the asset registry is unavailable, leave the relationship pending and keep the manual queryable.

## Completion gate

Core manual/reference ingestion is complete only after dedupe, durable Drive filing, Knowledge UUID assignment, metadata index upsert, and both required readbacks succeed. If the file cannot be downloaded, Drive is unavailable, or the Knowledge Index cannot be written, surface a precise Action Required instead of leaving the only copy in chat.

Cross-authority asset/receipt/project linkage is reported separately. A pending link does not invalidate a verified knowledge object and must not cause the manual to be duplicated on retry.

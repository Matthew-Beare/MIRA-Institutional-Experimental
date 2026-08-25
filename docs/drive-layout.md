# Google Drive Layout Contract

The exact folder names are deployment state. Resolve the selected Drive root and
domain folders through the private Authority Registry; public source contains no
personal school, employer, vehicle, credential, household, or project names.

A useful deployment may choose short top-level domains such as:

- `Archive & Backups`
- `Assets & Equipment`
- `Education`
- `Household`
- `LyfeOS`
- `Personal`
- `Projects`
- `Recipes`

Deep filing follows ownership and purpose. Education uses the configured
institution/program/course hierarchy. Assets use one hub per immutable Asset UUID
with a friendly alias, for example:

- `Assets & Equipment/<friendly asset alias>/{Manuals & Reference, Maintenance & Parts, Receipts & Purchases}`
- `Assets & Equipment/Tools & Supplies`

Canonical receipt evidence remains under `LyfeOS/02 Receipts & Purchases/Receipt Archive/02 Receipts by Category`. Vehicle and tool hubs contain links to those canonical records, not duplicate financial copies. Multi-vehicle orders have one canonical receipt plus explicit vehicle references.

Active vehicle/tool hubs use native Google Docs, native Sheets views, or supported Drive shortcuts with human-readable titles. Raw `.html`, JSON, Markdown, or source-code link cards are never the user-facing navigation; if retained for provenance, they live under backups.

Legacy full-text receipt material lives under receipt backups and is never the front end. Asset manuals live inside the exact configured asset's `Manuals & Reference` folder and link back to immutable Knowledge and Asset UUIDs.

An issued credential is personal; study material used to earn a credential is education. A filename is not trusted when its content contradicts it. Blank files are named by type and date and retained under `Archive & Backups/Blank Files` rather than left loose.

# External Route / Run Spreadsheet Import

Use this workflow when an employer, dispatch, payroll, driver, or other authoritative source supplies a spreadsheet/export of completed or planned runs, terminals, origins/destinations, paid miles, route identifiers, dates, or related work-leg evidence.

## Non-duplication invariant

An imported spreadsheet is an evidence source, not a new route database. Update/enrich the existing canonical Ops `Routes` / `Trips` records and canonical Mileage & Pay ledger. Never create a parallel mileage/route store merely because the source arrives later or uses different labels.

## Staging and normalization

1. Read the source non-destructively and preserve source file/title/date/version provenance.
2. Detect headers/columns for run ID, trip/load identifier, origin, destination, terminal/customer codes, dates, paid/settlement miles, status, driver/team, and notes where present.
3. Normalize whitespace/case and known terminal aliases, but retain the original source text in provenance. Do not silently merge two locations solely because their city names resemble each other.
4. Treat mileage as directional. `A -> B` does not prove `B -> A` pays the same miles.
5. Separate actual paid/settlement miles from map/odometer/estimated miles. Only company/user-authoritative paid miles enter pay calculations.

## Matching / dedupe keys

Match existing canonical rows from strongest to weakest evidence:

1. exact employer run/trip/load ID when stable;
2. exact source identifier + date/work-cycle;
3. exact origin code + destination code + departure/date + paid miles when unique;
4. normalized origin/destination + date/time + other run facts when uniquely identifying.

If a source row matches an existing trip/mileage fact, enrich that row with provenance and any stronger evidence rather than insert a duplicate. If the new source conflicts with an existing value, preserve both evidence records and mark the canonical field according to source precedence; never overwrite conflict history silently.

## Learned route facts

A historical terminal-pair value may become a learned reference only after exact directional evidence. Store source/date/range so later changes in the company's mileage table can be detected. Do not use a learned value to fabricate a new paid-mile leg before an authoritative source confirms that leg.

## Multi-leg work weeks

Each actual leg remains independent. Import rows into the existing trip sequence, close arrived legs, open/associate subsequent legs only when source evidence supports them, and aggregate all company/user-confirmed paid miles in the configured pay week. Do not infer destination -> home merely because the source export ends.

## Audit

After import verify:

- source rows are accounted for as matched, inserted, conflicting, or explicitly ignored with reason;
- no duplicate Receipt/Trip/Mileage IDs were created;
- directional paid miles remain directional;
- pay totals derive only from supported paid-mile records;
- existing manual/user-confirmed facts were not silently erased;
- source provenance can reproduce every imported change.

# Qualified IT Job Watch

Load this reference for the PM job-monitor phase or a manual qualified-job scan.

## Canonical candidate configuration

- Load the private Ops Status Register `Job Watch Settings` table before making any fit decision. Required columns are `Setting Key`, `Value`, `Updated (ET)`, `Source`, and `Active`.
- Required active keys are `candidate_qualifications`, `education_status`, `hands_on_experience`, `work_history`, `professional_experience_constraints`, `good_fit_role_families`, `excluded_seniority`, `excluded_role_types`, `max_required_relevant_years`, `mandatory_gap_constraints`, and `preferred_vs_required_rule`. `minimum_compensation` is optional and applies only when explicitly configured.
- Treat those owner-approved values as private deployment state. Never hard-code them into portable policy, infer missing qualifications from chat memory, or silently widen the candidate baseline.
- If a required key is missing, duplicated, inactive, invalid, or unavailable, write no fit disposition. Fold one `Action Required — Job Watch Settings unavailable or invalid` item into the brief and continue unrelated modules.

## Search and fit rules

Read new job-opportunity mail in connected Gmail since the last successful PM scan, including configured government sources and legitimate employers or recruiters. Evaluate title family, seniority, mandatory qualifications, relevant professional-experience requirement, education/clearance requirements, location, and compensation only against the active canonical settings.

Reject only when a stated mandatory constraint conflicts with the canonical baseline. A preferred qualification is not a mandatory qualification and does not cause automatic rejection. Record the exact evidence and configured rule behind every rejection or likely-fit decision; if the posting is ambiguous, use `Needs Review` rather than guessing.

## Canonical dedupe and output

- Use the Ops Status Register `Job Watch` table as canonical mutable scan/report state. Required columns are `Job Watch ID`, `Source Message ID`, `Job Key`, `Title`, `Employer`, `Location / Remote`, `Salary`, `Closing Date`, `Application URL`, `Fit Evidence`, `Must-have Gap`, `Disposition`, `First Seen (ET)`, `Reported (ET)`, and `Updated (ET)`.
- Deduplicate first by Gmail message/thread identity, then by normalized application URL, then by normalized employer/title/location key. Enrich one row rather than creating duplicate reports.
- Allowed dispositions are `Likely Fit`, `Rejected`, `Needs Review`, `Reported`, and `Closed`.
- For each newly reportable likely fit, retain title, employer, location/remote status, salary and closing date when available, source identity, application link when available, concise fit evidence, and any genuine must-have gap.
- Fold only new likely fits or a specific review/blocker into the PM Ops Brief. If nothing new is a realistic match, omit the job section.
- Never apply, reply, contact anyone, send email, or mark a role closed without explicit authority.
- If Gmail or the `Job Watch` authority is unavailable, degrade only this module and continue the control cycle.

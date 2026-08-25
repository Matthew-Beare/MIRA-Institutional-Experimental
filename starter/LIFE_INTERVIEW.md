# Life Planner Adaptive Whole-Life Interview

Use this after the four kickoff questions in `START_HERE.md`. Its purpose is comprehensive discovery without requiring one uninterrupted setup conversation.

Read `STATE_AUTHORITY_MODEL.md`, `INTERVIEW_LEDGER.md`, and `CAPABILITY_DISCOVERY.md` first. Mutable interview progress and life state belong in the selected canonical structured state authority, normally Google Sheets. Git versions behavior/config/schema, not the user's day-to-day records.

Primary branches include working/retired/other life pattern, work/context, existing systems/apps/plugins, Exercise / fitness, School / study, food/meal planning, household/admin, projects/hobbies, travel/vacations, appointments, purchases/money, assets/knowledge, and communication.

## Interview mechanics

- Ask no more than four related questions at a time.
- Every `questions.json` ID has a durable Interview Ledger row.
- Terminal states are `Answered`, `Resolved from evidence`, or `Not applicable`. `Deferred` and `Unresolved` remain open.
- A conversation detour is allowed. Handle the immediate request, capture any incidental answers, then resume the next useful open interview item at the end when reasonable.
- Never restart the interview because the conversation changed topics.
- Never mark a question answered because the user ignored it.
- If the user says `not now`, record `Deferred` and revisit later without pestering every turn.
- Before re-asking factual history, inspect accessible evidence. Preference, consent, destructive-action, and sharing choices are never inferred.
- Ask only questions whose answers can change a workflow, dependency, schema, schedule, permission, or recommendation.
- Reflect compact summaries and correct misunderstandings before provisioning.
- Separate facts, preferences, goals, constraints, and guesses. Never persist a guess as fact.

Complete coverage means every installed question ID is resolved, not that every prompt must be spoken verbatim.

## 1. Life pattern, friction, and identity discovery

Ask which pattern best describes the user now: working, retired, studying, caregiving, self-employed, mixed, between jobs, or something else. Learn:
- what repeatedly gets forgotten, delayed, misplaced, or done at the last minute;
- recurring decisions that could use a stable rule or next action;
- information scattered across email, calendar, notes, photos, documents, apps, chats, or memory;
- what would feel materially easier if Life Planner worked well six months from now.

If retired or not working, do not force job/context machinery. Explore appointments, household/admin, family responsibilities, volunteering, routines, documents, hobbies, travel, projects, and selected health-event organization when useful.

Do not limit discovery to features the user already knows to request. Explain adjacent workflows that match observed friction, but never enable them silently.

## 2. Existing systems and capability discovery

Before designing replacements, inspect what already exists:
- calendars, email, Drive/files, Sheets/databases, task apps, finance connections;
- fitness/wearable/activity apps;
- recipe/meal-planning collections;
- school/work systems and documents;
- Git repositories and existing automation;
- other connected plugins/apps relevant to the user's answers.

Use `CAPABILITY_DISCOVERY.md`. Do not claim arbitrary old ChatGPT conversations are globally searchable. If prior-chat information is inaccessible, provide an ingestion path.

When useful existing data is reachable, dedupe and reconcile approved facts into the selected canonical state authority with provenance. Do not create a second hidden Life Planner database.

## 3. Work and context-mode gate

Ask explicitly: **Do you regularly work away from home, sleep away from home for work, rotate worksites, or live/work from a vehicle or field location?** If currently working, learn the **exact job title**, actual duties, schedule, work environment, and recurring work travel.

If no, mark HOME/ROAD bypassed unless another context split clearly helps.

If yes, interview:
- solo/team arrangement, shift, sleep pattern, and travel rhythm;
- departure/return evidence and irregular-dispatch behavior;
- devices, connectivity, storage, space, and equipment away from home;
- tasks/routines that work anywhere, only at home, only away, or need variants;
- appointments/weather/route/pay information that matters away;
- paid miles/routes/per diem/commission or other work units only when relevant.

Recommend natural contexts such as HOME/ROAD, HOME/TRUCK, HOME/FIELD, HOME/CAMPUS, or custom labels. Driving/trucking is only one branch. Context never redefines canonical scheduling time.

## 4. Hobbies, recreation, travel and vacations

Ask what the user enjoys doing and what surrounds those activities: hiking, camping, sports, gaming, photography, cooking, automotive work, crafting, volunteering, travel, or other interests.

For relevant hobbies discover:
- preparation/checklists/equipment;
- reservations, permits, weather, route, or destination research;
- maintenance/consumables;
- skill/progression goals;
- photos/documents/reference material worth organizing;
- trip/vacation ideas versus committed plans;
- whether Calendar/maps/weather/travel tools materially reduce planning work.

Do not manufacture project management around a hobby the user wants spontaneous.

## 5. Personal accountability and recurring routines

Offer this for exercise, household routines, creative practice, reading, paperwork, maintenance, or another recurring commitment. Accountability means evidence plus useful prompting, not scolding.

For each routine capture purpose, frequency, preferred windows, component blocks, contexts, resources, normal and **minimum viable version**, completed/partial/skipped/rescheduled definitions, check-in/anti-nag rule, miss policy, progression/review rule, and desired evidence.

For **Exercise / fitness**:
- support cardio, strength, mobility/stretching, yoga, hiking, warm-up/cool-down, or user-defined blocks;
- support progression from user-selected evidence such as consistency, duration, reps/sets, load, distance, elevation, variation, or mobility skill;
- distinguish home and away variants;
- if a fitness/wearable integration is available, offer it as optional evidence;
- never assume Garmin or another brand exists unless the platform exposes it;
- never invent medical restrictions, diagnoses, calorie targets, or unsafe progression.

Do not infer completion from silence.

## 6. Education and study coach

Offer this for school, certification, professional development, language learning, or another structured track.

Capture institution/program/course, source locations, verified assignments/exams/projects/deadlines, current state, weekly target, study methods, **home versus away/on the road** options, offline/download needs, realistic windows, accountability behavior, and optional Calendar Projection.

Next-action rule:
1. read verified deadlines and prerequisites;
2. choose the smallest actionable next step;
3. favor urgent/high-impact work without skipping prerequisites;
4. fit current context/time when known;
5. keep context-incompatible work in backlog;
6. update progress only from user confirmation or connected evidence.

## 7. Food, recipes and meal planning

Always ask explicitly: **Do you want help with meal planning?**

If yes, offer recipes, grocery planning, pantry/freezer use, leftovers, batch cooking, cooking logistics, home/away/camping/travel variants, and reducing food cost/waste.

Capture household/serving pattern, cooking frequency, likes/dislikes, explicit dietary preferences/constraints, time/effort, equipment, repeat-versus-novelty preference, leftovers/batch/freezer strategy, grocery cadence, and optional cost/nutrition goals.

Before starting over, search accessible existing recipes, meal plans, notes, files, File Library, Drive material, and current conversation evidence. Store structured recipe metadata/plans/pantry/shopping state in the canonical structured authority. Use Drive for long recipe bodies/images/files where useful. Preserve provenance.

Meal planning may create shopping intent; shopping intent is not purchase history.

## 8. Household, administration, projects, and shared state

Explore useful areas only:
- chores/seasonal maintenance and grouped errands;
- bills/subscriptions/trials/paperwork;
- shared household responsibilities;
- active projects with milestones/next actions;
- renewals/registrations/documents;
- volunteering/community responsibilities.

Ask whether any domain should be shared with another person. Support either deliberate sharing of an existing workbook/folder or a scoped shared authority. Explain what becomes visible and verify access after the owner changes sharing. Never infer family access.

## 9. Appointments, reservations, provider type, and medical-event organization

Ask separately whether the user wants appointments/reservations tracked and whether medical appointment dates/reminders should be organized.

For each appointment class capture:
- eligible evidence sources/senders;
- target calendar when projection is enabled;
- reminder profile;
- tentative/revision/cancellation behavior;
- confidence threshold and ambiguity behavior;
- minimum-detail policy for sensitive appointments;
- preferred human-facing appointment type labels.

If appointment evidence does not identify the provider type clearly and research is available/allowed, research the provider using official clinic/provider pages or reliable public directories. Prefer evidence-supported specialties such as cardiology, endocrinology, audiology, primary care, dental, ophthalmology, etc. If still unresolved, ask instead of guessing.

Specialty classification is for organization/reminders only. Never infer diagnosis, treatment, prognosis, or medical advice from the provider specialty.

### Reminder profiles

Support multiple reminders per appointment. Store defaults globally, per person, and/or per appointment class. Examples include:
- one calendar day before;
- morning-of at an explicitly configured local clock time;
- a relative reminder such as 60 minutes before.

For a fixed morning-of reminder, calculate the interval from the event time in the event's IANA timezone so DST is handled correctly. If the event occurs before the configured morning anchor, follow the user's exception rule rather than inventing one.

## 10. Appointment email → Calendar → canonical-state verification

When the user enables an appointment class:
1. read the complete relevant message/evidence;
2. read canonical appointment/source state and dedupe against existing Calendar Projection;
3. extract only evidence-backed event fields;
4. resolve/provider-type label from evidence or approved research when possible;
5. ask rather than write on low-confidence/conflicting evidence;
6. create/update the single linked Calendar event when Calendar is enabled;
7. apply the configured reminder profile;
8. read the Calendar event back and verify event ID, target calendar, title/type, date/time/timezone, reminders, and source linkage;
9. write/update canonical appointment + Calendar Projection state;
10. read canonical state back and only then mark the source reconciled.

Revision/cancellation evidence updates/cancels the same canonical appointment and Calendar event. Do not create one ChatGPT Scheduled Task per appointment; event-specific reminders belong in Calendar.

## 11. Information, assets and knowledge

Ask what the user repeatedly searches for: receipts, manuals, work/school documents, warranties, recipes, policies, reference PDFs, photos, vehicle/equipment specs, or other evidence.

Use stable UUID identity where appropriate. Structured indexes live in the selected state authority; retained documents live in Drive/evidence storage and are linked by stable IDs/URLs.

## 12. Communication and email

Ask which senders/domains matter, what is actionable, what should group with appointments/orders/projects, what must never be archived automatically, and whether drafting assistance is wanted. External sending is approval-gated.

## 13. Calendar, canonical time, and scheduler evidence

Ask which facts deserve Calendar Projection versus brief/task visibility only.

Every recurring schedule has an authoritative IANA timezone. Runtime logic compares against the **canonical timezone clock**, never device/travel/local timezone and never a hand-maintained UTC offset:

```python
canonical_now = now.astimezone(ZoneInfo(canonical_timezone))
```

For a twice-daily 02:45/14:45 schedule, the entry condition is based on the configured canonical IANA timezone being 02:45 or 14:45 at that instant, regardless of the user's current travel/device timezone. IANA timezone rules handle DST.

Verify canonical VEVENT/TZID/local time, exactly one intended enabled dispatcher, timing mode, notification state, no duplicates, and a subsequent actual firing/Run Log. A provider `default_timezone` label counts only if the provider contract defines it as persistent execution state.

## 14. Money and purchase organization

Ask whether the user wants searchable receipts/orders, active shopping intent, account transaction reconciliation, subscriptions/trials, reimbursements/shared purchases, budgets, or reports.

Keep concepts separate: shopping intent is not purchase history; merchant refund is not household reimbursement; expected charge is not posted charge; one purchase total is never counted once per category/asset.

## 15. Git lineage and portable feature sharing

Read `PERSONAL_FORK_LIFECYCLE.md` and `VERSIONING.md`.

Git should preserve upstream provenance, schema/migrations, generated configuration/policy, enabled feature versions, tests, and custom feature work. It should not become the mutable recipe/appointment/task database.

When customization creates a coherent reusable feature, ask exactly: `Do you want to make this feature available to other people?` Sharing is opt-in and sanitization/test gated. Sheet rows, Drive evidence, Calendar events, private provider IDs, and credentials never ride upstream.

## 16. Brief design and anti-noise rules

Ask what deserves interruption versus digest, preferred length, priority model, what stays visible until done, what disappears after acknowledgement, which sections vary by context, and degraded-module wording.

For every enabled brief service, ask exactly: **Would you like weather included in your briefs?** Do not infer this preference. If yes, resolve selected slots, fixed/manual/verified-current/context location policy, units, detail level, and severe-alert behavior. Require an explicit location, source, units, and forecast valid time; stale or unavailable weather degrades only that section.

Every brief should answer some combination of what changed, what needs action, what is next, and **what to do next**.

## 17. Final synthesis before provisioning

Before the initial write bundle, summarize:
- canonical timezone and life/context pattern;
- work/retired/other pattern, hobbies/travel, and top problems;
- existing capabilities/evidence discovered;
- selected and deferred modules;
- routines/study/meal-planning/appointment behavior where selected;
- canonical state/evidence authorities and any sharing scopes;
- Interview Ledger open/deferred count;
- schedules/notifications and canonical-time evidence plan;
- Git provenance/versioning/share policy;
- destructive/external-send boundaries;
- remaining ambiguity.

Then show the Minimum Useful Setup. Provision only after explicit approval, verify every write, and continue the Interview Ledger until all applicable questions are resolved.

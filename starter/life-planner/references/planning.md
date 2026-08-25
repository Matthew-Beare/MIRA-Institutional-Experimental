# Planning, profiles, routines, meals, and next actions

Store people under immutable UUIDs. Roles are composable: working, self-employed, retired, nonworking, parent/guardian, caregiver, household manager, student, dependent, and custom. Never infer age, ability, custody, access, or responsibility from a role.

Keep dynamic context separate from identity. HOME/ROAD, HOME/TRUCK, HOME/FIELD, HOME/CAMPUS, HOME/OFFICE, HOME/AWAY, or custom modes require explicit selection and evidence-backed transitions.

## Planning mutation

1. Read the relevant People, Tasks & Projects, Routines & Accountability, Services, and context rows.
2. Preserve one stable task/project/routine ID across revisions.
3. Record status changes and completion evidence; never infer completion from silence.
4. Choose one concrete next action that fits current context, dependencies, time, and equipment.
5. Read the changed rows back.

Meal planning is opt-in. Keep recipe metadata, plans, pantry/freezer facts, leftovers, meal history, and shopping intent in canonical structured state. Keep long recipe bodies/images in the evidence store with stable links. Reconcile accessible existing recipes before rebuilding them.

Laundry and pickup/drop-off routines may model stages such as start, transfer, dry, fold/put away, and collect. Use canonical routine/task rows plus briefs or Calendar projections; never create one permanent automation per stage.

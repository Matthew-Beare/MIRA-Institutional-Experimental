# Meal Planning Acceptance Contract

A compliant deployment must prove:

1. first boot explicitly asks `Do you want help with meal planning?`;
2. existing accessible recipe/meal-plan evidence is offered for import/reconciliation before manual recreation;
3. inaccessible old chats are never claimed as read;
4. structured recipe indexes, accepted meal plans and pantry/freezer facts live in the meal module's selected canonical structured authority;
5. long recipe bodies/images/documents may live in Drive/evidence storage with stable canonical references;
6. source-state mutations receive canonical authority readback before success;
7. meal plan, active shopping intent and purchase history remain separate identities;
8. when shopping-intent projection is enabled, the canonical meal plan commits/readbacks first, the declared shopping projection uses a stable correlation identity, and target readback is required before that projection is successful;
9. shopping-projection failure leaves the meal plan committed and only the projection Degraded/Pending; retry reconciles source state to target state rather than duplicating the meal plan or creating a hidden retry job;
10. private meal/pantry/history state stays out of portable upstream source;
11. explicit user preferences drive dietary behavior and the system does not invent medical restrictions;
12. missing optional connectors degrade only their adapter path;
13. state sharing is explicit and distinct from public feature sharing.

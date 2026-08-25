# Ops Brief Regression Contract

This file is retained from the emergency `main` fixes as a human-readable compatibility index. Executable regression authority lives in:

- `skill/ops-brief-policy/scripts/test_ops_policy.py`
- `skill/ops-brief-policy/scripts/test_ops_policy_entry.py`
- `skill/ops-brief-policy/scripts/test_financial_resolution.py`
- `skill/ops-brief-policy/scripts/test_reconcile_shipments.py`
- `tests/test_bootstrap.py`
- `tests/test_contract.py`

The suite must continue covering at least:

1. active trip outranks the weekly HOME default and forces ROAD;
2. live unexpired explicit HOME override outranks an active trip;
3. `Home early` closes current mileage accrual and keeps HOME through the next Friday 2:45 PM ET brief;
4. non-Thursday mileage authority failure cannot abort the whole brief;
5. Thursday mileage failure degrades the run and emits the canonical Action Required message;
6. Thursday mileage/pay renders even while HOME;
7. Saturday AM appointment horizon is seven days;
8. terminal company-paid miles are directional and reverse values are never inferred;
9. one receipt may contain independently classified line items and balanced allocations without duplicate spend;
10. identifiable part/SKU fitment is evidenced before final asset assignment, with ambiguous matches queued rather than guessed;
11. cancellation and financial resolution remain separate, with unresolved expected corrections surfaced after five business days;
12. replacement orders retain separate Receipt IDs and reciprocal linkage;
13. no automatic email sending or destructive Gmail behavior occurs without explicit bounded approval.

CI, not this document, decides whether the regression contract passes.

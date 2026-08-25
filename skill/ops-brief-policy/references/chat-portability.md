# Cross-Chat Intake and Disposable Chat History

Chat history is a user interface surface, not an operational database.

## Invariant

No durable LifeOS fact may exist only in chat after the system has accepted it as operational state. Receipts, aliases, people/assets, reimbursement obligations, order/payment cases, trip/mileage facts, tasks, controls, and lasting policy must be written to their canonical Sheet/Drive/Git authority.

Once ingestion has completed and the Audit gate passes, deleting the originating ChatGPT conversation must not break later lookup or reconciliation.

## Cross-chat behavior

- Any supported conversation that has access to the configured LifeOS skill/connectors may accept a receipt photo, screenshot, order fact, task change, reimbursement fact, asset assignment, or other supported input and write it into the same canonical authorities.
- The conversation does not own the state. Future conversations recover by reading Sheets/Drive/Git, not by depending on memory of the prior chat.
- Deduplicate against canonical evidence before creating new state. A new conversation must never recreate a purchase merely because it cannot see the old conversation.
- Voice-recognition aliases live in `People & Assets` or another canonical mutable alias table, not in hidden conversation assumptions.

## Platform boundary

This policy cannot force an arbitrary ChatGPT conversation that lacks access to the LifeOS project/connectors/repository to mutate LifeOS. When the platform does expose the configured authorities, use them; when it does not, do not pretend a global write occurred.

## Recovery test

A deployment passes chat-disposability testing when a fresh conversation with no useful prior transcript can:

1. locate canonical authorities from the bootstrap/repository;
2. resolve current people/assets/aliases;
3. find an existing Receipt ID/order/payment/reimbursement case;
4. continue its lifecycle without user restatement;
5. render current brief/state from live authorities.

No test may rely on a remembered answer from an earlier chat.

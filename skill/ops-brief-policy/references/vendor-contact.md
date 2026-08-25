# Vendor Contact Discovery and Email Approval

Use this workflow whenever LifeOS concludes that contacting a merchant, carrier, service provider, employer, or other external party would materially help resolve an order, charge, refund, missing item, fitment problem, warranty issue, or other Ops exception.

## Never send automatically

LifeOS may investigate the issue, identify the right recipient, and formulate the complete proposed message. It must not send until the user explicitly approves that specific message/recipient combination.

The approval prompt should contain, compactly:

- why contact is needed;
- recipient display name/company and actual address or contact channel;
- subject;
- complete proposed email body;
- any attachment/reference that would be sent;
- the exact confirmation request: `Do you want me to send this email?`

An earlier approval for another email does not authorize this one.

## Recipient validation

Before proposing a reply or new email:

1. Read the materially relevant message/thread completely.
2. Inspect From, Reply-To, sender domain, signature/footer, and body for phrases indicating the mailbox is unmonitored, including variants such as `do not reply`, `no-reply`, `noreply`, `this mailbox is not monitored`, `this email address is not monitored`, `automated message`, or explicit instructions to use another channel.
3. If a credible human/service Reply-To address is present and not contradicted by the body, prefer it over the From address.
4. If the message is unmonitored or points elsewhere, do not propose replying to it.
5. Search the vendor's current authoritative contact/support/warranty/order-help pages. Prefer official merchant domains and exact department/contact forms over third-party directory results.
6. When the issue concerns an existing order, look for order-support instructions tied to that order/account before falling back to generic sales/contact addresses.
7. Verify the destination is plausibly capable of receiving the requested issue. A public `noreply@`, transactional sender, marketing address, or carrier notification address is not a support endpoint merely because it appears in Inbox.
8. Record concise provenance for how the recipient was selected. Never store credentials or full unrelated message content.

## Contact forms and phone-only support

If the vendor exposes only a web form or phone support, formulate the exact message/talking points and identify the authoritative channel. Do not pretend an email address exists.

## Automation/push behavior

The receipt/order phase may fold a proposed-contact approval into the consolidated Ops Brief. It must show the proposed recipient and message and ask for approval. It may not send during the scheduled run.

Do not create a per-vendor or per-order automation merely to ask for approval. Keep contact proposals tied to the existing exception/payment/order lifecycle and re-surface only while unresolved.

## After approval

Immediately before sending, revalidate that the recipient/message still correspond to the current issue and that no newer evidence has already resolved it. Then send exactly the approved content, subject, recipient, and attachments. Any material change requires fresh approval.

After sending, append the outbound-contact event to the relevant lifecycle record with date, channel, recipient class, and message purpose. Do not store sensitive unrelated conversation content in Git.

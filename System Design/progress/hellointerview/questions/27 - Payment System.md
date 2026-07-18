# 27 - Payment System (like Stripe)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/payment-system
**Author:** Evan King · Difficulty: Hard · Pattern: Multi-step Processes

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section, functional requirements, and the scale framing of the non-functional requirements were freely visible. All design content (entities, API, high-level design, deep dives, level expectations) is behind the Hello Interview Premium paywall. This note captures the free content plus the article's structure/outline.

## Understanding the Problem

**What is Stripe?** Payment processing systems like Stripe allow businesses (referred to as **merchants**) to accept payment from customers without having to build their own payment processing infrastructure. Customers input their payment details on the merchant's website, and the merchant sends the payment details to Stripe. Stripe then processes the payment and returns the result to the merchant.

## Functional Requirements

**Core Requirements**

1. Merchants should be able to initiate payment requests (charge a customer for a specific amount).
2. Users should be able to pay for products with credit/debit cards.
3. Merchants should be able to view status updates for payments (e.g., pending, success, failed).

**Below the line (out of scope)**

- Customers saving payment methods for future use.
- Full or partial refunds.
- Transaction history and reports for merchants.
- Alternative payment methods (bank transfers, digital wallets).
- Recurring payments (subscriptions).
- Payouts to merchants.

## Non-Functional Requirements

Free-visible framing: before defining non-functional requirements, ask the interviewer about **scale** — it meaningfully impacts the design. This breakdown targets a system handling about **10,000 transactions per second (TPS) at peak load**.

🔒 *The actual non-functional requirements list is premium-locked.* (From the deep-dive titles you can infer the key ones: high security, durability/auditability with zero transaction data loss, transaction safety and financial integrity despite asynchronous external payment networks, and scalability to 10,000+ TPS.)

## Article Structure (locked sections)

The full breakdown follows this outline — all of the following sections are premium-locked:

- **The Set Up**
  - Defining the Core Entities
  - API or System Interface
- **High-Level Design**
  1. Merchants should be able to initiate payment requests
  2. Users should be able to pay for products with credit/debit cards
  3. The system should provide status updates for payments
- **Potential Deep Dives**
  1. The system should be highly secure
  2. The system should guarantee durability and auditability with no transaction data ever being lost, even in case of failures
  3. The system should guarantee transaction safety and financial integrity despite the inherently asynchronous nature of external payment networks
  4. The system should be scalable to handle high transaction volume (10,000+ TPS) — with subsections on Servers, Kafka, and Database
- **Bonus Deep Dives**
  1. How can we expand the design to support Webhooks?
- **What is Expected at Each Level?** — Mid-level / Senior / Staff+ subsections (content locked)

## Locked Sections Note

Premium-locked and not captured: Non-Functional Requirements list, Core Entities, API/System Interface, all three High-Level Design walkthroughs, all four deep dives (security; durability & auditability; transaction safety/financial integrity with async payment networks; scaling to 10k+ TPS incl. Servers/Kafka/Database), the Webhooks bonus deep dive, and level expectations (Mid/Senior/Staff+).

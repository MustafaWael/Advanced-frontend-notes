# Multi-step Processes

**Source:** https://www.hellointerview.com/learn/system-design/patterns/multi-step-processes

> Note: This page is premium-locked. Everything below is the free/visible content captured on 2026-07-17. Locked sections are listed at the bottom.

## What This Pattern Is

Real production systems must survive failures, retries, and long-running operations spanning hours or days. Often these take the form of **multi-step processes or sagas** which coordinate multiple services and systems. The solutions covered: **distributed transactions, sagas, workflow systems, and durable execution**.

## The Problem (free content)

Building reliable multi-step processes in distributed systems is startlingly hard. While clean systems like databases often deal with a single "write" or "read", real applications need to coordinate dozens of (flaky) services to do the user's bidding, quickly and reliably.

The article recommends Jimmy Bogard's talk ["Six Little Lines of Fail"](https://www.youtube.com/watch?v=VvUdvte1V3s): distributed systems make even a simple sequence of steps surprisingly hard.

**Running example — e-commerce order fulfillment workflow:**

1. Charge payment
2. Reserve inventory
3. Create a shipping label
4. Wait for a warehouse worker to pick the item (human step)
5. Send the confirmation email

Each step calls different services or waits on humans, any of which might fail or time out. Some steps call external systems (like a payment gateway) and wait for completion. Mid-orchestration, your server might crash or get redeployed. And the business may want to change the ordering or nature of steps.

You can patch this organically — fortify each service against failures, use delay queues and hooks for waits and human tasks — but each patch makes the system more complex and brittle. The key design smell: **interweaving system-level concerns (crashes, retries, failures) with business-level concerns (what happens if we can't find the item?)**.

Workflow systems, event-driven sagas, and durable execution solve this. They show up in many system design interviews — particularly where there's a lot of state and a lot of failure handling. **AI system design interviews lean on this even harder, since agent pipelines are long chains of exactly these flaky, stateful steps.** Interviewers love this topic because it dominates on-call rotations for many production teams.

## Solutions Covered (section headings — details premium-locked)

- **Single Server Primitives** — what you can do before reaching for distributed machinery (transactions on one box)
- **The Saga Pattern** — sequence of local transactions with compensating actions on failure
- **Event-Driven Choreography** — services react to each other's events with no central coordinator
- **Workflow Orchestration** — a central orchestrator drives the steps, with subsections:
  - Durable Execution Engines
  - How Durable Execution Works
  - Managed Workflow Systems
  - Implementations (e.g., the Temporal/Step Functions class of tools)

(Only headings visible; each option's mechanics and tradeoffs are behind the paywall.)

## Interview Problems Using This Pattern

The page links this pattern to these Hello Interview problem breakdowns:

- Uber
- Payment System

## When to Use in Interviews (headings — details locked)

- Common interview scenarios
- When NOT to use it in an interview

## Common Deep Dives (headings — details locked)

- "What happens if the process running your saga crashes partway through?"
- "How will you handle updates to the workflow?" (subsections: Workflow Versioning, Workflow Migrations)
- "How do we keep the workflow state size in check?"
- "How do we deal with external events?"
- "How can we ensure X step runs exactly once?"

## Locked Sections (premium-only, not captured)

- Single Server Primitives (details)
- The Saga Pattern (details)
- Event-Driven Choreography (details)
- Workflow Orchestration: Durable Execution Engines, How Durable Execution Works, Managed Workflow Systems, Implementations (details)
- When to Use in Interviews: Common interview scenarios, When NOT to use it
- All five Common Deep Dives listed above (including Workflow Versioning / Migrations)
- Conclusion

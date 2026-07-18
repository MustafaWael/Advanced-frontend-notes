# 07 - Managing Long Running Tasks

**Source:** https://www.hellointerview.com/learn/system-design/patterns/long-running-tasks

> **⚠️ Premium-locked page.** Only the introduction and "The Problem" section were freely visible. All detailed sections (marked 🔒 below) require Hello Interview Premium and are not reproduced here.

---

## What the Pattern Is

The **Managing Long-Running Tasks** pattern splits API requests into **two phases: immediate acknowledgment and background processing.**

When a user submits a heavy task (e.g., video encoding):

1. The web server **instantly validates** the request,
2. **pushes a job to a queue** (Redis / RabbitMQ),
3. **returns a job ID** — all within milliseconds.

Meanwhile, separate **worker processes** continuously poll the queue, grab pending jobs, execute the time-consuming work, and **update job status in a database** (which the client can poll or be notified about via the job ID).

Core architecture components: **web/API server → message queue → worker pool → job-status store (DB)**.

## The Problem It Solves (free content)

The article's motivating example:

- **Fast case:** loading a profile page = one quick DB query; the whole request takes <100ms. Synchronous is fine.
- **Slow case:** generating a PDF report of a user's annual activity — querying multiple tables, aggregating millions of rows, rendering charts, producing a formatted document — takes **45+ seconds**.

Why synchronous processing fails here:

- The browser sits waiting for 45 seconds.
- Most web servers and load balancers enforce **timeout limits around 30–60 seconds**, so the request may never complete.
- Even if it completes, UX is poor: a spinner with **no progress feedback**.

Other examples of work that far exceeds what users will wait for:

- Video uploads → transcoding takes several minutes.
- Profile photo uploads → resizing, cropping, generating multiple thumbnail sizes.
- Bulk operations → sending newsletters to thousands of users, importing large CSV files.

## Article Structure (🔒 = premium-locked detail)

- The Problem *(free — summarized above)*
- 🔒 The Solution
- 🔒 Trade-offs
  - 🔒 What you gain
  - 🔒 What you lose (e.g., immediate consistency, simplicity — details locked)
- 🔒 How to Implement
  - 🔒 Message Queue
  - 🔒 Workers
  - 🔒 Putting It Together
- 🔒 When to Use in Interviews
  - 🔒 For Example
- 🔒 Common Deep Dives
  - 🔒 Handling Failures
  - 🔒 Handling Repeated Failures (dead-letter queues, retry limits — details locked)
  - 🔒 Preventing Duplicate Work (idempotency — details locked)
  - 🔒 Managing Queue Backpressure
  - 🔒 Handling Mixed Workloads (separate queues/worker pools — details locked)
  - 🔒 Orchestrating Job Dependencies
- 🔒 Conclusion

## Interview Problems Where This Pattern Applies

The page doesn't expose an explicit free list, but this pattern is central to these Hello Interview breakdowns (async/background-processing-heavy systems):

- **YouTube** (video transcoding) — https://www.hellointerview.com/learn/system-design/problem-breakdowns/youtube
- **Job Scheduler** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler
- **Web Crawler** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/web-crawler
- **Dropbox** (file processing) — https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox
- **LeetCode** (code execution) — https://www.hellointerview.com/learn/system-design/problem-breakdowns/leetcode

## Key Takeaways from the Free Content

1. Anything that takes longer than users will wait (or longer than LB/server timeouts, ~30–60s) must move off the request path.
2. The pattern = validate fast, enqueue, return a **job ID** immediately; workers do the real work asynchronously.
3. Job status lives in a database, keyed by job ID, so clients can track progress.
4. Expect interview deep dives on: worker failures and retries, repeated failures, duplicate-work prevention, queue backpressure, mixed workloads, and job dependencies (all premium-locked in this article).

## Locked Sections — Study Gaps to Fill Elsewhere

Premium content covers (per the outline): the full solution walkthrough, explicit gain/lose tradeoffs, queue and worker implementation details, interview usage guidance with examples, and the six deep-dive answers (failures, repeated failures, duplicates, backpressure, mixed workloads, job dependency orchestration). These details are **not** captured here because they are premium-only.

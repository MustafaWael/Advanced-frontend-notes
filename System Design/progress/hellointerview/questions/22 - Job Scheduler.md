# 22 - Job Scheduler (Airflow-style)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler

- **Author:** Evan King (Hello Interview)
- **Difficulty:** Medium

> **⚠️ Premium-locked page:** Only the free preview of this breakdown was accessible. The section outline below reflects the article's own structure, but the detailed content of most sections (planning, core entities, API, data flow, high-level design, all deep dives, and level expectations) is behind the Hello Interview Premium paywall and is NOT reproduced here. See "Locked sections" at the bottom.

## Understanding the Problem

**What is a Job Scheduler?** A job scheduler is a program that automatically schedules and executes jobs at specified times or intervals. It is used to automate repetitive tasks, run scheduled maintenance, or execute batch processes.

Two key terms defined before solving the problem:

- **Task**: The abstract concept of work to be done, e.g. "send an email". Tasks are reusable and can be executed multiple times by different jobs.
- **Job**: An instance of a task. It is made up of the task to be executed, the schedule for when the task should be executed, and the parameters needed to execute the task. E.g., if the task is "send an email", a job could be "send an email to john@example.com at 10:00 AM Friday".

The main responsibility of a job scheduler is to take a set of jobs and execute them according to the schedule.

## Functional Requirements

**Core Requirements**

1. Users should be able to schedule jobs to be executed immediately, at a future date, or on a recurring schedule (e.g. "every day at 10:00 AM").
2. Users should be able to monitor the status of their jobs.

**Below the line (out of scope)**

- Users should be able to cancel or reschedule jobs.

## Non-Functional Requirements

The article notes this is a good time to ask about scale: the interviewer would specify that the system should be able to **execute 10k jobs per second**.

*(The specific list of non-functional requirements is premium-locked. From the deep-dive titles, key targets include: executing jobs within 2 seconds of their scheduled time, scaling to 10k jobs/second, and at-least-once execution guarantees.)*

## The Set Up

### Planning the Approach
*(Content premium-locked.)*

### Defining the Core Entities
*(Content premium-locked.)*

### The API
*(Content premium-locked.)*

### Data Flow
*(Content premium-locked.)*

## High-Level Design

The high-level design addresses each functional requirement in turn (details premium-locked):

1. Users should be able to schedule jobs to be executed immediately, at a future date, or on a recurring schedule.
2. Users should be able to monitor the status of their jobs.

## Potential Deep Dives

Three deep dives (all detail premium-locked):

1. **How can we ensure the system executes jobs within 2s of their scheduled time?** — precision of scheduling/dispatch.
2. **How can we ensure the system is scalable to support up to 10k jobs per second?** — throughput and horizontal scaling of the scheduler and workers.
3. **How can we ensure at-least-once execution of jobs?** — failure handling, retries, and avoiding lost jobs.

## What is Expected at Each Level?

The article includes sections for **Mid-level**, **Senior**, and **Staff+** expectations, but the content is premium-locked.

---

## Locked sections (premium-only, not captured)

- Non-Functional Requirements (detailed list)
- Planning the Approach
- Defining the Core Entities
- The API
- Data Flow
- High-Level Design (both requirement walkthroughs, diagrams)
- Deep Dive 1: Executing jobs within 2s of scheduled time (tradeoffs and "great solution")
- Deep Dive 2: Scaling to 10k jobs per second
- Deep Dive 3: At-least-once execution
- What is Expected at Each Level (Mid-level / Senior / Staff+)
- Premium video walkthrough

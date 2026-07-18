# 28 - Metrics Monitoring Platform (like Datadog)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring
**Author:** Stefan Mai · Difficulty: Hard · Patterns: Scaling Writes, Scaling Reads

> **⚠️ Premium-locked page.** The "Understanding the Problem" section, functional requirements, and full non-functional requirements (including scale estimation and an insightful callout on alert latency) were freely visible. All design content beyond that is behind the Hello Interview Premium paywall. This note captures the free content plus the article's structure/outline.

## Understanding the Problem

**What is a Metrics Monitoring Platform?** A metrics monitoring platform collects performance data (CPU, memory, throughput, latency) from servers and services, stores it as **time-series data**, visualizes it on dashboards, and triggers alerts when thresholds are breached. Think Datadog, Prometheus/Grafana, or AWS CloudWatch. This is infrastructure that engineers rely on to understand system health and respond to incidents.

## Functional Requirements

The article notes: even though a metrics monitoring system is simple at face value (collect, store, query), there's lots of potential complexity — narrow the scope with the interviewer.

**Core Requirements**

1. The platform should be able to ingest metrics (CPU, memory, latency, custom counters) from services.
2. Users should be able to query and visualize metrics on dashboards with filters, aggregations, and time ranges.
3. Users should be able to define alert rules with thresholds over time windows (e.g., "alert if p99 latency > 500ms for 5 minutes").
4. Users should receive notifications when alerts fire (email, Slack, PagerDuty).

**Below the line (out of scope)**

- Log aggregation and full-text search (separate concern).
- Distributed tracing (spans, traces).
- Anomaly detection via ML.

## Non-Functional Requirements

**Scale estimation (the crux of the problem):** design for monitoring **500k servers**. If each server emits 100 metric data points every 10 seconds, that's **5 million metrics per second** at peak. Each data point is small (timestamp, value, labels) at roughly 100-200 bytes, but at that volume it's about **1 GB per second** of raw ingestion.

**Core Requirements**

1. The system should scale to ingest 5M metrics per second from 500k servers.
2. Dashboard queries should return within seconds, even for queries spanning days or weeks.
3. Alerts should evaluate with low latency (< 1 minute from metric emission to alert firing).
4. The system should be highly available. Eventual consistency is tolerable for dashboards, but alert evaluation should be reliable.
5. The system should handle late or out-of-order data gracefully (network delays are common).

**Below the line (out of scope)**

- Multi-region replication (would add complexity).
- Strong consistency guarantees.

**Callout — why "< 1 minute" for alerts isn't slow:** In most production systems it's difficult to detect an event until you've accumulated enough data; alerts are often (sensibly) set on moving averages or trends over time. When you truly want instant alerts, the metric itself is designed for it — e.g., Amazon detects order drops (their most important event) by alerting on breaches of "milliseconds since last order." Because order volume is huge, this number is very stable, enabling near-instant firing. Designing metrics like this is an art, but rarely the interview focus.

## Article Structure (locked sections)

The full breakdown follows this outline — all of the following sections are premium-locked:

- **The Set Up**
  - Planning the Approach
  - Defining the Core Entities
  - Data Flow
  - API or System Interface
- **High-Level Design**
  1. The platform can ingest metrics from services
  2. Users can query and visualize metrics on dashboards
  3. Users can define alert rules with thresholds
  4. Users receive notifications when alerts fire
- **Potential Deep Dives**
  1. How do we serve low-latency dashboard queries over weeks of data?
  2. How do we reduce alert latency below 1 minute?
  3. How do we ensure high availability during spikes and failures?
  4. How do we handle cardinality explosion?
- **What is Expected at Each Level?** — Mid-level / Senior / Staff+ subsections (content locked)

## Locked Sections Note

Premium-locked and not captured: Planning the Approach, Core Entities, Data Flow, API design, all four High-Level Design walkthroughs, all four deep dives (low-latency dashboard queries; sub-minute alert latency; HA during spikes/failures; cardinality explosion), and level expectations (Mid/Senior/Staff+). Related free resource on the same site: the "Time Series Databases" advanced-topics deep dive.

# 19 - Strava (Fitness Tracking App)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/strava

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section (functional + non-functional requirements) is freely visible. The Core Entities, API, High-Level Design, and all four Deep Dives are behind the Hello Interview Premium paywall. (This page does not show a "What is Expected at Each Level?" section in its table of contents.) Locked section headings are listed below.

- **Difficulty:** Medium
- **Pattern tags:** Scaling Writes · Real-time Updates
- **Author:** Evan King

## Understanding the Problem

**What is Strava?** Strava is a fitness tracking application that allows users to record and share their physical activities — primarily running and cycling — with their network. It provides detailed analytics on performance and routes, and allows social interactions among users.

Scope note from the breakdown: while Strava supports many activity types, **this question focuses on running and cycling only**.

### Functional Requirements

**Core requirements:**

1. Users should be able to **start, pause, stop, and save** their runs and rides.
2. While running or cycling, users should be able to **view live activity data**: route, distance, and time.
3. Users should be able to **view details of completed activities** — their own and their friends'.

**Below the line (out of scope):**

- Adding or deleting friends (friend management).
- Authentication and authorization.
- Commenting or liking runs.

### Non-Functional Requirements

**Core requirements:**

1. Highly available (**availability >> consistency**).
2. The app should **function in remote areas without network connectivity** (offline support).
3. The app should provide the athlete with **accurate and up-to-date local statistics** during the run/ride.
4. Scalable to support **10 million concurrent activities**.

Notice how unusual these are compared to typical web-service NFRs: offline-first behavior and on-device accuracy are first-class requirements, which is what makes this problem distinctive (client-side buffering + write-heavy ingestion).

## Structure of the Full Breakdown (🔒 premium-locked sections)

- **The Set Up**
  - Defining the Core Entities 🔒
  - The API 🔒
- **High-Level Design** 🔒
  1. Users should be able to start, pause, stop, and save their runs and rides
  2. While running or cycling, users should be able to view activity data (route, distance, time)
  3. Users should be able to view details about their own completed activities and friends' activities
- **Potential Deep Dives** 🔒
  1. How can we support **tracking activities while offline**?
  2. How can we **scale to support 10 million concurrent activities**?
  3. How can we support **realtime sharing of activities with friends**?
  4. How can we expose a **leaderboard of top athletes**?

## Study Hints (inferred from tags and question titles, not the locked text)

- Tagged **Scaling Writes**: 10M concurrent activities each emitting GPS points means very high write throughput — expect discussion of **client-side batching of location updates**, write-optimized stores (Cassandra-style/time-series), and partitioning by activity/user.
- The offline deep dive points to an **offline-first client design**: record GPS data locally on the device, compute stats on-device (which also satisfies requirement 3 without a network round trip), and sync/upload when connectivity returns.
- Tagged **Real-time Updates**: sharing live activities with friends suggests push mechanisms (polling vs. SSE/WebSockets tradeoffs — see the Real-time Updates pattern page).
- Leaderboards are classically solved with **Redis sorted sets** or periodic batch aggregation depending on freshness requirements.

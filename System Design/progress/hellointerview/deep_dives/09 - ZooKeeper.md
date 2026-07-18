# ZooKeeper

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/zookeeper

> **Note: This page is premium-locked.** Only the introduction and the start of the motivating example are freely visible. The notes below capture the free content faithfully; the locked sections are listed at the end.

## What Is ZooKeeper (Interview Framing)?

ZooKeeper (released 2008) is a **coordination service for distributed systems**. The core problem it addresses: how do you orchestrate dozens or hundreds of servers to work together — **electing leaders, maintaining consistent configurations, and detecting failures in real time**?

Although it has aged and numerous alternatives have emerged, it remains **central to the Apache ecosystem**. The article's key argument: understanding ZooKeeper teaches essential distributed systems concepts even if you never use it directly. Its simple primitives — a **hierarchical namespace, data nodes (znodes), and watches** — give you insight into universal problems like **consensus, leader election, and configuration management**.

## A Motivating Example (free portion)

Building a chat application:

- Initially, the app runs on a **single server**. Life is simple: when Alice sends a message to Bob, both are connected to the same server, which knows exactly where to deliver it — all in-memory, low latency, **no coordination needed**.
- (The rest of the example — scaling to multiple chat servers and the coordination problems that follow — is behind the paywall.)

## Locked Sections (premium-only, content not captured)

The following sections exist in the article but are behind the premium paywall:

- ZooKeeper Basics: Data Model (ZNodes), Server Roles and Ensemble, Watches (Knowing When Things Change)
- Key Capabilities: Configuration Management, Service Discovery, Leader Election, Distributed Locks
- How ZooKeeper Works: Consensus with ZAB, Strong Consistency Guarantees, Read and Write Operations, Sessions and Connection Management, Storage Architecture, Handling Failures
- ZooKeeper in the Modern World: Current Usage in Major Distributed Systems, Alternatives to Consider, Limitations, When to use ZooKeeper (Smart Routing; Certain Infrastructure Design Problems; Durable Distributed Locks)
- Summary, References

The section outline itself is a useful study map: ZooKeeper's interview-relevant capabilities are **configuration management, service discovery, leader election, and distributed locks**, backed by the **ZAB consensus protocol** with strong consistency guarantees.

---
tags: [synthesis, system-design, low-level-design, concept-map]
module: "_Synthesis"
priority: must-know
status: solid
verified_on: 2026-07-17
version_scope: "HelloInterview SD + LLD scrapes, GreatFrontEnd FE SD, as of 2026-07"
---

# Concept Map — System Design + LLD + Frontend

The master graph of the scraped knowledge base. Nodes are the load-bearing concepts; edges name the *relationship*, not just "related." Cross-domain edges (the ones that turn three separate study piles into one model) are called out explicitly in the second diagram and fully written up in [[01 - Cross-Domain Wiring]].

Three domains:

- **BE-SD** — backend system design (HelloInterview): distributed systems at multi-server scale.
- **LLD** — low-level design (HelloInterview): single-process OOP, design patterns, in-process concurrency.
- **FE-SD** — frontend system design (GreatFrontEnd): client architecture + the client↔server boundary, server treated as a black box.

The vault already owns FE-SD (module 29) and most of its supporting mechanisms (modules 08, 09, 13, 17, 19, 20, 21, 28). BE-SD and LLD are new territory ([[03 - Vault Integration Plan]]).

## Diagram 1 — Within-domain structure

```mermaid
graph TD
    subgraph BE["BE-SD (distributed, multi-server)"]
        NET[Networking: TCP/UDP, HTTP, SSE/WS/gRPC]
        API[API Design: REST/GraphQL/RPC, pagination, versioning]
        DATA[Data Modeling: SQL/NoSQL, normalization]
        IDX[Indexing: B-Tree, LSM]
        CACHE[Caching: cache-aside, CDN, eviction, stampede]
        SHARD[Sharding + partitioning]
        CH[Consistent Hashing]
        CAP[CAP / consistency levels]
        NUM[Numbers to Know 2026]

        NET --> API --> DATA --> IDX
        DATA --> SHARD --> CH
        DATA --> CACHE
        SHARD --> CAP
        CACHE --> CAP
        NUM -.sizes every decision.-> CACHE
        NUM -.-> SHARD

        subgraph PAT["7 Access Patterns"]
            P1[Real-time Updates]
            P2[Dealing with Contention]
            P3[Multi-step Processes]
            P4[Scaling Reads]
            P5[Scaling Writes]
            P6[Handling Large Blobs]
            P7[Long-Running Tasks]
        end
        P4 --> CACHE
        P4 --> SHARD
        P5 --> SHARD
        P1 --> NET
        subgraph TECH["Deep-dive technologies"]
            REDIS[Redis / Valkey]
            KAFKA[Kafka]
            ES[Elasticsearch]
            CASS[Cassandra]
            DDB[DynamoDB]
            PG[PostgreSQL]
            FLINK[Flink]
            ZK[ZooKeeper]
            GW[API Gateway]
        end
        P4 --> REDIS
        P1 --> KAFKA
        P3 --> KAFKA
        P7 --> KAFKA
    end

    subgraph LLD["LLD (single-process, OOP)"]
        PRIN[Principles: KISS/DRY/YAGNI/SoC/Demeter]
        SOLID[SOLID]
        OOP[Encapsulation/Abstraction/Polymorphism/Inheritance]
        DP[~5 patterns that matter: Factory, Builder, Strategy, Observer, State]
        CONC[Concurrency: atomics, locks, semaphores, condvars, queues]
        PRIN --> SOLID --> OOP --> DP
        OOP -.composition over inheritance.-> DP
        CONC --> COR[Correctness: races]
        CONC --> COORD[Coordination: producer/consumer]
        CONC --> SCAR[Scarcity: pools, rate limits]
    end

    subgraph FE["FE-SD (client + boundary)"]
        RADIO[RADIO framework]
        FEARCH[View / Store / Data-access / Server-black-box]
        FEAPI[Component API + Network API]
        FEOPT[Optimizations: perf, a11y, i18n, resilience]
        RADIO --> FEARCH --> FEAPI --> FEOPT
    end
```

## Diagram 2 — Cross-domain bridges (the high-value edges)

```mermaid
graph LR
    subgraph LLDc["LLD"]
        L_CONC[Concurrency: mutex, optimistic lock<br/>two users book one seat]
        L_DP[Design patterns:<br/>Strategy, Observer, Factory, State]
        L_SOLID[SOLID / SoC]
    end
    subgraph BEc["BE-SD"]
        B_CONT[Dealing with Contention:<br/>distributed locks, idempotency, OCC]
        B_CACHE[Caching: Redis, cache-aside,<br/>CDN, eviction, stampede]
        B_RT[Real-time: SSE / WebSockets / polling]
        B_PAG[Cursor vs offset pagination]
        B_CAP[Consistency spectrum]
    end
    subgraph FEc["FE-SD / vault"]
        F_RACE[Client races:<br/>AbortController, request dedup]
        F_CACHE[Client data layer:<br/>HTTP cache, normalized store, optimistic UI]
        F_RT[Live UI transport choice]
        F_FEED[Infinite feed pagination]
        F_STATE[State mgmt + component patterns]
        F_OPTIMISTIC[Optimistic update + rollback]
    end

    L_CONC ===|same problem, different scale| B_CONT
    B_CONT ===|mirror on the client| F_RACE
    L_CONC -.optimistic lock == optimistic UI.-> F_OPTIMISTIC
    B_CACHE ===|mirror-image decisions| F_CACHE
    B_CAP ===|eventual consistency = stale UI window| F_OPTIMISTIC
    B_RT ===|identical transport table| F_RT
    L_DP ===|recur as| F_STATE
    L_SOLID ===|component boundaries| F_STATE
    B_PAG ===|same API contract| F_FEED
```

## How to read the edges

- `===` bold cross-domain edges are the ones worth memorizing; each is a place where knowing one side sharpens the other. All are written out with mechanism-and-divergence in [[01 - Cross-Domain Wiring]].
- `-.->` dotted edges are "sizes / constrains / motivates" relationships.
- The seven patterns (P1–P7) are the *connective tissue* of BE-SD: each one pulls specific KB concepts and specific technologies. They are the backend analog of RADIO's "O" deep-dives.

## Legend of node clusters

| Cluster | Where it lives now | Where it's going ([[03 - Vault Integration Plan]]) |
| --- | --- | --- |
| BE-SD KB + patterns + tech | `System Design/progress/hellointerview/` | new `30 - Backend System Design` |
| LLD principles/patterns/concurrency | `Low Level Design/progress/hellointerview/` | new `31 - Low Level Design` |
| FE-SD framework + case studies | `System Design/progress/greatfrontend/` | already in vault `29 - Frontend System Design` |

## Coverage note

Large portions of the HelloInterview patterns, deep dives, and Numbers-to-Know are **premium-locked in the scrapes** (only headings captured). The concept inventory ([[02 - Concept Inventory]]) marks every locked node so Phase B fills those gaps from primary sources rather than treating the scrape as complete. Locked nodes are still placed on this map because their *headings* tell us the shape of what's missing.

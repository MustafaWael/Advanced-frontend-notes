# 08 - Rate Limiter (In-Memory, API Gateway)

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/rate-limiter
**Difficulty:** Hard · By Evan King (Hello Interview)

> **Note on completeness:** This page is premium-locked past the "Core Entities" intro. The *Understanding the Problem* and *Requirements* sections below are captured from the free portion. Locked sections are listed at the bottom with their visible headings.

---

## Understanding the Problem

**What is a Rate Limiter?** A rate limiter controls how many requests a client can make to an API within a specific time window. When a request comes in, the rate limiter checks if the client has exceeded their quota. If they're under the limit, the request proceeds. If they've hit the cap, the request gets rejected. This protects APIs from abuse and ensures fair resource allocation across clients.

## Requirements

The interview prompt:

> "You're building an **in-memory rate limiter for an API gateway**. The system receives configuration from an external service that provides rate limiting rules per endpoint. Each endpoint can have its own limit with a specific algorithm. Example configuration for one endpoint:
>
> ```json
> {
>   "endpoint": "/search",
>   "algorithm": "TokenBucket",
>   "algoConfig": {
>     "capacity": 1000,
>     "refillRatePerSecond": 10
>   }
> }
> ```
>
> This config allows bursts up to 1000 requests, refilling at 10 requests per second. Your job is to build the in-memory rate limiter that enforces these rules."

### Clarifying Questions (and what each answer tells you)

1. **"Are there different parameter sets for different algorithms?"**
   → *"Yes — different algorithms need different parameters. The `algoConfig` object always exists, but the parameters inside it vary."*
   Takeaway: the config is **heterogeneous** per algorithm. (This is the hint pointing at a **Factory** that maps algorithm name + config → the right Limiter implementation, behind a common `Limiter` interface — Strategy pattern.)

2. **"When a request comes in, what information do we receive?"**
   → *"Each request provides a client ID and an endpoint. The client ID is just a string uniquely identifying who's making the request."*

3. **"What should we return when checking a request? Just allowed/denied?"**
   → *"Return three things: whether it's allowed, how many requests remain in their quota, and if denied, when they can retry."*
   Takeaway: the return type needs **structure, not just a boolean** → a `RateLimitResult` value object.

4. **"What if a request comes in for an endpoint with no configuration?"**
   → *"Fall back to a default configuration. Don't reject requests just because we're missing config."*

5. **"Should the system handle concurrent requests from multiple threads?"**
   → *"Don't worry about it to start. We'll get to it if we have time."*

   > **Interviewer pattern worth memorizing:** "Don't worry about X" usually means they want a clean foundation first, not that they don't care about X. If you finish early, they'll circle back with "now how would you handle X?" — your cue to discuss extending the design. Thread safety returns in the extensibility section.

6. **"Distributed rate limiting across servers, or single-process in-memory?"**
   → *"Single process, in-memory. Keep it simple."*
   Takeaway: huge simplification — no network coordination, no shared state across machines. (The distributed version is a separate **system design** question; Hello Interview has a "Design a Distributed Rate Limiter" breakdown.)

7. **"Is configuration dynamic, or loaded once at startup?"**
   → *"Loaded at startup. Don't worry about hot-reloading."*

### Final Requirements

```
Requirements:
1. Configuration is provided at startup (loaded once)
2. System receives requests with (clientId: string, endpoint: string)
3. Each endpoint has a configuration specifying:
   - Algorithm to use (e.g., "TokenBucket", "SlidingWindowLog", etc.)
   - Algorithm-specific parameters (e.g., capacity, refillRatePerSecond for Token Bucket)
4. System enforces rate limits by checking clientId against the endpoint's configuration
5. Return structured result: (allowed: boolean, remaining: int, retryAfterMs: long | null)
6. If endpoint has no configuration, use a default limit

Out of scope:
- Distributed rate limiting (Redis, coordination)
- Dynamic configuration updates
- Metrics and monitoring
- Config validation beyond basic checks
```

## Core Entities and Relationships

Free intro only: scan the requirements for **nouns that represent things with behavior or state**; treat each noun as a candidate entity, then prune until the list makes sense to model. *(The pruned list itself is locked.)*

## Class Design (headings visible; content locked)

The breakdown designs:

- **RateLimiter** — the facade the gateway calls: `check(clientId, endpoint) → RateLimitResult`; routes to the right per-endpoint limiter, falls back to a default config
- **LimiterFactory** — Factory pattern: reads a config entry (`algorithm` + `algoConfig`) and constructs the matching Limiter implementation
- **Limiter** — Strategy interface all algorithms implement (TokenBucket, SlidingWindowLog, ...), tracking state per client
- **RateLimitResult** — value object: `(allowed, remaining, retryAfterMs)`

Plus a **Final Class Design** diagram. *(Signatures and diagram are premium-locked.)*

## Implementation (locked)

Sections: LimiterFactory, RateLimiter, Rate Limiting Algorithms (**TokenBucketLimiter** shown), Complete Code Implementation, Verification.

## Extensibility (headings visible; content locked)

1. "How would you add a new rate limiting algorithm?" — (the Factory + Strategy split should make this a new class + one factory case)
2. "How would you handle dynamic configuration updates?"
3. "How would you handle thread safety for concurrent requests?"
4. "How would you handle memory growth from tracking many clients?" — (per-client state eviction, e.g. TTL/LRU territory)

## What is Expected at Each Level? (locked)

Junior / Mid-level / Senior expectation sections are premium-locked.

---

## Premium-locked sections on this page

- Core Entities (pruned list)
- Class Design: RateLimiter, LimiterFactory, Limiter, RateLimitResult + Final Class Design
- Implementation: all code including TokenBucketLimiter, Complete Code Implementation, Verification
- Extensibility: all four follow-up answers
- What is Expected at Each Level: Junior / Mid-level / Senior

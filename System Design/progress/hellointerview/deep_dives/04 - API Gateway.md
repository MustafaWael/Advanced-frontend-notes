# API Gateway

**Source:** [hellointerview.com — API Gateway Deep Dive](https://www.hellointerview.com/learn/system-design/deep-dives/api-gateway)

## What an API Gateway Is

An API Gateway is a **single entry point for all client requests**, managing and routing them to the appropriate backend services. Analogy: the front desk of a luxury hotel — guests don't need to know where housekeeping or maintenance is; clients shouldn't need to know your internal microservice structure.

Gateways rose alongside **microservices**: as monoliths were broken into smaller services, a centralized point of control became necessary. Without one, clients must know about and call multiple services directly — tighter coupling and more complex client code.

Key framing: API gateways are **thin, relatively simple components with a clear purpose**. Don't overcomplicate them in interviews.

## Core Responsibilities

The **primary function is request routing** — deciding which backend service handles each request. (Candidates often introduce a gateway, list all the middleware it does, and forget to mention routing — the core reason it exists.)

Beyond routing, gateways handle **cross-cutting concerns / middleware**: authentication, rate limiting, caching, SSL termination, logging, and more.

## Tracing a Request (Request Lifecycle)

1. **Request validation** — check the request is well-formed: valid URL, required headers present, body matches expected format. Catches obvious failures (malformed JSON, missing API key) before they waste backend resources; gateway rejects early with a helpful error.
2. **Middleware** — configurable tasks, e.g.:
   - Authenticate requests (JWT tokens)
   - Rate limiting / throttling
   - SSL termination
   - Logging and monitoring
   - Response compression
   - CORS headers
   - IP whitelisting/blacklisting
   - Request size validation, response timeouts
   - API versioning, service discovery integration

   Most interview-relevant: **authentication, rate limiting, IP allow/deny lists**. Suggested interview line: *"I'll add an API Gateway to handle routing and basic middleware"* — then move on.
3. **Routing** — the gateway maintains a **routing table** mapping requests to services, keyed on URL paths (`/users/*` → user service), HTTP methods, query params, and headers. Example config:

   ```yaml
   routes:
     - path: /users/*
       service: user-service
       port: 8080
     - path: /orders/*
       service: order-service
       port: 8081
     - path: /payments/*
       service: payment-service
       port: 8082
   ```

4. **Backend communication** — usually HTTP, but the gateway can translate protocols (e.g. external HTTP → internal gRPC), letting services use whatever is most efficient internally. Relatively uncommon in practice.
5. **Response transformation** — transform the backend response into the client-requested format (e.g. gRPC response → JSON over HTTP), presenting a clean, consistent external API.
6. **Caching (optional)** — for frequently accessed, **non-user-specific** data that changes rarely. Strategies:
   - **Full response caching** for hot endpoints
   - **Partial caching** of infrequently-changing parts
   - **Cache invalidation** via TTL or events

   Cache in memory or in a distributed cache like Redis.

## Scaling an API Gateway

Two dimensions: increased load and global distribution.

### Horizontal Scaling

Gateways are typically **stateless**, so scale horizontally behind a load balancer. Note the load-balancing distinction:

- **Client-to-gateway LB**: a dedicated load balancer (AWS ELB, NGINX) in front of the gateway instances.
- **Gateway-to-service LB**: the gateway itself load-balances across backend service instances.

In an interview, abstract this: a single box labeled "API Gateway & Load Balancer" is usually sufficient — entry-point details are a distraction from your core design.

### Global Distribution

For globally distributed users, deploy gateways close to users (CDN-like):

1. **Regional deployments** — gateway instances in multiple regions
2. **DNS-based routing** — GeoDNS routes users to the nearest gateway
3. **Configuration synchronization** — keep routing rules/policies consistent across regions

## Popular API Gateways

**Managed services** (easiest, most expensive):

- **AWS API Gateway** — deep AWS integration; REST and WebSocket APIs; throttling, API keys/usage plans, Lambda integration, CloudWatch monitoring.
- **Azure API Management** — strong OAuth/OpenID Connect, policy-based configuration, developer portal.
- **Google Cloud Endpoints** — deep GCP integration, strong gRPC support, automatic OpenAPI docs.

**Open source** (more control / on-prem):

- **Kong** — built on NGINX; extensive plugin ecosystem; traditional and service-mesh deployments.
- **Tyk** — native GraphQL support, built-in analytics, multi-datacenter.
- **Express Gateway** — JavaScript/Node.js based, lightweight, good for Node microservices.

## When to Propose an API Gateway (Interview Guidance)

**TL;DR: use it with a microservices architecture; skip it for a simple client-server architecture.**

- With microservices, a gateway is almost essential — it cleanly separates internal service architecture from the external API surface and prevents clients from coupling to many services.
- For simple monoliths or single-client systems, a gateway is **overkill** — unnecessary complexity.

## Pitfalls

- Introducing a gateway and pitching only its middleware while never mentioning **routing**, its core purpose.
- **Spending too much time on it.** The gateway is not the interesting part of your design. You're far more likely to err by over-explaining it than under-explaining it. *"Get it down, say it will handle routing and middleware, and move on."*
- Getting bogged down in load-balancer-vs-gateway entry-point details instead of the system's core functionality.
- Caching user-specific responses at the gateway (only cache when the same input reliably yields the same output).

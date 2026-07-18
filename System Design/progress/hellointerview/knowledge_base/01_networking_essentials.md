# Networking Essentials

**Source:** [hellointerview.com — Networking Essentials](https://www.hellointerview.com/learn/system-design/core-concepts/networking-essentials)

Networking is fundamental to system design: you're nearly always designing systems of independent devices communicating over a network. Networking is a stronger focus in infrastructure/distributed-systems interviews; for full-stack and product roles a surface understanding usually suffices — but be ready if your interviewer probes (e.g., they just dealt with load balancer or CDN issues on-call).

## Networking 101

Networks are built on a layered architecture (the OSI model) that abstracts away lower-level details. Layers are abstractions letting application developers reason about communication without knowing, e.g., which voltages represent 1s and 0s on the wire — like using `open` in your language instead of manually instructing a disk.

### The Three Key Layers for Interviews

- **Network Layer (Layer 3):** IP — routing and addressing. Breaks data into packets, forwards packets between networks, best-effort delivery to any destination IP. (Other L3 protocols exist, e.g., InfiniBand, used for massive ML training workloads.)
- **Transport Layer (Layer 4):** TCP, UDP, QUIC — end-to-end communication with features like reliability, ordering, and flow control on top of the network layer.
- **Application Layer (Layer 7):** DNS, HTTP, WebSockets, WebRTC — protocols built on TCP (or UDP for WebRTC) for web application data.

Application layer is processed in **user space**; lower layers in **kernel space**. User space = flexible and easy to modify; kernel space = hard to change but very efficient.

### Example: A Simple Web Request

What happens when you type a URL:

1. **DNS Resolution:** Domain name (hellointerview.com) → IP address (e.g., 32.42.52.62).
2. **TCP Handshake (3-way):** SYN (client requests connection) → SYN-ACK (server acknowledges) → ACK (client establishes connection).
3. **HTTP Request:** Client sends HTTP GET over the established connection.
4. **Server Processing:** Server processes and prepares the response (usually the only latency engineers think about and control!).
5. **HTTP Response:** Server returns the page content.
6. **TCP Teardown (4-way):** FIN (client) → ACK (server) → FIN (server) → ACK (client).

Key observations:

- Abstractions simplify our mental models: TCP guarantees ordered, reliable delivery; DNS + IP handle finding and routing to servers.
- One conceptual "request/response" involves many packets and round trips — all adding latency. The higher up the stack, the more latency/processing (relevant for load balancers).
- The connection is **state** both client and server must maintain. Without HTTP keep-alive or HTTP/2 multiplexing, connection setup repeats for every request — significant overhead. Important for systems needing persistent connections (real-time updates).

## Network Layer Protocols

Dominated by **IP** (routing and addressing). Nodes usually get IPs from a DHCP server at boot. **Public IPs** are allocated by Regional Internet Registries (RIRs) and are routable on the internet — e.g., any address starting with 17 (17.0.0.0) belongs to Apple, and internet backbone routers know to send those packets to Apple's routers. Private networks can use arbitrary IPs, but internet traffic can't find them.

## Transport Layer Protocols

The real interview choice is **TCP vs UDP**. **QUIC** is a newer protocol offering TCP-like benefits with modernization and performance gains — think of it as "a better TCP" but without broad baseline adoption yet. Knowing QUIC/HTTP-3 may impress performance-oriented interviewers, but most want your time spent elsewhere.

### UDP: Fast but Unreliable

"The machinegun of protocols" — spray and pray. Connectionless service with no delivery, ordering, or duplicate protection guarantees. You only see source/destination IP and port, plus a binary blob.

Key characteristics:
1. **Connectionless** — no handshake/setup
2. **No guarantee of delivery** — packets may be lost silently
3. **No ordering** — packets may arrive out of order
4. **Lower latency** — less overhead

Perfect where **speed matters more than reliability**: live video streaming, online gaming, VoIP, DNS lookups. E.g., VoIP just drops an occasional packet (small audio hiccup) rather than clogging the network with retransmits and ACKs.

Caveat: browsers don't broadly support UDP outside WebRTC. If a design could use UDP (e.g., spamming hearts/reactions in FB Live Comments), plan an alternative for browser users (e.g., app users get real-time UDP, browser users get a slower batched HTTP stream).

### TCP: Reliable but with Overhead

The workhorse of the internet: reliable, ordered, error-checked delivery. Establishes a connection via 3-way handshake; the connection ("stream") is a **stateful** connection — two messages on the same stream arrive in order. Receivers ACK messages; unacknowledged messages get retransmitted.

Key characteristics:
1. **Connection-oriented**
2. **Reliable delivery** — in order, without errors
3. **Flow control** — don't overwhelm receivers
4. **Congestion control** — adapts to network congestion

Ideal wherever data integrity is critical — i.e., basically everything UDP isn't good for.

### When to Choose Each

Default is TCP — often doesn't even need mentioning. Consider **UDP** when:
- Low latency is critical (real-time apps, gaming)
- Some data loss is acceptable (media streaming)
- High-volume telemetry/logs where occasional loss is fine
- You don't need browser support (or have an alternative client path)

Modern apps often use both: e.g., a video conferencing app uses TCP/HTTP for signaling/auth and UDP/WebRTC for audio/video streams.

### TCP vs UDP Comparison

| Feature | UDP | TCP |
|---|---|---|
| Connection | Connectionless | Connection-oriented |
| Reliability | Best-effort delivery | Guaranteed delivery |
| Ordering | No ordering guarantees | Maintains order |
| Flow Control | No | Yes |
| Congestion Control | No | Yes |
| Header Size | 8 bytes | 20–60 bytes |
| Speed | Faster | Slower due to overhead |
| Use Cases | Streaming, gaming, VoIP | Everything else |

## Application Layer Protocols

### HTTP/HTTPS

Request-response protocol; the de-facto web standard. **Stateless** — each request is independent; the server keeps no info about previous requests. Minimize the stateful surface area of your system; most simple HTTP servers are pure functions of request parameters.

Key concepts: request methods, status codes, headers, body.

**Common request methods:**
- GET — request data; idempotent, no body
- POST — send data to the server
- PUT — update data
- PATCH — partial update
- DELETE — delete data; idempotent

**Common status codes:**
- 2xx Success: 200 OK, 201 Created
- 3xx Moved: 301 Moved Permanently, 302 Found (temporary)
- 4xx Client Error: 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests
- 5xx Server Error: 500 Server Error, 502 Bad Gateway

Headers are flexible key/value pairs — a lesson in designing interfaces flexible to unknown future use-cases. Example: content negotiation via `Accept-Encoding` (client says it can handle gzip/brotli) and `Content-Encoding` in the response — backward compatibility plus graceful degradation.

**HTTPS** adds TLS/SSL encryption against eavesdropping and man-in-the-middle attacks — mandatory for public sites. But encryption doesn't mean the request is trustworthy: never trust request body contents without validation. Classic mistake: taking a user ID from the request body and using it directly — an attacker can change it and read arbitrary user data. Validate everything server-side.

### REST: Simple and Flexible

The most common API paradigm in interviews. Core principle: clients perform simple operations against **resources** (like DB tables or files). Uses HTTP verbs + path conventions, typically JSON bodies. Core Entities from your design usually map directly to resources.

```
GET /users/{id} -> User
PUT /users/{id} + body -> update user
POST /users + body -> create user (server assigns ID)
GET /users/{id}/posts -> [Post]   (nested resources for relationships)
```

Think resources, not operations: `updateUser` → `PUT /users/{id}`; `startGame` → `PATCH /games` with `{"status": "started"}`.

REST is not the most performant option (JSON serialization is inefficient), but most apps aren't bottlenecked by serialization. **Default to REST in interviews**; reach for GraphQL, gRPC, SSE, or WebSockets only with specific needs.

### GraphQL: Flexible Data Fetching

Open-sourced by Facebook (~2015). Solves the frontend/backend coordination problem: with REST you either (a) cobble together many requests (**under-fetching** — multiple round trips, extra latency), (b) build huge, slow aggregation APIs (**over-fetching** — too much data, slow responses), or (c) write new APIs for every page.

GraphQL lets the frontend query exactly the data it needs; the backend responds in exactly that shape. Great for mobile apps and reducing data transfer. Sweet spot: complex clients, multiple teams making wide queries over overlapping data.

For interviews the benefits are murky — requirements are fixed, and interviewers want to see specific query-pattern optimization where GraphQL is "just in the way." Bring it up when the problem is clearly about flexibility or deliberately uncertain requirements.

### gRPC: Efficient Service Communication

High-performance RPC framework from Google using HTTP/2 and **Protocol Buffers** (like JSON but with a rigid schema, binary encoding). Example: a JSON object of 40 bytes becomes ~15 bytes in protobuf — less space and less CPU to parse.

Service definitions (`.proto` files) compile into client/server stubs in many languages. Features for microservices at scale: streaming, deadlines, client-side load balancing. Benchmarks show up to ~10x throughput vs JSON-over-HTTP REST.

**Where to use:** internal service-to-service communication, especially performance-critical or binary-data paths. Not for public-facing APIs (binary protocol, less mature tooling, no browser support). Recommended split: REST for external APIs, gRPC for internal. Using REST for both is fine in many interviews. Beware premature optimization of RPC protocol choice before handling bigger bottlenecks.

### Server-Sent Events (SSE): Real-Time Push

A "nice hack" on top of HTTP letting the server stream many messages over time in a single HTTP response. Instead of one cohesive JSON blob processed at completion, the server pushes newline-delimited `data:` chunks the client processes as they arrive — same TCP connection, one long-lived response.

Limitations:
- Connections can't stay open too long (servers/load balancers/proxies close them). The standard's `EventSource` auto-reconnects with the last-received message ID; servers are expected to track and resend missed messages.
- Misbehaving networks sometimes batch all SSE chunks into one response, defeating the purpose.

Most interviewers don't know these limitations, but interviewers who've implemented SSE may probe whether you've actually used it. **Use for:** near-real-time notifications where the server pushes, e.g., keeping bidders updated on an auction's current highest bid.

### WebSockets: Real-Time Bidirectional Communication

Persistent, TCP-style connection allowing real-time **bidirectional** communication with broad support including browsers. Server can push without a request; client pushes without waiting.

How it works:
1. Client initiates WebSocket handshake over HTTP (backed by a TCP connection)
2. Connection **upgrades** to the WebSocket protocol (can reuse HTTP session info like cookies/headers)
3. Both sides send binary messages over the connection
4. Connection stays open until explicitly closed

WebSockets don't dictate an application protocol — you define the message format (serialized JSON is often fine), which doubles as your API definition. Caveat: every piece of infrastructure between client and server (firewalls, proxies, load balancers) must support WebSockets.

**Use when** you need high-frequency, persistent, bi-directional communication (real-time apps, games). If request/response or SSE push suffices, WebSockets are overkill — launching into WebSockets without justification is a great way to get a thumbs down. Stateful connections at scale require significant design accommodations.

### WebRTC: Peer-to-Peer Communication

Direct peer-to-peer communication between browsers without an intermediary data server — and the only application-level protocol here using **UDP**. Ideal for video/audio calling and conferencing; occasionally for collaborative apps (with CRDTs for truly P2P editors).

Challenges: most clients block inbound connections and sit behind NAT. Components:
- **Signaling server:** central server tracking available peers and their connection info.
- **STUN** (Session Traversal Utilities for NAT): techniques like "hole punching" to establish publicly routable addresses/ports.
- **TURN** (Traversal Using Relays around NAT): relay service bouncing requests through a central server when direct connection fails.

Four steps: (1) connect to signaling server to learn about peers, (2) hit a STUN server to get your public IP/port, (3) share info via signaling server, (4) establish direct P2P connection. Fallback to TURN when direct connection fails.

Advice: stick to WebRTC only for audio/video calling/conferencing. Candidates go "wildly off trail" designing P2P systems that don't need it. (Google Docs-style editors are usually better with WebSockets and a central server anyway.)

## Load Balancing

Scaling options: **vertical** (bigger servers) vs **horizontal** (more servers). Author's preference: vertical where possible — modern hardware is incredibly powerful. But interviews almost always involve horizontal scaling, which requires deciding which server handles each request: load balancing.

### Client-Side Load Balancing

The client decides which server to talk to, usually via a service registry/directory of available servers, with periodic polling or pushed updates. Fast and efficient: no extra network hop per request.

Examples:
- **Redis Cluster:** nodes gossip cluster state; every node knows every other. Clients fetch node/shard info from any node, hash keys to pick the shard, and talk directly to the right node. Wrong node → `MOVED` response redirects you.
- **DNS:** resolvers return a rotated list of IPs per request, so different clients hit different servers. This is also how you avoid a load balancer as a single point of failure: two load balancers (different data centers/regions) rotated via DNS. DNS TTLs cap update speed — far-flung DNS servers cache entries, so updates can't propagate faster than the TTL.

**Use when** (1) small number of clients you control (Redis Cluster client, gRPC's built-in client-side LB for internal services), or (2) many clients but slow updates are tolerable (DNS). Great answer for internal microservice communication.

### Dedicated Load Balancers

A server/hardware device between clients and backends. Costs an extra hop, but gives fast server-list updates and fine-grained routing control.

#### Layer 4 Load Balancers (transport layer)

Route on network info (IPs/ports) **without inspecting packet contents**. Effectively as if the client had a direct TCP connection to a randomly selected backend.

- Maintain persistent TCP connections between client and server
- Fast/efficient, minimal packet inspection
- Cannot route on application data
- Used when raw performance is priority

A client's TCP session sticks to one server — ideal for **persistent connections like WebSockets**.

#### Layer 7 Load Balancers (application layer)

Understand protocols like HTTP; **examine request content and make smarter routing decisions**. They terminate incoming connections and create new ones to backends.

- Route on URL, headers, cookies, etc. (e.g., API traffic to one pool, web pages to another — like an API Gateway; or cookie-based stickiness)
- More CPU-intensive (packet inspection)
- More flexible/featureful; best for HTTP-based traffic

Rule of thumb: **WebSockets → L4; everything else (HTTP, long polling) → L7.** (Some L7 LBs support connection-oriented protocols, but L4 is generally better for WebSockets.)

#### Health Checks and Fault Tolerance

Load balancers monitor backend health and stop routing to failed servers until recovery — automatic failover is what makes LBs essential for high availability. TCP health checks verify a server accepts connections; L7 health checks make an HTTP request and expect a 200 (vs 500 or no response).

#### Load Balancing Algorithms

- **Round Robin** — sequential distribution
- **Random**
- **Least Connections** — fewest active connections
- **Least Response Time** — fastest server
- **IP Hash** — client IP picks server (session persistence)

Round robin/random suit stateless apps and naturally absorb newly added servers. For persistent connections (SSE/WebSockets), **Least Connections** avoids one server accumulating all active connections.

#### Real-World Implementations

- **Hardware:** F5 Networks BIG-IP — can scale to hundreds of millions of requests/sec
- **Software:** HAProxy, NGINX, Envoy — more limited
- **Cloud:** AWS ELB/ALB/NLB, Google Cloud Load Balancing, Azure Load Balancer

Scaling load balancers is almost never in a SWE system design interview; if LB throughput gets large, mentioning hardware LBs is a good way out.

## Common Deep Dives and Challenges

### Regionalization and Latency

Global services distribute servers worldwide: multiple data centers per region ("availability zones" at AWS), replicated across cities. Physics matters: light in fiber travels ~2/3 the speed of light in vacuum (~200,000 km/s), so a New York–London round trip (~5,600 km) has a theoretical minimum of ~56 ms before any processing. Nearby server: <1 ms; NY→London: >80 ms in practice.

Answer: **data locality** — keep the data needed for a query (a) close together and (b) close to the user.

- **CDNs:** networks of edge servers in hundreds/thousands of cities. Works via *caching* — great for static or infrequently changing content (images, video, assets), and even cacheable dynamic data (e.g., caching Facebook post search results at the edge) to cut latency and backend load.
- **Regional partitioning:** partition data by region when it's naturally regional. Uber example: a Miami rider never books a New York driver. Bundle nearby cities into regions ("Northeast US"), each with its own co-located servers and databases — regional queries answered by regional services against local data. Fast and optimal.

### Handling Failures and Fault Modes

"The network is reliable" is one of the most dangerous fallacies in distributed systems. Design expecting network calls to fail, be delayed, or return unexpected results.

#### Timeouts and Retries with Backoff

Set timeouts; retry on failure — great for transient failures. But naive retries can make things worse. Use **exponential backoff**: wait, then wait longer on repeated failures, giving the system time to recover. Add **jitter** (randomness) so clients don't synchronize retries into a jackhammer. Interviewers often listen for the phrase **"retry with exponential backoff"**; senior interviews may probe jitter.

#### Idempotency

Retries are dangerous with side effects: retrying a $10 charge could charge $20 (or $2,000). Idempotent APIs produce the same result no matter how many times they're called. GETs are naturally idempotent. For writes, use an **idempotency key** — a unique request identifier; the server processes each key only once (friendly APIs return the completed result to all requesters; others return an "already exists" error). Either way, no double-charging.

#### Circuit Breakers

Guard against **cascading failures** (e.g., a cold database being pinned down by a firehose of retries — a "thundering herd" — so it can never boot back up). How they work:

1. Monitor failures when calling external services
2. When failures exceed a threshold, the circuit "trips" open
3. While open, requests fail immediately without attempting the call
4. After a timeout, the circuit goes "half-open"
5. A test request decides whether to close it or keep it open

Benefits: fail fast (no waiting for timeouts), reduce load on struggling services, self-healing, better UX (fast fallbacks vs hanging UI), overall system stability.

Where to apply: third-party API calls, database connections/queries, service-to-service calls in microservices, resource-intensive operations, any network call that could fail or slow down. Great answer when the interviewer deep-dives on reliability, failure modes, or disaster recovery.

## Wrapping Up

Focus areas:
1. **Basics:** IP addressing, DNS, TCP/IP model
2. **Protocols:** TCP vs UDP, HTTP/HTTPS, WebSockets, gRPC
3. **Load balancing:** client-side and dedicated (L4 vs L7)
4. **Practical realities:** regionalization and failure-handling patterns

Networking decisions affect latency, throughput, reliability, and security. Justify choices from the system's requirements — there's rarely one right answer; interviewers want to see tradeoff thinking. Hands-on follow-ups: capture traffic with Wireshark; simulate latency/packet loss with Mac's Network Link Conditioner.

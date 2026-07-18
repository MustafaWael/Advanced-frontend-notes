---
tags: [system-design, backend, networking, interview]
module: "30 - Backend System Design"
priority: must-know
status: not-started
aliases: [TCP UDP, gRPC, protocol choice]
---

# Networking and Protocols

## Maturity Target

- Priority: #must-know
- Study time: 40 minutes
- Interview signal: Choose a transport/protocol from the communication *shape* (request/response vs server-push vs bidirectional; public vs internal) and name what each choice costs at scale.
- Production signal: You reach for SSE or long-polling before WebSockets, and you know why gRPC is an internal-only default.
- Dependencies: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]

## Source Anchors

- [HelloInterview — Networking Essentials](https://www.hellointerview.com/learn/system-design/core-concepts/networking-essentials)
- [MDN — WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

## 1. Concept

Simple version: pick the cheapest protocol that matches how the two sides need to talk. Most of the time that's plain HTTP request/response.

The accurate layering, interview-relevant slice:

- **Transport — TCP vs UDP.** TCP: reliable, ordered, connection + handshake; the default for anything correctness-sensitive. UDP: fire-and-forget, no ordering or delivery guarantee, lower latency — video/voice, games, DNS. Choose UDP only when dropped packets are cheaper than waiting.
- **Application — over TCP:**
  - **HTTP/HTTPS** — request/response, stateless, cacheable. Handles ~90% of cases. Reach for it by default.
  - **REST** — resource-oriented HTTP; simple, cache-friendly, ubiquitous.
  - **GraphQL** — one endpoint, client selects fields; kills over/under-fetching, harder to cache at the HTTP layer.
  - **gRPC** — binary (protobuf) over HTTP/2; much faster than JSON for service-to-service. Browsers can't speak it natively (needs gRPC-Web + proxy), so the pattern is **REST/GraphQL externally, gRPC internally**.
  - **SSE (Server-Sent Events)** — server pushes down one long-lived HTTP response; unidirectional, auto-reconnect, works through standard HTTP infra. Live scores, notifications, token streaming.
  - **WebSockets** — full bidirectional channel; both sides send freely. Chat, collaborative editing, multiplayer.
  - **WebRTC** — peer-to-peer media/data, mostly bypassing your servers.

> [!warning] SSE and WebSockets are **stateful** connections. You can't put them behind a naive round-robin load balancer, and a server holding 50k live connections that dies drops them all at once (a reconnect stampede). Plan for sticky routing / a connection layer and for mass reconnection. This hidden cost is what makes "just use WebSockets" an incomplete answer.

**Load balancing:** L4 (transport, fast, opaque) vs L7 (application, can route on path/headers, terminate TLS). Regionalize to cut latency; design for node failure, not just happy path.

## 2. Why It Matters

"Make it real-time" is a trap: candidates jump to WebSockets and inherit stateful-connection complexity they don't need. The frontend mirror is identical — the transport table in [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]] is the same decision, viewed from the client. Getting protocol choice right is the difference between a design that scales and one that falls over on connection count.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: "Add live notifications to the app." The team ships WebSockets.

Trace of the cost: notifications are *server→client only* — the client almost never pushes back. WebSockets bought a bidirectional, stateful channel where a unidirectional one would do: now every app server is stateful, the load balancer needs sticky sessions, horizontal scaling means a pub/sub layer to fan a notification out to whichever server holds the user's socket, and a deploy drops every connection.

Fix: **SSE.** One long-lived HTTP response per client, server pushes notification events, the browser's `EventSource` auto-reconnects. It rides standard HTTP infrastructure and degrades gracefully. If later a feature genuinely needs client→server streaming (typing indicators), upgrade *that* feature to WebSockets.

Tradeoff: SSE is capped by HTTP/1.1 per-domain connection limits (mitigated under HTTP/2 multiplexing) and is text-only; WebSockets handle binary and true duplex. Match the protocol to the actual message directionality, not to the word "real-time."

## 4. Interview Answer

Short answer:

> Default to HTTP request/response. Add SSE when the server needs to push and the client mostly listens; use WebSockets only for genuinely bidirectional, high-frequency messaging like chat or collaboration. Internally, gRPC over HTTP/2 is the fast default for service-to-service; REST or GraphQL stays at the public edge because browsers don't speak gRPC natively.

Deeper answer:

> The decision axis is directionality and frequency, and the hidden cost is statefulness: SSE and WebSockets hold persistent connections, so they break the stateless-server assumption — you need sticky routing or a connection tier, a pub/sub backplane to fan messages to the right node, and a plan for a server dropping thousands of connections at once. That connection-count scaling problem, not the protocol syntax, is what senior answers focus on.

## 5. Practice

1. <details><summary>A prompt says "real-time price updates to millions of viewers, read-only." Which transport, and why not WebSockets?</summary>SSE (or even long-polling): the flow is unidirectional server→client, so a bidirectional stateful WebSocket adds cost with no benefit. At millions of viewers the real work is fan-out (pub/sub, edge) regardless; SSE keeps the per-connection cost and infra requirements lower.</details>
2. <details><summary>Why is gRPC great internally but rare on public APIs?</summary>Binary protobuf over HTTP/2 is compact and fast for service-to-service, but browsers can't call gRPC directly (need gRPC-Web + a translating proxy) and it's less debuggable/cacheable than REST. So: gRPC between your services, REST/GraphQL at the browser edge.</details>
3. <details><summary>What breaks when you put WebSockets behind a standard stateless load balancer?</summary>The connection is pinned to one server, but a stateless LB may route follow-up traffic elsewhere, and horizontal scaling means the server holding a user's socket isn't necessarily the one with their new message — you need sticky sessions plus a pub/sub backplane, and a reconnection strategy for when a node dies.</details>

## 6. Real-World Use Cases

Protocol choice is a frontend-facing decision; here it is as code you'd actually write.

### LLM token streaming over SSE (Next.js route handler)

A chat UI streams tokens as they generate — one-way server push over plain HTTP, which is exactly SSE's shape (no WebSocket needed).

```ts
// app/api/chat/route.ts
export async function POST(req: Request) {
  const stream = new ReadableStream({
    async start(controller) {
      for await (const token of generateTokens(await req.json())) {
        controller.enqueue(new TextEncoder().encode(`data: ${token}\n\n`)); // SSE frame
      }
      controller.close();
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}
```

Server pushes, client reads with `EventSource`, and it rides ordinary HTTP infra. See [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]].

### Collaborative presence over WebSockets

A Figma-style cursor/presence layer needs true client→server *and* server→client messages continuously — the case that justifies a stateful WebSocket over SSE.

```ts
const ws = new WebSocket("wss://api.example.com/room/42");
ws.onopen = () => ws.send(JSON.stringify({ type: "join", user }));
document.addEventListener("pointermove", (e) =>
  ws.send(JSON.stringify({ type: "cursor", x: e.clientX, y: e.clientY })));  // client→server
ws.onmessage = (e) => renderPeerCursor(JSON.parse(e.data));                   // server→client
```

Reserve WebSockets for genuinely bidirectional, high-frequency features — they cost a stateful connection per client. See [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]].

### REST at the edge, gRPC behind the BFF

Browsers can't speak gRPC natively, so the public edge stays REST while the BFF calls internal services over gRPC.

```ts
// Next.js route handler: REST in from the browser, gRPC out to services
export async function GET() {
  const user = await usersClient.getUser({ id });      // gRPC (typed protobuf) internally
  return Response.json(user);                          // REST/JSON to the browser
}
```

gRPC's efficiency and typing where you control both ends; REST where the client is a browser. See [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (API Gateway).

## Related Notes

- [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Real-time Updates)
- [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (API Gateway)

---
tags: [system-design, interview, real-time, websocket, sse]
module: "29 - Frontend System Design"
priority: important
status: not-started
aliases: [real-time UI, websocket design, live updates, presence]
verified_on: 2026-07-17
version_scope: "Web transport APIs (WebSocket, SSE + Last-Event-ID resume) as of 2026"
---

# Real-Time UI Patterns

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Choose a real-time transport from the message shape, and design the client concerns — ordering, reconnection, optimistic send, backpressure — that the transport doesn't solve.
- Production signal: Your live features reconnect gracefully, don't drop or reorder messages, and don't melt under a burst.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]

## Source Anchors

- [MDN — WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [MDN — Using server-sent events (Last-Event-ID / auto-reconnect)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [MDN — EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)

## 1. Concept

Simple version: pick the transport from *who sends and how often* (the table lives in [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]), then design the client concerns the transport leaves to you.

**Transport choice** (directionality + frequency):

- **Short polling** — client re-requests on an interval; simple, works everywhere; fine for low-frequency updates. Wasteful at high frequency (most requests return nothing) and latency is bounded by the interval.
- **Long polling** — the request hangs open until the server has data (or a timeout), then the client immediately re-requests. Near-real-time over plain HTTP with no persistent connection; the classic fallback before SSE/WS. Costs a held connection per client and awkward server plumbing.
- **SSE** — unidirectional server→client push over HTTP, **auto-reconnect with a built-in resume token** (see below); live scores, notifications, token streaming.
- **WebSockets** — bidirectional; chat, collaboration, multiplayer. Stateful and heavier; you build reconnect/resume yourself.

The ladder is short polling → long polling → SSE → WebSockets, trading simplicity for latency and bidirectionality.

**Client concerns the transport does NOT solve** (this is the design content):

- **Ordering** — messages can arrive out of order or duplicated; sequence numbers / server timestamps + client reordering, and idempotent apply by message id.
- **Reconnection** — connections drop; exponential backoff **with jitter** (so a mass reconnect after a server blip doesn't become a thundering herd), and on reconnect **catch up** (request messages since last-seen id) so you don't lose the gap. With **SSE this resume is native**: the browser sends the `Last-Event-ID` header on auto-reconnect carrying the `id:` of the last event it received, so the server can replay the gap — you get for free what you'd hand-build over WebSockets.
- **Optimistic send** — show the sent message immediately as "sending," reconcile to "sent" on ack, mark "failed" with retry on timeout ([[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|optimistic updates]]).
- **Backpressure / batching** — a burst (1000 messages/sec, presence spam) must not thrash rendering; coalesce, batch, throttle UI updates, and update a normalized store rather than re-rendering everything.
- **Presence & dedup** — join/leave events, "typing…", last-write-wins per key.

> [!tip] The framing that matters: the transport is the easy 20%. The design is the client state machine — connecting/open/reconnecting/offline — plus ordering, catch-up on reconnect, and burst handling. Interviewers who say "design a real-time X" are testing those, not whether you can name WebSocket.

## 2. Why It Matters

Real-time is a whole category of design questions (chat, live comments, collaborative editing, dashboards, multiplayer). The common failure is stopping at "use WebSockets" and ignoring reconnection, ordering, and backpressure — exactly the parts that make real-time hard in production. It also ties to backend: the client transport is Hop 1 of the [[30 - Backend System Design/10 - The Seven Access Patterns|Real-time Updates pattern]].

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a live comments feature works in the demo but in production comments sometimes appear out of order, duplicate after the user's train goes through a tunnel, and the tab freezes during a viral spike.

Trace: three missing client concerns. Out of order — no sequencing, messages rendered in arrival order. Duplicates after reconnect — the socket reconnected and the server replayed, with no idempotent apply. Freeze under spike — every message triggered a render; a burst = a render storm.

Fix: attach a monotonic `seq`/`id` per message; apply into a normalized store keyed by id (idempotent — duplicates no-op) and render sorted by `seq`. On reconnect, send `lastSeenId` and request the gap (catch-up), with exponential backoff. Under load, **batch** incoming messages per animation frame and update state once, not per message.

Tradeoff: sequencing + catch-up need server cooperation (ids, a "since" endpoint) and a reconnect protocol; batching adds a few ms of latency to smooth bursts. You're trading simplicity for the correctness and stability that make real-time usable — and if the feature is low-frequency, some of this is over-engineering worth cutting explicitly.

## 4. Interview Answer

Short answer:

> I choose the transport by directionality and frequency — polling for low-frequency, SSE for server-push, WebSockets for bidirectional. Then I design what the transport doesn't give me: message ordering via sequence ids applied idempotently into a normalized store, reconnection with backoff plus catch-up from the last-seen id, optimistic send with ack reconciliation, and backpressure by batching UI updates so a burst doesn't cause a render storm.

Deeper answer:

> The transport is the easy part; the design is a connection state machine plus three guarantees. Ordering and dedup: messages carry monotonic ids, I apply by id into a keyed store so duplicates are no-ops and I render sorted, which also survives reconnect replays. Reconnection: exponential backoff and, critically, catch-up — on reopen I ask for everything since my last-seen id so the offline gap is filled instead of lost. Backpressure: I coalesce a burst into one batched state update per frame. I'd scope this to frequency — a low-rate notification stream doesn't need batching — but for chat or collaboration all three are load-bearing.

## 5. Practice

1. <details><summary>Why isn't "use WebSockets" a sufficient answer to "design live comments"?</summary>The transport doesn't handle ordering, deduplication, reconnection/catch-up, optimistic send, or backpressure — the parts that actually break in production (out-of-order rendering, duplicate replays after a drop, render storms under load). The design is those client concerns; the socket is just the pipe.</details>
2. <details><summary>How do you keep messages correct across a reconnect?</summary>Give each message a monotonic id; apply idempotently into a store keyed by id so replays are no-ops; and on reconnect send your last-seen id and request the gap (catch-up) so nothing that arrived while you were offline is lost. Backoff on retries so a flapping connection doesn't hammer the server.</details>
3. <details><summary>A viral spike freezes the tab. What's the design fix?</summary>Backpressure: stop rendering per message. Buffer incoming messages and flush a single batched state update per animation frame (or on a throttle), update a normalized store once, and let virtualization keep the DOM small. The freeze is a render storm; batching collapses N renders into one.</details>

## 6. Real-World Use Cases

### SSE live updates with native resume

For one-way pushes (live scores, notifications), `EventSource` reconnects automatically and, if the server sends `id:` on each event, replays the gap via the `Last-Event-ID` header — resume you don't hand-build.

```ts
const es = new EventSource("/api/scores");
es.onmessage = (e) => {
  const evt = JSON.parse(e.data);
  applyUpdate(evt);   // browser tracks e.lastEventId; on reconnect it sends Last-Event-ID
};
// server sets each frame's `id:` so a reconnect resumes after the last seen event
```

The native resume token is the primitive to name instead of reinventing catch-up. See [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]].

### Reconnect with exponential backoff + jitter

A dropped WebSocket must reconnect, but a synchronized retry after a server blip is a thundering herd. Back off exponentially and add jitter so clients spread out.

```ts
function reconnectDelay(attempt: number) {
  const base = Math.min(1000 * 2 ** attempt, 30_000);  // cap at 30s
  return base / 2 + Math.random() * (base / 2);        // ±50% jitter
}
// attempt 0 → ~0.5–1s, attempt 3 → ~4–8s, capped — clients don't stampede together
```

Jitter is the difference between a graceful recovery and a self-inflicted DDoS. See [[29 - Frontend System Design/19 - Designing a Chat and Messaging App|Designing a Chat and Messaging App]].

### Backpressure — batch a burst per animation frame

A viral spike delivers hundreds of messages/second; rendering per message freezes the tab. Buffer arrivals and flush one state update per frame.

```ts
let buffer: Message[] = [];
let scheduled = false;
function onMessage(msg: Message) {
  buffer.push(msg);
  if (!scheduled) {
    scheduled = true;
    requestAnimationFrame(() => { mergeIntoStore(buffer); buffer = []; scheduled = false; });
  }
}
```

N renders collapse into one per frame — the render-storm fix. See [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]].

## Related Notes

- [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]
- [[29 - Frontend System Design/19 - Designing a Chat and Messaging App|Designing a Chat and Messaging App]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]
- [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]

---
tags: [javascript, network, realtime, websockets]
module: "20 - Network and Security"
priority: important
status: not-started
aliases: [WebSockets, SSE, Server-Sent Events]
---

# WebSockets, SSE, and Polling

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: you can pick a realtime strategy from requirements (direction, frequency, infra) and defend it, and explain reconnection/backpressure concerns.
- Production signal: your realtime feature handles reconnects, missed messages, and cleanup instead of assuming a perfect connection.
- Dependencies: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]

## Source Anchors

- [MDN - WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [MDN - Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [MDN - EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [web.dev - Realtime with WebSockets/SSE](https://web.dev/articles/websockets-vs-sse)

## 1. The Four Strategies

| Strategy | Direction | Transport | Reconnect | Best for |
| --- | --- | --- | --- | --- |
| Short polling | client pulls on a timer | plain HTTP | trivial | low-frequency, "good enough" freshness (dashboard every 30s) |
| Long polling | server holds request until data | plain HTTP | trivial | near-realtime fallback where WS is blocked |
| **SSE** (EventSource) | **server → client only** | HTTP (one long response stream) | **built-in, automatic** | feeds, notifications, live prices, LLM token streams |
| **WebSocket** | **full duplex** | ws/wss (upgraded from HTTP) | **manual — you build it** | chat, collaborative editing, games, anything bidirectional/high-frequency |

The decision axes: **direction** (one-way → SSE beats WS on simplicity; two-way → WS), **frequency** (seconds → polling; sub-second/push → SSE/WS), and **infra reality** (WS needs stateful connection handling, sticky routing, and proxy/load-balancer support; SSE and polling are ordinary HTTP and pass through most infrastructure and HTTP caching layers unmodified).

## 2. SSE — Underrated Default for One-Way

```js
const es = new EventSource("/api/notifications", { withCredentials: true });
es.onmessage = (e) => addNotification(JSON.parse(e.data));
es.addEventListener("price", (e) => updatePrice(JSON.parse(e.data))); // named events
es.onerror = () => {/* browser auto-reconnects; readyState shows CONNECTING */};
// cleanup:
es.close();
```

Why SSE is often the right call and under-chosen:

- **Automatic reconnection** with `Last-Event-ID` resume — the browser resends the last id header so the server can replay missed events. This is the single biggest reason to prefer it over hand-rolled WS for feeds.
- Plain HTTP: works with HTTP/2 multiplexing, existing auth cookies, proxies, and load balancers — no special ops.
- Text-only, UTF-8, one-directional. If you need to send data up, you still just do a normal `fetch` — most "realtime" apps are read-heavy, so this asymmetry is fine.
- Historic caveat (HTTP/1.1 6-connection limit made many SSE tabs starve the origin); under HTTP/2+ this largely dissolves.

> [!tip] LLM/streaming UIs are usually SSE
> Token-by-token AI responses, live logs, and progress streams are server→client only — SSE (or a raw `fetch` body stream, [[19 - DOM and Browser APIs/07 - fetch Deep Dive|reader loop]]) fits better than a WebSocket, with free reconnection. Reach for WS only when the client must also stream *up* continuously.

## 3. WebSocket — Power and Its Costs

```js
const ws = new WebSocket("wss://api.acme.com/chat");
ws.onopen = () => ws.send(JSON.stringify({ type: "join", room }));
ws.onmessage = (e) => dispatch(JSON.parse(e.data));
ws.onclose = (e) => scheduleReconnect(e.code); // YOU own reconnection
ws.onerror = () => {/* usually followed by close */};
```

What WS gives: true full-duplex, low per-message overhead (no HTTP headers per frame), binary support (ArrayBuffer/Blob — [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays]]), sub-protocols. What it *costs you* — the parts tutorials skip:

- **Reconnection is entirely yours**: exponential backoff with jitter, resubscribe to rooms on reconnect, and dedupe/replay missed messages (server needs message ids + a buffer; the client requests "since id N"). Without this, a 2-second network blip loses messages silently.
- **Heartbeats**: idle connections get killed by proxies/load balancers (~30–60s); app-level ping/pong keeps them alive and detects half-open sockets (`onclose` doesn't always fire).
- **Backpressure**: `ws.bufferedAmount` grows if you send faster than the socket drains — a fast producer with a slow client leaks memory; you must throttle/coalesce.
- **Auth**: the WS handshake can't set custom headers from the browser — auth rides on cookies (so it inherits [[20 - Network and Security/06 - CSRF and CSP|CSRF/origin]] concerns; validate `Origin` server-side) or a token in the URL/first message.
- **State**: sticky sessions or a shared pub/sub (Redis) so any server can reach any client — the reason managed services (Pusher, Ably, Supabase Realtime, socket.io infra) exist.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: notification bell "goes quiet" for some users after a while.

Buggy version — naive WebSocket:

```js
const ws = new WebSocket("wss://api.acme.com/notifications");
ws.onmessage = (e) => showBell(JSON.parse(e.data));
// no onclose handler, no heartbeat, no cleanup
```

Traced failures: a proxy silently closes the idle socket after 60s; `onclose` may not fire on a half-open connection → the client *thinks* it's connected and simply never receives anything again ("quiet"); on route change the socket leaks ([[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]); any messages sent while disconnected are gone forever.

Production-safe fix — pick SSE (one-way feed) and lean on the platform:

```jsx
function useNotifications(onNotify) {
  useEffect(() => {
    const es = new EventSource("/api/notifications", { withCredentials: true });
    es.addEventListener("notification", (e) => onNotify(JSON.parse(e.data)));
    // Browser auto-reconnects and sends Last-Event-ID so the server can replay misses.
    return () => es.close();   // cleanup: no leak
  }, [onNotify]);
}
```

If it *had* to be WebSocket (bidirectional), the fix is a reconnecting wrapper: backoff+jitter reconnect, ping/pong heartbeat, resubscribe on open, and a `lastSeenId` sent on reconnect so the server replays. That's ~100 lines you shouldn't hand-roll — adopt a library.

Tradeoffs: SSE can't push client→server, so actions still go over `fetch` (fine for a bell). WS wins for genuinely interactive/high-frequency two-way features but you buy the entire reliability layer. Polling remains the pragmatic choice when "realtime" really means "within 30 seconds" — no persistent connections, trivially cacheable, survives any infra, and cheapest to operate; don't reach for sockets when a timer will do.

## 5. Interview Answer

Short answer:

> Match transport to direction and frequency. Polling for low-frequency freshness. SSE for server→client streams — feeds, notifications, LLM tokens — because it's plain HTTP with automatic reconnection and Last-Event-ID replay. WebSockets for full-duplex, high-frequency, interactive features like chat or collaboration, accepting that you must build reconnection, heartbeats, and backpressure handling yourself.

Deeper answer:

> SSE's automatic reconnect and HTTP-native transport make it the underrated default for one-way data; most "realtime" needs are read-heavy, and the client can still POST for the rare write. WebSockets add real cost: manual exponential-backoff reconnection, app-level heartbeats to survive proxy idle timeouts and detect half-open sockets, `bufferedAmount` backpressure control, cookie/origin-based auth since the handshake can't set headers, and sticky sessions or shared pub/sub for horizontal scale. Those costs are why managed realtime services exist.

## 6. Practice

1. <details><summary>Live sports scores, server→client only, must survive flaky mobile networks. Choose and justify against WebSocket.</summary>SSE. It's server→client (matches), and its built-in reconnection with Last-Event-ID lets the server replay scores missed during a tunnel/handoff — exactly the flaky-network requirement — for free. A WebSocket would force you to hand-build reconnect + replay to match, with no upside since there's no client→server stream. Polling is a viable simpler fallback if ~10s staleness is acceptable.</details>

2. <details><summary>A WebSocket app "randomly stops updating" but never shows an error. Most likely cause and detection?</summary>A half-open connection: an intermediary dropped the socket without a clean close frame, so the client's `onclose`/`onerror` never fired and `readyState` still reads OPEN — it waits forever for data. Detection: app-level heartbeat (send ping every ~30s, expect pong within a timeout); if the pong doesn't arrive, treat the socket as dead, close it, and reconnect. Proxy idle timeouts are the usual trigger, which is also why heartbeats keep the connection alive.</details>

3. <details><summary>Why can't the browser WebSocket API attach an `Authorization: Bearer` header, and what are the options?</summary>The `WebSocket` constructor exposes no header API (only URL + subprotocols), so the upgrade request can't carry a custom Authorization header. Options: rely on the auth *cookie* sent with the handshake (then validate `Origin` server-side for CSRF, since it's ambient credential); pass a short-lived token as a query param (beware URL logging) or in the subprotocol field; or authenticate in the first message after `onopen` before subscribing. Cookie + origin check is common; query-token needs the token to be single-use/short-lived.</details>

4. <details><summary>`ws.send()` in a tight loop for a live-cursor feature; memory climbs and messages arrive late. Diagnose.</summary>Backpressure: you're enqueuing faster than the socket drains to the network, so frames pile in the send buffer — `ws.bufferedAmount` keeps rising (memory) and delivery lags. Fix: throttle/coalesce (send cursor position at most once per animation frame, only the latest), and gate sends on `bufferedAmount` staying below a threshold, dropping or merging intermediate updates. Live-cursor data is latest-wins, so coalescing is lossless in effect.</details>

## Related Notes

- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[30 - Backend System Design/02 - Networking and Protocols|Networking and Protocols]] — the same transport table from the server side
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] — Real-time Updates and its fan-out hop
- [[01 - Roadmap|Roadmap]]

---
tags: [networking, http, performance]
module: "26 - How the Web Works"
priority: important
status: not-started
aliases: [TCP TLS QUIC, HTTP versions]
---

# Connection Layer

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Explain what TCP, TLS, and QUIC each do, what HTTP/2 and HTTP/3 actually changed, and derive the frontend consequences (bundling, domain sharding, waterfalls) from the mechanics.
- Production signal: You can read a connection waterfall in DevTools, know when `preconnect` pays off, and stop cargo-culting HTTP/1.1-era optimizations.
- Dependencies: [[26 - How the Web Works/02 - DNS and Domains|DNS and Domains]], [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]

## Source Anchors

- [MDN - Evolution of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Evolution_of_HTTP)
- [web.dev - HTTP/2](https://web.dev/articles/performance-http2)
- [Cloudflare - What is HTTP/3?](https://www.cloudflare.com/learning/performance/what-is-http3/)

## 1. Concept

Simple version: before any HTTP request can be sent, the browser must establish a connection — agree to talk (TCP), agree to talk *secretly* (TLS), and only then talk (HTTP). Each agreement costs round trips, and round trips are the currency of web latency.

The accurate mechanism:

- **TCP** gives reliable, ordered byte delivery via a 3-way handshake (SYN → SYN-ACK → ACK): 1 round trip before data flows.
- **TLS** negotiates encryption keys on top: ~1 more round trip on TLS 1.3 (2 on 1.2). So a cold HTTPS connection costs roughly DNS + 2–3 RTTs before the first HTTP byte.
- **QUIC** replaces TCP+TLS with a single protocol over UDP: handshake and encryption merge into 1 RTT (0-RTT for resumed connections).

What each HTTP version changed, and *why*:

- **HTTP/1.1** — one request at a time per connection (responses must come back in order). Browsers work around this with ~6 parallel connections per origin. This era's optimizations: bundling everything into one file, sprite sheets, domain sharding — all tricks to fit more into few sequential pipes.
- **HTTP/2** — **multiplexing**: many streams interleaved on *one* TCP connection, plus header compression (HPACK) and stream prioritization. Bundling into one giant file and domain sharding become anti-patterns — sharding actively hurts because it forfeits the shared connection. But one problem remains: **TCP head-of-line blocking**. TCP guarantees ordered delivery of the whole byte stream, so one lost packet stalls *every* multiplexed stream behind it.
- **HTTP/3 (QUIC)** — moves multiplexing into the transport. Streams are independent at the UDP level: a lost packet stalls only its own stream. Plus faster handshakes and **connection migration** (switch Wi-Fi → cellular without reconnecting — QUIC connections are identified by ID, not by IP/port 4-tuple).

```text
HTTP/1.1: [conn1: A──────][conn2: B──────]   6 pipes, 1 response each at a time
HTTP/2:   [conn: A₁B₁A₂B₂A₃B₃…]              1 pipe, interleaved — but TCP loss stalls all
HTTP/3:   [conn: A₁B₁A₂✗B₂B₃…]               1 pipe, loss in A stalls only A
```

## 2. Why It Matters

- "HTTP/1.1 vs 2 vs 3" is a standard mid/senior networking question, and the senior answer derives *frontend strategy* from the mechanics rather than reciting features.
- Code-splitting granularity depends on this: under HTTP/2+, many small files are cheap, so fine-grained splitting + immutable caching beats one mega-bundle ([[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]).
- Connection setup cost explains `preconnect`, and why consolidating third-party origins matters more than minifying another 3KB.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a team "optimizes" their HTTP/2 site using a 2012-era checklist: they shard assets across `static1.example.com` … `static4.example.com` and inline all critical assets into one 800KB bundle.

Trace: sharding forces 4 separate DNS lookups + TCP + TLS handshakes and defeats HTTP/2's single multiplexed connection — priority information is also fragmented across connections. The mega-bundle means any one-line change invalidates the entire cached 800KB ([[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]).

```text
Fix:
- Serve all first-party assets from ONE origin → one warm connection, coherent priorities.
- Split the bundle by route/vendor → small immutable chunks, content-hashed filenames.
- preconnect only to unavoidable third-party origins.
```

Tradeoffs: many small chunks add scheduler overhead and can hurt compression ratio (bigger files compress better); extreme splitting creates request cascades of `import()` waterfalls. Measure — the optimum is per-app, but the *default* under HTTP/2+ is consolidation of origins and moderate splitting of bundles.

> [!warning] Footgun: HTTP/3 negotiation happens via the `Alt-Svc` header or DNS HTTPS records — the *first* visit often rides HTTP/2 and upgrades later. Don't be confused when DevTools shows mixed `h2`/`h3` in the Protocol column.

## 4. Interview Answer

Short answer:

> HTTP/1.1 allows one in-flight response per connection, so browsers opened six and we bundled everything. HTTP/2 multiplexes many streams over one TCP connection with header compression — which made bundling-everything and domain sharding obsolete — but TCP's ordered delivery means one lost packet stalls all streams. HTTP/3 runs over QUIC on UDP, making streams independent, merging the TCP+TLS handshake into one round trip, and surviving network switches via connection IDs.

Deeper answer:

> The frontend consequences are the senior part: under H2/H3, consolidate origins (each extra origin costs DNS+TCP+TLS and splits prioritization), split bundles into cacheable chunks instead of one blob, and use preconnect for unavoidable third parties. Know that head-of-line blocking exists at two levels — HTTP-level (fixed by H2) and TCP-level (fixed only by H3) — and that QUIC's 0-RTT resumption trades a replay-attack surface for latency, so it's limited to idempotent requests.

## 5. Practice

1. <details><summary>Why did HTTP/2 make domain sharding an anti-pattern?</summary>Sharding existed to get more parallel HTTP/1.1 connections. H2 already multiplexes unlimited streams on one connection — sharding adds handshake costs, splits priority scheduling across connections, and reduces congestion-window efficiency.</details>
2. <details><summary>HTTP/2 multiplexes streams, so why does packet loss still stall unrelated resources?</summary>Because multiplexing happens above TCP, and TCP presents a single ordered byte stream — a lost packet blocks delivery of all bytes after it until retransmission, regardless of which H2 stream they belong to. That's TCP head-of-line blocking; H3/QUIC fixes it with transport-level stream independence.</details>
3. <details><summary>A user rides a train and your SPA's requests keep dying on network switches. Which protocol feature helps and why?</summary>QUIC connection migration: connections are identified by a connection ID rather than the IP/port 4-tuple, so moving from Wi-Fi to cellular keeps the connection alive instead of forcing re-handshake and request failure.</details>

## Related Notes

- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]

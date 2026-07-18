# Real-time Updates

**Source:** https://www.hellointerview.com/learn/system-design/patterns/realtime-updates

> Note: This page is premium-locked. Everything below is the free/visible content captured on 2026-07-17. Locked sections are listed at the bottom.

## What This Pattern Is

**Real-time Updates** addresses the challenge of delivering immediate notifications and data changes from servers to clients as events occur. From chat applications where messages need instant delivery to live dashboards showing real-time metrics, users expect to be notified the moment something happens. The pattern covers architectural approaches to enable low-latency, bidirectional communication.

## The Problem

Consider a collaborative document editor like Google Docs. When one user types a character, all other users viewing the document need to see that change within milliseconds. You can't have every user constantly polling the server for updates every few milliseconds without crushing your infrastructure.

The core challenge is establishing efficient, persistent communication channels between clients and servers. Standard HTTP follows a request-response model: clients ask for data, servers respond, then the connection closes. This works great for traditional web browsing but breaks down when you need servers to **proactively push** updates to clients.

The article notes that these problems are often solved once by a specialized infrastructure team, so many experienced candidates have never built this layer themselves — which is exactly why interviewers probe it.

## The Solution: Two "Hops"

When systems require real-time updates or push notifications, the solution has two distinct pieces, each with its own trade-offs:

1. **The first hop:** how do we get updates from the server to the client? (client–server connection protocols)
2. **The second hop:** how do we get updates from the source to the server? (server-side push/pull)

### Hop 1: Client-Server Connection Protocols

Traditional HTTP request-response works for a startling number of use-cases, but real-time systems frequently need persistent connections or clever polling strategies so servers can **push** updates to clients. The page frames this as fundamentally a networking problem.

#### Networking 101 (free content)

Networks are built on a layered architecture (the OSI model), where each layer builds on the **abstractions** of the one below it. Three layers matter most in system design interviews:

- **Network Layer (Layer 3) — IP:** handles routing and addressing. Breaks data into packets, forwards packets between networks, and provides best-effort delivery to any destination IP. No guarantees: packets can be lost, duplicated, or reordered.
- **Transport Layer (Layer 4) — TCP and UDP:**
  - **TCP** is **connection-oriented**: you establish a connection before sending data, and it guarantees correct, in-order delivery. The cost: connections take time to establish, resources to maintain, and bandwidth to use.
  - **UDP** is **connectionless**: send to any IP without setup, with no delivery or ordering guarantees. "Spray and pray."
- **Application Layer (Layer 7):** protocols like DNS, HTTP, WebSockets, WebRTC that build on TCP (or UDP) to provide abstractions for web-application data.

**Request lifecycle:** typing a URL triggers DNS resolution (human-readable domain like hellointerview.com → IP address like 32.42.52.62), then a TCP connection, then the HTTP request/response. (The page includes a "Simple HTTP Request" diagram walking through the layers.)

#### Protocol options covered (section headings — details premium-locked)

The page compares five client-server options; the heading labels themselves telegraph the verdicts:

- **Simple Polling: The Baseline**
- **Long Polling: The Easy Solution**
- **Server-Sent Events (SSE): The Efficient One-Way Street** — a footnote notes Hello Interview itself uses SSE extensively, with many networking edge cases in practice
- **WebSockets: The Full-Duplex Champion**
- **WebRTC: The Peer-to-Peer Solution**
- **Overview** (comparison)

### Hop 2: Server-Side Push/Pull (headings — details premium-locked)

- **Pulling with Simple Polling**
- **Pushing via Consistent Hashes**
- **Pushing via Pub/Sub**

## Interview Problems Using This Pattern

The page links this pattern to these Hello Interview problem breakdowns:

- Ticketmaster
- Uber
- WhatsApp
- Robinhood
- Google Docs
- Strava
- Online Auction
- FB Live Comments
- Online Chess
- ChatGPT

## Locked Sections (premium-only, not captured)

The following sections exist on the page but their content is behind the paywall:

- Simple Polling: The Baseline (details)
- Long Polling: The Easy Solution (details)
- Server-Sent Events (SSE): The Efficient One-Way Street (details)
- Websockets: The Full-Duplex Champion (details)
- WebRTC: The Peer-to-Peer Solution (details)
- Protocol Overview/comparison
- Server-Side Push/Pull: Pulling with Simple Polling, Pushing via Consistent Hashes, Pushing via Pub/Sub (details)
- When to Use in Interviews / Common Interview Scenarios / When NOT to Use
- Common Deep Dives:
  - "How do you handle connection failures and reconnection?"
  - "What happens when a single user has millions of followers who all need the same update?"
  - "How do you maintain message ordering across distributed servers?"
- Conclusion

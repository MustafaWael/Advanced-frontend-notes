# 05 - Design a Messaging App Like WhatsApp

**Source:** [hellointerview.com/learn/system-design/problem-breakdowns/whatsapp](https://www.hellointerview.com/learn/system-design/problem-breakdowns/whatsapp)
**Difficulty:** Medium · **Pattern:** Real-time Updates · **Author:** Stefan Mai

## Understanding the Problem

WhatsApp is a messaging service that allows users to send and receive encrypted messages and calls from phones and computers. Famously built on Erlang and renowned for handling high scale with limited engineering/infrastructure outlay.

## Functional Requirements

Chat apps have tons of features — don't try to cover them all; confirm scope with the interviewer and don't dawdle in requirements.

**Core:**
1. Users should be able to start group chats with multiple participants (**limit 100**).
2. Users should be able to send/receive messages.
3. Users should be able to receive messages sent while they are offline (**up to 30 days**).
4. Users should be able to send/receive media in their messages.

**Below the line (out of scope):**
- Audio/video calling.
- Interactions with businesses.
- Registration and profile management.

## Non-Functional Requirements

Worth asking how the app is used (mostly 1:1? large groups? message frequency?) — usage dictates later design decisions.

**Core:**
1. Messages delivered to available users with **low latency, < 500ms**.
2. **Guaranteed deliverability** — messages must make their way to users.
3. Handle **billions of users** with high throughput.
4. Messages stored on centralized servers **no longer than necessary**.
5. Resilient against failures of individual components.

**Below the line:** exhaustive security treatment; spam/scraping prevention.

> Listing out-of-scope items is a nice-to-have showing product thinking, but don't burn time on it.

## Planning the Approach

- 1:1 messages are just a special case of group chats (2 participants) — solve the general case.
- Two halves of the problem: **durably delivering** messages, and doing so **in realtime**.
- Start with the simplest working design (single node), then scale/optimize in deep dives.

## Core Entities

- **Users**
- **Chats** (2–100 users)
- **Messages**
- **Clients** (a user might have multiple devices)

> Entities aren't graded directly, but getting them wrong builds on a broken foundation.

## API / System Interface

High-frequency bidirectional updates → not REST but a **bi-directional socket**: **WebSockets over TLS** (a custom protocol over raw TLS TCP would also work). The API is the set of commands sent/received over the connection.

Client → server commands:
```
// -> createChat
{ "participants": [], "name": "" } -> { "chatId": "" }

// -> sendMessage
{ "chatId": "", "message": "", "attachments": [] }
  -> { "status": "SUCCESS" | "FAILURE", "messageId": "" }

// -> createAttachment
{ "body": ..., "hash": } -> { "attachmentId": "" }   // amended later (presigned URLs)

// -> modifyChatParticipants
{ "chatId": "", "userId": "", "operation": "ADD" | "REMOVE" } -> "SUCCESS" | "FAILURE"
```

Server → client commands (each **ACKed** by the client — crucial so we know delivery happened all the way to the client and don't lose messages):
```
// <- chatUpdate
{ "chatId": "", "participants": [] } -> "RECEIVED"

// <- newMessage
{ "chatId": "", "userId": "", "message": "", "attachments": [] } -> "RECEIVED"
```

> In the interview you can shortcut by listing just command names; "I'll come back to this as I learn more" is fine.

## High-Level Design

### 1) Start group chats (limit 100)

- Chat service behind an **L4 load balancer** (WebSockets). L7 LBs support WebSockets, but we need no L7 capabilities (path/header routing, per-request spreading) — L4 is sufficient and generally faster.
- **DynamoDB** for chat metadata.

Flow: user connects, sends `createChat` → service writes a **Chat** record + a **ChatParticipant** record per user (single DynamoDB transaction for small chats, up to 100 items; batch writes near the limit) → returns `chatId`.

Tables:
- **Chat**: simple primary key on chat id.
- **ChatParticipant**: partition key `chatId`, sort key `participantId` (→ all participants of a chat). **GSI**: partition key `participantId`, sort key `chatId` (→ all chats for a user); kept in sync automatically by DynamoDB.

### 2) Send/receive messages

Start with a **single Chat Server host** (say so explicitly — terrible for scale, great starting point).

> For infra-style interviews, reason on a single node first; the path to scale is usually straightforward from there, and solving scale first can back you into a corner.

- In-memory hash map: `userId → websocket connection`.
- Send flow: sender sends `sendMessage` → server looks up participants via ChatParticipant → looks up each participant's socket in the hash map → sends the message on each connection.
- Strong assumptions for now: everyone online, all on the same server.

### 3) Receive messages sent while offline (up to 30 days)

Keep an **Inbox** per user with all *undelivered* messages.

Throughput check: mostly 1:1 chats, ~20 messages/user/day, 200M active users → 4B messages/day ≈ **40K messages/sec**; with Inbox writes and group chats ≈ **100K writes/sec** — well within DynamoDB's capability with `userId` partition key.

Send flow becomes:
1. Sender sends `sendMessage`.
2. Server looks up participants.
3. Server writes the message to the **Message table** and creates an **Inbox** entry per recipient (durable first).
4. Server returns SUCCESS/FAILURE + messageId to the sender.
5. Server attempts realtime delivery via `newMessage` to connected participants.
6. Connected clients **ACK**; the server then deletes the Inbox entry.

When an offline client reconnects: read its Inbox → fetch each message from the Message table → deliver via `newMessage` → client ACKs → delete from Inbox.

Cleanup: **TTL** on Inbox and Message table items (≤ 30 days).

### 4) Send/receive media

Media is bandwidth- and storage-intensive; use purpose-built tech (real WhatsApp uploads attachments via a separate HTTP service).

**Bad: attachments in the DB** — accept media over the WebSocket, store in DynamoDB. DBs aren't optimized for large blobs, and it cripples Chat Server bandwidth with dumb storage work.

**Good: via chat server to blob storage** — Chat Server accepts media, pushes to blob storage with a 30-day TTL; recipients fetch directly via presigned URLs. *Challenge:* the Chat Server still ferries the bytes (wasted step); expiry-after-all-downloads unhandled.

**Great: manage attachments separately with presigned URLs** ✅
- Client sends `getAttachmentTarget` → gets a **presigned upload URL** → uploads **directly to blob storage** → sends the resulting opaque URL in the message.
- Recipients download directly from blob storage via presigned URLs.
- CDN in front is possible but of limited benefit with ≤100 participants per chat.
- *Remaining challenges:* expiring media after all recipients downloaded; extra steps for encryption/security.

## Deep Dives

> The degree of proactivity expected here scales with seniority: all levels should immediately flag that the single-host design won't scale; mid-level interviews may be interviewer-driven beyond that, while senior/staff candidates should proactively look around corners.

### 1) How can we handle billions of simultaneous users?

1B users → ~200M concurrently connected. WhatsApp famously served 1–2M users per host, so hundreds of chat servers. New problem: sender and recipient may be on **different hosts** — a message routing problem.

**Bad: naive horizontal scaling** — LB + more hosts. Broken: the receiving server may not hold the recipient's connection; messages can't be delivered. Don't be tempted!

**Bad: Kafka topic per user** — keep the Inbox as a per-user Kafka topic that chat servers subscribe to. Kafka isn't built for billions of topics (~50KB overhead each → 50TB+ for 1B users). "Super topic" workarounds just reinvent the better solutions below.

**Good: consistent hashing of chat servers** — assign users to a chat server by user ID via consistent hashing; keep a central registry of servers and hash-space ownership in **ZooKeeper/Etcd**. Servers call each other directly to deliver.
- *Challenges:* full mesh of server-to-server connections (want big servers, few in number); scaling in/out needs careful connection-draining orchestration (avoid thundering herds, double-send during transitions). Workable if you're prepared to discuss these — rated Good, not Great, because of the problems it creates.

**Great: offload to Pub/Sub (Redis Pub/Sub)** ✅
- Purpose-built message bouncing: lightweight hashmap of socket connections; per-user channels; "at most once" delivery.
- Unlike Kafka, Pub/Sub does **no storage** — channels are in-memory pointers to subscribers, essentially free. Shard channels by user ID across a Redis cluster.
- On connect: chat server subscribes to the Pub/Sub topic for that user ID; forwards received messages to the socket.
- On send: publish to the recipient's topic; subscribing servers forward to the socket.
- At-most-once is acceptable **because durability comes first**: (1) write Message + Inbox entries (durable), (2) return success, (3) publish to Pub/Sub (best-effort). A dropped publish is recovered via Inbox sync on reconnect or periodic polling.
- Scalability is proven (Canva: 100K msgs/sec on one Redis host at 27% utilization — pub/sub is dumb and efficient).
- *Challenges:* small extra latency (single-digit ms) via Redis; connections from every chat server to every Redis node (fine — few nodes needed).

**Partition channels by chat or by user?**
- Scenario A — 250 1:1 chats per user: by-chat = 250 subscriptions per connected user; by-user = 1 subscription, 1 publish per message → **partition by user** wins.
- Scenario B — one 100-person chat per user: by-chat = 1 subscription, 1 publish; by-user = 99 publishes per message → **by chat** wins.
- WhatsApp is dominated by 1:1 chats → **partition by user**.
- Senior extension ("celebrity problem" for large chats): **adaptive partitioning** — for chats above a threshold (e.g. 25 users), clients' servers also subscribe to chat-level channels and messages publish to the chat channel instead. Edge cases: allow subscribe time when a chat crosses the threshold; may publish to both channels briefly.

### 2) Multiple clients/devices per user

Phone + tablet + laptop must all sync; the per-user Inbox no longer suffices.

Changes:
- New **Clients table** keyed by user id.
- Looking up chat participants → also look up all clients per user.
- **Inbox becomes per-client** rather than per-user.
- Send messages to all of a user's clients.
- Pub/Sub unchanged (still subscribe by userId).
- Introduce limits (e.g. **3 clients per account**) to cap storage/throughput.
- Also need a way to deactivate stale clients so we don't store messages for dead devices.

### 3) What happens if the WebSocket connection fails?

Poor networks leave sockets "open" but functionally dead; TCP keepalives take minutes.

**Bad: rely on TCP timeouts** — users stare at a "connected" app that's dead, missing messages. Unacceptable.

**Good: ACK timeouts + server-side retry** — on delivery, wait for client ACK (500–2000ms); retry a few times, then close the socket, forcing reconnect + Inbox sync. Pairs with the existing ACK mechanism. *Limit:* only detects failures when actively sending.

**Great: application-level heartbeats** ✅ — server pings every 10–30s; client must pong within ~5s or the connection is closed; client reconnects and syncs from Inbox. Guaranteed detection upper bound (interval + timeout, e.g. ≤15s). *Cost:* 200M users at 10s interval = 20M ping/pongs/sec — fine, tiny messages.

### 4) What happens if Redis (Pub/Sub) fails to deliver?

Durability is already ensured (Inbox written before publish — all messages *eventually* deliver). The question is fast recovery for connected clients.

**Good: periodic polling** — connected clients sync every 30–60s against the Inbox. ~7M qps at 200M users/30s; interval is a latency-vs-load knob. "Good enough" for most cases.

**Good: sequence numbers per chat + gap detection** — monotonically increasing per-chat sequence numbers (Redis INCR); client seeing #5 after #3 knows #4 is missing and re-syncs. *Limit:* gaps only detected when a later message arrives; still need polling as backstop.

**Great: piggyback sequence numbers on heartbeats** ✅
1. **Global sequence per user** (atomic counter, e.g. Redis INCR) incremented on every message to that user.
2. Server includes the current sequence in each heartbeat ping.
3. Client compares with its local sequence; if behind, immediately requests a sync.
- Detection within one heartbeat interval, minimal extra load. *Cost:* atomic counter coordination/dependency.
- In practice production systems combine all three: heartbeats detect dead sockets, sequence numbers detect missed messages, polling is the final backstop.

### 5) How do we handle out-of-order messages?

**We don't** — not directly. Strict ordering means delays and re-ordering machinery (cf. Flink's bounded out-of-orderness watermarks); users prefer speed over perfect order.

Instead: Chat Servers sync clocks via **NTP**; each message is **stamped with server receive time**; clients display messages ordered by that timestamp. Ordering is consistent across all clients even when arrival order differs. Occasionally a message "pops in" above a later-sent one — users find this acceptable.

### 6) "Last seen" functionality

**Bad: write to DB on every heartbeat/activity** — massive write amplification (millions of writes/sec for 200M connected users), expensive, and the data is instantly stale anyway.

**Great: utilize active connections** ✅
- Insight 1: the server *knows* when a socket connects/disconnects. Insight 2: online users can answer live.
- **LastSeen table** (DynamoDB) recording the *last disconnect* per user, updated on disconnect using **conditional writes** (only if new timestamp > existing) to avoid races between servers.
- Query flow:
  1. Client sends `getLastSeen { targetUserId, requestingUserId }`.
  2. Server, in parallel: (a) reads LastSeen and publishes `updateLastSeen` to the requester's channel; (b) forwards `getLastSeen` to the target's channel.
  3. If the target is connected, their server publishes `updateLastSeen: ONLINE` to the requester.
  4. Client merges: ONLINE beats the stored disconnect time.
- One record per user; writes only on disconnect.
- *Challenges:* the two responses may arrive with a small delay (client waits briefly or updates UI seamlessly); depends on servers reporting disconnects — if a server dies, users reconnect shortly anyway; for robustness also write on connect.

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; components may be surface-level abstractions.
- Interviewer probes basics (e.g. how WebSockets work at a high level); nothing taken for granted.
- You drive early stages; interviewer may drive later deep dives.
- **Bar for WhatsApp:** clearly defined API; functional high-level design meeting requirements. Scaling solution will have rough edges, but you should know some of its flaws.

### Senior (E5)
- ~60% breadth / 40% depth. Consistent hashing knowledge is essential here; understand mechanics of long-running sockets.
- **Bar:** speed through the high-level design; discuss scaling and robustness in detail; articulate pros/cons (e.g. partitioning by chat vs user).

### Staff+
- ~40% breadth / 60% depth; experience-driven, highly proactive.
- **Bar:** go 2–3 levels deep on failure modes and bottlenecks; discuss fault tolerance, database optimization, regionalization, cell-based architecture.

## Key Takeaways for Mid-Level Prep

- WebSockets (over TLS) behind an **L4** load balancer; API = commands over the socket, with client **ACKs**.
- Durability first: write Message + per-recipient Inbox **before** best-effort realtime delivery; TTL cleanup.
- Scale realtime routing with **Redis Pub/Sub, channels per user** (know why not Kafka-topic-per-user, and the by-chat vs by-user tradeoff).
- Presigned URLs for media — clients upload directly to blob storage.
- Reliability toolkit: heartbeats + sequence numbers + polling backstop; NTP timestamps instead of strict ordering; connection-event-driven "last seen".

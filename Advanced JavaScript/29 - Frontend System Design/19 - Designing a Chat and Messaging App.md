---
tags: [system-design, interview, chat, real-time, websocket]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [chat app design, messaging design, realtime chat]
---

# Designing a Chat and Messaging App

## Maturity Target

- Priority: #must-know
- Study time: 70 minutes
- Interview signal: Run RADIO on a chat app covering transport, message ordering/dedup, optimistic send with delivery states, reverse-pagination history, reconnection catch-up, and scroll behavior.
- Production signal: You can reason about every state a message passes through and every way real-time chat breaks.
- Dependencies: [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]], [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]], [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]]

## Source Anchors

- [MDN — WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [GreatFrontEnd — Chat application](https://www.greatfrontend.com/questions/system-design/chat-application)

## 1. Requirements

Ask: 1:1, group, or both? delivery/read receipts? typing indicators/presence? media messages? edit/delete? history depth and search? offline send? scale of a conversation (thousands of messages)? multi-device sync?

Design against: **1:1 + group chat, optimistic send with sent/delivered/read states, typing indicators, reverse-paginated history, reconnection with catch-up, virtualized message list.** Out of scope: E2E encryption internals, media transcoding.

The requirements that shape everything: **real-time + optimistic send + long history.** That combines the [[29 - Frontend System Design/13 - Real-Time UI Patterns|real-time patterns]] (ordering, reconnection, backpressure), optimistic UI with delivery states, and reverse-direction infinite scroll.

## 2. Architecture

```
<ChatApp>
 ┌─────────────┐   ┌──────────────────────────────┐
 │ Conversation │   │ Message store (normalized)    │
 │ list         │   │ byId, byConversation[order]   │
 └─────────────┘   │ pending outbox · lastSeenId    │
 ┌─────────────┐   └───────────────┬──────────────┘
 │ Virtualized  │◀── render ────────┘
 │ message list │   WebSocket (send/recv) + REST (history pages)
 │ (reverse)    │   connection state machine
 └─────────────┘
```

Two transports: **WebSocket** for live send/receive; **REST** for paginated history. A **normalized message store** (`byId` + per-conversation ordered id list) so a message updates once (status changes: sending→sent→delivered→read) and is shared across views. An **outbox** holds pending sends. A **connection state machine** (connecting/open/reconnecting) drives UI and catch-up.

> [!warning] History loads *upward* (reverse infinite scroll): prepending older messages must not move the viewport. Anchor to the first visible message and compensate scroll after prepend, or the user gets yanked while reading — the hard part flagged in the [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|feed]] note's chat transfer question.

## 3. Data Model

```ts
interface Message {
  id: string;                 // server id
  clientId: string;           // for optimistic reconciliation before server id exists
  conversationId: string;
  authorId: string;
  body: string;
  seq: number;                // ordering key (server-assigned)
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
  createdAt: number;
}
interface ChatState {
  // keyed by clientId until an ack arrives, then also reachable by server id
  messagesById: Map<string, Message>;          // key: clientId (pre-ack) → server id (post-ack)
  orderByConversation: Map<string, string[]>;  // holds clientIds, sorted by seq (or send time pre-seq)
  outbox: string[];           // clientIds pending ack
  lastSeenSeq: Map<string, number>;            // per conversation, for catch-up
}
```

`clientId` is the optimistic key and it must be the map key too: a sent message renders immediately under its `clientId` with `status:'sending'` before the server assigns `id`/`seq`. On ack you **re-key** — keep the `clientId` entry addressable (the ordering array still references it) while attaching the server `id`/`seq`, or maintain a small `clientId → id` alias map so late frames referencing either key resolve. Keying `messagesById` by server `id` alone would strand every not-yet-acked message. `seq` (server-assigned monotonic) is the ordering truth so messages render in order regardless of arrival order or reconnect replays; pre-ack messages sort by local send time until their `seq` lands.

## 4. Interface

**Network:** WebSocket frames (`send`, `message`, `ack`, `typing`, `receipt`, `presence`); REST `GET /conversations/:id/messages?before=<cursor>&limit=30` for history.

**Component API:** a headless `useConversation(id)` returning `{ messages, sendMessage, loadOlder, typing, connectionState }` — inversion of control over transport so it's testable with a mock socket.

## 5. Optimizations (ranked)

1. **Ordering & dedup** — messages carry server `seq`; apply idempotently into the store by `id` (reconnect replays no-op) and render sorted by `seq`. Optimistic messages sort by a temporary local seq until acked.
2. **Optimistic send + delivery states** — render on send (`sending`), reconcile to `sent` on ack (swap `clientId`→`id`), then `delivered`/`read` via receipts; `failed` + retry on timeout. Snapshot for rollback isn't needed (append), but a failed send must be clearly retryable.
3. **Reconnection catch-up** — connection state machine with exponential backoff; on reopen send `lastSeenSeq` per conversation and fetch the gap so nothing sent while offline is lost. Queue outbox sends until open.
4. **History & rendering** — reverse cursor pagination (load older upward), **virtualized** message list for long conversations, scroll-anchoring on prepend, auto-stick-to-bottom only if already at bottom (else an "unread" pill — the buffered-content pattern).
5. **Backpressure** — a group blast or typing spam batched per frame into one store update; typing indicators debounced/throttled.
6. **Accessibility** — message list as a log (`role="log"`/`aria-live="polite"`) announcing new messages without stealing focus; keyboard send; focus management on conversation switch.

## 6. Interview Answer

Short answer:

> Chat is a normalized message store fed by two transports — WebSocket for live send/receive, REST for paginated history — with a connection state machine. Sends are optimistic: render immediately with a clientId and 'sending' status, reconcile to sent on ack, then delivered/read via receipts, failed with retry. Ordering uses a server-assigned seq applied idempotently by id, so reconnect replays and out-of-order arrivals both resolve. History is reverse cursor pagination with scroll-anchoring on prepend, and the list is virtualized. On reconnect I catch up from the last-seen seq so nothing offline is lost.

Deeper answer:

> The subtle parts are optimistic reconciliation and reverse scroll. Optimistic send needs a clientId because the message exists in the UI before the server gives it an id — the ack maps clientId→id and updates status; a normalized store means that status change (and later delivered/read receipts) updates the one message everywhere. Reverse pagination is the feed problem inverted: prepending older messages must not move the viewport, so I anchor to the first visible message and compensate scroll after insert, and I only auto-scroll on new messages if the user is already at the bottom, otherwise an unread pill. Reconnection is a state machine with catch-up from lastSeenSeq, and bursts are batched per frame so a busy group doesn't cause a render storm. I'd scope receipts/presence to the requirements since each adds real complexity.

## 7. Practice

1. <details><summary>Why does an optimistic message need a `clientId` separate from the server `id`?</summary>The message is rendered before the server assigns an id, so you need a stable local key to track it (React key, status updates, retry). When the server acks, it returns the clientId alongside the new id, letting you reconcile the optimistic message to its server identity without duplicating or losing it.</details>
2. <details><summary>How is chat history pagination different from a normal infinite feed, and what's the hard part?</summary>It loads upward (older messages prepended above the viewport) instead of downward. The hard part is scroll preservation: prepending content shifts everything down, yanking the user's view. Fix by anchoring to the first visible message and restoring its position (compensating scrollTop by the inserted height) after the prepend.</details>
3. <details><summary>A user's connection drops for 30 seconds during an active group chat. How does the design avoid lost or duplicated messages?</summary>Ordering by server `seq` applied idempotently by `id` means replayed messages after reconnect are no-ops (dedup). A connection state machine reconnects with backoff and sends `lastSeenSeq` to fetch the gap (catch-up), so messages sent during the outage are retrieved. Outbound messages queued in the outbox flush on reconnect. Nothing is lost or shown twice.</details>

## Related Notes

- [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]
- [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]]
- [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]

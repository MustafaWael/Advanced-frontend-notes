# API Design

**Source:** [hellointerview.com — API Design](https://www.hellointerview.com/learn/system-design/core-concepts/api-design)

You define how clients interact with your system in the API step of the delivery framework. API design follows predictable patterns: pick a protocol, define resources, specify how clients pass data and get responses. Most interviewers don't care about perfect API design — they want a reasonable API so you can move on to more complex parts. Exceptions: frontend/product roles (APIs matter more day-to-day) and junior roles (less distributed-systems expectation, so more interview time may be spent on APIs). Don't spend more than ~5 minutes on APIs in the interview.

## API Types

Three main protocols:

1. **REST** — standard HTTP methods (GET, POST, PUT, DELETE) manipulating resources identified by URLs. Maps naturally to DB operations and HTTP semantics. **Default choice** — works for ~90% of use cases. If unsure, say "I'll use REST APIs" and move on.
2. **GraphQL** — single endpoint with a query language; clients specify exactly what data they need. Signal words from interviewer: "flexible data fetching," avoiding over-fetching/under-fetching, mobile vs web needing different data.
3. **RPC (e.g., gRPC)** — binary serialization + HTTP/2 for efficient service-to-service communication. Action-oriented (`checkPermission(userId, resource)`) rather than resource-oriented. Signals: microservices, internal APIs, high performance.

Real-time features (notifications, chat, live updates) need WebSockets or Server-Sent Events — persistent connections, not traditional APIs (see the Real-time Updates pattern).

## REST

### Resource Modeling

Resources = your core entities from the delivery framework. Ticketmaster example (events, venues, tickets, bookings):

```
GET /events                    # all events
GET /events/{id}               # specific event
GET /venues/{id}               # specific venue
GET /events/{id}/tickets       # available tickets for an event
POST /events/{id}/bookings     # create booking for an event
GET /bookings/{id}             # specific booking
```

- Resources represent **things**, not **actions** (bookings, not "book"/"purchase").
- Use **plural nouns** (bookings, events, tickets). Easy win with picky interviewers.
- Relationships: nest resources for clear parent-child (`/events/{id}/tickets`) or keep flat with query params (`/tickets?event_id=123`).
- Rule of thumb: **path parameter when the value is required** for the query to make sense; **query parameter when it's an optional filter** (`/tickets?event_id=123&section=VIP`).

### HTTP Methods

- **GET** — retrieve data, no changes. Idempotent.
- **POST** — create new resources (server assigns ID). Not safe, not idempotent — multiple calls create multiple bookings.
- **PUT** — replace an entire resource (or create if missing). Idempotent — same data sent repeatedly yields the same final state.
- **PATCH** — partial update. Not guaranteed idempotent ("set email to X" is; "append to list" isn't).
- **DELETE** — remove a resource. Idempotent — repeated calls leave the same server state (resource stays deleted), even if response codes differ (204 first, 404 after).

**Idempotency matters** because networks fail and clients retry — you don't want duplicate bookings from a retry. GET, PUT, DELETE are idempotent; POST and PATCH are not guaranteed to be.

### Passing Data to APIs

Three places for input:

- **Path parameters** — identify the specific resource (`/events/123`). Structural: required to identify the resource.
- **Query parameters** — filter/sort/modify retrieval (`/events?city=NYC&date=2024-01-01`), pagination (`/events?page=2&limit=20`). Optional modifiers. First param after `?`, subsequent joined by `&`.
- **Request body** — the payload for creates/updates; complex structures, or data too large/sensitive for URLs.

Combined example:

```
POST /events/123/bookings?notify=true
{
  "tickets": [
    {"section": "VIP", "quantity": 2},
    {"section": "General", "quantity": 1}
  ],
  "payment_method": "credit_card"
}
```

Event ID in path (required), notification preference as query param (optional behavior), booking details in body (core data).

### Returning Data

Response = status code + response body (typically JSON). Common status codes: **200** success, **201** created, **400** bad request, **401** authentication required, **404** not found, **500** server error. Interviewers care about the 4xx (client error) vs 5xx (server error) distinction more than memorized codes; even writing "4XX" is usually fine.

## GraphQL

Emerged from Facebook (2012): mobile needed different data than web, but fixed REST endpoints forced either endpoint proliferation or over-fetching (mobile downloading megabytes it doesn't use).

GraphQL consolidates into a single endpoint accepting queries describing exactly the desired data shape:

```
query {
  event(id: "123") {
    name
    date
    venue { name address }
    tickets { section price available }
  }
}
```

Server returns exactly what was asked — nothing more, nothing less.

### When to Use in Interviews

- Diverse clients with different data needs; "avoiding over-fetching/under-fetching" signals.
- Frontend teams iterating quickly without backend changes (new fields requestable if in schema).
- But: adds complexity (query parsing, schema validation, sophisticated caching). REST is simpler for most interviews.

### Schema Design

Design types and relationships rather than endpoints:

```
type Event {
  id: ID!
  name: String!
  date: DateTime!
  venue: Venue!
  tickets: [Ticket!]!
}
type Venue { id: ID!, name: String!, address: String! }
type Query {
  event(id: ID!): Event
  events(limit: Int, after: String): [Event!]!
}
```

Relationships are traversable in a single query — which creates the **N+1 problem**, the biggest GraphQL gotcha: querying 100 events with venues can mean 1 query for events + 100 for venues = 101 DB queries instead of 2. Solution: batching / DataLoader patterns — added complexity REST doesn't have.

Authorization is field-level (in schema resolvers) rather than endpoint-level: a user might see an event's name/date but not venue data.

Mention GraphQL when you see clear over/under-fetching problems, but don't default to it.

## RPC

RPC lets a client call a procedure on a server as if it were a local function, without understanding network details. Action-oriented vs REST's resource-oriented:

```
getEvent(eventId: "123")                          // vs GET /events/123
createBooking(eventId: "123", userId: "456", …)   // vs POST /events/123/bookings
getAvailableTickets(eventId: "123", section: "VIP")
```

Most popular: **gRPC** (Protocol Buffers + HTTP/2 — much faster than JSON-over-HTTP). Also notable: **Apache Thrift** (from Facebook; multi-language, multiple serialization formats).

### Protocol Buffers and Type Safety

`.proto` files define service methods and messages:

```
service TicketService {
  rpc GetEvent(GetEventRequest) returns (Event);
  rpc CreateBooking(CreateBookingRequest) returns (Booking);
  rpc GetAvailableTickets(GetTicketsRequest) returns (TicketList);
}
message GetEventRequest { string event_id = 1; }
message Event { string id = 1; string name = 2; int64 date = 3; Venue venue = 4; }
```

gRPC generates client/server code in multiple languages — compile-time type safety across, e.g., a Go backend and Java payment service.

### When to Use RPC

- **Performance-critical** paths (binary serialization + HTTP/2)
- **Type safety** (generated clients prevent runtime errors)
- **Internal service-to-service communication** (no need for REST resource semantics)
- **Streaming** (gRPC supports bidirectional streaming)

Typical split: REST for public endpoints (mobile/web), gRPC for internal communication (booking ↔ payment ↔ inventory services). In the API step, focus on user-facing APIs; at most note that internal services use RPC during high-level design.

## Common API Patterns

### Pagination

Can't return millions of records at once. Two approaches:

- **Offset-based:** `/events?offset=20&limit=10` (records 21–30). Simple and intuitive, but with large/changing datasets you can see duplicates or miss records as data shifts during pagination.
- **Cursor-based:** a pointer to a specific record. First request `/events?limit=10` returns events plus `"next_cursor": "cmd9atj3p000007ky19w1dpy2"` (typically an encoded record ID or timestamp); next request `/events?cursor=...&limit=10`. Stable under inserts, but "jump to page 5" is hard.

For interviews, offset-based is usually fine unless real-time data or high-volume scenarios come up. Interviewers care more that you *remembered pagination* than which approach.

### Versioning Strategies

- **URL versioning** (most common): `/v1/events`, `/v2/events`. Explicit, easy to understand/implement/route. Safest interview choice.
- **Header versioning:** `Accept-Version: v2` or `API-Version: 2`. Cleaner URLs, more standards-aligned, but less obvious and harder to test in browsers.

Hello Interview breakdowns often omit versioning entirely — not because it doesn't matter in practice (it does), but because most interviewers don't care.

## Security Considerations

### Authentication and Authorization

- **Authentication** verifies identity (the user is who they claim).
- **Authorization** verifies permissions (that user may perform this action — John can cancel only his own bookings).

For most interviews, just call out which endpoints require auth and say you'd rely on a JWT or a DB-stored session.

#### API Keys vs JWT

- **API keys:** long random strings acting as passwords for applications (e.g., `sk_live_abc123def456...`), sent in the Authorization header; server looks up the key with its permissions/rate limits. Great for server-to-server communication and third-party developer access. Almost never right for user-facing products — users shouldn't manage cryptographic strings, and keys don't expire or carry user context.

```
GET /events
Authorization: Bearer sk_live_abc123...
```

- **JWT:** encodes user info in the token itself (user ID, permissions, expiration), signed with a secret key at login. Verification checks the signature — no DB lookup needed; the token carries the context. Ideal for distributed systems: any service with the verification key can validate independently (gateway verifies, forwards with confidence). Stateless.

```
// JWT payload
{ "user_id": "123", "email": "john@example.com", "role": "customer", "exp": 1640995200 }
```

Rule: **API keys for internal service communication and external developers; JWTs for user sessions in web/mobile apps.**

#### Role-Based Access Control (RBAC)

Assign roles to users, permissions to roles:

```
customer:      book tickets, view own bookings
venue_manager: create events, view sales for their venues
admin:         everything
```

Endpoint checks combine both: `GET /bookings/{id}` → (1) authenticated (valid JWT)? (2) authorized (owns this booking OR admin)? In an interview, at most mention which endpoints each role can access — often not even relevant.

### Rate Limiting and Throttling

Protects against malicious abuse and accidental overuse. Common strategies:

- **Per-user:** e.g., 1000 requests/hour per authenticated user
- **Per-IP:** e.g., 100 requests/hour for unauthenticated requests
- **Endpoint-specific:** e.g., 10 booking attempts/minute (anti-scalping)

Implement at API gateway or middleware; return **429 Too Many Requests** when exceeded. In interviews, "we'll implement rate limiting to prevent abuse" is usually sufficient — don't design algorithms unless asked.

## Conclusion

Demonstrate engineering judgment, not perfect specs: pick the right protocol (usually REST), model resources clearly, show auth/security basics. Candidates more often err by spending **too much** time on API design than too little — cap it at ~5 minutes.

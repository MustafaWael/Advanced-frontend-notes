# 03 - The RADIO Framework

> Source: https://www.greatfrontend.com/front-end-system-design-playbook/framework (by Yangshun Tay, ex-Meta Staff Engineer). This article is the authoritative source of the RADIO framework.

The **RADIO framework** is an easy-to-remember, structured approach for answering front end system design questions. In front end interviews, the "system" is usually a product, so think of it as designing a product.

| Step | Objective | Time |
| --- | --- | --- |
| **R**equirements exploration | Understand the problem and determine scope via clarifying questions | ~10% |
| **A**rchitecture / high-level design | Identify key components and how they relate | ~20% |
| **D**ata model | Describe core entities, their fields, and which component owns them | ~10% |
| **I**nterface definition (API) | Define APIs between components: functionality, parameters, responses | ~20% |
| **O**ptimizations and deep dive | Discuss optimizations and dive into areas needing special attention | ~40% |

## How to use RADIO

- **Not a rigid linear order.** It's a checklist to ensure comprehensive coverage. R must come first; A/D/I are iterative (some prefer I before A/D — fine, and better for some products). O usually comes last as a refinement of the complete design.
- **Backtrack freely.** If during A you realize the data model won't support a requirement, revise D immediately. If the interviewer asks for a deep dive early, follow their lead — but resume where you left off until A/D/I are holistically covered.
- **Write things down.** Write "RADIO" on the whiteboard and refer to it to remember what's left.
- **RADIO isn't front-end specific** — it works for back end interviews too (may need extra areas).
- **Don't force it** onto overly-specific scenarios with little architecture (e.g. "implement a mention feature in Slack").

---

## R — Requirements exploration (~10%)

Questions are deliberately vague and under-specified. Treat the interviewer as a product manager and dig with clarifying questions:

- **Main use cases?** For "Design Facebook", focus on the defining features: the news feed, feed pagination, creating posts — not the befriending flow. Not clarifying wastes precious minutes and is noted against you.
- **Functional vs non-functional requirements:**
  - *Functional*: core flows the product cannot function without.
  - *Non-functional*: improvements — performance, scalability (items on page before slowdown), UX, etc.
  - Preferred approach: take the initiative to list requirements yourself and get alignment, rather than asking the interviewer to hand them to you.
- **Core vs good-to-have features.** E.g. post composer: text only, or photos/videos/polls/check-ins too?
- **Other useful questions:** Which devices/platforms (desktop/tablet/mobile)? Who are the main users? Offline usage? Performance requirements?

Write agreed requirements down and refer to them throughout.

## A — Architecture / high-level design (~20%)

Identify key components, their interactions and relationships. **Focus on client-side architecture; treat the server as a black box** exposing APIs over HTTP/GraphQL/WebSockets. Draw diagrams (boxes + labelled arrows; nested boxes for subcomponents). Practice Excalidraw or diagrams.net beforehand.

Typical components/modules:

- **Server** — black box exposing APIs.
- **View layer** — what the user sees and interacts with; subviews + local interaction state (React/Vue/Svelte components). Cross-cutting data should NOT live here.
- **Store/model layer** — application data and derived state; cross-cutting data (user profile, auth, layout state, shared domain data). Unidirectional data flow (Redux Toolkit, Zustand, Jotai, MobX).
- **Data access layer** — typed layer (React Query, tRPC, Apollo Client) handling fetching, caching, error management. Decouples the client from data origin — e.g. adding offline storage with background sync only affects this layer.

Notes:

- Not every component is needed for every product; small products/UI components can keep data in local component state.
- Consider **separation of concerns** (each component's purpose, data, services to the rest) and **where computation should occur** (server vs client — tradeoffs depend on product/context).
- Stay at design level; you don't need to pick a framework/library unless it changes architecture.
- After drawing, verbally describe each component's responsibilities.

**News Feed example responsibilities:** Server (HTTP APIs to fetch/create posts) · Store (app-wide, mostly server-originated data) · Data access layer (network requests + cache) · Feed UI (list of posts + composer) → Feed post (renders post, like/comment buttons) and Post composer.

## D — Data model (~10%)

Describe entities, fields, owning components. Two kinds of client data:

- **Server-originated data** — from the DB, seen by many people/devices: user data, posts, comments.
- **Client-only data (UI state)** —
  - *To be persisted*: form inputs destined for the server.
  - *Ephemeral*: fine to lose on tab close — validation state, current tab, expanded sections.

Note field types and origin. News Feed example:

| Source | Entity | Belongs to | Fields |
| --- | --- | --- | --- |
| Server | `Post` | Feed post | `id`, `created_time`, `content`, `image`, `author` (a `User`), `reactions` |
| Server | `Feed` | Feed UI | `posts` (list of `Post`), `pagination` metadata |
| Server | `User` | Store | `id`, `name`, `profile_photo_url` |
| User input (client) | `NewPost` | Composer UI | `message`, `image` |

Client data often mirrors DB schema, but not always — e.g. Notion stores each block as a DB row and the client assembles a tree. The model is iterative; add fields as requirements grow. Consider listing fields under the owning component in your diagram.

## I — Interface definition (API) (~20%)

All APIs share three parts:

| Part | Server-client | Client-client |
| --- | --- | --- |
| Name & functionality | HTTP path | JS function / event name |
| Parameters | HTTP query/POST params | Function/event parameters |
| Return value | HTTP response (JSON) | Return values (optional) |

### Server-client protocols

- **HTTP/REST** — stateless request/response; the most common in interviews.
- **WebSockets** — persistent bidirectional channel after HTTP handshake; chats, games, live dashboards, collaborative editing.
- **Server-Sent Events (SSE)** — one-way (server→client) stream over long-lived HTTP; notifications, tickers, logs. Simpler than WebSockets.
- **Long polling** — technique, not protocol; hold request open until data available. Rarely used now.
- **GraphQL** — client requests exactly the data shape it needs; solves over/under-fetching. Rarely mandatory in interviews.
- **WebRTC** — peer-to-peer low-latency media/data (video calls); signaling server for setup only.

Mostly you only need HTTP, WebSockets and SSE.

**News Feed example** — `GET /feed`, cursor-paginated:

```json
// Request params
{ "size": 10, "cursor": "=dXNlcjpXMDdRQ1JQQTQ" }

// Response
{
  "pagination": { "size": 10, "next_cursor": "=dXNlcjpVMEc5V0ZYTlo" },
  "results": [
    {
      "id": "123",
      "author": { "id": "456", "name": "John Doe" },
      "content": "Hello world",
      "image": "https://www.example.com/feed-images.jpg",
      "reactions": { "likes": 20, "haha": 15 },
      "created_time": 1620639583
    }
  ]
}
```

### Inter-client communication

- **Props and callbacks** — data down, callbacks up (parent↔child).
- **Store dispatching actions** — modules dispatch actions and subscribe to state changes; predictable unidirectional flow. Actions = objects with name + payload (Flux/Redux) or setter functions (Zustand/Pinia). Most common pattern to discuss.
- **Publish/subscribe via event listeners** — decoupled, non-hierarchical; prevalent in the browser (`element.addEventListener`), but hard to trace at scale.

### UI component API design (props)

For component questions, "interface" = props:

- **Data props** — `name`, `title`
- **Event/callback props** — `onClick`, `onSubmit`
- **Configuration/behavior props** — `isOpen`, `isDisabled`, `timeout`, `maxResults`
- **Styling/presentation props** — `className`, `style`, `color`, `size`
- **Render function / slot props** — invert control, e.g. `render`

Only spend time on component API design when asked to design a component (Autocomplete, Modal, Dropdown) or when a complex component is the core of the product (Pinterest masonry grid).

## O — Optimizations and deep dive (~40%)

No fixed path — pick areas deliberately:

1. **Focus on the unique/important areas of the product.** E-commerce → SEO + performance. Collaborative editors → concurrent modifications and conflict resolution.
2. **Showcase your strengths** (a11y, performance...) while staying relevant to the product — aim to teach the interviewer something new; no V8-internals tangents.

General areas: performance, networking, user experience, accessibility, SEO, i18n/multilingual, multi-device, security.

### Topics to AVOID (they don't affect architecture)

- JavaScript framework debates (React vs Vue vs Angular)
- Design system / CSS framework choices (Tailwind vs Material UI)
- Generic performance advice (minification, image compression) unless core to the problem
- Auxiliary infra: logging, analytics, monitoring
- DevOps/CI/CD, Docker, deployment pipelines
- Tooling: webpack vs Vite, linting, formatting

### Exceptions — when frameworks ARE relevant

- The problem domain dictates it (dynamic dashboard → React/Vue; SEO-heavy content site → Next.js/Remix/Nuxt for SSR/SSG).
- Rendering/deployment strategy is central: CSR vs SSR vs SSG vs ISR, SPA navigation vs server-rendered first load, CDN/edge delivery.

Rule of thumb: raise a topic only when it changes architectural trade-offs, not when it's implementation detail or something every app needs.

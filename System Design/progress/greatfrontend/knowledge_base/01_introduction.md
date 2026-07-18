# 01 - Introduction to Front End System Design

## Overview
Front End System Design interviews are open-ended sessions (typically 30-60 minutes) where candidates design software architectures for vague problems or scenarios. These usually take place on a whiteboard or virtual drawing app (e.g., Excalidraw).

Unlike standard coding interviews, there are no "right" answers. Success is measured by your ability to work with the interviewer to design a suitable software architecture, explain technical decisions, and discuss tradeoffs.

## Importance
- **Influence on Leveling**: Performance heavily influences job leveling and compensation. For senior roles and above, a weak system design round almost always results in a rejection. Passing this round separates Senior from Staff engineers.
- **Preparation Gap**: Generic system design resources focus on backend concepts (distributed systems, database sharding, capacity planning) which will mislead you.

## Front End vs Back End System Design

The core difference is that **Front End System Design focuses on the client-side architecture and API boundaries**, while Backend System Design focuses on distributed cloud services.

### Key Differences

| Aspect | Back End / Full Stack | Front End |
| :--- | :--- | :--- |
| **Requirements** | Required | Required |
| **Architecture** | Distributed services (Load balancers, CDN, Caches, DBs) | Client components (View, Store, Networking Layer) |
| **Capacity Estimation** | Usually required | Usually **not** required |
| **Data Model** | Database Schema | Application State |
| **Black Box** | Client | Server (treat it as a black box) |
| **APIs** | Server-to-Server (HTTP, gRPC) | Client-to-Server (HTTP, WebSocket) & Client Events |
| **Focus Areas** | Scalability, Reliability, Consistency, Availability | Performance, UX, Accessibility, Internationalization |

### Example Comparison: "Design Facebook News Feed"
- **Back End Focus**: Database schema, API between microservices, handling celebrity vs regular user feeds, scaling for high traffic.
- **Front End Focus**: HTTP API to fetch the feed, implementing pagination, liking/commenting interactions, post composer, performance, and accessibility.

## Actionable Takeaways
1. **Focus on Client Concepts**: Spend preparation time on rendering, state management, API shape, performance, and accessibility.
2. **Ignore Backend Noise**: Do not waste time in interviews on database schemas or load balancers unless explicitly asked.
3. **Use Collaborative Tools**: Practice drawing client architectures using Excalidraw or similar tools.

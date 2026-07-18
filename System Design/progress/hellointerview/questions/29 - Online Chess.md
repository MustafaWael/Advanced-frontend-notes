# 29 - Online Chess Platform (like Chess.com / Lichess)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-chess
**Author:** Evan King · Difficulty: Hard · Patterns: Real-time Updates, Dealing with Contention

> **⚠️ Premium-locked page.** The "Understanding the Problem" section, functional requirements, and the scale framing of the non-functional requirements were freely visible. All design content beyond that is behind the Hello Interview Premium paywall. This note captures the free content plus the article's structure/outline.

## Understanding the Problem

**What is Chess.com / Lichess?** Online chess platforms let players find an opponent of similar skill, play a real-time game with a shared clock, and climb a global rating leaderboard. **The server validates every move and owns both clocks**, so neither player can cheat the rules or the time.

Primer: two players alternate moves on a shared board; each side has its own countdown clock set by the time control. Games run from classical (hours per side) down to blitz/bullet (a minute per side), where every bit of delay eats into a player's clock. Players carry a **skill rating** that drives matchmaking and leaderboard placement. The breakdown builds a single game first, then uses deep dives for the parts that get hard at scale: matchmaking, running a large fleet of game servers, and keeping the clock fair across players with different network latency.

## Functional Requirements

Advice from the article: nail down the top few functional requirements; everything else goes below the line. Calling out out-of-scope items shows product sense, but keep the core list tight and check with your interviewer before moving on.

**Core Requirements**

1. Players should be able to find an opponent through skill-based matchmaking and start a game.
2. Players should be able to play a game in real time.
3. Players should be able to view a global leaderboard and see their own rank, both updating shortly after games finish.

**Below the line (out of scope)**

1. Spectating live games and broadcasting popular boards.
2. In-game chat, friends, and social features.
3. Puzzles, training, and post-game analysis or replay.
4. Tournaments and arena play.
5. Anti-cheat / engine detection (fair play) and tournament integrity — noted as interesting but out of scope.

## Non-Functional Requirements

**Scale framing (free-visible):** design for **500K concurrent games at peak**. Each game has two players on their own connections, so 500K games × 2 = **1M concurrent connections**, plus the compute to validate every move and run two clocks per game. These numbers carry through the deep dives.

🔒 *The actual non-functional requirements list is premium-locked.* (Expect themes like low-latency move delivery, strong consistency for game state/clocks, high availability, and fault tolerance for in-flight games — but the article's list is not visible.)

## Article Structure (locked sections)

The full breakdown follows this outline — all of the following sections are premium-locked:

- **The Set Up**
  - Planning the Approach
  - Defining the Core Entities
  - API or System Interface
- **High-Level Design**
  1. Players should be able to find an opponent through skill-based matchmaking and start a game
  2. Players should be able to play a game in real time
  3. Players should be able to view a global leaderboard and see their own rank
- **Potential Deep Dives**
  1. How do we match players fairly at scale?
     - Do we need to shard the pool across Redis nodes?
     - What happens if that Redis node goes down?
  2. How do we scale the game servers to 500K concurrent games?
  3. How do we keep the clock fair despite uneven latency?
  4. How do we keep the leaderboard correct and fast at 10M players?
  - Some additional deep dives you might consider
- **What is Expected at Each Level?** — Mid-level / Senior / Staff+ subsections (content locked)

Note the deep-dive subsection titles reveal that matchmaking is built on a **Redis-backed player pool** (with sharding and failover discussed), and the leaderboard targets **10M players**.

## Locked Sections Note

Premium-locked and not captured: Non-Functional Requirements list, Planning the Approach, Core Entities, API design, all three High-Level Design walkthroughs, all four deep dives (fair matchmaking at scale incl. Redis sharding/failover; scaling game servers to 500K games; clock fairness under uneven latency; leaderboard at 10M players), additional deep-dive suggestions, and level expectations (Mid/Senior/Staff+).

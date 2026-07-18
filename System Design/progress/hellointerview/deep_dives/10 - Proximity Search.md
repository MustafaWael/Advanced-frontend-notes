# Proximity Search

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/proximity-search

Learn how production systems index latitude and longitude for fast nearby queries, from spatial trees to encoded keys like geohash, S2, and H3.

---

## The Problem Space

Proximity search shows up anytime you search **by location** instead of by ID or value: drivers near a rider (Uber), restaurants near a user (Yelp/DoorDash), people near a location (Tinder).

### Why a normal index fails

- A B-tree is blazing fast for one-dimensional range queries ("users aged 20–25") because sorted keys are packed together on disk: one seek + a short sequential read.
- Location is **two-dimensional** (lat + long), and what you care about is straight-line distance between points.
  - Index on latitude → you get a horizontal strip of the earth.
  - Index on longitude → a vertical strip.
  - A composite index doesn't help either: a B-tree sorts by the first column and only breaks ties with the second, so it still effectively sorts on one dimension. The strip it returns can hold millions of rows, none ranked by distance.
- Result: the database falls back to brute force — computing the real distance to every row and discarding everything past the radius.

**Root problem:** a one-dimensional sort order can't preserve two-dimensional closeness. Points that are neighbors on the ground can land far apart in the index.

### The two approaches (and the one unifying idea)

Almost every production system takes one of two approaches, chosen by the **shape of your data**:

1. **Custom spatial trees** — for *geometric* data (polygons, roads, delivery zones) where containment/intersection matter. This is what PostGIS and Elasticsearch give you.
2. **Encoded keys** — for *points that move constantly* (drivers, live user locations). Flatten each location into a single sortable key that an ordinary index already handles. This is the trick behind Redis geospatial, geohash, S2, and H3.

**Unifying idea:** a spatial index almost never produces the final answer on its own. It turns "check every row" into "check a small candidate set," and then you finish with **exact distance or geometry math** on that handful of candidates. Every structure below is just a different way to generate that candidate set cheaply.

---

## Approach 1: Custom Spatial Trees

Purpose-made trees for spatial data. The trick that makes them work in a database (not just in memory) is shaping the tree to behave like a B-tree on disk: balanced, page-sized nodes, predictable depth. Each structure below fixes a problem the previous one couldn't.

### Quadtrees

- Turn the map itself into a tree: the whole map is the root; split into 4 quadrants → 4 children; any quadrant with too many points splits again; recurse until each leaf holds few enough points to scan directly. Points live only in the leaves.
- **Search:** walk down from the root comparing your query point to each cell's midpoint (N/S, E/W) until you reach a leaf. The leaf's points **plus the neighboring leaves** (so you don't miss anyone just across a boundary) are your candidate set; exact distance math picks winners.
- **Nice property:** adapts to density. Manhattan becomes a deep subtree; an empty lake stays one coarse cell.

**Problems at scale:**

1. **Depth.** Splits land at the *geometric midpoint*, never where the data sits. Dense clusters keep getting halved until points separate — 10+ levels downtown vs. 2 in rural Vermont. Latency depends on where you're looking; the busiest regions are slowest. Hard to reason about worst-case performance.
2. **Disk.** It's a pointer structure; every node sits at an arbitrary address. Fine in RAM, painful on disk: each pointer hop risks a random page read, so a few hops in you're mostly waiting on the disk.

Quadtrees are still everywhere *in memory* (Google Maps tiles, game-engine collision detection), but not for on-disk indexes that overflow RAM.

### k-d Trees and BKD Trees

- A **k-d tree** alternates dimensions: level 1 splits on x, level 2 on y, level 3 back to x, etc. A binary tree for multi-dimensional data — balanced (depth log n) as long as you split at the **median**.
- **Median split vs. midpoint split (the key difference from quadtrees):** picture 10 drivers on one street, 9 bunched east, 1 out west. A quadtree cuts at the geometric middle — one driver on one side, nine crammed on the other, requiring repeated cuts through empty space. A k-d tree cuts at the median (the 5th driver), landing the dividing line where the separating actually needs to happen. Every cut halves the *number of points*, not the area — that's what keeps it balanced regardless of skew.
- **Same disk problem as quadtrees:** pointers all the way down, no clean mapping onto disk pages.
- **BKD tree (block k-d tree)** is the modern fix: pack points into blocks sized to a disk page and build the whole tree once from a batch of data. Essentially **write-once** — great for static chunks, bad for constantly moving data.
- **Elasticsearch uses BKD trees for its geo fields** — a geo query in ES is the k-d tree idea repackaged into a disk-friendly, block-structured index.

### R-trees

The first spatial index built from the ground up for **on-disk database use**. Solves two problems earlier trees couldn't:

1. **Shapes.** Prior structures assume point data. Real geo data includes lines (highways), polygons (counties, delivery zones). You can't drop a county into one quadtree cell — it sprawls across many.
2. **Disk.** A database index needs the spatial equivalent of a B-tree: stays balanced as data changes, reads quickly off disk, updates cheaply.

**Core idea: the minimum bounding rectangle (MBR).** Wrap every object in the smallest axis-aligned rectangle that fully contains it (a point = degenerate rectangle; a highway = long thin sliver; a county = big box). Group nearby rectangles inside larger enclosing rectangles, nesting all the way up to the root.

**Why it works as a database index:**
- Stays balanced exactly like a B-tree — every leaf at the same depth, predictable page count per query.
- Every node is sized to fit a single disk page.
- Inserts/deletes rebalance by splitting/merging pages, like a regular B-tree.

**The tradeoff to watch: overlap.** Unlike quadtree cells, R-tree rectangles can overlap. If a query point lands inside two bounding rectangles, you must descend both branches. Sloppy insertion → lots of overlap → many branches → slow queries. The fix everyone ships is the **R\*-tree**, which keeps overlap low with smarter insertion heuristics.

**Where you'll see it:** R-trees are the workhorse of production spatial indexes. **PostGIS** builds spatial indexes on Postgres's GiST framework (R-tree-style bounding-box behavior); SQLite and Oracle Spatial ship their own R-tree variants. If your problem involves real geometry ("does this delivery zone contain this address," "does this road cross this county"), this is the approach.

---

## Approach 2: Encoded Keys

Custom trees work but are a lot of machinery: special indexing code, query code, tooling, usually a dedicated spatial extension. The encoded-key approach skips all of that — turn each lat/long into a **cell ID or sortable key** that an ordinary B-tree index can use to narrow the search to a small patch of map. Popular because it **reuses infrastructure every database already ships**.

### Geohash

- Built on space-filling-curve math: a single line threaded through 2D space so points close on the map stay close along the line.
- **Construction:** divide the world into a 32-cell grid, label each cell with a character — that's your first character. Divide that cell into 32 smaller cells — second character. Recurse as deep as you want. Each character zooms in: ~5 characters ≈ 5 km cell; 9 characters ≈ 5 m.
- **Underneath, it's just bits:** each character is 5 bits (1 of 32), so `dr5ru` is 25 bits. Read the bits as a number and you get an integer with the same ordering. That's why Redis stores a geohash as a 52-bit integer and Postgres as text — both indexes behave identically.
- **The payoff — shared prefixes mean nearby:** two points share a prefix only if they fell into the same cell at every level. Share 5 characters → same ~5 km box; share 6 → ~1 km. So a proximity query becomes an ordinary prefix scan: `WHERE geohash LIKE 'dr5ru%'` — a regular B-tree scan on any database.
- **Redis geo commands** are the same idea: `GEOADD` interleaves lat/long into a 52-bit geohash integer stored as a sorted-set score; a nearby query is a `ZRANGEBYSCORE` — the prefix scan wearing different syntax.

**The pitfall that bites people — boundary edge cases:** two points a meter apart can land in different cells with completely different prefixes if they straddle a cell boundary. A rider on the edge of `dr5ru` might have their nearest driver 10 m away in neighboring cell `dr5rg` — a naive prefix scan misses them entirely.

**Standard fix — the 3×3 trick:** compute the query point's cell, then the eight neighboring cells, and query all nine as a unit. Then **post-filter by exact distance** to drop corners that are inside the query window but too far away. Almost every encoded-key index in production does some version of this query-the-ring-and-post-filter dance.

### S2 (Google)

- Geohash treats lat/long as a flat rectangle, but the earth isn't flat: a degree of longitude is ~111 km at the equator and shrinks to zero at the poles, so geohash cells are fat squares near the equator and thin slivers up north.
- **S2 is the spherical cousin of geohash:** wraps the globe in a cube and projects onto the six faces, giving cells of **roughly equal area anywhere on earth**, each with a **64-bit hierarchical ID** you can truncate to get the parent cell.
- Because it understands the sphere, it handles cases a flat grid mangles — e.g., polygons crossing the antimeridian (where longitude wraps +180 → −180).
- It's the cell system underneath **MongoDB's 2dsphere index**.

### H3 (Uber)

- Open-sourced by Uber; runs their dispatch and surge pricing. Twist: **hexagons instead of squares**.
- A square has two kinds of neighbors (4 across edges, 4 across corners, farther away) — messy for "everything within N rings of me" queries and heat maps. A hexagon has **6 neighbors all roughly equidistant** — much cleaner for ring-based analytics.
- Like geohash and S2, each cell is a 64-bit hierarchical ID.
- **Key difference:** geohash and S2 lay cells along a space-filling curve, so a numeric *range scan* sweeps a neighborhood in one shot. **H3 doesn't** — close IDs aren't reliably close on the map. Instead it gives cheap **grid math** to compute the ring of cells around any cell directly, and you look those exact IDs up.
- **The dispatch pattern:** snap each driver to an H3 cell (say ~200 m). When a rider opens the app, take their cell plus the surrounding ring (widen if needed), then `WHERE h3_cell IN (list of cell IDs)` — a plain lookup on an ordinary integer index — and post-filter by exact distance. Cheap writes, cheap candidate generation, no spatial extension anywhere. Exactly the shape you want when location updates arrive constantly.

> **Interview tip:** you rarely need to name H3 vs. S2 vs. geohash to score the point. What lands is explaining *why* a plain index fails on lat/long, then reaching for the boring production option and walking the tradeoff out loud. The reasoning shows you understand the problem; the library name is a bonus.

---

## Which Should You Use?

| | **Custom spatial tree** (PostGIS/GiST R-tree, ES BKD) | **Encoded cells** (geohash, S2, H3, Redis geo) |
|---|---|---|
| **Data shape** | Geometric: polygons, roads, delivery zones; containment/intersection queries | Mostly points that move constantly: drivers, users, devices |
| **Strength** | Database understands shapes; handles points, lines, polygons alike | Cheap writes (a moving driver = one integer update), fast candidate generation; scales to millions of writes/sec |
| **Cost** | Spatial extension required; pricier writes (rebalancing rectangles is real work; BKD is essentially write-once — neither loves churn) | Mostly limited to points; cell boundaries mean you always query a ring of neighbors, never one exact cell |

**Mnemonic:** *Spatial tree for shapes. Encoded cells for moving points. And always, always post-filter.*

Whichever you pick, the index only hands you **candidates** — you still finish with exact distance or geometry math. Once that clicks, the specific library barely matters.

---

## Interview Pitfalls & Takeaways

- **Don't say "just add an index on lat and long."** Explain why B-trees (even composite) fail on two dimensions — this is the core insight interviewers listen for.
- **Never forget the boundary problem** with encoded cells; always mention querying the ring of neighboring cells and post-filtering by exact distance.
- **Match structure to workload:** BKD/write-once indexes are wrong for constantly moving drivers; encoded cells are wrong for polygon containment questions.
- **Quadtree depth skew:** hot dense areas make quadtrees deep and slow exactly where traffic is highest — a good tradeoff to volunteer.
- **R-tree overlap:** overlapping bounding rectangles force multi-branch descent; R\*-tree insertion heuristics are the production fix.
- Common problems where this comes up: Uber/Lyft (driver dispatch), Yelp (nearby restaurants), Tinder (nearby people), local delivery services.

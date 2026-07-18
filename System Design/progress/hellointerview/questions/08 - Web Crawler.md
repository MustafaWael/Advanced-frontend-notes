# 08 - Web Crawler

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/web-crawler
**Author:** Evan King (Hello Interview) · **Difficulty:** Hard

---

## Understanding the Problem

A web crawler automatically traverses the web by downloading pages and following links. Uses: indexing for search engines, research data collection, monitoring sites for changes.

The purpose of the output affects design: a search engine indexes and ranks (PageRank); an AI company dumps raw text to train LLMs. Either way, the interview focuses on the **crawling task**: efficiently crawl the web, extract data, store it accessibly.

**This design's goal:** extract text data from the web to **train an LLM** (à la OpenAI/GPT-4, Google/Gemini, Meta/LLaMA).

## Functional Requirements

**Core:**
1. Crawl the web starting from a given set of seed URLs.
2. Extract text data from each web page and store it for later processing.

**Below the line (out of scope):**
1. The actual processing of the text data (e.g., training an LLM).
2. Non-text data (images, videos).
3. Dynamic content (JavaScript-rendered pages).
4. Authentication (login-required pages).

> Note: you can't scrape the *entire* internet — many small sites are unreachable. A standard assumption worth clarifying with the interviewer.

## Non-Functional Requirements

**Scale assumptions (ask the interviewer!):** ~10B pages, average 2MB per page (total transfer size incl. inline resources; HTML alone is typically ~30KB, but 2MB is a reasonable worst case for bandwidth planning). Data needed for training **5 days** after starting the crawl.

**Core:**
1. **Fault tolerance** — handle failures gracefully, resume crawling without losing progress.
2. **Politeness** — adhere to robots.txt; don't overload website servers.
3. **Efficiency** — crawl the web in under 5 days.
4. **Scalability** — handle 10B pages.

**Below the line:** security, cost, legal/privacy compliance.

> Tip on estimations: delay back-of-envelope math until it's needed to solve a specific problem, rather than doing it all upfront. Communicate this approach to the interviewer.

## The Set Up

### Planning the Approach
Not a user-facing system — so instead of user flows, define the **system interface** and **data flow** before the high-level design.

### System Interface
- **Input:** seed URLs to start crawling from.
- **Output:** text data extracted from web pages.

### Data Flow
1. Take seed URL from frontier and request IP from DNS.
2. Fetch HTML from the external server using the IP.
3. Extract text data from the HTML.
4. Store the text data in a database.
5. Extract linked URLs from the page and add them to the list of URLs to crawl.
6. Repeat 1–5 until all URLs have been crawled.

Start simple; improve as you go.

## High-Level Design

Core components:
1. **Frontier Queue** — queue of URLs to crawl; seeded with initial URLs, grows as we crawl. Technology (Kafka / Redis / SQS) decided later.
2. **Crawler** — fetches pages, extracts text, extracts new URLs for the frontier queue.
3. **DNS** — resolves domain names to IPs. (Later: caching, failures, not overloading DNS.)
4. **Webpage** — the external servers we crawl (outside our system boundary).
5. **S3 Text Data** — blob storage for extracted text; S3 chosen for scalability, durability, cheap bulk storage (GCS/Azure Blob also fine).

> Ask about seed URLs — almost always provided, but asking shows holistic thinking. If not provided: start with popular search engines, news sites, social platforms, web directories.

## Potential Deep Dives

Go one-by-one through the non-functional requirements. (Well-defined NFRs mean you never run out of deep-dive material — especially important for senior candidates.)

### 1) Fault tolerance — don't lose progress

The single crawler service does too much (DNS, fetching, text extraction, URL extraction). A failure in any task loses all progress. Fetching is the most failure-prone task (servers down, slow connections, huge pages…).

**Key move: break the crawler into smaller, pipelined stages** — isolate failures to one stage, retry just that stage, scale and optimize each independently.

1. **URL Fetcher** — fetches HTML from the external server; stores **raw HTML in blob storage** for later processing; retries on failure without losing other progress.
2. **Text & URL Extraction** — extracts text and linked URLs. (Could be two stages, but both are simple and parallelizable — combining simplifies the design.)

> Rule of thumb: for data-processing questions, your first thought should be to break the system into pipelined stages.

**Added state:** a **Metadata DB** (DynamoDB fine; PostgreSQL/MySQL also work) with a URL table storing links to the blob-storage HTML and text. **Anti-pattern:** storing raw HTML in the queue — queues aren't for large payloads. Queue messages carry just the URL's id in the Metadata DB.

Bonus: the pipeline is robust to changing requirements — e.g., if the ML team wants image alt text included in extraction, swap the extraction stage without re-fetching the whole web.

**Retrying failed fetches:**

- **Bad — in-memory timer:** wait a few seconds and retry. Lost if the crawler dies; a few seconds rarely helps. Need exponential backoff.
- **Good — Kafka with manual exponential backoff:** separate topic for failed URLs + a retry service; store next-fetch time in the message; consumers wait until that time. Works, but complex to build and maintain.
- **Great — SQS with exponential backoff ← chosen:** SQS's **visibility timeout** is the primitive (default 30s, up to 12 hours). Use `ChangeMessageVisibility` to adjust the timeout based on `ApproximateReceiveCount` (number of times received) — hiding the message until the retry time. After a max number of failures (queue redrive policy, `maxReceiveCount`), the message moves to a **dead-letter queue (DLQ)**; we consider the site offline after **5 retries**.

**What if a crawler goes down?** Spin up a new one; ensure the half-finished URL isn't lost:
- **Kafka:** messages stay in the log; offsets aren't advanced until the URL is successfully fetched/processed, so the next crawler resumes where the last left off.
- **SQS:** messages remain until explicitly deleted; visibility timeout hides in-flight messages; if the crawler fails before confirming, the message reappears after the timeout for another crawler. Once HTML is safely in blob storage, the crawler deletes the message. Same logic protects parser workers.

**Decision: SQS** — visibility timeout makes backoff straightforward, built-in DLQ support, managed scaling.

> There's usually no right/wrong technology answer — it's about tradeoffs and justification. Not knowing Kafka/SQS retry internals is fine; just don't choose that as your deep-dive area.

### 2) Politeness and robots.txt

**Politeness** = respecting crawled sites' resources: don't overload servers, respect bandwidth, honor site rules.

**robots.txt** tells crawlers what they may crawl and how often:
```
User-agent: *
Disallow: /private/
Crawl-delay: 10
```
- `User-agent`: which crawler the rules apply to (`*` = all).
- `Disallow`: paths not to crawl.
- `Crawl-delay`: seconds to wait between requests. (Not part of the official standard — Googlebot ignores it — but respecting it is good etiquette and fits our use case.)

Two obligations:
1. **Respect robots.txt** — check before crawling; skip disallowed pages (ack the message); honor Crawl-delay.
2. **Rate limiting** — industry standard: **1 request/second per domain**.

**Handling Crawl-delay** requires state: add a **Domain table** to the Metadata DB storing the last crawl time per domain. If a URL's domain was crawled too recently, use SQS `ChangeMessageVisibility` to extend the visibility timeout and defer the message. (`DelaySeconds` only applies to *new* messages; for in-flight messages use `ChangeMessageVisibility`, extendable up to 12 hours.)

**Race condition:** two crawlers can pull URLs from the same domain simultaneously and both see a stale last-crawl time. Fix: acquire a **per-domain lock atomically** (e.g., Redis `SET NX` with a TTL equal to the crawl delay) before crawling; if the lock can't be acquired, defer via ChangeMessageVisibility.

Steps:
1. Fetch robots.txt for the domain.
2. Parse and store it in the Metadata DB.
3. On pulling a URL, check the stored rules for its domain.
4. Disallowed → ack and move on.
5. Allowed → check Crawl-delay.
6. Delay not yet elapsed → extend visibility timeout, defer.
7. Delay elapsed → crawl and update the domain's last crawl time.

**Global rate limiting:** centralized store (Redis) tracking request counts per domain per second; crawlers check before requesting; **sliding window** algorithm; wait if the limit is exceeded.

**Thundering herd risk:** many crawlers retry simultaneously when the window resets, one wins, repeat. Fix: **jitter** — add a small random delay to each crawler's retry so they don't synchronize.

### 3) Scaling to 10B pages / crawling in under 5 days

> Save scaling discussion for the end of the interview — with the full system in view, you make more informed decisions (e.g., the parser workers only appeared in a later deep dive).

**How many crawler machines?** It's an I/O-intensive task. Estimation:
- AWS network-optimized instance (c6in.32xlarge / c7gn.16xlarge): up to **200 Gbps**.
- 200 Gbps ÷ 8 bits/byte ÷ 2MB/page ≈ **12,500 pages/sec** per machine (theoretical).
- Practical utilization ~30% (server latency, DNS, rate limits, politeness, retries) ⇒ **~3,750 pages/sec**.
- 10B pages ÷ 3,750/sec ≈ 2,666,667 sec ≈ **30.9 days for one machine** ⇒ **~8 machines ≈ 3.9 days** — under the 5-day requirement.

> How can we do thousands of pages/sec while rate-limited to 1 req/sec/domain? We crawl **millions of domains in parallel** — each crawler holds thousands of concurrent connections to different sites; per-domain limits hold while aggregate throughput stays high.

> Lots of assumptions here — in reality you'd load test. In the interview it's less about being right, more about reasoning through the problem.

**Parser workers:** simple task (download HTML from blob storage, extract text, store back). Scale dynamically based on queue depth in the Further Processing Queue — Lambda, ECS on Fargate, or other auto-scaling compute.

**Don't forget DNS!** Often-overlooked bottleneck. At thousands of req/sec across millions of unique domains, resolution matters — the Mercator crawler paper found DNS lookups took up to **70% of each thread's elapsed time** before a custom resolver. Options:
1. **DNS caching** in crawlers — reuse lookups per domain.
2. **Multiple DNS providers**, round-robin — distributes load, avoids provider rate limits. (Suggested by a Staff candidate in a real interview — praised for being practical, breaking out of the "academic answer.")
3. Paying 3rd-party providers for higher rate limits is also an option given the time constraint.

**Efficiency — deduplication:**

- **URL-level dedup:** before enqueueing, check the Metadata DB's URL table; skip if already present. First line of defense.
- **Content-level dedup:** different URLs can serve identical content (example.com vs www.example.com; entirely different domains with identical content). Hash the page content **after fetching** and compare against seen hashes; on match, skip the parsing step.

Two options for content hashing:
- **Great — hash stored in Metadata DB with an index ← preferred:** store the content hash in the URL table; index the hash column for fast lookups. Concern about large index slowing writes is overly pessimistic — modern DBs handle large indexes efficiently.
- **Great — Bloom filter:** probabilistic set membership — definitive "not seen", probabilistic "seen" (small false-positive chance means occasionally skipping an uncrawled page). Redis with the RedisBloom module (`BF.ADD` / `BF.EXISTS`); tune size and hash-function count to reduce false positives.

> Author's take: the Bloom filter is a bit **overkill** — fun to discuss, common in the literature (candidates always bring it up), but the DB-index approach is simpler and more practical.

**Crawler traps:** pages designed to keep crawlers on a site indefinitely (self-linking pages, dense internal link farms). Fix: **maximum depth** — depth = number of **link hops from a seed URL** (seed = 0), *not* URL path segments. Add a `depth` field to the URL table, increment per followed link, stop the branch beyond a threshold (~15–20).

### Additional deep dives to consider on your own
1. **Dynamic content** — JS-framework sites (React/Angular) need a headless browser like Puppeteer to render and extract content.
2. **System health monitoring** — Datadog/New Relic for crawler and parser performance + alerting.
3. **Large files** — send an HTTP `HEAD` request first, check `Content-Length`, skip files over a threshold (say 10MB).
4. **Continual updates** — for re-crawling (monthly retraining, search-engine freshness): add a **URL Scheduler** component; parser workers write URLs to the Metadata DB, and the scheduler decides what to enqueue based on last-crawl time, popularity, etc.
5. **Priority crawling** — multiple SQS queues by priority; crawlers poll high-priority first. Kafka lacks native priority consumption but can approximate with separate topics per priority.

## What is Expected at Each Level?

### Mid-level
- **Breadth over depth (80/20)** — a functional high-level design; many components are surface-level abstractions.
- **Probing the basics** — e.g., if you add a Queue, expect "what does it do / how does it work (high level)?" Nothing taken for granted.
- **Mixture of driving and taking the backseat** — drive early stages; the interviewer may drive later deep dives.
- **The bar for Web Crawler (E4):** understand the high-level data flow and produce a simple system (like the high-level design) that can effectively crawl the web; discuss the basics of politeness and robots.txt; some idea of scaling, but **depth on queueing technologies and rate limiting is not necessarily expected**.

### Senior
- ~60% breadth / 40% depth; technical detail where you have hands-on experience; know how queues and caching work; breeze through basics (REST, normalization) to spend time on the interesting parts.
- Articulate pros/cons of architectural choices; justify tradeoffs.
- Proactive problem-solving: anticipate challenges, address bottlenecks.
- **The bar:** discuss the high-level design, then dive into the details of politeness/robots.txt handling; discuss scaling and how to crawl efficiently within the 5-day window.

### Staff+
- ~40% breadth / 60% depth; experience-backed, practical technology choices; a high degree of proactivity (interviewer intervenes only to focus, not steer); strong decision-making across scalability, performance, reliability, maintenance.
- **The bar:** deep, high-quality solutions in **3+ key areas**; innovative thinking; a good signal is the interviewer coming away having learned something new. Covering all the deep dives above (even partially) puts you in a good spot.

# How to Prepare for System Design Interviews

**Source:** [https://www.hellointerview.com/learn/system-design/in-a-hurry/how-to-prepare](https://www.hellointerview.com/learn/system-design/in-a-hurry/how-to-prepare)

Hello Interview's recommended prep path, distilled from helping thousands of candidates pass FAANG interviews. The core message: build a foundation first, then practice actively — you retain roughly **10x more by doing** than by passively consuming content.

---

## Phase 1: Build a Foundation

1. **Understand what a system design interview is.** If you've never done one, start with the guide's [Introduction](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction) or watch a [mock system design interview video](https://www.youtube.com/watch?v=tgSe27eoBG0) to see the format in action.
2. **Choose a delivery framework.** System design interviews move fast. You need a clear roadmap that helps you think linearly and avoid scope creep. Hello Interview strongly recommends their [Delivery Framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery) — this is the structure you follow on interview day. (See `02_delivery_framework.md`.)
3. **Start with the basics.** Map out the scope of required knowledge by reading, in order:
   - [Core Concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts) — technology-agnostic fundamentals (caching, sharding, CAP, etc.)
   - [Key Technologies](https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies) — the common building blocks (Redis, Kafka, Postgres, etc.)
   - [Common Patterns](https://www.hellointerview.com/learn/system-design/in-a-hurry/patterns) — recurring solution shapes (real-time updates, scaling reads/writes, etc.)

   These write-ups are intentionally high-level; their job is to build the mental model you'll deepen later.

## Phase 2: Practice, Practice, Practice

The recommended loop for each practice question:

1. **Choose a question** from the common-questions list (below).
2. **Read the requirements** of the system you'll need to design.
3. **Try to answer on your own first** — either with Hello Interview's Guided Practice (premium feature) or on a virtual whiteboard like [Excalidraw](https://excalidraw.com/).
4. **Only then read the answer key** and compare your design against it.
5. **Put your knowledge to the test** with a peer mock interview, ideally with someone at your target company. Explaining your design out loud under time pressure is a different skill from reading about it.

---

## Common Interview Questions (with write-ups), by Difficulty

### Easy
| Question | Write-up |
|---|---|
| Bitly (URL shortener) | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly) |
| Dropbox | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox) |
| Yelp | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/yelp) |
| Local Delivery Service (Gopuff) | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/gopuff) |

### Medium
| Question | Write-up |
|---|---|
| Ticketmaster | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/ticketmaster) |
| Instagram | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/instagram) |
| FB News Feed | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed) |
| Tinder | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/tinder) |
| LeetCode | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/leetcode) |
| WhatsApp | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/whatsapp) |
| Strava | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/strava) |
| Distributed Cache | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-cache) |
| Rate Limiter | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter) |
| Online Auction | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-auction) |
| YouTube | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/youtube) |
| Job Scheduler | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler) |
| FB Live Comments | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-live-comments) |
| News Aggregator (Google News) | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-news) |
| Price Tracking Service (CamelCamelCamel) | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/camelcamelcamel) |

### Hard
| Question | Write-up |
|---|---|
| YouTube Top K | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/top-k) |
| Uber | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/uber) |
| Robinhood | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/robinhood) |
| Google Docs | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-docs) |
| Web Crawler | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/web-crawler) |
| Ad Click Aggregator | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/ad-click-aggregator) |
| FB Post Search | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-post-search) |
| Payment System | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/payment-system) |
| Metrics Monitoring | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring) |
| Online Chess | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-chess) |
| ChatGPT | [link](https://www.hellointerview.com/learn/system-design/problem-breakdowns/chatgpt) |

### More Practice (Guided Practice only — no written guide; premium)
Sourced from real interview questions reported by the community, with step-by-step practice and AI feedback:

- Food Review App (Medium)
- Game Leaderboard (Medium)
- Donations Website (Hard)
- GitHub Actions (Hard)
- Notification System (Hard)

> **Premium note:** the interactive "Guided Practice" (with AI feedback and history) is a Hello Interview Premium feature. The written problem breakdowns linked above and the guide chapters are free.

---

## Key Takeaways for a Mid-Level Frontend Engineer

- Don't skip the framework: mid-level candidates most often fail by not finishing a working design, and a fixed structure prevents that.
- Read the high-level chapters once for scope, but spend most of your time solving problems on a whiteboard before reading answer keys.
- Start with Easy problems (Bitly, Dropbox) to internalize the framework, then work up to Mediums that match your target company's question pool.
- Finish with at least one timed mock spoken out loud — verbalizing under pressure is the actual skill being tested.

# Question Breakdowns (System Design in a Hurry)

**Source:** https://www.hellointerview.com/learn/system-design/in-a-hurry/problem-breakdowns

## Overview

This page is a **catalog/index** of Hello Interview's written breakdowns of popular system design questions — 30 fully written problems plus a few practice-only ones. The philosophy: *"The best way to learn is via example."* Each breakdown is written by FAANG staff engineers and senior managers who have asked these questions hundreds of times, and most include a video walkthrough, quiz, and AI-guided practice.

The individual breakdowns are free to read on the site; this index captures the full catalog with difficulty ratings so you can plan a study order.

---

## Easy Problems (4)

| Problem | Company/Analog | Link |
|---|---|---|
| Bitly (URL shortener) | Bitly | https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly |
| Dropbox (file storage/sync) | Dropbox | https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox |
| Yelp (business reviews) | Yelp | https://www.hellointerview.com/learn/system-design/problem-breakdowns/yelp |
| Local Delivery Service | Gopuff | https://www.hellointerview.com/learn/system-design/problem-breakdowns/gopuff |

## Medium Problems (15)

| Problem | Company/Analog | Link |
|---|---|---|
| Ticketmaster (ticket booking) | Ticketmaster | https://www.hellointerview.com/learn/system-design/problem-breakdowns/ticketmaster |
| Instagram (photo sharing) | Instagram | https://www.hellointerview.com/learn/system-design/problem-breakdowns/instagram |
| FB News Feed | Facebook | https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed |
| Tinder (dating/matching) | Tinder | https://www.hellointerview.com/learn/system-design/problem-breakdowns/tinder |
| LeetCode (online judge) | LeetCode | https://www.hellointerview.com/learn/system-design/problem-breakdowns/leetcode |
| WhatsApp (messaging) | WhatsApp | https://www.hellointerview.com/learn/system-design/problem-breakdowns/whatsapp |
| Strava (fitness tracking) | Strava | https://www.hellointerview.com/learn/system-design/problem-breakdowns/strava |
| Distributed Cache | Redis | https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-cache |
| Rate Limiter | — | https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter |
| Online Auction | eBay | https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-auction |
| YouTube (video platform) | YouTube | https://www.hellointerview.com/learn/system-design/problem-breakdowns/youtube |
| Job Scheduler | Apache Airflow | https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler |
| FB Live Comments | Facebook Live | https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-live-comments |
| News Aggregator | Google News | https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-news |
| Price Tracking Service | CamelCamelCamel | https://www.hellointerview.com/learn/system-design/problem-breakdowns/camelcamelcamel |

## Hard Problems (11)

| Problem | Company/Analog | Link |
|---|---|---|
| YouTube Top K (top-K videos) | YouTube | https://www.hellointerview.com/learn/system-design/problem-breakdowns/top-k |
| Uber (ride sharing) | Uber | https://www.hellointerview.com/learn/system-design/problem-breakdowns/uber |
| Robinhood (stock trading) | Robinhood | https://www.hellointerview.com/learn/system-design/problem-breakdowns/robinhood |
| Google Docs (collaborative editing) | Google Drive | https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-docs |
| Web Crawler | Google | https://www.hellointerview.com/learn/system-design/problem-breakdowns/web-crawler |
| Ad Click Aggregator | Google AdSense | https://www.hellointerview.com/learn/system-design/problem-breakdowns/ad-click-aggregator |
| FB Post Search | Facebook | https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-post-search |
| Payment System | Stripe | https://www.hellointerview.com/learn/system-design/problem-breakdowns/payment-system |
| Metrics Monitoring | Datadog | https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring |
| Online Chess | Lichess | https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-chess |
| ChatGPT (LLM chat app) | OpenAI | https://www.hellointerview.com/learn/system-design/problem-breakdowns/chatgpt |

## More Practice (no written breakdown yet — AI-guided practice only)

| Problem | Company/Analog | Difficulty |
|---|---|---|
| Food Review App | Trustpilot | Medium |
| Game Leaderboard | Steam | Medium |
| Donations Website | GoFundMe | Hard |
| GitHub Actions | GitHub Actions | Hard |
| Notification System | Twilio | Hard |

---

## Suggested Study Mapping (patterns → problems)

Based on how the guide's Common Patterns page references these breakdowns:

- **Realtime Updates:** WhatsApp (pub/sub), Google Docs (stateful servers in a consistent hash ring), FB Live Comments, Online Chess.
- **Long-Running Tasks:** YouTube (transcoding), LeetCode (code execution), Job Scheduler, Web Crawler.
- **Dealing with Contention:** Ticketmaster (last ticket), Online Auction (bidding), Robinhood.
- **Scaling Reads:** FB News Feed, Instagram, News Aggregator.
- **Scaling Writes:** Ad Click Aggregator, Metrics Monitoring, YouTube Top K.
- **Large Blobs:** YouTube, Dropbox, Instagram.
- **Multi-Step Processes:** Payment System, Job Scheduler.
- **Proximity-Based Services:** Uber, Gopuff (Local Delivery), Yelp, Tinder, Strava.

## Notes on Access

- The index page and the individual written breakdowns listed above are free.
- Premium features on the site include guided practice, quizzes, and exclusive/recent interview question content — not required for reading the breakdowns themselves.

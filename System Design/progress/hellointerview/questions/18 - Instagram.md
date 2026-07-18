# 18 - Instagram (Photo Sharing App)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/instagram

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section (functional requirements + scale context) is freely visible. The Core Entities, API, High-Level Design, all three Deep Dives, and the level expectations (Mid/Senior/Staff+) are behind the Hello Interview Premium paywall. Locked section headings are listed below.

- **Difficulty:** Medium
- **Pattern tags:** Scaling Reads · Managing Long Running Tasks · Handling Large Blobs
- **Author:** Evan King

## Understanding the Problem

**What is Instagram?** Instagram is a social media platform primarily focused on visual content, allowing users to share photos and videos with their followers.

Designing Instagram is one of the most common system design interview questions — not just at Meta, but across all FAANG and FAANG-adjacent companies. The breakdown notes it shares a lot with the **FB News Feed** and **Dropbox** breakdowns (feed fan-out + large file upload/delivery respectively).

### Functional Requirements

**Core requirements:**

1. Users should be able to **create posts** featuring photos, videos, and a simple caption.
2. Users should be able to **follow** other users.
3. Users should be able to see a **chronological feed** of posts from the users they follow.

**Below the line (out of scope):**

- Likes and comments on posts.
- Search for users, hashtags, or locations.
- Stories (ephemeral content).
- Going live (real-time video streaming).

### Non-Functional Requirements

The visible text emphasizes: before defining non-functional requirements, **ask about the scale of the system** — it meaningfully impacts the design. For this problem the stated scale is:

- **500M DAU**
- **100M posts per day**

The specific core non-functional requirement list itself is locked, but the deep-dive titles (visible) reveal the three that drive the design:

1. Deliver feed content with **low latency (< 500ms)**.
2. **Render photos and videos instantly**, supporting photos up to **8MB** and videos up to **4GB**.
3. **Scalable to support 500M DAU**.

General tip repeated in the breakdown: most systems are fault tolerant/scalable/etc. — identify the unique characteristics that make *this* system challenging (huge read-heavy feed traffic + very large media blobs).

## Structure of the Full Breakdown (🔒 premium-locked sections)

- **The Set Up**
  - Defining the Core Entities 🔒
  - API or System Interface 🔒
- **High-Level Design** 🔒
  1. Users should be able to create posts featuring photos, videos, and a simple caption
  2. Users should be able to follow other users
  3. Users should be able to see a chronological feed of posts from the users they follow
- **Potential Deep Dives** 🔒
  1. The system should deliver feed content with low latency (< 500ms)
  2. The system should render photos and videos instantly, supporting photos up to 8MB and videos up to 4GB
  3. The system should be scalable to support 500M DAU
- **What is Expected at Each Level?** 🔒 (Mid-level / Senior / Staff+ subsections exist but content is locked)

## Study Hints (inferred from tags and cross-references, not the locked text)

- Tagged **Scaling Reads**: the feed deep dive almost certainly covers **fan-out on write (precomputed feeds) vs. fan-out on read**, hybrid approaches for celebrity accounts, and heavy caching — the same territory as the (free) FB News Feed breakdown the article explicitly says it resembles.
- Tagged **Handling Large Blobs**: expect **direct-to-blob-storage uploads via presigned URLs**, multipart/chunked upload for 4GB videos, and **CDN delivery** with multiple transcoded/resized variants — territory shared with the Dropbox breakdown it references.
- Tagged **Managing Long Running Tasks**: expect **async media processing pipelines** (transcoding, thumbnail generation) via queues/workers after upload.

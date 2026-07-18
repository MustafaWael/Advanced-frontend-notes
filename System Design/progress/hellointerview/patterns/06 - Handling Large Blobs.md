# 06 - Handling Large Blobs

**Source:** https://www.hellointerview.com/learn/system-design/patterns/large-blobs

> **⚠️ Premium-locked page.** Only the introduction and "The Problem" section were freely visible. All detailed sections (marked 🔒 below) require Hello Interview Premium and are not reproduced here.

---

## What the Pattern Is

Large files — videos, images, documents — need special handling in distributed systems. Instead of shoving gigabytes through your application servers, this pattern uses **presigned URLs** so clients:

- **upload directly to blob storage** (e.g., S3), and
- **download directly from CDNs**.

The pattern also covers **resumable uploads, parallel transfers, and progress tracking** — "the stuff that separates real systems from toy projects."

## The Problem It Solves (free content)

**Why blob storage instead of a database?**
- Databases excel at structured data with complex queries, but are terrible with large binary objects.
- A 100MB file stored as a BLOB kills **query performance, backup times, and replication**.
- Object stores like S3 are purpose-built: **unlimited capacity, 99.999999999% (11 nines) durability, per-object pricing**.
- **Rule of thumb from the article: if it's over ~10MB and doesn't need SQL queries, it probably belongs in blob storage.**
- Separating blobs into object storage lets storage scale independently from compute and keeps database performance snappy.

**But blob storage alone doesn't solve data transfer.** The naive approach routes file bytes through application servers ("server as a proxy"):
- Client uploads a 2GB video → API server receives it → API server forwards it to blob storage.
- Downloads reverse the path: blob storage → API server → client.
- This works for small files but **breaks down as files get bigger** — the app servers become a bandwidth/memory/connection bottleneck for traffic they add no value to.

The solution direction (from the intro): cut the app server out of the data path with **presigned upload URLs** and **CDN-backed download URLs**; the server only handles metadata and authorization.

## Article Structure (🔒 = premium-locked detail)

- The Problem *(free — summarized above)*
- 🔒 The Solution
  - 🔒 Simple Direct Upload (presigned URL upload flow)
  - 🔒 Simple Direct Download (CDN / presigned download flow)
  - 🔒 Resumable Uploads for Large Files (chunking / multipart)
  - 🔒 State Synchronization Challenges (keeping DB metadata in sync with blob storage state)
  - 🔒 Cloud Provider Terminology (S3 vs GCS vs Azure equivalents)
- 🔒 When to Use in Interviews
  - 🔒 Common interview scenarios
  - 🔒 When NOT to use it in an interview
- 🔒 Common Deep Dives
  - 🔒 "What if the upload fails at 99%?"
  - 🔒 "How do you prevent abuse?"
  - 🔒 "How do you handle metadata?"
  - 🔒 "How do you ensure downloads are fast?"
- 🔒 Conclusion

## Interview Problems Where This Pattern Applies

The page doesn't expose an explicit free list, but the pattern is central to these Hello Interview breakdowns (file upload/download-heavy systems):

- **Dropbox** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox
- **YouTube** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/youtube
- **Instagram** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/instagram

## Key Takeaways from the Free Content

1. Blobs > ~10MB with no SQL-query need → blob storage, not the database.
2. Storing in S3 isn't enough — you must also fix the **transfer path**; don't proxy file bytes through app servers.
3. Presigned URLs (upload) + CDN (download) keep app servers in the control plane only.
4. Expect interview deep dives on: partial-upload failure (resume), abuse prevention, metadata consistency between DB and blob store, and download latency.

## Locked Sections — Study Gaps to Fill Elsewhere

Premium content covers (per the outline): the exact presigned upload/download flows, chunked/multipart resumable uploads, keeping metadata state in sync when uploads happen out-of-band, cloud-provider terminology mapping, when (not) to use the pattern in interviews, and the four deep-dive answers. These details are **not** captured here because they are premium-only.

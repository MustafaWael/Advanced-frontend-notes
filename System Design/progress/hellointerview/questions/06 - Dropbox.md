# 06 - Design a File Storage Service Like Dropbox

**Source:** [hellointerview.com/learn/system-design/problem-breakdowns/dropbox](https://www.hellointerview.com/learn/system-design/problem-breakdowns/dropbox)
**Difficulty:** Easy · **Pattern:** Handling Large Blobs · **Author:** Evan King

## Understanding the Problem

Dropbox is a cloud-based file storage service that lets users store and share files, with secure, reliable access from anywhere on any device.

Note: designing Blob Storage *itself* is a related but separate problem — out of scope here, worth researching on your own.

## Functional Requirements

**Core:**
1. Users should be able to upload a file from any device.
2. Users should be able to download a file from any device.
3. Users should be able to share a file with other users and view files shared with them.
4. Users can automatically sync files across devices.

**Below the line (out of scope):**
- Editing files.
- Viewing files without downloading them.

## Non-Functional Requirements

**Core:**
1. **Highly available** (availability over consistency).
2. Support files as large as **50GB**.
3. Secure and reliable — recover files if lost or corrupted.
4. Upload, download, and sync as **fast as possible** (low latency).

**Below the line:** storage limit per user; file versioning; virus/malware scanning.

> CAP tip: prioritize consistency only when every read *must* see the latest write (e.g. stock trading). For Dropbox, it's fine if a file uploaded in Germany takes a few seconds to appear for a US user → choose availability.

## Planning the Approach

Product-design style question: build up sequentially through the functional requirements one by one, then use the non-functional requirements to guide the deep dives.

## Core Entities

1. **File** — the raw data users upload/download/share.
2. **FileMetadata** — name, size, mime type, uploader, etc.
3. **User** — the user of the system.

## API Design

Initial simple endpoints (say "I may come back and improve these" — the upload/download APIs evolve significantly later):

```
POST /files
Request: { File, FileMetadata }              // upload

GET /files/{fileId} -> File & FileMetadata   // download

POST /files/{fileId}/share
Request: { User[] }                          // share with users

GET /files/changes?since={timestamp} -> ChangeEvent[]   // sync: changes since last sync
```

Each `ChangeEvent` includes the fileId, change type (created/updated/deleted), and updated metadata.

User info goes in **headers** (session token/JWT), never the request body — the body is client-manipulable.

## High-Level Design

### 1) Upload a file from any device

Two questions: where do the raw bytes go, and where does metadata go?

**Metadata:** NoSQL like **DynamoDB** (loosely structured, few relations, main query = files by user). PostgreSQL would work just as well — don't get hung up on the choice.

```
{ "id": "123", "name": "file.txt", "size": 1000,
  "mimeType": "text/plain", "uploadedBy": "user1" }
```

**File bytes:**

**Bad: upload to a single server** — store on the File Service's local filesystem. Doesn't scale (ever-growing storage), unreliable (server dies → files gone).

**Good: store in Blob Storage (S3/GCS)** — backend receives the file and forwards to blob storage; metadata to the DB. Virtually unlimited, reliable, lifecycle policies, versioning. *Challenges:* file/metadata consistency handling, and the file is **uploaded twice** (client→backend, backend→S3) — redundant.

**Great: upload directly to Blob Storage via presigned URLs** ✅ — faster and cheaper. Three-step flow:
1. `POST /files/presigned-url` with FileMetadata → backend generates a presigned URL (S3 SDK) and saves metadata with status **"uploading"**.
2. Client **PUTs the file directly to S3** via the presigned URL.
3. **S3 event notification** tells the backend the upload finished → metadata status updated to **"uploaded"**.

**Pattern — Handling Large Blobs:** bypass application servers for data transfer, use signed URLs for security, chunk uploads for reliability.

### 2) Download a file from any device

**Bad: download through the file server** — S3→backend→client downloads the file twice; slow and expensive.

**Good: download directly from Blob Storage** — `GET /files/{fileId}/presigned-url` → client downloads straight from S3 with a time-limited presigned URL. *Limit:* single-region S3 is slow for far-away users.

**Great: download from a CDN** ✅ — CDN (e.g. CloudFront) caches files at edge servers near users; backend issues **CDN signed URLs** (time-limited, permissioned). *Challenge:* CDNs are expensive — use cache-control headers, cache only hot files, and invalidate on update/delete.

### 3) Share a file with other users

Share by email address (like Google Drive); users are authenticated. Key concern: making "list all files shared with me" fast.

**Bad: sharelist inside file metadata** — `"sharelist": ["user2","user3"]`. Sharing and per-file access checks are easy, but "files shared with me" requires scanning every file's sharelist — slow.

**Good: cache the inverse mapping** — keep the sharelist plus a cached `userId → [fileIds shared with them]`. Fast lookup. *Challenge:* keeping both in sync (use same DB + transaction).

**Great: separate normalized SharedFiles table** ✅
```
| userId (Partition Key) | fileId (Sort Key) |
| user1                  | fileId1           |
| user1                  | fileId2           |
| user2                  | fileId3           |
```
Composite key (DynamoDB: userId partition + fileId sort; SQL: composite PK). No sharelist in metadata to keep in sync. *Tradeoff:* index query instead of a single KV lookup — slightly less efficient, usually worth it.

### 4) Automatically sync files across devices

Copies live locally on each device and remotely (the cloud = **source of truth**). Two directions:

**Local → Remote:** client-side **sync agent** that:
1. Monitors the local Dropbox folder via OS file-system events (FileSystemWatcher on Windows, FSEvents on macOS).
2. Queues changed files for upload.
3. Uses the upload API to push changes + metadata.
4. Conflict resolution: **last write wins**. (Versioning out of scope; in reality you'd add new files/chunks and bump a version pointer, not overwrite.)

**Remote → Local:** two base options — **polling** (`GET /files/changes?since=...`; simple, but slow to detect and wasteful) or **WebSocket/SSE push** (real-time but more complex). **Use a hybrid** ✅:
- One WebSocket/SSE connection **per device/session** (not per file); server pushes change events in real time.
- **Periodic polling as a safety net** (every few minutes) via `GET /files/changes?since={timestamp}` to catch missed events when connections drop → eventual consistency guaranteed.

### Tying it all together — components

- **Uploader / Downloader clients** — browser/mobile/desktop; detect local changes, pull remote changes.
- **LB & API Gateway** — routing, SSL termination, rate limiting, request validation.
- **File Service** — control plane: reads/writes metadata, generates presigned URLs (a purely local cryptographic signing operation — no S3 call). Never touches file bytes.
- **File Metadata DB** — file metadata + SharedFiles table (also enforces download permissions).
- **S3** — actual file storage, uploaded directly via presigned URLs.
- **CDN (CloudFront)** — serves downloads via signed URLs from the nearest edge; fetches from S3 on cache miss.

## Deep Dives

### 1) How can you support large files (50GB)?

This is "the meat of the problem" where interviews spend the most time. UX drives the design:
1. **Progress indicator** during upload.
2. **Resumable uploads** — pick up where you left off, not re-upload 49GB.

Why a single POST fails:
- **Timeouts** — 50GB over 100Mbps = 50GB × 8 / 100Mbps ≈ 4000s ≈ **1.11 hours**; exceeds server/client timeouts.
- **Payload limits** — browsers/servers cap request size; Amazon API Gateway hard-caps at **10MB**.
- **Network interruptions** — one drop = start over.
- **UX** — no visibility into progress.

**Solution: chunking on the client** (a very common mistake is chunking on the *server*, which defeats the purpose). Break into **5–10MB chunks**, upload sequentially or in parallel. Progress = chunks completed.

**Resumability:** track chunk state in FileMetadata:
```
{ "id": "123", ..., "status": "uploading",
  "chunks": [
    { "id": "chunk1", "status": "uploaded" },
    { "id": "chunk2", "status": "uploading" },
    { "id": "chunk3", "status": "not-uploaded" } ] }
```

**Keeping the chunks field in sync with reality:**

**Good: client PATCH updates** — client uploads chunk to S3, then `PATCH /files/{fileId}/chunks` marks it uploaded. *Risk:* trusting the client — a malicious client could mark chunks uploaded without uploading (only corrupts their own file, but creates inconsistent, hard-to-debug state).

**Great: server-side chunk verification via ETags** ✅ — S3 event notifications don't fire per multipart part, so: each uploaded chunk returns an **ETag**; the client includes it in the PATCH; the backend verifies via S3's **ListParts** API. Accept client updates for real-time progress, but **verify server-side before marking the file "uploaded"** — *trust but verify*.

**Identifying files/chunks — fingerprints:** don't rely on filename (collisions). A **fingerprint** is a content-derived hash (e.g. SHA-256) — unique per content. Compute for the whole file (dedup + resume check) *and* per chunk (know exactly which parts were sent). Note: the fingerprint identifies *content*, not the record — fileId stays a UUID; fingerprint is a separate field.

**Full large-upload flow:**
1. Client chunks the file (5–10MB), fingerprints each chunk and the whole file.
2. Client asks if a file with that fingerprint exists for this user; if status "uploading", resume from existing chunk statuses.
3. Otherwise, backend calls S3 **CreateMultipartUpload** → uploadId; generates presigned URLs per part; saves metadata status "uploading"; returns uploadId + URLs.
4. Client uploads each chunk to its presigned URL (each part needs its own URL with uploadId + partNumber); after each, PATCHes status + ETag; backend verifies via ListParts.
5. When all chunks are "uploaded", backend calls S3 **CompleteMultipartUpload** with part numbers + ETags; only after S3 confirms assembly does metadata flip to "uploaded".

This is exactly **S3 Multipart Upload** — mention you know it (shows hands-on experience), but be able to explain how you'd implement it yourself; "I'd use the S3 API" alone won't fly.

**Downloads don't need chunking:** after CompleteMultipartUpload, S3 has one object; a single presigned/CDN URL suffices. For very large files, HTTP **Range requests** allow parallel/resumable downloads without knowing original chunk boundaries.

### 2) Making uploads, downloads, and syncing as fast as possible

- **Downloads:** CDN edge caching (recap).
- **Uploads:** chunking maximizes fixed bandwidth via **parallel chunk uploads** and **adaptive chunk sizes** based on network conditions.
- **Sync:** only sync the chunks that changed (delta sync), not the whole file.
- **Fixed-size chunk pitfall:** inserting one byte early shifts every later boundary → every subsequent chunk fingerprint changes → delta sync useless. Fix: **Content-Defined Chunking (CDC)** — boundaries determined by content via a rolling hash (Rabin fingerprinting); a small edit only affects nearby chunks. This is how Dropbox actually does efficient delta sync.
- **Compression (client-side):** compress before uploading directly to S3; decompress after download — backend stays out of the data path. Only worth it when transfer savings beat compress/decompress time: great for text (5GB → 1GB possible), useless for already-compressed media (png/video, a few %). Client logic decides based on file type, size, network conditions.
- Algorithms: **Gzip** (ubiquitous), **Brotli** (better ratios for text, all modern browsers), **Zstandard** (excellent speed/ratio balance, tunable — strong choice for client-side compression).
- **Always compress before encrypting** — encryption's randomness makes data incompressible.

### 3) How can you ensure file security?

1. **Encryption in transit** — HTTPS.
2. **Encryption at rest** — S3 server-side encryption; per-file keys stored separately from files.
3. **Access control** — the SharedFiles table is the ACL; download links only for authorized users.
4. **Leaked-link problem:** what if an authorized user posts a link publicly? **Signed URLs valid ~5 minutes**. Caveat: signed URLs are *bearer tokens* — anyone with an unexpired URL can download; short expiry limits exposure but doesn't prevent sharing. Higher security: IP binding, or require auth cookies alongside.
5. **CDN signed-URL mechanics (CloudFront):** (a) server generates URL with signature over path + expiration (+ optional restrictions like IP) using a private key; (b) URL distributed to the authorized user; (c) CDN verifies signature with the registered public key + checks expiry; serves or denies.

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; components may be surface-level abstractions.
- Interviewer probes basics (e.g. what the API Gateway does); nothing taken for granted.
- You drive early; interviewer may drive later deep dives.
- **Bar for Dropbox:** clearly defined API endpoints and data model; a functional high-level design for uploading, downloading, and sharing. **Not expected** to know presigned URLs, direct-to-S3 upload/download, or chunking up front — but when probed ("you're uploading the file twice, how can we avoid that?", "how do you show progress and allow resume?") you should reason to a solution through back-and-forth.

### Senior (E5)
- ~60% breadth / 40% depth; blob storage for large files, CDN for fast downloads; justify trade-offs.
- **Bar:** move quickly through the high-level design; spend time on **large file uploads** in particular, proactively working through options; many candidates can speak to multipart upload APIs directly.

### Staff+
- ~40% breadth / 60% depth; experience-backed, highly proactive; treat the interviewer as a peer.
- **Bar:** deep on all the above topics, may steer toward a particularly interesting area; solid command of trade-offs between solutions.

## Key Takeaways for Mid-Level Prep

- **Availability over consistency** — know the CAP reasoning (contrast with stock trading).
- Presigned URLs: client uploads/downloads **directly to/from S3**; the File Service is only the control plane; CDN signed URLs for downloads.
- Large files = **client-side chunking** (5–10MB) + multipart upload + chunk state in metadata + ETag/ListParts verification ("trust but verify") + content **fingerprints** for dedup/resume.
- Sharing: normalized **SharedFiles(userId, fileId)** table beats an embedded sharelist.
- Sync: local watcher + last-write-wins; remote via **WebSocket push with polling fallback**; delta sync needs **content-defined chunking**; compress (text only) before encrypt.

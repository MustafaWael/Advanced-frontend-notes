# 09 - YouTube (Video Streaming Platform)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/youtube
**Author:** Evan King · Difficulty: **Medium** · Patterns: **Handling Large Blobs**, **Scaling Reads**

> YouTube is a video-sharing platform that allows users to upload, view, and interact with video content — the second most visited website in the world. There's heavy conceptual overlap with the Dropbox breakdown (file upload/download); read that first if unfamiliar.

---

## 1. Understand the Problem

### Functional Requirements

**Core:**
1. Users can upload videos.
2. Users can watch (stream) videos.

**Below the line (out of scope):**
- View info about a video (view counts)
- Search for videos
- Comment on videos
- Recommended videos
- Channels (create/manage)
- Subscribe to channels

> For feature-rich apps like YouTube, briefly negotiate with the interviewer to find which part of the system they care most about.

### Non-Functional Requirements

**Core:**
1. Highly available (prioritize **availability over consistency**).
2. Support uploading and streaming **large videos (10s of GBs)**.
3. **Low latency streaming**, even in low-bandwidth environments.
4. Scale to **~1M videos uploaded/day, 100M videos watched/day**.
5. Support **resumable uploads**.

**Below the line:** bad-content protection, bot/fake-account protection, monitoring/alerting.

> With only two functional requirements, the non-functional requirements are what characterize the real complexity of "upload" and "watch" — they deeply affect the design. Enumerate them carefully.

---

## 2. The Set Up

### Planning the Approach
Build the design up sequentially, one functional requirement at a time. Then use non-functional requirements to guide deep dives.

### Core Entities
1. **User** — uploader or viewer.
2. **Video** — the video that is uploaded/watched (the actual data).
3. **VideoMetadata** — metadata: uploading user, URL reference to transcript, format/segment references, etc.

### API Design

Upload (initial version):
```
POST /upload
Request: { Video, VideoMetadata }
```

Stream/watch (initial version):
```
GET /videos/{videoId} -> Video & VideoMetadata
```

> APIs may evolve as the design progresses — say so proactively: "I'll outline simple APIs but may come back and improve them as we delve deeper." Here both APIs change significantly:
> - Upload becomes `POST /presigned_url` (metadata only; video goes directly to S3).
> - `GET /videos/{videoId}` returns **just VideoMetadata**, which contains the S3/manifest URLs needed to stream.

---

## 3. High-Level Design

### Background: Video Streaming Fundamentals
You don't need to be a video expert, but know these at a high level:

- **Video codec** — compresses/decompresses digital video ("encoder/decoder"). Trades off: compression time, platform support, compression efficiency, and quality (lossy or not). Popular: H.264, H.265 (HEVC), VP9, AV1, MPEG-2, MPEG-4.
- **Video container** — file format storing video data (frames, audio) plus metadata (e.g., transcripts). Codec = how it's compressed; container = how it's stored. Container support varies by device/OS.
- **Bitrate** — bits transmitted per unit time (kbps/Mbps). Higher resolution + framerate = higher bitrate; better compression lowers it.
- **Manifest files** — text documents describing video streams. A **primary** manifest lists all available versions (formats) of a video and points to **media** manifests; each media manifest indexes the URLs of the small segment files (a few seconds each) for one version. Video players use them as an "index" for streaming.

"Video format" below = container + codec combination.

### Requirement 1: Users can upload videos

Three fundamental questions: where to store metadata, where to store video data, and *what* to store for video data.

**Metadata storage:** ~1M uploads/day → ~365M records/year. Use a horizontally partitionable DB like **Cassandra** (high availability, choose your partition key). **Partition on `videoId`** — we only do point lookups by videoId, no bulk access patterns.

> When designing storage that must scale, think about partitioning. Some systems need consistency within a domain (relational DB sharded by that domain, e.g., Ticketmaster by concert ID). This system doesn't need careful partitioning — videoId point lookups only.

**Video data upload:** Same as Dropbox — most efficient to upload **directly to blob storage (S3) via a presigned URL with multipart upload**, bypassing application servers entirely.

> **Pattern: Handling Large Blobs.** Multi-GB files bypass app servers using presigned URLs for direct S3 upload, with resumable chunked transfers and CDN distribution. Same pattern for photo storage, document sharing, backups. This changes the API: `POST /upload` → `POST /presigned_url` (payload = metadata only).

**What do we store for video data?** (tradeoff ladder)

- **Bad: Store the raw video.** No post-processing. Doesn't work — different devices need different formats for playback.
- **Good: Store different video formats.** On S3 upload, an event notification triggers a video processing service that transcodes the original into multiple formats, stores each in S3, and updates VideoMetadata with the URLs. *Challenge:* whole-file storage means the client can't download "part" of a video — which is essential for streaming.
- **Great: Store different video formats *as segments*.** Post-processing splits the video into small segments (each a playable unit, a few seconds long), then converts each segment into multiple formats. Strictly better — enables efficient streaming. *Challenge:* the post-processing service becomes a "pipeline" (split → transcode per segment), and the system must store/track segment references sanely for the streaming flow — a key deep-dive topic.

### Requirement 2: Users can watch videos

Client first fetches VideoMetadata (`GET /videos/{videoId}` now returns metadata only, containing the URLs needed to watch).

- **Bad: Download the full video file.** Not really streaming. A 10GB video takes 13+ minutes at 100 Mbps; a single HTTP request that fails mid-way loses all progress. Not viable.
- **Good: Download segments incrementally.** Client picks a format (based on device/bandwidth/preference), loads the first few-second segment to start playback fast, and loads more in the background. *Challenges:* depends on segment storage; doesn't adapt to fluctuating network conditions mid-watch — 1080p segments on a degrading network cause buffering.
  > Segment download is distinct from (and strictly better than) naive chunked download of a whole file: not all formats are playable from partial byte-ranges, whereas segments are guaranteed playable units.
- **Great: Adaptive bitrate streaming.** Requires segments stored in different formats plus a **manifest file** created at upload time. Client logic:
  1. Fetch VideoMetadata → URL of manifest file in S3.
  2. Download the manifest.
  3. Choose a format based on network conditions/settings; get the first segment's URL from the manifest; download it.
  4. Play it while downloading more segments.
  5. If network conditions worsen (or improve), switch to lower-resolution/more-compressed (or higher-quality) segment formats to avoid interruption.

  *Challenge:* most complex; the client is an active participant (not a bad thing); relies on upstream decisions (segmenting, multi-format storage, manifest creation).

---

## 4. Deep Dives

### Deep Dive 1: How to process a video to support adaptive bitrate streaming?

Post-processing pipeline output:
1. Segment files in different formats (codec + container combos) in S3.
2. Manifest files (primary + media manifests) in S3, referencing the segments.

Stepwise operations:
1. **Split** the original file into segments (e.g., with ffmpeg).
2. **Transcode** each segment (and process audio, generate transcripts).
3. **Create manifest files** referencing the segments in each format.
4. Mark upload as **complete**.

Key ideas:
- This is a **DAG of work**: fan-out/fan-in with one-way dependencies. Segment-level work (transcoding, audio, transcription) parallelizes across worker nodes since segments are independent.
- **Transcoding is the most expensive (CPU-bound) step** — run with extreme parallelism across many machines/cores.
- Use an **orchestrator** (e.g., Temporal) to build the work graph and assign workers at the right time.
- Store temporary artifacts (segments, audio files) in **S3** and pass URLs between workers, not files.

> You don't need to draw an exact DAG; what matters is diving into inputs/outputs of post-processing and showing how to do it scalably and efficiently. Note: this design uploads the full original first; some services pipeline processing while the client uploads segments — a speed optimization skipped here for simplicity.

### Deep Dive 2: How do we support resumable uploads?

Track progress of the *original* upload (strong overlap with Dropbox's large-file deep dive):

1. Client divides the video into chunks (~5–10MB), each with a **fingerprint hash**.
2. VideoMetadata gets a `chunks` field: list of `{ fingerprint, status }`.
3. Client POSTs to backend to record chunks with status `NotUploaded`.
4. Client uploads each chunk to S3.
5. When S3 acknowledges a part it returns part number + ETag; client relays to backend (e.g., `PATCH /videos/{id}/chunks`), which verifies fingerprint/ETag via S3 APIs and marks the chunk `Uploaded`.
6. On `CompleteMultipartUpload`, S3 emits one object-level notification (`ObjectCreated:CompleteMultipartUpload`) that kicks off downstream processing; chunk-level progress stays client-driven.
7. To resume, the client fetches VideoMetadata and skips already-uploaded chunks.

> In practice this is **AWS multipart upload**, but walking through the details shows depth of understanding of how file uploads actually work.

### Deep Dive 3: How do we scale to ~1M uploads / 100M watches per day?

Component-by-component analysis:
- **Video Service** — stateless (presigned URLs + metadata point queries); horizontally scale behind a load balancer.
- **Video Metadata (Cassandra)** — scales horizontally via leaderless replication + consistent hashing; uniform distribution partitioned by videoId. *Risk:* a node with a **popular ("hot") video** can become a bottleneck.
- **Video Processing Service** — scales via internal queuing (absorbs upload bursts); queue depth can trigger elastic scaling of workers.
- **S3** — scales extremely well; a bucket lives in one region (replicated across AZs). *Risk:* users far from the region see slow initial loads/buffering; needs cross-region replication or a CDN.

Improvements ("great" choices):
- **Hot video metadata:** tune Cassandra to replicate metadata across several nodes to share read load, and add a **distributed cache** (LRU, partitioned by videoId) for popular video metadata — faster reads, insulates the DB.
- **Geo latency:** use **CDNs** to cache popular video files — both **segments and manifest files** — at edge servers near users. If everything is in the CDN, streaming never touches the backend at all.

> **Pattern: Scaling Reads.** Extreme read-to-write ratio (a viral video: uploaded once, watched millions of times) → aggressive metadata caching, CDN for content, read replicas.

### Additional deep dives to consider
1. **Speeding up uploads** — pipeline upload + post-processing: the client segments the video and uploads segments; backend processes them immediately. Risks "garbage" segments on abandoned uploads, but improves average upload experience.
2. **Resume streaming where the user left off** — store per-user, per-video playback position.
3. **View counts** — exact vs. estimated counting; can be its own dedicated deep dive.

---

## 5. What is Expected at Each Level?

### Mid-level
- **Breadth over depth (80/20).** High-level design meeting functional requirements; many components may be surface-level abstractions.
- Interviewer probes basics (e.g., "what does the API Gateway do?") — nothing is taken for granted.
- Drive the early stages; interviewer may take over and drive later stages.
- **Bar for YouTube:** clearly defined API endpoints and data model; a functional high-level design for upload/playback. Deep video-streaming knowledge is NOT expected, but you should converge on **multipart upload** and **segment-based streaming**, understand the need to interface **directly with S3** for upload/streaming, and drive clarity on **one** relevant deep-dive topic.

### Senior
- **60% breadth / 40% depth**; technical detail where you have hands-on experience; articulate pros/cons and tradeoffs; proactive problem-solving.
- **Bar for YouTube:** move quickly through the high-level design to spend time on **video post-processing details and upload handling**. Expected to know multipart upload for resumable uploads and how videos are post-processed efficiently to enable adaptive streaming.

### Staff+
- **40% breadth / 60% depth**; experience-backed practical technology choices; exceptional proactivity (interviewer intervenes only to focus, not steer); may steer deep into a topic of interest; articulates tradeoffs like a peer.

---

## Key Takeaways (study notes)
- Two deceptively simple requirements; the NFRs (large files, low-latency adaptive streaming, resumability, scale) carry the complexity.
- Presigned URL + multipart upload directly to S3 = the Large Blobs pattern; app servers never touch video bytes.
- Store video as **segments in multiple formats + manifest files** → enables adaptive bitrate streaming.
- Post-processing is a **DAG** (split → parallel transcode → manifests) run by an orchestrator like Temporal; transcoding is the CPU-bound hot spot.
- Scale reads with **Cassandra partitioned by videoId + distributed LRU cache + CDN (segments AND manifests)**.

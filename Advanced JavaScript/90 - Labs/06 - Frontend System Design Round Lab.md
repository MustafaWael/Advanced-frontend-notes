---
tags: [labs, system-design, radio, interview, frontend]
module: "90 - Labs"
priority: important
status: not-started
aliases: [design round lab, RADIO lab, frontend system design lab]
---

# Lab 06 — Frontend System Design Round Lab

A different lab format: there's no repo and no code to ship. You rehearse the **frontend design interview** itself — a timed [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]] walkthrough delivered out loud, then graded against a hidden model outline. The skill being trained is *structure and coverage under a clock*: naming requirements before drawing boxes, choosing a data model and APIs deliberately, and ranking optimizations by requirement — without forgetting races, caching, a11y, or failure states.

Read [[29 - Frontend System Design/01 - The Frontend System Design Framework|the framework]] and skim [[29 - Frontend System Design/03 - Frontend System Design Checklist|the checklist]] first if RADIO isn't yet muscle memory.

## How to Work This Lab

1. Pick one prompt (below). **Do not read the model outline first.**
2. Set a **40-minute timer** and talk (or whiteboard) the whole round out loud — record yourself if you can. Use the phase budget so you don't sink 30 minutes into architecture and skip optimizations.
3. Produce all five RADIO phases: **R**equirements → **A**rchitecture → **D**ata model → **I**nterface (component + network APIs) → **O**ptimizations, closing with the tradeoffs you deferred.
4. Only then open the model outline and the self-grade rubric. Score honestly.
5. Write a short retrospective ([[98 - Vault Operations/Templates/Lab Retrospective Template|template]]): which phase you rushed, what you forgot, and the one axis to drill next time.

> [!tip] The clock is the lab. Most failures aren't ignorance — they're spending 25 minutes on requirements/architecture and never reaching optimizations or a11y. Practicing the *allocation* is the point.

### Phase budget (40 min)

| Phase | Minutes | You must produce |
| --- | --- | --- |
| Requirements | 6 | functional + non-functional; scope cut; the one requirement that shapes the design |
| Architecture | 8 | components, the controller/query-layer split, data flow |
| Data model | 6 | the client state shape; what's normalized; server vs UI state |
| Interface | 8 | the component API (props/events/IoC) *and* the network API (endpoints, pagination, payloads) |
| Optimizations | 10 | ranked by the requirement, each tied to a metric or failure mode: perf, a11y, network, resilience |
| Tradeoffs / wrap | 2 | what you deferred and why |

## The Prompt

**Primary: Design a multi-file uploader** (Dropbox/Gmail-attachment style). A user drags in several large files; each shows progress, can fail and retry, and the UI stays responsive and accessible throughout.

This prompt is chosen because it's *not* one of the module-29 walkthroughs — you can't recall an answer, you have to run the framework. It also touches the cross-domain material: presigned uploads ([[30 - Backend System Design/10 - The Seven Access Patterns|Handling Large Blobs]]) and a concurrency limiter ([[31 - Low Level Design/05 - Concurrency Foundations|the JS semaphore]]).

**Alternates (for repeat runs — these map to walkthrough notes so you can self-grade precisely):** [[29 - Frontend System Design/02 - Designing an Autocomplete|autocomplete]], [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|infinite scroll feed]], [[29 - Frontend System Design/17 - Designing a Data Table|data table]], [[29 - Frontend System Design/19 - Designing a Chat and Messaging App|chat]]. Run the clock on those, then grade against the note.

## Self-Grade Rubric

Score each axis /5 (total /30). A phase only counts if you *justified* the choice, not just named it.

- **Requirements & scope** — did you separate functional from non-functional, cut scope explicitly, and name the one requirement that drives the design?
- **Architecture** — a clean controller/query-layer split; data flow that survives the non-functional requirements?
- **Data model** — concrete state shape; correct server-state vs UI-state boundary; normalized where it earns it?
- **Interface** — both APIs designed (component contract *and* network contract); inversion of control where it keeps the component reusable?
- **Optimizations ranked by requirement** — not a grab bag; each tied to a metric (LCP/INP/CLS) or a failure mode; a11y and network included, not just rendering?
- **Communication** — did you narrate tradeoffs and drive the round, or did the interviewer have to drag dimensions out of you?

25+/30 with all phases covered = solid. Missing an entire phase (esp. optimizations or a11y) = redo in a week.

## Model Outline — Multi-File Uploader

Open only after your timed round. This is a *coverage key*, not the only correct answer.

<details>
<summary>R — Requirements</summary>

- **Functional:** drag-drop + file-picker input; multiple files at once; per-file progress; cancel a file; retry a failed file; overall "N of M done"; success/error per file.
- **Non-functional:** large files (100s of MB) without freezing the tab; resilient to flaky networks (retry/resume); accessible (keyboard operable, progress announced); don't melt the network with 50 parallel uploads.
- **Scope cut (say it):** no image editing/cropping, no folder upload, no resumable-chunk protocol unless asked (mention it as the scale-up).
- **The requirement that shapes it:** *large files + many at once* → uploads must go direct-to-storage (not through your app), must be concurrency-limited, and progress/state is per-file.
</details>

<details>
<summary>A — Architecture</summary>

- `<Uploader>` (drop zone + file input + list) → an **upload controller** (owns the queue, concurrency limit, per-file state machine) → a **transfer layer** (per-file `XMLHttpRequest`/`fetch` with progress events) → object storage via **presigned URLs**.
- Flow: select files → controller enqueues each as `queued` → a **semaphore-style limiter** (e.g. 3 in flight) pulls from the queue → request a presigned URL from your API → PUT bytes directly to S3 → notify API "done" → mark `succeeded`.
- Why direct-to-storage: streaming megabytes through app servers ties up request threads and buffers memory — the [[30 - Backend System Design/10 - The Seven Access Patterns|Large Blobs]] pattern.
</details>

<details>
<summary>D — Data model</summary>

```ts
type UploadStatus = "queued" | "uploading" | "succeeded" | "failed" | "canceled";
interface UploadItem {
  id: string;            // clientId
  file: File;
  status: UploadStatus;
  progress: number;      // 0..1, from XHR progress events
  error?: string;
  abort?: () => void;    // to cancel an in-flight PUT
}
// state: Map<string, UploadItem> keyed by clientId; derived "N of M" is computed, not stored
```

- Per-file state machine (queued → uploading → succeeded/failed/canceled); failed is retryable back to queued.
- This is UI/transient state (not server cache) — it lives in the controller, not a query cache. Overall counts are *derived*, never a separate source of truth.
</details>

<details>
<summary>I — Interface (both APIs)</summary>

**Component API (IoC keeps it reusable):**
```tsx
<Uploader
  accept="image/*,application/pdf"
  maxConcurrent={3}
  getUploadUrl={(file) => api.presign(file.name, file.type)}  // inversion of control
  onItemComplete={(item) => {}}
  onAllComplete={(items) => {}}
/>
```

**Network API:**
- `POST /uploads/presign` → `{ url, fields, objectKey }` (short-lived signed PUT).
- `PUT <presigned url>` directly to storage (not your API); progress via `XHR.upload.onprogress`.
- `POST /uploads/complete` `{ objectKey }` → server records it, kicks off async validation/virus scan, returns a `pending` asset that flips to `ready`.
</details>

<details>
<summary>O — Optimizations (ranked by requirement)</summary>

1. **Responsiveness (INP):** never block the main thread — uploads are I/O; if you hash/preview large files, do it in a Web Worker. Progress updates batched (don't `setState` on every byte; throttle or rAF).
2. **Network health:** concurrency limiter (3–6 in flight) — the client [[31 - Low Level Design/05 - Concurrency Foundations|semaphore]]; exponential backoff **with jitter** on retry; resumable/chunked upload as the scale-up for huge files.
3. **Resilience:** per-file retry without restarting the batch; cancel via `AbortController`; on reload, an outbox in IndexedDB could resume (mention, scope out).
4. **Accessibility:** the list is a live region so progress/completion is announced (`aria-live="polite"`, errors assertive); the drop zone has a real `<input type="file">` fallback and is keyboard operable; per-file remove/retry are real `<button>`s ([[29 - Frontend System Design/14 - Accessibility in System Design|a11y in design]]).
5. **CLS/perception:** reserve the list row height so appending files doesn't shift layout; show optimistic "queued" rows immediately.
</details>

<details>
<summary>Tradeoffs to name out loud</summary>

- Direct-to-storage means validation/scanning can't be inline — do it async and hold the asset `pending` (a small UX state) rather than blocking the upload.
- A fixed concurrency limit trades peak throughput for stability; too low wastes bandwidth, too high reproduces the overload.
- Full resumable chunked upload is real complexity — justified only when files are large enough that a failed 90%-done upload is unacceptable. Say when you'd add it.
</details>

## After the Round

- Grade against the rubric; note the phase you rushed and the axis you forgot (it's usually optimizations or a11y).
- Re-run in a week on an **alternate** prompt and compare coverage.
- If you cleanly cover all phases twice, that's the signal to move [[29 - Frontend System Design/01 - The Frontend System Design Framework|the framework note]] toward `solid` — update its `status` yourself.

## Related Notes

- [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]]
- [[29 - Frontend System Design/03 - Frontend System Design Checklist|Frontend System Design Checklist]]
- [[29 - Frontend System Design/00 - Frontend System Design MOC|Frontend System Design MOC]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Large Blobs)
- [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]] (concurrency limiter)
- [[90 - Labs/00 - Labs MOC|Labs MOC]]

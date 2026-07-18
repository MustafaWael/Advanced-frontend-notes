---
tags: [javascript, typed-arrays, binary, files]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
aliases: [ArrayBuffer, DataView, Blob, TypedArray]
---

# Typed Arrays and Binary Data

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain ArrayBuffer vs typed array views vs DataView, and Blob/File, and when binary handling beats strings.
- Production signal: you handle file uploads/downloads, base64, and binary API responses without materializing everything as strings.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]

## Source Anchors

- [MDN - ArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer)
- [MDN - Typed arrays](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Typed_arrays)
- [MDN - Blob](https://developer.mozilla.org/en-US/docs/Web/API/Blob)
- [MDN - DataView](https://developer.mozilla.org/en-US/docs/Web/API/DataView)
- [MDN - FileReader](https://developer.mozilla.org/en-US/docs/Web/API/FileReader)

## 1. Concept

For raw bytes, JavaScript separates *storage* from *interpretation*:

- **`ArrayBuffer`** — a fixed-length block of raw bytes. You can't read/write it directly; it's just memory.
- **Typed array views** (`Uint8Array`, `Float32Array`, `Int32Array`, …) — a *typed window* onto an ArrayBuffer. `new Uint8Array(buffer)` lets you index bytes as unsigned 8-bit integers. Multiple views can share one buffer.
- **`DataView`** — a view for reading/writing mixed types at explicit byte offsets, with **endianness control** — for parsing binary formats (file headers, network protocols).

Higher-level browser types build on these: **`Blob`** (immutable binary data with a MIME type — files, images, generated downloads) and **`File`** (a Blob with a name, from `<input type=file>`).

```js
const buffer = new ArrayBuffer(8);        // 8 raw bytes
const u8 = new Uint8Array(buffer);        // view as 8 unsigned bytes
u8[0] = 255;
const view = new DataView(buffer);
view.setInt32(0, 1000, /* littleEndian */ true);  // write a 32-bit int at offset 0
```

## 2. Why It Matters

- File uploads/downloads, image manipulation (canvas pixels are a `Uint8ClampedArray`), audio (`AudioBuffer`), WebGL, streaming, and any binary API response require this model. Treating binary as strings (base64 everywhere) inflates memory ~33% and blocks the main thread ([[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]).
- Typed arrays are also the *transferable* payload for [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers]] — moving an ArrayBuffer is O(1), copying a string isn't.

## 3. Converting Between Representations

The common conversions in frontend code:

```js
// string ↔ bytes
const bytes = new TextEncoder().encode("héllo");     // Uint8Array (UTF-8)
const text  = new TextDecoder().decode(bytes);       // back to string

// Blob ↔ ArrayBuffer / text
const buf  = await blob.arrayBuffer();
const blob = new Blob([uint8Array], { type: "image/png" });

// File (input) → data
const file = input.files[0];                          // a File (Blob subclass)
const buf  = await file.arrayBuffer();

// base64 (for data URLs / JSON transport)
btoa(String.fromCharCode(...bytes));                  // small data only — see warning
```

> [!warning] base64 is for transport, not storage/processing
> Base64 encoding a file to embed in JSON inflates it ~33% and, done via `String.fromCharCode(...bigArray)`, can blow the call stack and materialize the whole thing in memory on the main thread. Use base64 only for genuinely small payloads (a tiny inline image data URL). For real files, keep them as Blob/ArrayBuffer and send via `FormData`/`fetch` body, which streams the bytes without a string round-trip.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an image editor lets users crop, then upload. The naive version base64s everything.

Buggy version:

```js
const reader = new FileReader();
reader.onload = () => {
  const base64 = reader.result;                  // "data:image/png;base64,...." (huge string)
  fetch("/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: base64 }),      // ~33% larger, all in memory, on main thread
  });
};
reader.readAsDataURL(file);                        // materializes the whole file as a string
```

Trace: `readAsDataURL` builds a base64 string of the entire (possibly 20MB) image on the main thread; `JSON.stringify` copies it again; the request body is ~33% bigger than the file; the server must base64-decode before touching the image. Large files jank or crash the tab.

Production-safe fix — keep it binary:

```js
// For a cropped canvas result:
canvas.toBlob(async (blob) => {                    // Blob, not base64
  const form = new FormData();
  form.append("image", blob, "crop.png");
  await fetch("/upload", { method: "POST", body: form });  // streams multipart bytes
}, "image/png");

// Or for an untouched file, upload it directly:
const form = new FormData();
form.append("image", file);                        // File is already a Blob
await fetch("/upload", { method: "POST", body: form });
```

Tradeoffs: binary/FormData streams bytes and stays memory-flat, but needs server-side multipart handling (standard) and gives no upload progress from `fetch` (drop to `XMLHttpRequest.upload.onprogress` or chunked/resumable uploads for a progress bar). Base64/data URLs remain the right tool for *tiny* inline assets (a 1KB icon in CSS) or when a string is genuinely required. And for heavy pixel processing, do it in a worker with the pixel `Uint8ClampedArray` transferred, not copied ([[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Workers]]).

## 5. Interview Answer

Short answer:

> `ArrayBuffer` is raw fixed-length bytes you can't touch directly; typed array views (`Uint8Array`, `Float32Array`, …) interpret those bytes as numbers, and multiple views can share one buffer; `DataView` reads/writes mixed types at explicit offsets with endianness control for parsing binary formats. `Blob` is immutable binary + MIME type; `File` is a named Blob from an input. `TextEncoder`/`TextDecoder` convert to/from UTF-8 bytes.

Deeper answer:

> The point is separating storage (ArrayBuffer) from interpretation (views), which is why canvas pixels, WebGL, audio, and binary protocols use typed arrays, and why ArrayBuffers are the O(1) transferable payload for workers. The common mistake is routing files through base64/data URLs: it inflates size ~33%, materializes everything as a string on the main thread, and can overflow the stack — use Blob/File with FormData/fetch to stream bytes instead, reserving base64 for tiny inline assets. Heavy binary processing belongs in a worker with the buffer transferred, not copied.

## 6. Practice

1. <details><summary>What's the relationship between an ArrayBuffer and a Uint8Array, and can two views share one buffer?</summary>An ArrayBuffer is raw bytes with no way to read them directly; a Uint8Array is a *view* that interprets those bytes as unsigned 8-bit integers. Yes — multiple views (e.g., a Uint8Array and a Float32Array, or two views at different offsets) can share the same ArrayBuffer, and writes through one are visible through the others because they point at the same memory. That aliasing is the basis for parsing structured binary and for zero-copy reinterpretation.</details>

2. <details><summary>When do you need DataView instead of a plain typed array?</summary>When you must read/write *mixed* types at specific byte offsets and control *endianness* — e.g., parsing a file header or network packet where bytes 0–3 are a little-endian int32, byte 4 is a flag, bytes 5–8 a float. Typed arrays assume the platform's native endianness and a uniform element type; DataView's `getInt32(offset, littleEndian)`/`setFloat64(...)` give explicit, per-field control needed for binary formats that don't match the host layout.</details>

3. <details><summary>Why is base64-in-JSON a poor way to upload a 15MB file?</summary>Base64 inflates the payload ~33% (20MB on the wire for 15MB), the encoding materializes the entire file as a string on the main thread (jank/possible crash, stack overflow if done via `String.fromCharCode(...arr)`), and `JSON.stringify` copies it again; the server must also decode before use, and JSON body parsers often cap size. Use a Blob/File with `FormData` + `fetch`, which streams the raw bytes as multipart without a string round-trip, keeping memory flat.</details>

4. <details><summary>You need to send a large ArrayBuffer to a Web Worker for processing. Copy or transfer, and what's the consequence?</summary>Transfer it: `worker.postMessage(buf, [buf])`. Transfer moves ownership in O(1) (no copy) and *detaches* the buffer on the sender side (its byteLength becomes 0, further use throws). Copying (omitting the transfer list) duplicates all the bytes via structured clone — O(n) and doubles memory, wasteful for large buffers. Transfer when the sender no longer needs the data; copy only if both sides must retain it.</details>

## Related Notes

- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|Strings, Unicode and Template Literals]]
- [[01 - Roadmap|Roadmap]]

---
tags: [browser, architecture, security]
module: "26 - How the Web Works"
priority: important
status: not-started
aliases: [Multi-process browser, Browser process model]
---

# Browser Architecture

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: Draw the modern browser's process model, explain what runs where (your JS, layout, GPU work, network), and justify sandboxing and site isolation.
- Production signal: You understand *why* a tab crash doesn't kill the browser, what "main thread" actually means, and where workers fit.
- Dependencies: [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]

## Source Anchors

- [Chrome - Inside look at modern web browsers, part 1](https://developer.chrome.com/blog/inside-browser-part1)
- [Chrome - Inside look at modern web browsers, part 2](https://developer.chrome.com/blog/inside-browser-part2)
- [Chromium - Site Isolation](https://www.chromium.org/Home/chromium-security/site-isolation/)

## 1. Concept

Simple version: a modern browser is not one program but a small operating system — a coordinator process plus many isolated worker processes, so that one misbehaving page can't crash, spy on, or freeze everything else.

The accurate mechanism (Chromium's model; Firefox and Safari are structurally similar):

- **Browser process** — the coordinator. Owns the UI (address bar, tabs, buttons), user profile, and brokers access to disk, and other privileged resources.
- **Network process** — performs actual network I/O (DNS, connections, HTTP) on behalf of everyone.
- **Renderer processes** — one per site instance. This is where *your* code lives: HTML parsing, DOM, CSS, layout, paint commands, and the JS engine all run here. The renderer is **sandboxed**: it cannot open files or sockets directly — it must ask the browser/network process over IPC.
- **GPU process** — takes the compositor's layers and actually rasterizes/draws using the GPU.
- **Utility/plugin processes** — audio, extensions, etc.

Inside a renderer, the threads matter most for frontend work:

- **Main thread** — JS execution, DOM, style, layout, paint. The famous "don't block the main thread" refers to *this* thread of *this* process.
- **Compositor thread** — assembles pre-painted layers and handles scrolling; this is why a page can scroll smoothly while the main thread is busy (as long as there are no non-passive touch/wheel listeners forcing a wait).
- **Worker threads** — [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers]] each get their own thread and event loop, no DOM access.

**Site isolation** goes further: after Spectre/Meltdown showed that any code sharing an address space might read its memory, browsers ensured *different sites* never share a renderer process — even cross-site iframes get their own process. This is why `SharedArrayBuffer` requires cross-origin isolation headers (COOP/COEP).

```text
Browser process ──┬── Network process
                  ├── GPU process
                  ├── Renderer (site A, tab 1)   ← your JS, DOM, layout
                  ├── Renderer (site A, tab 2)
                  └── Renderer (site B iframe)   ← isolated even inside tab 1
```

## 2. Why It Matters

- "How does the browser work?" answered at the *process* level (not just "it parses HTML") is a strong senior signal.
- It explains everyday observations mechanically: "Aw, snap" in one tab only (renderer crash), smooth scroll during jank (compositor thread), why `fetch` can proceed while JS is blocked (network process) but the *callback* can't run (main thread event loop — [[09 - Event Loop Advanced/00 - Event Loop Advanced MOC|Event Loop Advanced]]).
- Security questions ("why can't a web page read my files?") have a real answer: the renderer sandbox + brokered IPC, not "JavaScript can't do that."

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```ts
// Buggy: parsing a 50MB CSV on the main thread — the tab freezes,
// but users report "scrolling still works, clicking doesn't". Why?
input.addEventListener('change', async (e) => {
  const text = await file.text();
  const rows = parseCsvSync(text); // 4 seconds of main-thread work
  render(rows);
});
```

Trace: `parseCsvSync` occupies the renderer's main thread. Event loop can't process input events or run rAF → clicks queue up, React can't render. Scrolling *may* still work because the compositor thread scrolls already-rasterized layers without the main thread. The freeze is scoped to this one renderer process — other tabs are fine, which is the architecture visibly at work.

```ts
// Fix: move the work off the main thread
const worker = new Worker(new URL('./csv.worker.ts', import.meta.url));
input.addEventListener('change', async () => {
  const text = await file.text();
  worker.postMessage(text);          // structured clone → worker thread
});
worker.onmessage = (e) => render(e.data); // main thread only renders
```

Tradeoffs: `postMessage` copies data (structured clone) — for 50MB, prefer `Transferable` (ArrayBuffer) to move instead of copy. Workers have no DOM, so the boundary must be designed: compute there, render here. More moving parts, real gain.

> [!warning] Footgun: a non-passive `wheel`/`touchstart` listener forces the compositor to wait for the main thread before scrolling — one line (`{ passive: true }`) is the difference between smooth and janky scroll on busy pages.

## 4. Interview Answer

Short answer:

> Modern browsers are multi-process: a browser process coordinates UI and privileged access, a network process does I/O, a GPU process draws, and each site gets its own sandboxed renderer process — which is where the DOM, CSS, layout, and my JavaScript actually run. Inside a renderer, the main thread runs JS and rendering, while a separate compositor thread handles scrolling. Sandboxing plus per-site isolation means a compromised or crashed page can't touch other sites, the filesystem, or the network directly.

Deeper answer:

> Deeper: renderers reach resources only via IPC to privileged processes, which is the actual enforcement behind the web security model. Site isolation was hardened post-Spectre so cross-site documents never share an address space — the reason SharedArrayBuffer now requires COOP/COEP cross-origin isolation. For performance, the process model defines the units of parallelism: workers for CPU work, the compositor for scroll/animation (hence `transform`/`opacity` animations and passive listeners), and OffscreenCanvas to paint from a worker.

## 5. Practice

1. <details><summary>One tab shows "Aw, snap" — why do your other tabs survive?</summary>Each site instance runs in its own renderer process with its own address space. A crash (OOM, engine bug) kills that process only; the browser process detects it and shows the sad-tab UI, everything else is untouched.</details>
2. <details><summary>Why can the page scroll smoothly while your JS blocks for 2 seconds?</summary>The compositor thread scrolls already-rasterized layers without consulting the main thread — unless a non-passive wheel/touch listener forces it to wait for JS, or the scroll reveals unrasterized content.</details>
3. <details><summary>What actually stops fetched malicious JS from reading ~/.ssh/id_rsa?</summary>The renderer sandbox: the process running that JS has no OS-level file access. Any file operation must go through IPC to the browser process, which only grants what user-mediated APIs (file pickers) allow. Defense is the process boundary, not the JS language.</details>

## Related Notes

- [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[09 - Event Loop Advanced/00 - Event Loop Advanced MOC|Event Loop Advanced MOC]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

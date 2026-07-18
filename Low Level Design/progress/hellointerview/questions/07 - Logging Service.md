# 07 - Logging Service (Logger Library)

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/logging-service
**Difficulty:** Medium · By Evan King (Hello Interview)

> **Note on completeness:** This page is premium-locked past the "Core Entities" heading. The *Understanding the Problem* and *Requirements* sections below are captured from the free portion. Locked sections are listed at the bottom with their visible headings.

---

## Understanding the Problem

**What is a Logger?** A logger is the **in-process library** an application uses to record what's happening at runtime. Code calls `logger.info("user signed in")` from anywhere in the app, and the library timestamps the message, attaches the severity level, and writes it to one or more places like the console, a file, or both. Think Log4j, SLF4J, or Python's `logging` module. We're designing the library that lives inside one application — **not** a distributed log aggregation service.

## Requirements

The prompt is deliberately short:

> "Design a logging service. Or call it a logger, whichever you prefer."

Most of the design is hidden in what they *didn't* say. Spend the first few minutes pulling it apart before drawing anything.

### Clarifying Questions (and what each answer tells you)

1. **"In-process library, or something that ships logs over the network to a central aggregator?"**
   → *"In-process library. Network shipping, ingestion pipelines, and central aggregation are someone else's problem."*
   Takeaway: cuts most of the design space. No queues, no schema registries, no fan-out across services. The deliverable is an object model inside one process writing to local destinations (stdout, files).

2. **"What severity levels, and is there an ordering?"**
   → *"DEBUG, INFO, WARN, ERROR, FATAL. Ordered from least to most severe."*
   Takeaway: a finite set with no per-level behavior is **a textbook enum**. Reaching for a `Level` class hierarchy (`DebugLevel`, `InfoLevel`, ...) is doing too much.

3. **"Can a single logger write to multiple destinations at the same time (console + file)?"**
   → *"Yes. That's the common case. Each call should fan out to every configured destination."*
   Takeaway: **destination is a first-class concept**; the logger holds a list of destinations and iterates over them on every call.

4. **"Does each destination decide its own filter level, or is there one global level on the logger?"**
   → *"Per destination. Each destination has its own minimum level. Console might want DEBUG+, the file destination might only care about WARN+. Records below a destination's threshold are dropped before being written."*
   Takeaway: the level filter lives on the **destination**, not the logger. The same record is evaluated independently by each destination — fine because the record is **immutable** once created.

5. **"Is the output format fixed, or does it vary?"**
   → *"Varies. Sometimes plain text, sometimes JSON. Format is independent of destination type — JSON to console, plain text to file, any combination."*
   Takeaway: **this requirement shapes the class model.** If format and destination were coupled you'd get a class per (format, target) pair — `JsonFileDestination`, `PlainConsoleDestination`, ... 3 formats × 3 targets = 9 classes. Since they vary independently, **compose** them instead of multiplying classes.

   > **Key interview signal:** When a requirement gives you two dimensions that vary independently, that's almost always a signal to use **composition over inheritance**. Two interfaces composed together let you mix any combination without writing N×M classes. Watch for these axes-of-variation hints in any LLD prompt. (This is essentially the Strategy/Bridge idea: `Formatter` and `Sink` composed inside a `Destination`.)

6. **"What about concurrency — multiple threads calling log() simultaneously?"**
   → *"Thread-safe. Each record's bytes must land on a destination atomically — one record's bytes can't be split across or mixed with another's. For a single thread, records appear in call order. Across threads, no strict ordering beyond each record's timestamp."*
   Takeaway: locking is part of the design, not a cleanup pass. **Per-record atomicity is the bar.** Strict global submission order across threads would push toward queues and single-writer threads — not asked for here.

7. **"Static config at startup, or hot-reload at runtime?"**
   → *"Static, configured once at startup. Hot-reload, async/buffered writes, log rotation, and network destinations are all out of scope — though the design should not block adding a remote destination later."*
   Takeaway: the last clause shapes the design. Don't build remote destinations now, but keep destinations **pluggable behind an interface** so adding one later doesn't force a Logger rewrite.

### Final Requirements

```
Requirements:
1. Five severity levels: DEBUG < INFO < WARN < ERROR < FATAL.
2. Each record carries timestamp, level, message, emitting thread name.
3. Logger writes each record to one or more destinations, set at startup.
4. Each destination has its own min-level threshold and its own format.
   Format and destination type vary independently.
5. Concurrent calls are safe. A record's bytes never interleave with
   another record's bytes on the same destination.

Out of scope:
- Hot-reloading config at runtime
- Async / buffered writes
- Remote / network destinations in v1 (design should accommodate)
- Hierarchical / named loggers (com.app.service inheriting from com.app)
```

**Scoping tip from the article:** explicitly naming async writes, hot-reload, and remote destinations as out of scope signals you considered them and chose not to build them — which reads very differently from forgetting they exist. Each is a layer on top of the core object model, and most return as extensibility follow-ups.

## Core Entities and Relationships (locked)

*(The entity derivation is premium-locked.)* From the visible class-design headings, the model is:

- **Logger** — the entry point; holds destinations, fans out each record
- **LogRecord** — immutable value: timestamp, level, message, thread name
- **Formatter** — interface: turns a LogRecord into a string (PlainText, JSON implementations)
- **Destination** — pairs a Formatter + Sink with a per-destination min level
- **Sink** — interface: where bytes go (console, file implementations); the extension point for future remote sinks

## Class Design (headings visible; content locked)

Sections: Logger, LogRecord, Formatter, Destination, Sink, Final Class Design.

## Implementation (locked)

Sections: Logger, Destination, Formatter implementations, Sink implementations, LogRecord, Complete Code Implementation, Verification.

## Extensibility (headings visible; content locked)

1. "How would you make `log()` non-blocking?" — (async/buffered writes: producer-consumer queue + background writer thread territory)
2. "How would you support hierarchical named loggers?" — (Log4j-style `com.app.service` inheriting config from `com.app`)

## What is Expected at Each Level? (locked)

Junior / Mid-level / Senior expectation sections are premium-locked.

---

## Premium-locked sections on this page

- Core Entities and Relationships (derivation)
- Class Design: Logger, LogRecord, Formatter, Destination, Sink + Final Class Design
- Implementation: all code, Complete Code Implementation, Verification
- Extensibility: both follow-up answers
- What is Expected at Each Level: Junior / Mid-level / Senior

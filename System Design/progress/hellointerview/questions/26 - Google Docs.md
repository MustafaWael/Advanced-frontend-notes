# 26 - Google Docs (Collaborative Document Editor)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-docs
**Author:** Stefan Mai · Difficulty: Hard · Pattern: Real-time Updates

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section and functional requirements were freely visible. Everything below the functional requirements (non-functional requirements content, core entities, API design, high-level design details, deep dives, level expectations, references) is behind the Hello Interview Premium paywall. This note captures the free content plus the article's structure/outline so you know what the breakdown covers.

## Understanding the Problem

**What is Google Docs?** Google Docs is a browser-based collaborative document editor. Users can create rich text documents and collaborate with others in real-time.

The breakdown designs a system supporting the core functionality of Google Docs, dipping into **websockets** and **collaborative editing systems**, following Hello Interview's Delivery Framework (requirements → set up → high-level design → deep dives).

## Functional Requirements

**Core Requirements**

1. Users should be able to create new documents.
2. Multiple users should be able to edit the same document concurrently.
3. Users should be able to view each other's changes in real-time.
4. Users should be able to see the cursor position and presence of other users.

**Below the line (out of scope)**

1. Sophisticated document structure — assume a simple text editor.
2. Permissions and collaboration levels (e.g., who has access to a document).
3. Document history and versioning.

## Non-Functional Requirements

🔒 *Content premium-locked.* (Typical themes for this problem: low-latency propagation of edits, eventual convergence of all replicas to the same document state, high availability, scale to millions of concurrent documents/connections — but the article's actual list is not visible.)

## Article Structure (locked sections)

The full breakdown follows this outline — all of the following sections are premium-locked:

- **Set Up**
  - Planning the Approach
  - Defining the Core Entities
  - Defining the API
- **High-Level Design**
  1. Users should be able to create new documents.
  2. Multiple users should be able to edit the same document concurrently.
     - Collaborative Edits Breakdown (this is where Operational Transformation / CRDT-style concurrency discussion lives)
  3. Users should be able to view each other's changes in real-time.
     - When the Document is Loaded
     - When Updates Happen
  4. Users should be able to see the cursor position and presence of other users.
- **Potential Deep Dives**
  1. How do we scale to millions of websocket connections?
  2. How do we keep storage under control?
  - Some additional deep dives you might consider
- **What is Expected at Each Level?** — Mid-level / Senior / Staff subsections (content locked)
- **References**

## Locked Sections Note

Premium-locked and not captured: Non-Functional Requirements details, Planning the Approach, Core Entities, API design, all High-Level Design content, both deep dives ("scale to millions of websocket connections", "keep storage under control"), additional deep dive suggestions, level expectations (Mid/Senior/Staff), and References.

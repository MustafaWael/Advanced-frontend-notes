# 30 - ChatGPT

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/chatgpt
**Author:** Evan King · Difficulty: Hard · Patterns: Real-time Updates, Managing Long Running Tasks

> **⚠️ Premium-locked page.** The "Understanding the Problem" section, functional requirements, and the non-functional requirements framing were freely visible. All design content beyond that is behind the Hello Interview Premium paywall. This note captures the free content plus the article's structure/outline.

## Understanding the Problem

**What is ChatGPT?** A conversational AI product where users send prompts in natural language and get responses **streamed back** from a large language model. Conversations are saved, so users can return to an old chat and pick up where they left off.

**Key scoping decision:** treat the LLM as a **black box** we call — not something we train or run the internals of. All the design lives in the **serving system around it**:

- streaming tokens back fast,
- scheduling scarce GPUs,
- keeping cost sane as conversations grow.

Scope is text in, text out only — no images/audio/video, and no editing or branching of existing messages.

## Functional Requirements

**Core Requirements**

1. Users should be able to send a prompt in a chat and receive an AI-generated response.
2. Users should be able to view past chats and resume a conversation, with the chat's prior context carried into the prompt.

**Below the line (out of scope)**

- Editing or branching existing messages.
- Image, audio, or video input and output (text only).
- Sharing chats or collaborating on a chat with other users.
- Custom GPTs, tool/function calling, and web browsing.
- Full-text search across a user's chat history.

## Non-Functional Requirements

Free-visible framing:

- ChatGPT feels broken if you stare at a blank screen after hitting enter, so **latency to the first token matters more than total completion time**.
- **GPUs are the scarce, expensive resource**, so the system must be deliberate about who gets compute and when.
- Scale target: a little over **200M daily active users**.

🔒 *The actual bulleted non-functional requirements list is premium-locked.*

## Article Structure (locked sections)

The full breakdown follows this outline — all of the following sections are premium-locked:

- **The Set Up**
  - Planning the Approach
  - Defining the Core Entities
  - API or System Interface
- **High-Level Design**
  1. Users should be able to send a prompt and receive an AI-generated response
  2. Users should be able to view past chats and resume a conversation with context carried across turns
- **Potential Deep Dives**
  1. How do we stream tokens back fast, and keep the stream smooth?
  2. How do we route and schedule generation requests across GPU workers?
  3. How do we keep heavy users from monopolizing GPUs while giving paid tiers a better experience? (rate limiting / fairness / priority tiers)
  4. As conversations get longer, how do we control inference cost without making the assistant feel forgetful? (context management/summarization)
     - Cancelling a run and reclaiming the GPU
  - Some additional deep dives you might consider
- **What is Expected at Each Level?** — Mid-level / Senior / Staff+ subsections (content locked)

## Locked Sections Note

Premium-locked and not captured: Non-Functional Requirements list, Planning the Approach, Core Entities, API design, both High-Level Design walkthroughs, all four deep dives (token streaming; GPU routing/scheduling; heavy-user fairness and paid-tier priority; long-conversation cost control incl. run cancellation and GPU reclamation), additional deep-dive suggestions, and level expectations (Mid/Senior/Staff+).

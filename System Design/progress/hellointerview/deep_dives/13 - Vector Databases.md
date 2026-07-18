# Vector Databases

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/vector-databases

Learn how vector databases power similarity search, recommendations, and AI applications in system design.

> **Note: this page is premium-locked.** Only the introduction and the "What's a Vector Anyway?" section are freely visible; everything under the "Locked sections" list was behind the paywall at fetch time and is NOT covered in this note.

---

## The Problem Space (free content)

Embeddings are everywhere: search engines that understand what you *mean*, recommendation systems surfacing eerily relevant content, chatbots retrieving from massive document collections. All rely on the same primitive: **finding things that are similar to other things, fast.**

This isn't new — vector databases and related techniques have long powered recommendation systems — but modern ML has amplified their power and unlocked a new set of infra applications.

The gap they fill: traditional databases are great at **exact lookups** ("user with ID 12345", "orders on January 1st") but fail at "find me documents similar to this one." That's where vector databases come in.

> **Author's framing for interviews:** most system design interviews won't cover vector databases, and those that do care less that you know the internals than that you know **how and where to use them**. If the detail is frightening, skip to the applications and work backwards.

## What's a Vector Anyway? (free content)

A **vector** (or **embedding**) is an array of numbers representing something — a word, sentence, image, user, or product — anything you can feed into an ML model. The magic: **similar things end up with similar vectors.**

```
"The cat sat on the mat"   → [0.12, -0.34, 0.78, ..., 0.45]  // 1536 numbers
"A feline rested on a rug" → [0.11, -0.32, 0.79, ..., 0.44]  // very similar!
"The stock market crashed" → [-0.89, 0.12, -0.45, ..., 0.23] // very different
```

- Typical embeddings have **128–1536 dimensions** (OpenAI's text-embedding-3-large uses 3072).
- Individual dimensions aren't human-interpretable; what matters is that **geometric relationships between vectors reflect semantic relationships** between the things they represent.

**"Similarity" depends on the embedding model:**

- **Pre-trained models** — text: OpenAI's embedding API, Sentence Transformers, BERT; images: CLIP, ResNet. Trained on diverse tasks so the notion of similarity you care about is *probably* captured — think vague "semantic" similarity. To you, the model is an expensive GPU function: data in, fixed-length vector out.
- **Custom models** — similarity can be much more precise for the application. Recommendation example: diapers and bottles are only vaguely semantically similar, but *profoundly* similar as items new parents buy together. A custom ML model can create embeddings targeting exactly that notion of similarity.

---

## Locked sections (premium-only, not captured)

The following sections were behind the "Purchase Premium to Keep Reading" wall:

- **Similarity Metrics**
- **The Nearest Neighbor Problem**
- **How Vector Databases Work**
  - Indexing Strategies: **HNSW (Hierarchical Navigable Small World)**, **IVF (Inverted File Index)**, **Locality Sensitive Hashing (LSH)**, **Annoy**
  - Filtering and Hybrid Search
  - Inserts, Updates, and Index Maintenance
- **Vector Database Options**
  - Vector Extensions for Traditional DBs and Stores (Start Here)
  - Purpose-Built Vector DBs (When You Need Scale)
- **Using Vector Databases in Your Interview**
  - Common Interview Scenarios
  - Architecture Patterns
  - Key Design Decisions to Discuss
  - Numbers to Know
- **Gotchas and Limitations**
- **Summary**

### What the locked table of contents still tells you (for interview prep)

Even from the headings, the article's structure signals the key study areas:

- **Exact nearest-neighbor search doesn't scale** — hence a dedicated "Nearest Neighbor Problem" section and a set of *approximate* nearest neighbor (ANN) indexing strategies: HNSW, IVF, LSH, Annoy. Knowing these four names (HNSW being the dominant one in production) is the core technical content.
- **Filtering/hybrid search** (combining vector similarity with metadata filters or keyword search) is a named topic — a known hard problem in vector search.
- **Index maintenance under inserts/updates** gets its own section — ANN indexes are typically expensive to update, a classic tradeoff.
- **The recommended default is a vector extension of your existing database** ("Start Here" — e.g., pgvector-style extensions) with purpose-built vector DBs reserved for "When You Need Scale" — mirroring the site's general "boring technology first" philosophy.
- Interview-facing sections (scenarios, architecture patterns, design decisions, numbers to know) confirm the author's advice: interviewers care about **when and how to use vector search** (semantic search, RAG, recommendations) more than internals.

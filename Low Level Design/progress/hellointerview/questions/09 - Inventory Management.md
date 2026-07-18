# 09 - Inventory Management

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/inventory-management
**Difficulty:** Hard · By Evan King (Hello Interview)

> **Note on completeness:** This page is premium-locked past the "Core Entities" intro. The *Understanding the Problem* and *Requirements* sections below are captured from the free portion. Locked sections are listed at the bottom with their visible headings.

---

## Understanding the Problem

**What is an Inventory Management System?** An inventory management system tracks product stock across multiple warehouse locations. When inventory arrives, the system records it. When orders ship, the system deducts stock. The system can also transfer inventory between locations and alert managers when stock runs low.

## Requirements

The interview prompt:

> "Design an inventory management system that tracks products across multiple warehouses. The system needs to handle adding and removing inventory, transferring stock between locations, and alerting when inventory runs low."

Lots of room for interpretation — spend a few minutes clarifying before touching the whiteboard.

**Question structure tip from the article:** organize clarifying questions around four themes — *what operations does the system support, what can go wrong, what's in scope, and what might we extend later.*

### Clarifying Questions (and what each answer tells you)

1. **"Fixed set of warehouses configured at startup, or added dynamically?"**
   → *"Keep it simple. Fixed set, configured when the system initializes."*
   Takeaway: no warehouse lifecycle management.

2. **"How do low-stock alerts work — threshold per product, or more granular?"**
   → *"Per product **per warehouse**. Different warehouses might need different thresholds for the same product. When stock drops below the threshold, trigger a notification."*
   Takeaway: alerts are **warehouse-specific, not global**. A product could be low in Warehouse A but fine in Warehouse B.

3. **"How should the notification happen — email, webhook, return value?"**
   → *"Keep it pluggable. The system should call some **callback interface** when stock is low. What happens after that — email, webhook, logging — is someone else's problem."*
   Takeaway: build the alert **mechanism**, not the notification delivery. (This is the **Observer/listener pattern** hint: an `AlertListener` interface consumers implement.)

4. **"Should we allow negative inventory, or reject operations that would take stock below zero?"**
   → *"Reject them. Removing 100 units when we only have 50 should fail. Same with transfers — validate before moving anything."*
   Takeaway: the system **enforces invariants**; stock can't go negative.

5. **"Concurrent access — two processes modifying the same warehouse's inventory at once?"**
   → *"Yes, concurrency is important here. One warehouse receiving a shipment while another fulfills an order for the same product. Make sure operations are thread-safe."*
   Takeaway: think about **synchronization from the start** (and note the visible test case: transfers must be atomic with proper locking — a classic two-lock / lock-ordering-to-avoid-deadlock scenario).

6. **"What's out of scope — product catalogs, orders?"**
   → *"Products exist externally. Orders and payments are handled upstream. Focus on the inventory tracking logic."*

### Final Requirements

```
Requirements:
1. Track inventory for products across multiple warehouses
2. Add stock to a specific warehouse (receiving shipments)
3. Remove stock from a specific warehouse (fulfilling orders)
4. Check availability: given a product and quantity, return which warehouses can fulfill it
5. Transfer stock between warehouses
6. Low-stock alerts
7. Reject operations that would result in negative inventory
8. System must be thread-safe to handle concurrent operations

Out of Scope:
- Product catalog management (products exist externally)
- Order processing / payment / serviceability
- Persistence
```

## Core Entities and Relationships

Free intro only: scan the requirements for **nouns that represent things with behavior or state**; treat each noun as a candidate entity, then prune until the list makes sense to model. *(The pruned list itself is locked.)*

## Class Design (headings visible; content locked)

The breakdown designs:

- **InventoryManager** — the orchestrator/facade: add, remove, transfer, checkAvailability across warehouses
- **Warehouse** — owns per-product stock counts for one location; the unit of locking
- **AlertConfig** — per-product-per-warehouse threshold configuration
- **AlertListener** — pluggable callback interface (Observer) invoked when stock drops below threshold

Plus a **Final Class Design** diagram. *(Signatures and diagram are premium-locked.)*

## Implementation (locked)

Sections: InventoryManager, Warehouse, AlertConfig, AlertListener, Complete Code Implementation, and **Verification** with three test cases whose names are visible:

1. Alert threshold **crossing** behavior (implies alerts fire on the crossing transition, not repeatedly while below threshold)
2. Atomic transfer with proper locking
3. Validation prevents negative inventory

## Extensibility (headings visible; content locked)

1. "How do you prevent overselling when orders are in progress?" — (reservation/hold semantics territory)
2. "How would you handle inventory that's being shipped between warehouses?" — (in-transit state between source deduction and destination arrival)

## What is Expected at Each Level? (locked)

Junior / Mid-level / Senior expectation sections are premium-locked.

---

## Premium-locked sections on this page

- Core Entities (pruned list)
- Class Design: InventoryManager, Warehouse, AlertConfig, AlertListener + Final Class Design
- Implementation: all code, Complete Code Implementation, Verification test bodies
- Extensibility: both follow-up answers
- What is Expected at Each Level: Junior / Mid-level / Senior

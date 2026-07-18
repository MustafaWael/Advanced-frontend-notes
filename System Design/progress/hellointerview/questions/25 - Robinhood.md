# 25 - Robinhood (Stock Trading Platform)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/robinhood

- **Author:** Joseph Antonakakis (Hello Interview)
- **Difficulty:** Hard
- **Key pattern:** Real-time Updates

> **⚠️ Premium-locked page:** Only the free preview of this breakdown was accessible. The section outline below reflects the article's own structure, but the detailed content of most sections (non-functional requirements, planning, core entities, API, high-level design, all deep dives, and level expectations) is behind the Hello Interview Premium paywall and is NOT reproduced here. See "Locked sections" at the bottom.

## Understanding the Problem

**What is Robinhood?** Robinhood is a commission-free trading platform for stocks, ETFs, options, and cryptocurrencies. It features real-time market data and basic order management. Robinhood isn't an exchange in its own right, but rather a **stock broker**; it routes trades through market makers ("exchanges") and is compensated by those exchanges via payment for order flow.

### Background: Financial Markets

Basic financial terms to understand before jumping into this design:

- **Symbol**: An abbreviation used to uniquely identify a stock (e.g. META, AAPL). Also known as a "ticker".
- **Order**: An order to buy or sell a stock. Can be a *market order* or a *limit order*.
- **Market Order**: An order to trigger immediate purchase or sale of a stock at the current market price. Has no price target and just specifies a number of shares.
- **Limit Order**: An order to purchase or sell a stock at a specified price. Specifies a number of shares and a target price, and can sit on an exchange waiting to be filled or cancelled by the original creator of the order.

**Key scoping insight:** Robinhood is a brokerage and interfaces with external entities that actually manage order filling/cancellation. We are building a brokerage system that facilitates customer orders and provides customers stock data — **we are not building an exchange.**

For this problem, assume Robinhood interfaces with an "exchange" that offers:

- **Order Processing**: Synchronously places orders and cancels orders via a request/response API.
- **Trade Feed**: Offers subscribing to a trade feed for symbols. "Pushes" data to the client every time a trade occurs, including the symbol, price per share, number of shares, and the orderId.

Interview tip from the article: when the interviewer offers an external API (the exchange), briefly clarify the exchange interface (synchronous and asynchronous APIs) so you know the tools at your disposal — assumptions about this interface have broad consequences in your design, so align with the interviewer on the details.

## Functional Requirements

**Core Requirements**

1. Users can see live prices of stocks.
2. Users can manage orders for stocks (market / limit orders, create / cancel orders).

**Below the line (out of scope)**

- Users can trade outside of market hours.
- Users can trade ETFs, options, crypto.
- Users can see the order book in real time.

Scoping note from the article: this question focuses on stock viewing and ordering; it excludes advanced trading behaviors and doesn't primarily involve viewing historical stock or portfolio data. For feature-rich apps like Robinhood, have brief back-and-forth with the interviewer to figure out which part of the system they care most about.

## Non-Functional Requirements

*(Content premium-locked. From the deep-dive titles, key concerns include scaling live price updates, tracking order updates, and order consistency.)*

## The Set Up

### Planning the Approach
*(Content premium-locked.)*

### Defining the Core Entities
*(Content premium-locked.)*

### The API
*(Content premium-locked.)*

## High-Level Design

The high-level design addresses each functional requirement in turn (details premium-locked):

1. Users can see live prices of stocks.
2. Users can manage orders for stocks.

## Potential Deep Dives

Three main deep dives plus additional suggestions (all detail premium-locked):

1. **How can the system scale up live price updates?** — real-time fan-out of the exchange trade feed to millions of clients.
2. **How does the system track order updates?** — reconciling asynchronous order fills/cancellations from the exchange with internal order state.
3. **How does the system manage order consistency?** — keeping the brokerage's view of orders consistent with the exchange.
4. Some additional deep dives you might consider (list locked).

## What is Expected at Each Level?

The article includes sections for **Mid-level**, **Senior**, and **Staff+** expectations, but the content is premium-locked.

---

## Locked sections (premium-only, not captured)

- Non-Functional Requirements
- Planning the Approach
- Defining the Core Entities
- The API
- High-Level Design (both requirement walkthroughs, diagrams)
- Deep Dive 1: Scaling live price updates (tradeoffs and "great solution")
- Deep Dive 2: Tracking order updates
- Deep Dive 3: Managing order consistency
- Additional deep dives
- What is Expected at Each Level (Mid-level / Senior / Staff+)

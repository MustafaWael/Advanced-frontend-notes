# 02 - Types of Front End System Design Questions

> Source: https://www.greatfrontend.com/front-end-system-design-playbook/types-of-questions

Front end system design questions fall into two main categories: **Applications** and **UI Components**.

## 1. Applications

Feels similar to general SWE system design — the questions are often the same — but instead of distributed systems, discuss the **client application architecture** and how it communicates with the server. Modern web apps are interactive and dynamic; navigation doesn't need full page refreshes (JS fetches data and updates content/URL). Classic architectures apply (MVC, MVVM), and many React apps use a unidirectional reducer architecture (Flux/Redux).

### Key concept: the product category decides the deep-dive topics

Before optimizing, identify the one or two axes that define the product. Applying a generic checklist to every question reliably wastes the time that matters. E.g. e-commerce → SEO + performance (direct sales impact); messaging → real-time protocols (SEO is meaningless there).

### Commonly asked applications and what matters

| Application | Examples | Important features | Important topics |
| --- | --- | --- | --- |
| News feed | Facebook, Twitter | Feed list, feed interactions, post composer | Pagination approaches, performance |
| Messaging/Chat | Messenger, Slack, Discord | Real-time messaging | Real-time communication protocols |
| E-commerce | Amazon, eBay | Listing pages, product detail pages, cart & checkout | SEO, performance |
| Photo sharing | Instagram, Flickr, Google Photos | Browsing, editing, uploading | Media optimization |
| Travel booking | Airbnb, Skyscanner | Search UI, results, booking UI | SEO, performance |
| Video streaming | Netflix, YouTube | Video player, streaming | Streaming implementation |
| Pinterest | Pinterest | Masonry layout | Media optimizations |
| Collaborative apps | Google Docs/Sheets/Slides, Notion | Real-time collaboration | Collaboration protocols, conflict resolution, state syncing |
| Email client | Outlook, Apple Mail, Gmail | Mailbox syncing, mailbox UI, composer | App state, offline usage |
| Drawing | Figma, Excalidraw, Canva | Canvas, client state/data model, state management | Canvas rendering |
| Maps | Google/Apple Maps, Foursquare | Map rendering, displaying locations | Map rendering & interactions |
| File storage | Google Drive, Dropbox | Upload, download, file explorer | Uploading experience |
| Video conferencing | Zoom, Google Meet | Video streaming, viewing modes | Video streaming, performance |
| Ridesharing | Uber, Lyft | Trip booking, driver location | App state |
| Music streaming | Spotify, Apple Music | Audio streaming, player UI, playlists | Media streaming, app state |
| Games | Tetris, Snake | Game state, game loop, game logic | Same as features |

## 2. UI Components

Front End Engineers are expected to build the components an app needs (as in libraries like Radix UI, Bootstrap, Material UI, Chakra UI). Interview prompts almost always target the **interaction-heavy, accessibility-heavy** set — autocomplete, modal, dropdown, date picker, rich editor — not styled buttons.

### Approach for component questions

1. Determine the **subcomponents** (e.g. image carousel = current image, pagination buttons, preview thumbnails).
2. Define the **external-facing API** (props/options the component accepts).
3. Describe **internal component state**.
4. Define the **API between subcomponents** (if relevant).
5. Dive into **optimizations**: performance, accessibility (keyboard navigation, focus management, ARIA semantics), UX, security.

You may need to write small amounts of code to: (1) describe the component hierarchy, (2) describe the shape of component state, (3) explain non-trivial logic.

```jsx
<ImageCarousel
  images={...}
  onPrev={...}
  onNext={...}
  layout="horizontal">
  <ImageCarouselImage style={...} />
  <ImageThumbnail onClick={...} />
</ImageCarousel>
```

### Customizing theming

You will almost certainly be asked to design how developer-users customize the component's appearance. See GreatFrontEnd's "UI Components API Design Principles" guide for the approaches and comparisons (e.g. class injection, style props, CSS variables, render props/slots).

### Example component questions

Autocomplete · Dropdown menu · Image carousel · Embeddable poll widget · Rich text editor · Modal dialog · Data table (sorting + pagination) · Date picker · Multiselect

## What next

Use the RADIO framework (see `03_radio_framework.md`) to answer both question types in a structured way.

# Progressive Text Engagement Interface — Refined Implementation Plan

## Overview

This is the refined implementation plan for building a progressive reading interface for Pope Leo XIV's *Magnifica Humanitas*, incorporating feedback on the original proposal. The working prototype will be deployed to `https://matthewkudija.com/magnifica-humanitas/index.html`.

---

## Key Decisions (Departures from Original Proposal)

### 1. Name: Not "Lectio"

The name "Lectio" (from *lectio divina*) is overloaded in Catholic contexts. Proposed alternatives — pick one or suggest your own:

- **Gradus** — Latin for "step/stage," captures progressive engagement
- **Aperio** — Latin for "to open/reveal," captures the expand-to-reveal mechanic
- **Conspectus** — Latin for "overview/survey," captures the bird's-eye-to-detail movement
- **Viaticum Lectionis** — "provision for the journey of reading" (probably too long, but evocative)

For now the project directory is `magnifica-humanitas` and the tool can be named later. The immediate build focuses on this specific document.

### 2. Tech Stack: Vanilla HTML/CSS/JS (No React, No Tailwind)

**Decision**: Plain HTML + CSS + vanilla JavaScript, no build step.

**Rationale**:
- The `order-of-mass` repo uses exactly this stack and achieves the same UI patterns we need (floating TOC, footnote popups, responsive layout). It works, it's proven, it deploys trivially.
- React is overkill. This is a document viewer with expand/collapse, not an app with complex state mutations. The entire interactive state is: (1) which time tier is selected, (2) which passages are expanded. That's two variables.
- Tailwind adds a build step for no benefit — the CSS is ~300-500 lines total.
- Astro was the sub-agent's recommendation for a framework approach, and it's a good one. But given the `order-of-mass` precedent and the desire for self-contained simplicity, vanilla wins.
- Zero build step means: edit, refresh, deploy. Copy files to GitHub Pages. Done.

**Deployment**: Static files served from `https://matthewkudija.com/magnifica-humanitas/index.html` via GitHub Pages. No build, no CI/CD. Same pattern as `order-of-mass`.

### 3. Time Tiers: Based on Actual Document Analysis

The document is **~43,000 words** across **245 numbered paragraphs**, 5 chapters + introduction + conclusion, with **224 footnotes**. At ~200 wpm for dense theological text:

| Tier | Words | % of Document | Reading Time | What You Get |
|------|-------|---------------|-------------|--------------|
| **2 min** | ~400 | 1% | A single page | The thesis: what is this document and why does it matter |
| **10 min** | ~2,000 | 5% | Key arguments | Core argument of each chapter, the "skeleton" |
| **30 min** | ~6,000 | 14% | Substantial summary | Major sections with key passages, definitions, pivotal claims |
| **60 min** | ~12,000 | 28% | Deep reading | All important arguments, examples, key elaborations |
| **Full** | ~43,000 | 100% | ~3.5 hours | The complete text |

**Why these tiers, not 1/5/20/60/120**:
- 1 minute is too short to convey anything meaningful from a 43k-word encyclical — you'd get ~1 paragraph.
- 5 minutes gives only ~1,000 words (2%) — barely a skeleton. Better to merge with a slightly longer tier.
- 120 minutes (56% of text) is an awkward middle — you've committed 2 hours but still miss half. Better to jump to "Full."
- The 2/10/30/60/Full tiers create natural jumps: **glance → skeleton → substantial → deep → complete**.

### 4. AI Processing: Use Smallest Model Needed

The original proposal hardcoded `claude-sonnet-4-20250514`. Instead:

| Task | Model | Rationale |
|------|-------|-----------|
| **Essentiality scoring** | Sonnet | Requires nuanced judgment about theological arguments. Haiku would miss subtlety. |
| **Context notes** (what's skipped) | Haiku | Summarization of adjacent paragraphs. Straightforward. |
| **Footnote enrichment** (Bible passage lookup, source categorization) | Haiku | Structured extraction from footnote text. |
| **HTML parsing / text extraction** | None (Python) | Deterministic processing, no AI needed. |

Processing is done once, offline. The output `document.json` ships with the site. No API calls at runtime.

### 5. Progressive Reveal: Reading-Time Labels

The `···` ellipsis elements should indicate *how much reading time* you're expanding, not just "there's more here." When you click to expand a section:

- The ellipsis shows something like: `··· 3 min · The principle of subsidiarity applied to digital platforms`
- After expanding, if more is hidden, the next ellipsis appears with its own time estimate
- The top-level time display updates to reflect your current "expanded" reading time: `"30 min base + 8 min expanded = ~38 min"`

This makes progressive reveal feel intentional rather than arbitrary. You're always making an informed choice about where to spend your time.

Collapsing is equally important: click a section header or a "collapse" affordance to fold a section back to its summary state. This supports the **"zoom in, zoom out"** pattern — dive into Chapter 3 on AI, then pull back to skim Chapter 4 on work.

---

## Document Structure (from analysis)

### Chapters and Sections

```
INTRODUCTION (¶1-16)
  ├── The res novae of our time
  ├── Two biblical images
  ├── Building for the common good
  └── Remaining human

CHAPTER ONE: A DYNAMIC APPROACH FAITHFUL TO THE GOSPEL (¶17-45)
  ├── A Church journeying through human history
  │   ├── The wisdom of the word of God in dialogue with the human sciences
  │   └── Social Doctrine as a shared discernment
  └── The development of Social Doctrine from Leo XIII to the present
      ├── The first stages of the Church's Social Doctrine
      ├── The years of the Second Vatican Council
      ├── The recent Magisterium
      └── Interpreting history in the light of faith

CHAPTER TWO: FOUNDATIONS AND PRINCIPLES OF THE SOCIAL DOCTRINE (¶46-75)
  ├── The foundations of Social Doctrine
  │   ├── The human person: image of the Triune God
  │   ├── The equal dignity of all human beings
  │   └── The supreme value of human rights
  ├── The principles of Social Doctrine
  │   ├── The principle of the common good
  │   ├── The principle of the universal destination of goods
  │   ├── The principle of subsidiarity
  │   ├── The principle of solidarity
  │   └── The principle of social justice
  ├── Integral human development
  └── An examen for the Church

CHAPTER THREE: TECHNOLOGY AND DOMINANCE (¶76-130 est.)
  ├── The technocratic paradigm and digital power
  ├── Artificial intelligence
  │   ├── A valuable tool that requires vigilance
  │   └── Responsibility, transparency and the governance of AI
  ├── What must not be lost
  │   ├── Underlying narratives: transhumanism and posthumanism
  │   └── The limit, the heart and the grandeur of the human person
  ├── The authentic "more than human": grace and Christian humanism
  └── Two cities and two loves

CHAPTER FOUR: SAFEGUARDING HUMANITY — TRUTH, WORK, FREEDOM (¶131-195 est.)
  ├── Truth as a common good
  │   ├── Truth and democracy
  │   ├── Communication and the collective imagination
  │   ├── Toward an ecology of communication
  │   ├── An educational alliance for the digital age
  │   └── The central role of schools
  ├── The dignity of work at a time of digital transition
  │   ├── The value of work
  │   ├── The problem of unemployment
  │   ├── An economy that values dignity
  │   └── Families and young people: the social conditions for hope
  ├── Protecting freedom against dependencies and commercialization
  │   ├── Dependencies and societal control
  │   └── Breaking the chains of new forms of slavery
  └── A shared responsibility

CHAPTER FIVE: THE CULTURE OF POWER AND THE CIVILIZATION OF LOVE (¶196-235 est.)
  ├── The civilization of love in the digital age
  ├── The culture of power
  │   ├── The normalization of war
  │   ├── Force without limits
  │   ├── Weapons and artificial intelligence
  │   ├── The crisis of multilateralism
  │   └── A supposed political realism
  └── Building the civilization of love
      ├── We can all do our part
      ├── The need to disarm words
      ├── Building peace through justice
      ├── Adopting the perspective of victims
      ├── Cultivating a healthy realism
      ├── Reviving dialogue
      ├── The necessity of diplomacy and multilateralism
      └── Praying and hoping

CONCLUSION (¶236-245 est.)
  ├── The Word became flesh
  ├── One body in Christ
  ├── The construction site of our time
  └── The song of hope: the Magnificat
```

### Footnote Profile (224 footnotes)

| Category | Count (approx.) | Examples |
|----------|-----------------|----------|
| Papal encyclicals | ~52 | *Rerum Novarum*, *Laudato Si'*, *Fratelli Tutti* |
| Vatican II documents | ~16 | *Gaudium et Spes*, *Lumen Gentium*, *Dignitatis Humanae* |
| Papal exhortations | ~10 | *Evangelii Gaudium* |
| Curial/DDF documents | ~6 | *Dignitas Infinita*, *Compendium of Social Doctrine* |
| Biblical references (inline) | Many | Gen 1:26-27, Mt 25:14-30, Jn 10:10, Rev 21:2 |
| Church Fathers | ~1 | St. Augustine, *Confessions* |
| Leo XIV's own statements | ~6 | Prior addresses, original teaching |
| Secular/philosophical | ~8+ | Various |

---

## Architecture

### File Structure

```
magnifica-humanitas/
├── index.html                    # Main reading interface
├── styles.css                    # All styles (~400-600 lines)
├── app.js                        # Core application logic
├── toc.js                        # Table of contents (floating sidebar)
├── reading-pane.js               # Passage rendering + expand/collapse
├── footnotes.js                  # Right-panel footnote viewer
├── data/
│   └── document.json             # Pre-processed document (shipped with site)
├── scripts/
│   ├── parse-html.py             # Extract text + structure from Vatican HTML
│   ├── score-passages.py         # AI essentiality scoring (Sonnet)
│   ├── generate-context-notes.py # AI context notes for gaps (Haiku)
│   └── enrich-footnotes.py       # Categorize + expand footnotes (Haiku)
├── source/
│   └── magnifica-humanitas.html  # Original Vatican HTML
├── docs/
│   ├── 01-initial-claude-prompt.md
│   ├── 02-claude-output.md
│   ├── 03-claude-code-prompt.md
│   └── 04-claude-code-response.md  # This file
└── README.md
```

### Data Model (`document.json`)

```json
{
  "title": "Magnifica Humanitas",
  "subtitle": "On Safeguarding the Human Person in the Time of Artificial Intelligence",
  "author": "Pope Leo XIV",
  "date": "2026-05-15",
  "totalWords": 42940,
  "totalParagraphs": 245,
  "readingTimeTiers": [
    { "label": "2 min", "minutes": 2, "wordBudget": 400 },
    { "label": "10 min", "minutes": 10, "wordBudget": 2000 },
    { "label": "30 min", "minutes": 30, "wordBudget": 6000 },
    { "label": "60 min", "minutes": 60, "wordBudget": 12000 },
    { "label": "Full", "minutes": 215, "wordBudget": 42940 }
  ],
  "sections": [
    {
      "id": "introduction",
      "title": "Introduction",
      "level": 1,
      "subsections": [
        {
          "id": "res-novae",
          "title": "The res novae of our time",
          "level": 2,
          "passages": [
            {
              "id": "p-001",
              "paragraphNumber": 1,
              "text": "...",
              "wordCount": 120,
              "essentialityScore": 0.95,
              "essentialityReason": "Opening statement positioning the encyclical",
              "contextNote": "The Pope introduces the encyclical by...",
              "footnotes": [
                {
                  "number": 1,
                  "marker": "[1]",
                  "text": "Cf. Second Vatican Ecumenical Council...",
                  "category": "vatican-ii",
                  "sourceTitle": "Gaudium et Spes",
                  "biblePassage": null,
                  "fullText": null
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## UI Design

### Layout (Reusing `order-of-mass` Patterns)

Adopt the same layout architecture as `order-of-mass`:

```
┌─────────────────────────────────────────────────────────┐
│  Title · Author · Date · One-sentence description       │
│  [ 2 min ] [ 10 min ] [ 30 min ] [ 60 min ] [ Full ]   │
│  ~6,000 words · 30 min reading time · 14% of document   │
├──────────┬──────────────────────────────┬───────────────┤
│          │                              │               │
│  TOC     │   Reading Pane               │  Footnotes    │
│  (sticky │                              │  (slide-out)  │
│  240px)  │   Section heading            │               │
│          │   ¶1 passage text...         │  [1] Cf. GS   │
│  Intro   │   ¶2 passage text...         │  22. "The     │
│  Ch. 1   │                              │  mystery..."  │
│  Ch. 2 ← │   ··· 3 min · principles    │               │
│  Ch. 3   │       of social doctrine     │               │
│  Ch. 4   │                              │               │
│  Ch. 5   │   ¶15 passage text...        │               │
│  Concl.  │                              │               │
│          │                              │               │
└──────────┴──────────────────────────────┴───────────────┘
```

**TOC** (left, sticky):
- Mirrors `order-of-mass` implementation: `position: sticky; top: 20px; max-height: calc(100vh - 40px); overflow-y: auto`
- Hidden scrollbar, active section highlighted with left border accent
- Sections not included in current tier shown dimmed (not hidden)
- Indented subsections: `.toc-h2 { padding-left: 16px; }`
- Click scrolls smoothly to section
- Auto-tracks scroll position via `IntersectionObserver` (more efficient than scroll events)

**Reading Pane** (center, max-width 700px):
- Rendered passages in document order
- Section headings always visible, even when content is partially hidden
- Ellipsis gaps between included passages

**Footnote Panel** (right, slide-out 320px):
- Triggered by clicking footnote markers in text
- Slides in from right without navigating away
- Can stay open while scrolling
- Close button or click-outside to dismiss
- For Bible references: show the full passage text (enhancement, can be v2)
- Pattern from `liturgybible.github.io`: modal/popup with lazy-loaded reference text

### Mobile (< 1024px)
- TOC hidden (same as `order-of-mass`: `@media (max-width: 1024px) { #toc { display: none; } }`)
- Footnotes open as bottom sheet or modal instead of side panel
- Time selector becomes horizontally scrollable pills

### Aesthetic

Adopt the `order-of-mass` color palette with minor adjustments:

| Element | Color | Source |
|---------|-------|--------|
| Background | `#FAF8F2` | `order-of-mass` cream |
| Text | `#1C1A18` | Dark ink |
| Accent (headings, TOC active) | `#7B2E2B` | `order-of-mass` burgundy |
| AI-generated elements | `#B5943A` | Muted gold (distinct from text) |
| Footnote markers | Gray pill, burgundy hover | `order-of-mass` `.footnote-ref` pattern |
| Ellipsis gaps | Thin left gold border, muted background | Visually distinct from source text |

**Typography**:
- Body: Serif (system serif stack or load one web font — Lora or similar)
- UI chrome (TOC, time selector, metadata): System sans-serif
- AI context notes: Italic, slightly smaller, muted color, `✦` prefix, thin left border

### Ellipsis Gap Component

```html
<div class="ellipsis-gap" data-expand-time="3" data-passage-ids="p-045,p-046,p-047">
  <span class="ellipsis-dots">···</span>
  <span class="ellipsis-label">3 min · The principle of subsidiarity applied to digital platforms</span>
</div>
```

**Behavior**:
1. Default: shows `···` with time estimate and topic hint
2. Click: expands to show AI context note (what was skipped)
3. "Show passage" button within note: reveals actual text inline
4. After reveal: next `···` appears if more is hidden in that gap
5. Collapse: click section header or collapse affordance to fold back

**AI Context Note** (visually distinct):
```html
<div class="ai-context-note">
  <span class="ai-icon">✦</span>
  <p>The Pope applies the principle of subsidiarity to digital platforms, 
     arguing that algorithmic governance should not be centralized...</p>
  <button class="show-passage-btn">Show passage (3 min)</button>
</div>
```

---

## Processing Pipeline

### Step 1: Parse HTML → Structured Text (`parse-html.py`)

Input: `source/magnifica-humanitas.html` (Vatican website HTML)
Output: `data/raw-document.json` (structured text with paragraphs, sections, footnotes)

- Extract paragraph text, preserving paragraph numbers (¶1-245)
- Identify section headings from `<b>` tags (the Vatican HTML uses bold for headings, not semantic heading tags)
- Extract footnotes with their markers and text
- Identify inline Bible references
- Handle special characters, `&nbsp;`, italics for Latin phrases

No AI needed. Pure Python HTML parsing.

### Step 2: Score Essentiality (`score-passages.py`)

Input: `data/raw-document.json`
Output: `data/scored-document.json`

For each passage, send to **Sonnet** with section context:

```
You are analyzing paragraph ¶{n} from "Magnifica Humanitas" by Pope Leo XIV.

Section: {section_title}
Subsection: {subsection_title}

Previous paragraph (for context): {prev_text[:200]}

This paragraph: {text}

Next paragraph (for context): {next_text[:200]}

Rate this paragraph's essentiality on a 0.0–1.0 scale for a reader trying to 
understand the document's core argument and this section's contribution to it.

High scores (0.8-1.0): Key thesis statements, definitions, pivotal arguments, 
  novel claims, direct AI-related teaching
Medium scores (0.4-0.7): Important supporting arguments, significant examples, 
  transitions between major ideas
Low scores (0.0-0.3): Elaboration, repetition of earlier points, historical 
  detail that doesn't advance the argument, rhetorical amplification

Return JSON: {"score": 0.0-1.0, "reason": "one sentence"}
```

**Batch by section** to maintain context window efficiency. ~245 paragraphs, batched in groups of ~20-30 per API call.

### Step 3: Generate Context Notes (`generate-context-notes.py`)

Input: `data/scored-document.json`
Output: `data/document-with-notes.json`

For each gap between selected passages at each tier, send to **Haiku**:

```
A reader is skipping paragraphs ¶{start}-¶{end} of "Magnifica Humanitas."
The skipped text covers: {skipped_text[:500]}

Write a 1-2 sentence note explaining what the reader is skipping, focusing on 
what they'd miss that matters for understanding the document's argument.
Do NOT summarize — describe what's there so the reader can decide whether to expand.
```

### Step 4: Enrich Footnotes (`enrich-footnotes.py`)

Input: `data/document-with-notes.json`
Output: `data/document.json` (final)

For each footnote, use **Haiku** to:
1. Categorize: `papal-encyclical`, `vatican-ii`, `bible`, `church-father`, `secular`, `leo-xiv-original`
2. Extract source title (e.g., "Gaudium et Spes")
3. For Bible references: extract book/chapter/verse for potential full-text lookup
4. Flag footnotes that contain Leo XIV's original teaching (not citing predecessors)

---

## Implementation Plan

### Phase 1: Parse and Build Static Shell
1. Write `parse-html.py` to extract structured text from Vatican HTML
2. Build `index.html` with layout (TOC + reading pane + footnote panel)
3. Wire up `styles.css` using `order-of-mass` patterns as starting point
4. Create sample `document.json` with a few manually-scored sections for development
5. Get the reading experience working with static data

### Phase 2: Core Interactivity
1. Implement time tier selector and passage filtering logic (`app.js`)
2. Implement `···` ellipsis gap component with expand/collapse
3. Implement TOC scroll tracking and active section highlighting
4. Implement footnote panel slide-out
5. Test the full read flow at each time tier

### Phase 3: AI Processing Pipeline
1. Build and run `score-passages.py` (Sonnet) on the full document
2. Build and run `generate-context-notes.py` (Haiku) for all tiers
3. Build and run `enrich-footnotes.py` (Haiku)
4. Assemble final `document.json`
5. Validate: does the 10-min tier actually capture the core argument? Iterate on scoring.

### Phase 4: Polish and Deploy
1. Responsive design (mobile layout)
2. Reading time display updates as passages are expanded
3. Smooth scroll, keyboard navigation
4. Performance: ensure instant tier switching (all data is local, just show/hide)
5. Deploy to GitHub Pages

---

## Future Extensions (Designed For, Not Built)

These are noted to inform architecture decisions, not to build now:

1. **Footnote enrichment**: For Bible references, fetch and display the full passage text in the footnote panel (similar to `liturgybible.github.io` patterns — lazy-load JSON data, render in popup/panel). For papal documents, link to full text on vatican.va.

2. **Multi-document corpus**: Process other CST documents (*Rerum Novarum*, *Laudato Si'*, etc.) and cross-link references. The `document.json` format supports this — each document is independent, references can link between them.

3. **Obsidian export**: Click a passage to copy it as markdown with citation metadata (`> "passage text" — *Magnifica Humanitas* ¶42`).

4. **Configurable text source**: A processing UI for any text/URL. The pipeline is already document-agnostic; just needs a frontend.

5. **Reading session state**: LocalStorage to remember which tier you were on, which sections you expanded, scroll position. Resume where you left off.

6. **Progressive tier labels**: Instead of fixed time labels, dynamically update to reflect expanded state: "30 min base + 12 min expanded in Ch. 3 = ~42 min total."

---

## Open Questions for User

1. **Name**: Any preference among Gradus/Aperio/Conspectus, or another idea? Or just ship it as "Magnifica Humanitas" (the document name, not the tool name) for now?

2. **Time tiers**: The proposed 2/10/30/60/Full — do these feel right? Would you prefer different breakpoints?

3. **Footnote depth (v1)**: For v1, should footnotes just show the footnote text from the document? Or should we also categorize them and add source links? (Full Bible passage expansion would be v2.)

4. **AI context notes**: Should these be visible by default in the ellipsis gaps, or hidden behind a click? The current design hides them behind click to keep the reading pane clean.

5. **Scope of v1**: Build the full pipeline (parsing + AI scoring + all 5 tiers working) before deploying? Or deploy a working shell with manually-curated tiers for the Introduction + Chapter 3 (the AI-specific chapter) first, then expand?

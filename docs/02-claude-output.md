This is a beautifully conceived idea, Matthew — essentially a “progressive disclosure” reading interface that respects both the integrity of the source text and your finite time. Let me write a detailed Claude Code prompt for you.

Here’s the prompt:

Claude Code Prompt: Progressive Text Engagement Interface

Build a web application called “Lectio” — a progressive text engagement interface. The immediate use case is Pope Leo XIV’s Magnifica Humanitas (a ~40,000-word document on AI), but the system must be architected to work with any structured long-form text.

Core Concept

The reader selects how much time they have. The app surfaces only the most essential passages for that time window, with natural affordances to dive deeper without losing the main flow. The goal is to honor the source text — every word shown is the actual document, never a summary pretending to be the text.

Architecture

Stack: React (single-page app), with Tailwind for layout and a clean editorial aesthetic. Use the Anthropic API (claude-sonnet-4-20250514) for all AI processing steps.

Data model for a processed document:

{
  "title": "Magnifica Humanitas",
  "author": "Pope Leo XIV",
  "date": "2025",
  "totalWords": 40000,
  "sections": [
    {
      "id": "sec-1",
      "title": "Introduction",
      "level": 1,
      "passages": [
        {
          "id": "p-001",
          "text": "...",
          "wordCount": 120,
          "essentialityScore": 0.95,  // 0–1, AI-generated
          "aiContextNote": "...",       // brief AI note on what's skipped before/after
          "footnotes": [...],
          "references": [...]
        }
      ]
    }
  ]
}


Processing Pipeline (run once per document)

Build a Node.js script process-document.js that:

        1.      Ingests a plain text or markdown file with structural markers (headings, footnotes, paragraph breaks).
        2.      Chunks the document into paragraphs, grouped by section.
        3.      Scores each passage for essentiality via the Anthropic API. Send sections in batches. Prompt the model:
“You are analyzing a passage from [document title]. Rate this passage’s essentiality on a 0.0–1.0 scale based on how much a reader would lose if they skipped it while trying to understand the whole work and this section. Consider: Is it a key argument? A definition? A pivot point? Or is it elaboration, example, or repetition? Return only a JSON object: {score: 0.0-1.0, reason: "one sentence"}”
        4.      Generates a short context note for each non-essential passage (what a reader misses if they skip it) — these are clearly marked as AI-generated.
        5.      Outputs a document.json file.

Time-to-word-count mapping (tune these):

        •       1 min → ~200 words
        •       5 min → ~1,000 words
        •       20 min → ~4,000 words
        •       1 hr → ~12,000 words
        •       2 hr → ~24,000 words

For each time window, include passages in descending essentiality order until the word budget is exhausted, but preserve reading order in the final display (re-sort by document position after selection).

UI: Main Reading Interface

Layout:

        •       Left sidebar (fixed, ~220px): floating TOC showing all sections. Active section highlighted. Sections not included in current time window are shown dimmed but visible, so you always know where you are in the whole work.
        •       Center column (~680px max-width): the reading pane.
        •       Right panel (slide-out, ~320px): footnote/reference viewer — appears when a footnote or reference is clicked, slides in without navigating away.

Top of page:

        •       Document title, author, date
        •       A one-sentence description of the document
        •       Time selector: pill buttons — 1 min · 5 min · 20 min · 1 hr · 2 hr
        •       Word count and estimated read time shown for current selection

Reading pane behavior:

        •       Render included passages in document order with their actual text.
        •       Between included passages (i.e., where text is skipped), show a ··· ellipsis element. Clicking it reveals a subtle AI context note (visually distinct — italic, slightly muted color, with a small ✦ icon prefix and a thin left border) explaining what was skipped. A “Show passage” button within that note expands the actual skipped text inline.
        •       Footnote markers in the text are clickable — they open the footnote in the right panel without interrupting reading flow.
        •       Section headings are shown even when their content is partially skipped.

Progressive reveal:

        •       Each ··· can be clicked to show one more “layer” — the next-highest essentiality passage in that gap.
        •       After revealing, another ··· appears if more is still hidden.

Aesthetic Direction

Editorial and refined — think The Atlantic meets a scholarly critical edition.

        •       Typography: Lora or Freight Text for body (serif, warm), DM Sans or Söhne for UI chrome.
        •       Color: warm off-white background (#FAF8F4), dark ink text (#1C1A18), muted gold accent (#B5943A) for AI-generated elements and interactive affordances.
        •       The AI context notes must be visually unmistakable as not-the-text — italic, slightly smaller, different background tint, prefixed with a small icon.
        •       No clutter. The text is the hero.

File Structure

lectio/
├── public/
├── src/
│   ├── App.jsx
│   ├── components/
│   │   ├── TimeSelector.jsx
│   │   ├── TOC.jsx
│   │   ├── ReadingPane.jsx
│   │   ├── Passage.jsx
│   │   ├── EllipsisGap.jsx       // the ··· skipped-text element
│   │   ├── FootnotePanel.jsx     // right slide-out
│   │   └── AIContextNote.jsx
│   ├── hooks/
│   │   └── useDocumentSelection.js  // given doc + time budget, returns ordered passages
│   └── data/
│       └── document.json         // pre-processed document
├── scripts/
│   └── process-document.js       // the processing pipeline
├── package.json
└── README.md


Future Extension Points (build with these in mind but don’t implement)

        •       Multi-document mode: navigate a corpus (e.g., all Catholic social teaching documents) with cross-references linking between them.
        •       Obsidian export: highlight a passage and export it as a markdown clip with citation metadata.
        •       Reading session state: save progress so you can return and “go deeper” in a subsequent session.
        •       Configurable text source: a UI for pasting in any text or URL to run the processing pipeline on-demand.

Start here

        1.      Scaffold the React app with the layout (TOC + reading pane + footnote panel), wired up to a small sample dataset (use the first two sections of MH, or fabricate plausible structured content).
        2.      Implement useDocumentSelection — the hook that takes a document and a time budget and returns the selected passages in order.
        3.      Implement the EllipsisGap component with the expand-on-click behavior.
        4.      Get the reading experience working end-to-end before wiring the Anthropic API.
        5.      Then add the processing pipeline script.

A few notes on this prompt:

The essentiality scoring is the hardest and most important piece — you may want to iterate on that prompt. Sending section context (not just the isolated paragraph) to the model will produce much better scores.

For MH specifically, the Vatican has the full text at vatican.va — you’ll want to grab the plain text version and pre-process it once, then ship document.json with the app.

The “body of texts” vision (CST corpus, references, etc.) is the long game. The architecture above supports it — each external reference becomes its own processable document, and footnotes/references can link to them when they’re available.

Want me to go ahead and build the initial artifact from this prompt, or refine any part of it first?
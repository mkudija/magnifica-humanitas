# How passage scoring works

This document records exactly how the per-paragraph **essentiality scores** that
power the reading-time tiers (2 / 5 / 10 / 30 / 60 min) are produced, so a future
human or LLM can understand, trust, and regenerate them. Read this before changing
any score.

## TL;DR

- Every paragraph has an `essentialityScore` (0.0–1.0). Higher = more essential to
  the document's core argument.
- The browser (`app.js`) sorts paragraphs by that score and greedily fills each
  tier's **word budget**; whatever fits, shows. Everything else collapses into the
  `···` gaps. So **the score decides what appears in the short views.**
- Scores are an **LLM pass over the real text, calibrated to the reader's own
  highlights** (the Obsidian note `~Magnifica Humanitas`).
- **`data/document.json` is authoritative for the page.** Editing a score there
  changes the site immediately. `scripts/score-passages.py` regenerates it.

## Data flow

```
source/magnifica-humanitas.html
        │  scripts/parse-html.py
        ▼
data/raw-document.json ──► data/document.json   ◄── THE FILE THE APP LOADS (app.js fetches this)
                               ▲        ▲
                               │        │ footnote sourceTitle/category: scripts/enrich-footnotes.py
                               │
        scripts/score-passages.py  writes essentialityScore + scoreReason
        (also writes data/scored-document.json as a copy of the run output)
```

> ⚠️ There is **no build step that rebuilds `document.json` from the other data
> files.** `document.json` is the committed, authoritative artifact. `score-passages.py`
> patches it in place. `data/raw-document.json`, `data/scored-document.json`, and
> `data/enriched-footnotes.json` are git-ignored, regenerable intermediates.

## What "essential" means here — calibration to reader anchors

The scores are **not** generic. The reader (Matthew Kudija) read the encyclical and
saved the paragraphs he found important in the Obsidian note **`~Magnifica Humanitas`**
(`Reading Notes/`). Those saved paragraphs are extracted into:

- **`data/scoring-anchors.json`** — a committed file so scoring no longer depends on
  the private Obsidian vault. It contains:
  - `anchors`: `{ "<paragraph#>": "<the quote the reader saved>" }` — the calibration set.
  - `score_floor` (0.90): every anchored paragraph is floored to at least this, so a
    reader-flagged paragraph can never rank below un-flagged material.
  - `explicit_overrides` (e.g. `{"100": 0.96}`): exact scores the reader dictated.

The anchors do double duty: they are passed to the LLM as **exemplars of what this
reader considers essential** (so non-anchored paragraphs are weighted consistently),
and they are enforced afterward as a **deterministic floor + overrides**.

To refresh the anchors after editing the Obsidian note, re-run the extraction in
"Regenerating" below.

## The scoring rubric

`scripts/score-passages.py` sends each paragraph (with its chapter/section, its
neighbours for context, and the anchor exemplars) to an LLM with this scale:

| Score | Meaning |
|------|---------|
| 0.85–1.00 | Central thesis, pivotal claims, definitions of the five principles, the distinctive moral teaching on AI/technology, the concluding program |
| 0.55–0.84 | Important supporting arguments, application of a principle, key examples/transitions |
| 0.30–0.54 | Elaboration, secondary examples, historical-survey detail, rhetorical amplification |
| 0.00–0.29 | Minor connective or repetitive material |

## Provenance of the current scores

The scores currently committed in `data/document.json` were generated **2026-06-13 by
Claude Opus 4.8 in-session (Claude Code)**, reading the full source text and
calibrating to `data/scoring-anchors.json`. See `document.json → scoringMetadata`.

> **History / pitfall:** before this, `score-passages.py` held a hand-typed
> `PARAGRAPH_SCORES` dict whose "reasons" referenced a **hallucinated outline**
> (e.g. a non-existent "Chapter 6 – Education and Formation", "AI and Human Work").
> Those numbers were never grounded in the real text and never used the reader's
> notes. They have been replaced. The real document has 5 chapters:
> 1. A Dynamic Approach Faithful to the Gospel
> 2. Foundations and Principles of the Social Doctrine of the Church
> 3. Technology and Dominance — The Grandeur of Humanity in Light of the Promises of AI
> 4. Safeguarding Humanity — Truth, Work, Freedom
> 5. The Culture of Power and the Civilization of Love

## Regenerating

**Re-score all paragraphs (LLM pass):**

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
# optional: export ANTHROPIC_MODEL=claude-sonnet-4-6   (default)
python scripts/score-passages.py            # writes document.json + scored-document.json
python scripts/score-passages.py --dry-run  # build prompts only; works with no API key
```

LLM scoring is non-deterministic, so numbers vary slightly run-to-run; the anchor
floor and overrides are deterministic.

**Refresh anchors from the Obsidian note** (paragraph numbers are the `(N)` markers
on saved quotes):

```python
import re, json
note = open("/Users/mkudija/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Reading Notes/~Magnifica Humanitas.md").read()
anchors = {}
for line in note.splitlines():
    s = line.strip()
    for m in re.finditer(r"\((\d{1,3})(?:,[^)]*)?\)", s):
        n = int(m.group(1))
        if 1 <= n <= 245:
            anchors.setdefault(n, re.sub(r'^[->\s"*]+', "", s)[:160])
cfg = json.load(open("data/scoring-anchors.json"))
cfg["anchors"] = {str(n): anchors[n] for n in sorted(anchors)}
json.dump(cfg, open("data/scoring-anchors.json", "w"), indent=2, ensure_ascii=False)
```

**Change one score by hand:** edit `essentialityScore` for that paragraph in
`data/document.json` (and, to keep the source consistent, add it to
`explicit_overrides` in `data/scoring-anchors.json`).

## Tuning what shows per tier

The amount shown at each tier is the **word budget**, set in `app.js`
(`App.tiers`, ~line 32) and/or `readingTimeTiers` in the data. Bigger budget →
more (lower-scored) paragraphs survive. The selection algorithm is
`computeIncludedPassages()` in `app.js`.

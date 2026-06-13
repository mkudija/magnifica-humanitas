#!/usr/bin/env python3
"""
Score every paragraph of Magnifica Humanitas for *essentiality* (0.0-1.0).

This is a real, grounded LLM scoring pass — NOT a hand-typed table of numbers.
An earlier version of this file hard-coded a static `PARAGRAPH_SCORES` dict whose
"reasons" were written against a hallucinated chapter outline (e.g. a non-existent
"Chapter 6 - Education") and never read the actual paragraph text or the reader's
notes. This version:

  1. Reads the ACTUAL paragraph text from data/document.json.
  2. Reads reader-supplied calibration ANCHORS from data/scoring-anchors.json
     (paragraphs the reader saved as important in the Obsidian note
     "~Magnifica Humanitas"). These define what "important" means here.
  3. Scores each paragraph with an LLM, giving it section context, its neighbours,
     and the calibration anchors so the model matches the reader's sense of weight.
  4. Floors every anchored paragraph at `score_floor` and applies any explicit
     overrides (e.g. paragraph 100 = 0.96) so a saved-important paragraph can
     never be ranked below un-flagged material.
  5. Writes data/scored-document.json AND patches the live data/document.json
     (essentialityScore + scoreReason on every paragraph).

How the front end uses these scores: app.js sorts paragraphs by essentialityScore
(descending) and greedily fills each reading-time tier's word budget. So the score
is what decides which paragraphs survive the 2/5/10/30-min views. See docs/scoring.md.

-------------------------------------------------------------------------------
Provenance of the CURRENTLY COMMITTED scores
-------------------------------------------------------------------------------
The scores presently in data/document.json were generated on 2026-06-13 by
Claude Opus 4.8 running in-session (Claude Code), reading the full source text and
calibrating to data/scoring-anchors.json. Running this script with an API key
reproduces/refreshes that pass; because LLM scoring is non-deterministic, exact
numbers will vary slightly between runs, but the anchor floor and overrides are
deterministic. The data files (not this script) hold the authoritative output.

-------------------------------------------------------------------------------
Running
-------------------------------------------------------------------------------
    pip install anthropic
    export ANTHROPIC_API_KEY=...            # or set ANTHROPIC_MODEL to override
    python scripts/score-passages.py        # scores all paragraphs, writes data files
    python scripts/score-passages.py --dry-run   # build prompts, don't call the API

If the `anthropic` SDK or API key is unavailable, the script explains what to do
and exits without touching the data files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DOCUMENT_JSON = ROOT / "data" / "document.json"
ANCHORS_JSON = ROOT / "data" / "scoring-anchors.json"
SCORED_JSON = ROOT / "data" / "scored-document.json"

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

RUBRIC = """\
You are scoring a single paragraph of Pope Leo XIV's encyclical *Magnifica Humanitas*
(on safeguarding the human person in the age of artificial intelligence) for its
ESSENTIALITY: how much a reader on a tight time budget needs THIS paragraph to grasp
the document's core argument.

Return a score from 0.0 to 1.0:
  0.85-1.00  Central thesis, pivotal claims, definitions of the core principles,
             the document's distinctive moral teaching on AI/technology, and the
             concluding program of action.
  0.55-0.84  Important supporting arguments, the application of a principle,
             significant examples, key transitions.
  0.30-0.54  Elaboration, secondary examples, historical survey detail, and
             rhetorical amplification that develop but do not carry the argument.
  0.00-0.29  Minor connective or repetitive material.

CALIBRATION: The reader has marked certain paragraphs as important (see the anchor
examples below). Treat those as exemplars of what this reader considers essential —
the encyclical's framing images (Babel / Nehemiah), the five principles of Social
Doctrine, the core anthropological teaching on what AI is and is not, and the
concluding spiritual program. Weight paragraphs that do similar work accordingly.

Respond with ONLY a JSON object: {"score": <float>, "reason": "<one concise sentence>"}.
"""


def load_paragraphs() -> list[dict]:
    doc = json.loads(DOCUMENT_JSON.read_text(encoding="utf-8"))
    chapter_titles = {c["id"]: c["title"] for c in doc.get("chapters", [])}
    paras = sorted(doc["allParagraphs"], key=lambda p: p["paragraphNumber"])
    for p in paras:
        p["_chapterTitle"] = chapter_titles.get(p.get("chapterId"), p.get("chapterId", ""))
    return paras


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)          # strip inline HTML
    text = re.sub(r"\{\{FN:\d+\}\}", "", text)    # strip footnote placeholders
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def anchor_examples(paras: list[dict], anchors: set[int], limit: int = 6) -> str:
    """A few short exemplars of reader-flagged-important paragraphs for calibration."""
    by_num = {p["paragraphNumber"]: p for p in paras}
    lines: list[str] = []
    for n in sorted(anchors):
        if n in by_num and len(lines) < limit:
            snippet = clean_text(by_num[n]["text"])[:160]
            lines.append(f"  - ¶{n}: {snippet}...")
    return "\n".join(lines)


def build_prompt(p: dict, prev: Optional[dict], nxt: Optional[dict], examples: str) -> str:
    parts = [RUBRIC, "", "Reader-flagged-important exemplars:", examples, ""]
    parts.append(f"Chapter: {p['_chapterTitle']}")
    if p.get("sectionTitle"):
        parts.append(f"Section: {p['sectionTitle']}")
    if prev:
        parts.append(f"\nPrevious paragraph (context): {clean_text(prev['text'])[:300]}")
    parts.append(f"\nParagraph to score (¶{p['paragraphNumber']}): {clean_text(p['text'])}")
    if nxt:
        parts.append(f"\nNext paragraph (context): {clean_text(nxt['text'])[:300]}")
    return "\n".join(parts)


def score_with_anthropic(client, model: str, prompt: str) -> tuple[float, str]:
    msg = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in model response: {raw!r}")
    obj = json.loads(match.group(0))
    return float(obj["score"]), str(obj["reason"]).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Score Magnifica Humanitas paragraphs for essentiality.")
    ap.add_argument("--dry-run", action="store_true", help="build prompts but do not call the API")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Anthropic model id (default {DEFAULT_MODEL})")
    args = ap.parse_args()

    paras = load_paragraphs()
    anchor_cfg = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))
    anchors = {int(k) for k in anchor_cfg["anchors"]}
    floor = float(anchor_cfg.get("score_floor", 0.9))
    overrides = {int(k): float(v) for k, v in anchor_cfg.get("explicit_overrides", {}).items()}
    examples = anchor_examples(paras, anchors)

    if args.dry_run:
        sample = build_prompt(paras[0], None, paras[1], examples)
        print(f"[dry-run] {len(paras)} paragraphs, {len(anchors)} anchors, floor={floor}, overrides={overrides}")
        print("\n----- sample prompt (¶1) -----\n" + sample)
        return 0

    try:
        import anthropic  # imported here so --dry-run works without the SDK
    except ImportError:
        print("The 'anthropic' SDK is not installed. Run: pip install anthropic", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Export it and re-run.", file=sys.stderr)
        return 2

    client = anthropic.Anthropic()
    scores: dict[int, tuple[float, str]] = {}
    for i, p in enumerate(paras):
        prev = paras[i - 1] if i > 0 else None
        nxt = paras[i + 1] if i + 1 < len(paras) else None
        num = p["paragraphNumber"]
        score, reason = score_with_anthropic(client, args.model, build_prompt(p, prev, nxt, examples))
        scores[num] = (max(0.0, min(1.0, score)), reason)
        print(f"¶{num}: {scores[num][0]:.2f}  {reason[:70]}")

    # Deterministic calibration: anchor floor + explicit overrides.
    for num in anchors:
        s, r = scores[num]
        if s < floor:
            scores[num] = (floor, r)
    for num, val in overrides.items():
        scores[num] = (val, scores[num][1])

    write_outputs(paras, scores, anchor_cfg, args.model)
    return 0


def write_outputs(paras: list[dict], scores: dict[int, tuple[float, str]], anchor_cfg: dict, model: str) -> None:
    doc = json.loads(DOCUMENT_JSON.read_text(encoding="utf-8"))
    for p in doc["allParagraphs"]:
        s, r = scores[p["paragraphNumber"]]
        p["essentialityScore"] = s
        p["scoreReason"] = r
    doc["scoringMetadata"] = {
        "method": "LLM essentiality scoring grounded in the full source text, calibrated to reader anchors",
        "model": model,
        "anchorsFile": "data/scoring-anchors.json",
        "anchorFloor": anchor_cfg.get("score_floor"),
        "explicitOverrides": anchor_cfg.get("explicit_overrides"),
        "regenerateWith": "scripts/score-passages.py  (see docs/scoring.md)",
    }
    DOCUMENT_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    SCORED_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {DOCUMENT_JSON.relative_to(ROOT)} and {SCORED_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())

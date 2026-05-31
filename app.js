/* ============================================================
   app.js — Core application state and data loading
   ============================================================ */

// Global application state
const App = {
  data: null,               // loaded document.json
  tiers: [],                // readingTimeTiers
  activeTierIndex: 2,       // default to 30 min
  includedPassageIds: new Set(),  // passages visible in current tier
  expandedPassageIds: new Set(),  // passages manually expanded by user
  allPassages: [],           // flat list of all passages with chapter/section metadata
  footnoteMap: {},           // number -> footnote object
  expandedWords: 0,          // word count of manually expanded passages
};

/* ---------- Data Loading ---------- */

async function loadData() {
  try {
    const resp = await fetch('data/document.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    App.data = await resp.json();
  } catch (err) {
    document.getElementById('reading-pane').innerHTML =
      '<p style="padding:2rem;color:#7B2E2B;">Error loading document data. Please ensure data/document.json exists.</p>';
    console.error('Failed to load document.json:', err);
    return;
  }

  // Build tiers
  App.tiers = App.data.readingTimeTiers || [
    { label: '2 min', minutes: 2, wordBudget: 400 },
    { label: '10 min', minutes: 10, wordBudget: 2000 },
    { label: '30 min', minutes: 30, wordBudget: 6000 },
    { label: '60 min', minutes: 60, wordBudget: 12000 },
    { label: 'Full (~3 hrs)', minutes: 185, wordBudget: App.data.totalWords },
  ];

  // Build flat passage list and footnote map
  buildPassageIndex();
  buildFootnoteMap();

  // Render header
  renderHeader();

  // Set initial tier
  selectTier(App.activeTierIndex);
}

/* ---------- Passage Index ---------- */

function buildPassageIndex() {
  App.allPassages = [];
  const chapters = App.data.chapters || [];

  for (const chapter of chapters) {
    // Passages directly under chapter (not in a section)
    if (chapter.passages) {
      for (const p of chapter.passages) {
        App.allPassages.push({
          ...p,
          chapterId: chapter.id,
          chapterTitle: chapter.title,
          sectionId: null,
          sectionTitle: null,
        });
      }
    }
    // Sections
    if (chapter.sections) {
      for (const section of chapter.sections) {
        if (section.passages) {
          for (const p of section.passages) {
            App.allPassages.push({
              ...p,
              chapterId: chapter.id,
              chapterTitle: chapter.title,
              sectionId: section.id,
              sectionTitle: section.title,
            });
          }
        }
      }
    }
  }
}

/* ---------- Footnote Map ---------- */

function buildFootnoteMap() {
  App.footnoteMap = {};
  if (App.data.footnotes) {
    for (const fn of App.data.footnotes) {
      App.footnoteMap[fn.number] = fn;
    }
  }
}

/* ---------- Header Rendering ---------- */

function renderHeader() {
  const subtitle = document.getElementById('doc-subtitle');
  subtitle.textContent = `${App.data.author} · ${App.data.subtitle}`;

  const controls = document.getElementById('tier-controls');
  controls.innerHTML = '';

  App.tiers.forEach((tier, i) => {
    const btn = document.createElement('button');
    btn.className = 'tier-pill' + (i === App.activeTierIndex ? ' active' : '');
    btn.textContent = tier.label;
    btn.setAttribute('data-tier', i);
    btn.addEventListener('click', () => selectTier(i));
    controls.appendChild(btn);
  });
}

/* ---------- Tier Selection ---------- */

function selectTier(index) {
  App.activeTierIndex = index;
  const tier = App.tiers[index];

  // Clear expanded state when switching tiers
  App.expandedPassageIds.clear();
  App.expandedWords = 0;

  // Update pill UI
  document.querySelectorAll('.tier-pill').forEach((btn, i) => {
    btn.classList.toggle('active', i === index);
  });

  // Compute which passages to include
  computeIncludedPassages(tier);

  // Update status line
  updateTierStatus();

  // Render reading pane
  renderReadingPane();

  // Build / update TOC
  renderTOC();
}

/* ---------- Passage Selection Algorithm ---------- */

function computeIncludedPassages(tier) {
  App.includedPassageIds.clear();

  const isFull = (tier.wordBudget >= App.data.totalWords);
  if (isFull) {
    // Include everything
    for (const p of App.allPassages) {
      App.includedPassageIds.add(p.id);
    }
    return;
  }

  // Sort by essentialityScore descending, then by paragraphNumber ascending for ties
  const scored = App.allPassages.map(p => ({
    id: p.id,
    score: p.essentialityScore != null ? p.essentialityScore : 0.5,
    wordCount: p.wordCount || 0,
    paragraphNumber: p.paragraphNumber || 0,
  }));

  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.paragraphNumber - b.paragraphNumber;
  });

  let budget = tier.wordBudget;
  for (const item of scored) {
    if (item.wordCount <= budget) {
      App.includedPassageIds.add(item.id);
      budget -= item.wordCount;
    }
    if (budget <= 0) break;
  }
}

/* ---------- Tier Status ---------- */

function updateTierStatus() {
  const status = document.getElementById('tier-status');
  const tier = App.tiers[App.activeTierIndex];
  const isFull = (tier.wordBudget >= App.data.totalWords);

  // Count included words
  let baseWords = 0;
  for (const p of App.allPassages) {
    if (App.includedPassageIds.has(p.id)) {
      baseWords += (p.wordCount || 0);
    }
  }

  const pct = Math.round((baseWords / App.data.totalWords) * 100);

  if (isFull) {
    status.textContent = `~${numberWithCommas(App.data.totalWords)} words · ~${tier.minutes} min reading time · Full document`;
  } else if (App.expandedWords > 0) {
    const expandedMin = Math.round(App.expandedWords / 200);
    const totalMin = tier.minutes + expandedMin;
    const totalWords = baseWords + App.expandedWords;
    const totalPct = Math.round((totalWords / App.data.totalWords) * 100);
    status.textContent = `${tier.minutes} min base + ${expandedMin} min expanded = ~${totalMin} min · ${totalPct}% of document`;
  } else {
    status.textContent = `~${numberWithCommas(baseWords)} words · ${tier.minutes} min reading time · ${pct}% of document`;
  }
}

/* ---------- Expand / Collapse Passages ---------- */

function expandPassage(passageId) {
  const p = App.allPassages.find(x => x.id === passageId);
  if (!p) return;
  App.expandedPassageIds.add(passageId);
  App.expandedWords += (p.wordCount || 0);
  updateTierStatus();

  // Preserve approximate scroll position by tracking a nearby element
  const scrollAnchor = findScrollAnchor();
  renderReadingPane();
  renderTOC();
  restoreScrollAnchor(scrollAnchor);

  // Then scroll to the newly expanded passage
  requestAnimationFrame(() => {
    const el = document.getElementById(passageId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
}

function collapsePassage(passageId) {
  const p = App.allPassages.find(x => x.id === passageId);
  if (!p) return;
  App.expandedPassageIds.delete(passageId);
  App.expandedWords = Math.max(0, App.expandedWords - (p.wordCount || 0));
  updateTierStatus();

  const scrollAnchor = findScrollAnchor();
  renderReadingPane();
  renderTOC();
  restoreScrollAnchor(scrollAnchor);
}

/* ---------- Scroll Position Helpers ---------- */

function findScrollAnchor() {
  // Find the first visible passage or heading to anchor scroll restoration
  const headerH = document.getElementById('site-header')?.offsetHeight || 0;
  const els = document.querySelectorAll('.passage, .chapter-heading, .section-heading');
  for (const el of els) {
    const rect = el.getBoundingClientRect();
    if (rect.top >= headerH - 10) {
      return { id: el.id, offsetFromTop: rect.top };
    }
  }
  return null;
}

function restoreScrollAnchor(anchor) {
  if (!anchor || !anchor.id) return;
  requestAnimationFrame(() => {
    const el = document.getElementById(anchor.id);
    if (el) {
      const rect = el.getBoundingClientRect();
      const diff = rect.top - anchor.offsetFromTop;
      window.scrollBy(0, diff);
    }
  });
}

/* ---------- Keyboard Navigation ---------- */

document.addEventListener('keydown', (e) => {
  // Don't intercept when focused on an input or textarea
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

  if (e.key === 'ArrowLeft') {
    e.preventDefault();
    if (App.activeTierIndex > 0) selectTier(App.activeTierIndex - 1);
  } else if (e.key === 'ArrowRight') {
    e.preventDefault();
    if (App.activeTierIndex < App.tiers.length - 1) selectTier(App.activeTierIndex + 1);
  } else if (e.key === 'Escape') {
    closeFootnotePanel();
  }
});

/* ---------- Utilities ---------- */

function numberWithCommas(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function estimateReadingTime(wordCount) {
  const minutes = Math.max(1, Math.round(wordCount / 200));
  return minutes === 1 ? '1 min' : `${minutes} min`;
}

/* ---------- Init ---------- */

document.addEventListener('DOMContentLoaded', loadData);

/* ============================================================
   toc.js — Floating Table of Contents
   ============================================================ */

let tocObserver = null;
let tocLinks = [];

function renderTOC() {
  const toc = document.getElementById('toc');
  if (!toc || !App.data) return;
  toc.innerHTML = '';
  tocLinks = [];

  const chapters = App.data.chapters || [];

  for (const chapter of chapters) {
    // Chapter link
    const chLink = document.createElement('a');
    chLink.className = 'toc-chapter';
    chLink.textContent = chapter.title;
    chLink.href = `#ch-${chapter.id}`;
    chLink.setAttribute('data-target', `ch-${chapter.id}`);
    chLink.addEventListener('click', (e) => {
      e.preventDefault();
      scrollToElement(`ch-${chapter.id}`);
    });
    toc.appendChild(chLink);
    tocLinks.push({ el: chLink, targetId: `ch-${chapter.id}` });

    // Section links
    if (chapter.sections) {
      for (const section of chapter.sections) {
        const secLink = document.createElement('a');
        secLink.className = 'toc-section';
        secLink.textContent = section.title;
        secLink.href = `#sec-${section.id}`;
        secLink.setAttribute('data-target', `sec-${section.id}`);

        // Dim sections that have no visible passages in current tier
        const hasVisible = sectionHasVisiblePassages(section);
        if (!hasVisible) {
          secLink.classList.add('dimmed');
        }

        secLink.addEventListener('click', (e) => {
          e.preventDefault();
          scrollToElement(`sec-${section.id}`);
        });
        toc.appendChild(secLink);
        tocLinks.push({ el: secLink, targetId: `sec-${section.id}` });
      }
    }
  }

  // Set up IntersectionObserver for active tracking
  setupTocObserver();
}

function sectionHasVisiblePassages(section) {
  if (!section.passages) return false;
  for (const p of section.passages) {
    if (App.includedPassageIds.has(p.id) || App.expandedPassageIds.has(p.id)) {
      return true;
    }
  }
  return false;
}

function scrollToElement(id) {
  const el = document.getElementById(id);
  if (el) {
    const headerHeight = document.getElementById('site-header').offsetHeight;
    const top = el.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
    window.scrollTo({ top, behavior: 'smooth' });
  }
}

/* ---------- IntersectionObserver for Active Tracking ---------- */

function setupTocObserver() {
  // Disconnect previous observer
  if (tocObserver) {
    tocObserver.disconnect();
  }

  const headerHeight = document.getElementById('site-header').offsetHeight;

  tocObserver = new IntersectionObserver(
    (entries) => {
      // Find the topmost visible heading
      let activeId = null;
      let minTop = Infinity;

      for (const entry of entries) {
        if (entry.isIntersecting) {
          const top = entry.boundingClientRect.top;
          if (top < minTop) {
            minTop = top;
            activeId = entry.target.id;
          }
        }
      }

      if (activeId) {
        setActiveTocLink(activeId);
      }
    },
    {
      rootMargin: `-${headerHeight + 20}px 0px -60% 0px`,
      threshold: 0,
    }
  );

  // Observe all chapter and section headings
  document.querySelectorAll('.chapter-heading, .section-heading').forEach((el) => {
    tocObserver.observe(el);
  });
}

function setActiveTocLink(targetId) {
  for (const link of tocLinks) {
    const isActive = link.targetId === targetId;
    link.el.classList.toggle('active', isActive);

    // Scroll the TOC to keep active link visible
    if (isActive) {
      const toc = document.getElementById('toc');
      const linkTop = link.el.offsetTop;
      const tocScroll = toc.scrollTop;
      const tocHeight = toc.clientHeight;
      if (linkTop < tocScroll || linkTop > tocScroll + tocHeight - 40) {
        toc.scrollTo({ top: linkTop - tocHeight / 3, behavior: 'smooth' });
      }
    }
  }
}

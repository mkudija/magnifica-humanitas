/* ============================================================
   footnotes.js — Sidenote interactions + mobile fallback
   ============================================================ */

/* ---------- Sidenote toggle (desktop) ---------- */

window.toggleSidenote = function(el) {
  const fnNum = el.getAttribute('data-fn');
  if (!fnNum) return;
  const fn = App.footnoteMap[parseInt(fnNum)];
  if (!fn) return;

  // If we have a source URL, open it in a new tab
  const url = getFootnoteSourceUrl(fn);
  if (url) {
    window.open(url, '_blank');
    return;
  }

  // On mobile, use bottom sheet
  if (window.innerWidth <= 1024) {
    openMobileFootnote(parseInt(fnNum));
    return;
  }

  // Otherwise toggle expanded detail
  document.querySelectorAll('.sidenote.expanded').forEach(sn => {
    if (sn !== el) sn.classList.remove('expanded');
  });
  el.classList.toggle('expanded');
};

window.closeSidenote = function(btn) {
  const sidenote = btn.closest('.sidenote');
  if (sidenote) sidenote.classList.remove('expanded');
};

/* ---------- Footnote marker click handler ---------- */

window.handleFootnoteClick = function(number) {
  // On mobile, open bottom sheet
  if (window.innerWidth <= 1024) {
    openMobileFootnote(number);
    return;
  }

  // On desktop, find and expand the corresponding sidenote
  const sidenote = document.querySelector(`.sidenote[data-fn="${number}"]`);
  if (sidenote) {
    document.querySelectorAll('.sidenote.expanded').forEach(sn => {
      if (sn !== sidenote) sn.classList.remove('expanded');
    });
    sidenote.classList.add('expanded');
    sidenote.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

/* ---------- Mobile bottom sheet ---------- */

function openMobileFootnote(number) {
  const fn = App.footnoteMap[number];
  if (!fn) return;

  const panel = document.getElementById('fn-mobile-panel');
  const content = document.getElementById('fn-content');
  const overlay = document.getElementById('fn-overlay');

  const cleanText = (fn.text || '').replace(/&nbsp;/g, ' ').replace(/ /g, ' ');
  let html = `<div class="fn-number">Footnote ${fn.number}</div>`;
  if (fn.category) {
    html += `<span class="fn-category">${formatMobileCategory(fn.category)}</span>`;
  }
  if (fn.sourceTitle) {
    html += `<div class="fn-source-title">${fn.sourceTitle}</div>`;
  }
  html += `<div class="fn-text">${cleanText}</div>`;
  if (fn.bibleRef && fn.bibleText) {
    html += `<div class="fn-bible-text">${fn.bibleRef}: ${fn.bibleText}</div>`;
  }

  content.innerHTML = html;
  panel.classList.add('open');
  overlay.classList.add('active');
}

function closeMobileFootnote() {
  const panel = document.getElementById('fn-mobile-panel');
  const overlay = document.getElementById('fn-overlay');
  panel.classList.remove('open');
  overlay.classList.remove('active');
}

window.closeFootnotePanel = closeMobileFootnote;

function formatMobileCategory(cat) {
  if (!cat) return '';
  return cat.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/* ---------- Source URL Resolution ---------- */

const SOURCE_URLS = {
  'Gaudium et Spes': 'https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19651207_gaudium-et-spes_en.html',
  'Lumen Gentium': 'https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19641121_lumen-gentium_en.html',
  'Dignitatis Humanae': 'https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_decl_19651207_dignitatis-humanae_en.html',
  'Laudato Si\'': 'https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html',
  'Fratelli Tutti': 'https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20201003_enciclica-fratelli-tutti.html',
  'Evangelii Gaudium': 'https://www.vatican.va/content/francesco/en/apost_exhortations/documents/papa-francesco_esortazione-ap_20131124_evangelii-gaudium.html',
  'Caritas in Veritate': 'https://www.vatican.va/content/benedict-xvi/en/encyclicals/documents/hf_ben-xvi_enc_20090629_caritas-in-veritate.html',
  'Centesimus Annus': 'https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_01051991_centesimus-annus.html',
  'Rerum Novarum': 'https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_15051891_rerum-novarum.html',
  'Populorum Progressio': 'https://www.vatican.va/content/paul-vi/en/encyclicals/documents/hf_p-vi_enc_26031967_populorum.html',
  'Redemptor Hominis': 'https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_04031979_redemptor-hominis.html',
  'Sollicitudo Rei Socialis': 'https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_30121987_sollicitudo-rei-socialis.html',
  'Laborem Exercens': 'https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_14091981_laborem-exercens.html',
  'Pacem in Terris': 'https://www.vatican.va/content/john-xxiii/en/encyclicals/documents/hf_j-xxiii_enc_11041963_pacem.html',
  'Mater et Magistra': 'https://www.vatican.va/content/john-xxiii/en/encyclicals/documents/hf_j-xxiii_enc_15051961_mater.html',
  'Quadragesimo Anno': 'https://www.vatican.va/content/pius-xi/en/encyclicals/documents/hf_p-xi_enc_19310515_quadragesimo-anno.html',
  'Dilexit Nos': 'https://www.vatican.va/content/francesco/en/encyclicals/documents/20241024-enciclica-dilexit-nos.html',
  'Octogesima Adveniens': 'https://www.vatican.va/content/paul-vi/en/apost_letters/documents/hf_p-vi_apl_19710514_octogesima-adveniens.html',
  'Dignitas Infinita': 'https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_ddf_doc_20240402_dignitas-infinita_en.html',
};

function getFootnoteSourceUrl(fn) {
  if (!fn.sourceTitle) return null;
  // Exact match
  if (SOURCE_URLS[fn.sourceTitle]) return SOURCE_URLS[fn.sourceTitle];
  // Partial match
  for (const [title, url] of Object.entries(SOURCE_URLS)) {
    if (fn.sourceTitle.includes(title) || title.includes(fn.sourceTitle)) return url;
  }
  return null;
}

/* ---------- Event Listeners ---------- */

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('fn-close')?.addEventListener('click', closeMobileFootnote);
  document.getElementById('fn-overlay')?.addEventListener('click', closeMobileFootnote);

  // Close expanded sidenotes when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.sidenote') && !e.target.closest('.fn-marker')) {
      document.querySelectorAll('.sidenote.expanded').forEach(sn => {
        sn.classList.remove('expanded');
      });
    }
  });
});

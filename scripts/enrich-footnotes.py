#!/usr/bin/env python3
"""
Enrich footnotes with categorization and Bible passage text.
Reads raw-document.json, categorizes footnotes, extracts Bible references,
looks up passage text from RSVCE vault, and outputs enriched-footnotes.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Bible book abbreviation mapping to vault directory structure
BIBLE_BOOK_MAPPING = {
    # Old Testament
    'Gen': ('01 - Genesis', 'Gn'),
    'Ex': ('02 - Exodus', 'Ex'),
    'Lev': ('03 - Leviticus', 'Lev'),
    'Num': ('04 - Numbers', 'Num'),
    'Deut': ('05 - Deuteronomy', 'Deut'),
    'Josh': ('06 - Joshua', 'Josh'),
    'Judg': ('07 - Judges', 'Judg'),
    'Ruth': ('08 - Ruth', 'Ruth'),
    '1Sam': ('09 - 1 Samuel', '1Sam'),
    '2Sam': ('10 - 2 Samuel', '2Sam'),
    '1Kgs': ('11 - 1 Kings', '1Kgs'),
    '2Kgs': ('12 - 2 Kings', '2Kgs'),
    '1Chr': ('13 - 1 Chronicles', '1Chr'),
    '2Chr': ('14 - 2 Chronicles', '2Chr'),
    'Ezra': ('15 - Ezra', 'Ezra'),
    'Neh': ('16 - Nehemiah', 'Neh'),
    'Tob': ('17 - Tobit', 'Tob'),
    'Jdt': ('18 - Judith', 'Jdt'),
    'Esth': ('19 - Esther', 'Esth'),
    '1Macc': ('20 - 1 Maccabees', '1Macc'),
    '2Macc': ('21 - 2 Maccabees', '2Macc'),
    'Job': ('22 - Job', 'Job'),
    'Ps': ('23 - Psalms', 'Ps'),
    'Prov': ('24 - Proverbs', 'Prv'),
    'Eccl': ('25 - Ecclesiastes', 'Eccl'),
    'Song': ('26 - Song of Solomon', 'Song'),
    'Wis': ('27 - Wisdom', 'Wis'),
    'Sir': ('28 - Sirach', 'Sir'),
    'Isa': ('29 - Isaiah', 'Isa'),
    'Jer': ('30 - Jeremiah', 'Jer'),
    'Lam': ('31 - Lamentations', 'Lam'),
    'Bar': ('32 - Baruch', 'Bar'),
    'Ezek': ('33 - Ezekiel', 'Ezek'),
    'Dan': ('34 - Daniel', 'Dan'),
    'Hos': ('35 - Hosea', 'Hos'),
    'Joel': ('36 - Joel', 'Joel'),
    'Amos': ('37 - Amos', 'Amos'),
    'Obad': ('38 - Obadiah', 'Obad'),
    'Jon': ('39 - Jonah', 'Jon'),
    'Mic': ('40 - Micah', 'Mic'),
    'Nah': ('41 - Nahum', 'Nah'),
    'Hab': ('42 - Habakkuk', 'Hab'),
    'Zeph': ('43 - Zephaniah', 'Zeph'),
    'Hag': ('44 - Haggai', 'Hag'),
    'Zech': ('45 - Zechariah', 'Zech'),
    'Mal': ('46 - Malachi', 'Mal'),
    # New Testament
    'Mt': ('47 - Matthew', 'Mt'),
    'Mk': ('48 - Mark', 'Mk'),
    'Lk': ('49 - Luke', 'Lk'),
    'Jn': ('50 - John', 'Jn'),
    'Acts': ('51 - Acts', 'Acts'),
    'Rom': ('52 - Romans', 'Rom'),
    '1Cor': ('53 - 1 Corinthians', '1Cor'),
    '2Cor': ('54 - 2 Corinthians', '2Cor'),
    'Gal': ('55 - Galatians', 'Gal'),
    'Eph': ('56 - Ephesians', 'Eph'),
    'Phil': ('57 - Philippians', 'Phil'),
    'Col': ('58 - Colossians', 'Col'),
    '1Thess': ('59 - 1 Thessalonians', '1Thess'),
    '2Thess': ('60 - 2 Thessalonians', '2Thess'),
    '1Tim': ('61 - 1 Timothy', '1Tim'),
    '2Tim': ('62 - 2 Timothy', '2Tim'),
    'Titus': ('63 - Titus', 'Titus'),
    'Phlm': ('64 - Philemon', 'Phlm'),
    'Heb': ('65 - Hebrews', 'Heb'),
    'Jas': ('66 - James', 'Jas'),
    '1Pet': ('67 - 1 Peter', '1Pet'),
    '2Pet': ('68 - 2 Peter', '2Pet'),
    '1Jn': ('69 - 1 John', '1Jn'),
    '2Jn': ('70 - 2 John', '2Jn'),
    '3Jn': ('71 - 3 John', '3Jn'),
    'Jude': ('72 - Jude', 'Jude'),
    'Rev': ('73 - Revelation', 'Rv'),
}

# ============================================================
# Footnote source-title + category derivation
#
# Earlier versions hard-coded a per-footnote (category, sourceTitle) map that
# drifted badly out of sync with the actual citations (most footnotes wrongly
# showed "Fratelli Tutti" / "Laudato Si'"). We now derive both fields directly
# from each footnote's citation text:
#   - named works (encyclicals, councils, the Compendium, ...) are matched by
#     title, preferring the earliest/longest match in the primary citation;
#   - everything else (addresses, homilies, messages, books) gets a short
#     descriptive title generated from the lead of the citation;
#   - "Ibid." inherits the previous footnote's resolved source.
# ============================================================

# Canonical named works -> category. Longest, earliest match wins.
WORKS = {
    'Gaudium et Spes': 'vatican-ii', 'Lumen Gentium': 'vatican-ii', 'Dignitatis Humanae': 'vatican-ii',
    'Rerum Novarum': 'papal-encyclical', 'Quadragesimo Anno': 'papal-encyclical', 'Mater et Magistra': 'papal-encyclical',
    'Pacem in Terris': 'papal-encyclical', 'Populorum Progressio': 'papal-encyclical', 'Redemptor Hominis': 'papal-encyclical',
    'Dives in Misericordia': 'papal-encyclical', 'Laborem Exercens': 'papal-encyclical', 'Sollicitudo Rei Socialis': 'papal-encyclical',
    'Centesimus Annus': 'papal-encyclical', 'Veritatis Splendor': 'papal-encyclical', 'Evangelium Vitae': 'papal-encyclical',
    'Caritas in Veritate': 'papal-encyclical', 'Deus Caritas Est': 'papal-encyclical', 'Spe Salvi': 'papal-encyclical',
    'Laudato Si': 'papal-encyclical', 'Fratelli Tutti': 'papal-encyclical', 'Dilexit Nos': 'papal-encyclical',
    'Humanae Vitae': 'papal-encyclical', 'In Plurimis': 'papal-encyclical',
    'Evangelii Gaudium': 'papal-exhortation', 'Laudate Deum': 'papal-exhortation',
    'Sacramentum Caritatis': 'papal-exhortation', 'Menti Nostrae': 'papal-exhortation',
    'Octogesima Adveniens': 'apostolic-letter', 'Tertio Millennio Adveniente': 'apostolic-letter',
    'Socialium Scientiarum': 'apostolic-letter', 'Gratissimam Sane': 'apostolic-letter',
    'Incarnationis Mysterium': 'apostolic-letter',
    'Compendium of the Social Doctrine of the Church': 'curial', 'Dignitas Infinita': 'curial',
    'Antiqua et Nova': 'curial', 'Oeconomicae et Pecuniariae Quaestiones': 'curial',
    'Confessions': 'church-father', 'De civitate Dei': 'church-father', 'Enarrationes in Psalmos': 'church-father',
    'Summa Theologiae': 'church-doctor', 'Super Boetium de Trinitate': 'church-doctor',
}
WORK_KEYS = sorted(WORKS, key=len, reverse=True)

# Author / corporate-author prefixes to strip when generating a descriptive title.
AUTHORS = [
    'Second Vatican Ecumenical Council', 'Saint John Paul II', 'Saint John XXIII', 'Saint Paul VI',
    'Benedict XVI', 'Pius XII', 'Pius XI', 'Leo XIII', 'Francis', 'Saint Augustine', 'Saint Thomas Aquinas',
    r'Dicastery for the Doctrine of the Faith\s*[–—-]\s*Dicastery for Culture and Education',
    r'Dicastery for the Doctrine of the Faith\s*[–—-]\s*Dicastery for the Promotion of Integral Human Development',
    'Dicastery for the Doctrine of the Faith', 'Pontifical Council [Ff]or Justice and Peace',
    'International Theological Commission', 'United States Conference of Catholic Bishops', 'United Nations',
]

DESCRIPTOR_MAXLEN = 70


def _clean_citation(text: str) -> str:
    """Normalize whitespace and smart punctuation in a footnote's text."""
    return (text.replace('&nbsp;', ' ').replace(' ', ' ')
            .replace('’', "'").replace('“', '"').replace('”', '"').strip())


def _lead_citation(t: str) -> str:
    """Return the primary citation (before any ';' or '. Cf.'/'. Cfr.' secondary)."""
    if t.startswith('"'):
        # A block quotation precedes the citation; the source follows the closing quote.
        m = re.match(r'"[^"]*"\s*', t)
        if m:
            t = t[m.end():].strip()
    return re.split(r';|\.\s+Cfr?\b', t)[0].strip()


def _find_named_work(segment: str):
    """Find the earliest (tie-break: longest) canonical work title in a segment."""
    best = None
    for key in WORK_KEYS:
        # "Centesimus Annus Pro Pontifice Foundation" is an address, not the encyclical.
        if key == 'Centesimus Annus' and 'Centesimus Annus Pro Pontifice' in segment:
            continue
        idx = segment.find(key)
        if idx != -1 and (best is None or idx < best[0] or (idx == best[0] and len(key) > len(best[1]))):
            best = (idx, key)
    if best:
        disp = "Laudato Si'" if best[1] == 'Laudato Si' else best[1]
        return WORKS[best[1]], disp
    return None


def _descriptor_title(lead: str):
    """Generate a short descriptive title for a non-named source (address, book, ...)."""
    s = re.sub(r'^(Cf\.?|Cfr\.?)\s+', '', lead).strip()
    for a in AUTHORS:
        m = re.match(a + r'\s*,?\s*', s)
        if m:
            s = s[m.end():].strip()
            break
    # Leading book-author initials, e.g. "R. Guardini,", "J.R.R. Tolkien,", "P. de Berulle,".
    s = re.sub(r"^[A-Z]\.(?:[A-Z]\.)*\s*(?:de\s+)?[A-ZÀ-Þ][\wÀ-ÿ'’-]+,\s*", '', s)
    s = re.sub(r"^(Plato|Giorgio La Pira),\s*", '', s)
    s = re.sub(r'^[–—-]\s*', '', s)
    s = re.sub(r'^As in the\s+', '', s)
    s = re.sub(r'^(Apostolic Letter issued "Motu Proprio"|Apostolic Letter|Encyclical Letter|'
               r'Dogmatic Constitution|Pastoral Constitution|Apostolic Exhortation|Declaration|Bull|'
               r'Letter to Families|Note|Radio Message|Papal Bulls)\s+', '', s)
    # Drop trailing publication metadata (dates, AAS/ASS refs, publishers, page numbers).
    s = re.split(r"\s*\(\d|:\s*AAS|:\s*ASS|:\s*Insegnamenti|:\s*L'Oss|:\s*CCSL|:\s*PL|:\s*Acta|"
                 r", ed\.|: ed\.|, Acta|, Vatican City|, San Francisco|, Würzburg|, Boston|"
                 r", New York|, Turnhout|, Rome|, Paris|, Florence|\. Address of|\(Rome", s)[0]
    s = re.sub(r'\s+', ' ', s).strip().strip(',').strip()
    if len(s) > DESCRIPTOR_MAXLEN:
        s = s[:DESCRIPTOR_MAXLEN].rsplit(' ', 1)[0] + '…'
    return s or None


def _descriptor_category(lead: str) -> str:
    """Best-effort category for a non-named source."""
    l = lead.lower()
    if 'saint augustine' in l:
        return 'church-father'
    if 'saint thomas aquinas' in l:
        return 'church-doctor'
    if re.search(r'dicastery|pontifical council|congregation|theological commission|synod of bishops', l):
        return 'curial'
    if re.search(r'homily|angelus|address|message|audience|blessing|meditation|greeting|appeal|'
                 r'regina caeli|discourse|urbi et orbi|vespers|radio message|video message', l):
        return 'papal-address'
    if re.search(r'guardini|arendt|tolkien|frankl|bérulle|la pira|plato|united nations charter|'
                 r'conference of catholic bishops', l):
        return 'reference'
    return 'other'


def derive_footnote_sources(footnotes: list) -> dict:
    """Map footnote number -> (category, sourceTitle), derived from citation text."""
    resolved = {}
    prev = ('other', None)
    for fn in sorted(footnotes, key=lambda f: f['number']):
        num = fn['number']
        t = _clean_citation(fn['text'])
        # Internal cross-reference ("Cf. above, nos. ...") has no external source.
        if re.match(r'^(cf\.?\s*)?(above|below)\b', t.lower()):
            resolved[num] = prev = ('other', None)
            continue
        # "Ibid." inherits the previous footnote's resolved source.
        stripped = re.sub(r'^(cf|cfr)\s*\.\s*', '', t.lower()).strip()
        if stripped.startswith('ibid'):
            resolved[num] = prev
            continue
        lead = _lead_citation(t)
        work = _find_named_work(lead)
        resolved[num] = work if work else (_descriptor_category(lead), _descriptor_title(lead))
        prev = resolved[num]
    return resolved


RSVCE_VAULT_PATH = Path("/Users/mkudija/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Scripture (RSVCE)")


def extract_bible_references(text: str) -> List[str]:
    """Extract Bible references from text (e.g., 'Gen 1:26-27', 'Mt 25:14-30')."""
    # Pattern matches references like: Gen 1:26-27, Mt 25:14-30, Ps 85:10, 2 Cor 12:9, etc.
    pattern = r'\b([123]?\s?(?:' + '|'.join(BIBLE_BOOK_MAPPING.keys()) + r')\.?)\s+(\d+):(\d+)(?:-(\d+))?'
    matches = re.findall(pattern, text, re.IGNORECASE)

    refs = []
    for match in matches:
        book = match[0].strip().replace('.', '')
        chapter = match[1]
        verse_start = match[2]
        verse_end = match[3] if match[3] else verse_start

        # Normalize book abbreviation
        book_normalized = None
        for abbrev in BIBLE_BOOK_MAPPING.keys():
            if book.replace(' ', '').lower() == abbrev.lower():
                book_normalized = abbrev
                break

        if book_normalized:
            if verse_end:
                refs.append(f"{book_normalized} {chapter}:{verse_start}-{verse_end}")
            else:
                refs.append(f"{book_normalized} {chapter}:{verse_start}")

    return refs


def lookup_bible_passage(ref: str) -> Optional[str]:
    """
    Look up Bible passage text from RSVCE vault.
    ref format: 'Gen 1:26-27', 'Mt 25:14', etc.
    """
    # Parse reference
    match = re.match(r'([123]?\w+)\s+(\d+):(\d+)(?:-(\d+))?', ref)
    if not match:
        return None

    book_abbrev = match.group(1)
    chapter = int(match.group(2))
    verse_start = int(match.group(3))
    verse_end = int(match.group(4)) if match.group(4) else verse_start

    # Get book directory and file prefix
    if book_abbrev not in BIBLE_BOOK_MAPPING:
        return None

    book_dir, file_prefix = BIBLE_BOOK_MAPPING[book_abbrev]

    # Construct file path
    # Files are named like Mt-25.md (two-digit chapter number)
    file_path = RSVCE_VAULT_PATH / book_dir / f"{file_prefix}-{chapter:02d}.md"

    if not file_path.exists():
        # Try single-digit chapter (for books with <10 chapters)
        file_path = RSVCE_VAULT_PATH / book_dir / f"{file_prefix}-{chapter}.md"
        if not file_path.exists():
            return None

    # Read file and extract verses
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract verses between verse_start and verse_end
        verses = []
        for v in range(verse_start, verse_end + 1):
            # Pattern: ###### v{verse_number}
            pattern = rf'###### v{v}\s*\n(.*?)(?=\n###### v\d+|\n##|\n---|\Z)'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                verse_text = match.group(1).strip()
                # Remove footnote markers like [^a]
                verse_text = re.sub(r'\[\^[a-z]+\]', '', verse_text)
                verses.append(verse_text)

        if verses:
            return ' '.join(verses)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return None


def enrich_footnotes():
    """Main function to enrich footnotes with categorization and Bible passages."""

    # Read raw document
    raw_path = Path("data/raw-document.json")
    with open(raw_path, 'r') as f:
        doc = json.load(f)

    # Derive (category, sourceTitle) for every footnote from its citation text
    derived_sources = derive_footnote_sources(doc['footnotes'])

    # Enrich footnotes
    enriched_footnotes = []
    for fn in doc['footnotes']:
        num = fn['number']
        category, source_title = derived_sources.get(num, ('other', None))

        enriched_fn = {
            'number': num,
            'text': fn['text'],
            'category': category,
            'sourceTitle': source_title,
            'bibleRef': None,
            'bibleText': None
        }

        # Check if footnote contains Bible references
        bible_refs = extract_bible_references(fn['text'])
        if bible_refs:
            # For simplicity, take the first reference if multiple
            enriched_fn['bibleRef'] = bible_refs[0]
            enriched_fn['bibleText'] = lookup_bible_passage(bible_refs[0])

        enriched_footnotes.append(enriched_fn)

    # Extract Bible references from paragraph text
    bible_references = {}  # ref -> {ref, text, paragraphs, footnotes}

    for chapter in doc['chapters']:
        for section_or_passage in chapter.get('passages', []) + chapter.get('sections', []):
            # Handle both direct passages and nested sections
            passages = []
            if 'passages' in section_or_passage:
                passages = section_or_passage['passages']
            else:
                passages = [section_or_passage]

            for passage in passages:
                para_num = passage.get('paragraphNumber')
                text = passage.get('text', '')

                refs = extract_bible_references(text)
                for ref in refs:
                    if ref not in bible_references:
                        bible_references[ref] = {
                            'ref': ref,
                            'text': lookup_bible_passage(ref),
                            'paragraphs': [],
                            'footnotes': []
                        }

                    if para_num and para_num not in bible_references[ref]['paragraphs']:
                        bible_references[ref]['paragraphs'].append(para_num)

    # Also check which footnotes reference each Bible passage
    for fn in enriched_footnotes:
        if fn['bibleRef']:
            ref = fn['bibleRef']
            if ref in bible_references:
                bible_references[ref]['footnotes'].append(fn['number'])

    # Sort paragraphs for each reference
    for ref_data in bible_references.values():
        ref_data['paragraphs'].sort()
        ref_data['footnotes'].sort()

    # Output enriched data
    output = {
        'footnotes': enriched_footnotes,
        'bibleReferences': list(bible_references.values())
    }

    output_path = Path("data/enriched-footnotes.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Enriched {len(enriched_footnotes)} footnotes")
    print(f"✓ Extracted {len(bible_references)} unique Bible references")
    print(f"✓ Wrote enriched data to {output_path}")

    # Summary statistics
    category_counts = {}
    for fn in enriched_footnotes:
        cat = fn['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\nFootnote categories:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Bible passage lookup success rate
    successful_lookups = sum(1 for ref_data in bible_references.values() if ref_data['text'])
    print(f"\nBible passages successfully looked up: {successful_lookups}/{len(bible_references)}")


if __name__ == '__main__':
    enrich_footnotes()

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

# Footnote categorization mapping (all 224 footnotes)
FOOTNOTE_CATEGORIES = {
    1: ('vatican-ii', 'Gaudium et Spes'),
    2: ('vatican-ii', 'Gaudium et Spes'),
    3: ('vatican-ii', 'Lumen Gentium'),
    4: ('papal-encyclical', 'Rerum Novarum'),
    5: ('papal-encyclical', 'Caritas in Veritate'),
    6: ('papal-encyclical', 'Laudato Si\''),
    7: ('papal-encyclical', 'Laudato Si\''),
    8: ('church-father', 'St. Augustine - Confessions'),
    9: ('papal-exhortation', 'Evangelii Gaudium'),
    10: ('vatican-ii', 'Gaudium et Spes'),
    11: ('vatican-ii', 'Gaudium et Spes'),
    12: ('papal-exhortation', 'Evangelii Gaudium'),
    13: ('papal-encyclical', 'Socialium Scientiarum'),
    14: ('papal-encyclical', 'Laudato Si\''),
    15: ('papal-encyclical', 'Sollicitudo Rei Socialis'),
    16: ('papal-encyclical', 'Tertio Millennio Adveniente'),
    17: ('leo-xiv', 'Address to Centesimus Annus Pro Pontifice'),
    18: ('papal-exhortation', 'Evangelii Gaudium'),
    19: ('papal-encyclical', 'Fratelli Tutti'),
    20: ('vatican-ii', 'Lumen Gentium'),
    21: ('papal-exhortation', 'Evangelii Gaudium'),
    22: ('papal-encyclical', 'Laudato Si\''),
    23: ('papal-encyclical', 'Fratelli Tutti'),
    24: ('vatican-ii', 'Dignitatis Humanae'),
    25: ('papal-encyclical', 'Pacem in Terris'),
    26: ('papal-encyclical', 'Laudato Si\''),
    27: ('vatican-ii', 'Gaudium et Spes'),
    28: ('vatican-ii', 'Gaudium et Spes'),
    29: ('papal-encyclical', 'Laudato Si\''),
    30: ('papal-encyclical', 'Evangelium Vitae'),
    31: ('papal-encyclical', 'Veritatis Splendor'),
    32: ('curial', 'Compendium of Social Doctrine'),
    33: ('papal-encyclical', 'Centesimus Annus'),
    34: ('papal-encyclical', 'Sollicitudo Rei Socialis'),
    35: ('papal-encyclical', 'Evangelium Vitae'),
    36: ('papal-encyclical', 'Caritas in Veritate'),
    37: ('papal-encyclical', 'Caritas in Veritate'),
    38: ('papal-encyclical', 'Laudato Si\''),
    39: ('papal-encyclical', 'Laudato Si\''),
    40: ('papal-encyclical', 'Laudato Si\''),
    41: ('papal-encyclical', 'Laudato Si\''),
    42: ('papal-encyclical', 'Laudato Si\''),
    43: ('papal-encyclical', 'Laudato Si\''),
    44: ('papal-encyclical', 'Laudato Si\''),
    45: ('papal-encyclical', 'Laudato Si\''),
    46: ('papal-encyclical', 'Laudato Si\''),
    47: ('papal-encyclical', 'Laudato Si\''),
    48: ('papal-exhortation', 'Evangelii Gaudium'),
    49: ('papal-encyclical', 'Laudato Si\''),
    50: ('papal-encyclical', 'Laudato Si\''),
    51: ('curial', 'Compendium of Social Doctrine'),
    52: ('vatican-ii', 'Gaudium et Spes'),
    53: ('papal-encyclical', 'Centesimus Annus'),
    54: ('papal-encyclical', 'Sollicitudo Rei Socialis'),
    55: ('papal-encyclical', 'Centesimus Annus'),
    56: ('papal-encyclical', 'Centesimus Annus'),
    57: ('papal-encyclical', 'Populorum Progressio'),
    58: ('papal-encyclical', 'Populorum Progressio'),
    59: ('papal-encyclical', 'Caritas in Veritate'),
    60: ('papal-encyclical', 'Centesimus Annus'),
    61: ('papal-encyclical', 'Laudato Si\''),
    62: ('papal-encyclical', 'Laudato Si\''),
    63: ('papal-encyclical', 'Laudato Si\''),
    64: ('papal-encyclical', 'Laudato Si\''),
    65: ('papal-encyclical', 'Laudato Si\''),
    66: ('papal-encyclical', 'Laudato Si\''),
    67: ('papal-encyclical', 'Laudato Si\''),
    68: ('papal-encyclical', 'Laudato Si\''),
    69: ('papal-encyclical', 'Laudato Si\''),
    70: ('papal-encyclical', 'Laudato Si\''),
    71: ('papal-encyclical', 'Laudato Si\''),
    72: ('papal-encyclical', 'Laudato Si\''),
    73: ('papal-encyclical', 'Laudato Si\''),
    74: ('papal-encyclical', 'Laudato Si\''),
    75: ('papal-encyclical', 'Laudato Si\''),
    76: ('papal-encyclical', 'Laudato Si\''),
    77: ('papal-encyclical', 'Laudato Si\''),
    78: ('papal-encyclical', 'Laudato Si\''),
    79: ('papal-exhortation', 'Evangelii Gaudium'),
    80: ('papal-encyclical', 'Caritas in Veritate'),
    81: ('papal-encyclical', 'Caritas in Veritate'),
    82: ('papal-exhortation', 'Evangelii Gaudium'),
    83: ('papal-encyclical', 'Fratelli Tutti'),
    84: ('papal-encyclical', 'Fratelli Tutti'),
    85: ('papal-encyclical', 'Fratelli Tutti'),
    86: ('leo-xiv', 'Address to Members of Diplomatic Corps'),
    87: ('papal-encyclical', 'Fratelli Tutti'),
    88: ('papal-encyclical', 'Fratelli Tutti'),
    89: ('papal-encyclical', 'Centesimus Annus'),
    90: ('papal-encyclical', 'Fratelli Tutti'),
    91: ('papal-encyclical', 'Fratelli Tutti'),
    92: ('papal-encyclical', 'Fratelli Tutti'),
    93: ('papal-encyclical', 'Fratelli Tutti'),
    94: ('papal-encyclical', 'Fratelli Tutti'),
    95: ('papal-encyclical', 'Fratelli Tutti'),
    96: ('papal-encyclical', 'Fratelli Tutti'),
    97: ('papal-encyclical', 'Fratelli Tutti'),
    98: ('papal-encyclical', 'Fratelli Tutti'),
    99: ('papal-encyclical', 'Fratelli Tutti'),
    100: ('papal-encyclical', 'Fratelli Tutti'),
    101: ('papal-encyclical', 'Fratelli Tutti'),
    102: ('papal-encyclical', 'Fratelli Tutti'),
    103: ('papal-encyclical', 'Fratelli Tutti'),
    104: ('papal-encyclical', 'Fratelli Tutti'),
    105: ('papal-encyclical', 'Fratelli Tutti'),
    106: ('papal-encyclical', 'Fratelli Tutti'),
    107: ('papal-encyclical', 'Fratelli Tutti'),
    108: ('papal-encyclical', 'Fratelli Tutti'),
    109: ('papal-encyclical', 'Fratelli Tutti'),
    110: ('papal-encyclical', 'Fratelli Tutti'),
    111: ('papal-encyclical', 'Fratelli Tutti'),
    112: ('papal-encyclical', 'Fratelli Tutti'),
    113: ('papal-encyclical', 'Fratelli Tutti'),
    114: ('papal-encyclical', 'Fratelli Tutti'),
    115: ('papal-encyclical', 'Fratelli Tutti'),
    116: ('papal-encyclical', 'Fratelli Tutti'),
    117: ('papal-encyclical', 'Fratelli Tutti'),
    118: ('papal-encyclical', 'Dives in Misericordia'),
    119: ('papal-encyclical', 'Fratelli Tutti'),
    120: ('papal-encyclical', 'Fratelli Tutti'),
    121: ('papal-encyclical', 'Fratelli Tutti'),
    122: ('papal-encyclical', 'Fratelli Tutti'),
    123: ('papal-exhortation', 'Evangelii Gaudium'),
    124: ('papal-encyclical', 'Fratelli Tutti'),
    125: ('papal-encyclical', 'Fratelli Tutti'),
    126: ('papal-encyclical', 'Evangelium Vitae'),
    127: ('papal-encyclical', 'Evangelium Vitae'),
    128: ('papal-encyclical', 'Evangelium Vitae'),
    129: ('papal-encyclical', 'Evangelium Vitae'),
    130: ('vatican-ii', 'Gaudium et Spes'),
    131: ('papal-encyclical', 'Evangelium Vitae'),
    132: ('vatican-ii', 'Gaudium et Spes'),
    133: ('papal-encyclical', 'Laudato Si\''),
    134: ('papal-encyclical', 'Laudato Si\''),
    135: ('papal-encyclical', 'Laudato Si\''),
    136: ('papal-encyclical', 'Laudato Si\''),
    137: ('papal-encyclical', 'Laudato Si\''),
    138: ('papal-encyclical', 'Laudato Si\''),
    139: ('papal-encyclical', 'Laudato Si\''),
    140: ('papal-encyclical', 'Laudato Si\''),
    141: ('papal-encyclical', 'Laudato Si\''),
    142: ('papal-encyclical', 'Laudato Si\''),
    143: ('papal-encyclical', 'Laudato Si\''),
    144: ('papal-encyclical', 'Laudato Si\''),
    145: ('papal-encyclical', 'Laudato Si\''),
    146: ('papal-encyclical', 'Laudato Si\''),
    147: ('papal-encyclical', 'Laudato Si\''),
    148: ('papal-encyclical', 'Laudato Si\''),
    149: ('papal-encyclical', 'Laudato Si\''),
    150: ('papal-encyclical', 'Laudato Si\''),
    151: ('papal-encyclical', 'Laudato Si\''),
    152: ('papal-encyclical', 'Laudato Si\''),
    153: ('papal-encyclical', 'Laudato Si\''),
    154: ('papal-encyclical', 'Laudato Si\''),
    155: ('papal-encyclical', 'Laudato Si\''),
    156: ('papal-encyclical', 'Laudato Si\''),
    157: ('papal-encyclical', 'Laudato Si\''),
    158: ('papal-encyclical', 'Laudato Si\''),
    159: ('papal-encyclical', 'Laudato Si\''),
    160: ('papal-encyclical', 'Laudato Si\''),
    161: ('papal-encyclical', 'Laudato Si\''),
    162: ('papal-encyclical', 'Laudato Si\''),
    163: ('papal-encyclical', 'Laudato Si\''),
    164: ('papal-encyclical', 'Laudato Si\''),
    165: ('papal-encyclical', 'Laudato Si\''),
    166: ('leo-xiv', 'Video Message to TED Conference'),
    167: ('papal-encyclical', 'Laudato Si\''),
    168: ('papal-encyclical', 'Laudato Si\''),
    169: ('papal-encyclical', 'Laudato Si\''),
    170: ('papal-encyclical', 'Laudato Si\''),
    171: ('papal-encyclical', 'Laudato Si\''),
    172: ('papal-encyclical', 'Laudato Si\''),
    173: ('papal-encyclical', 'Laudato Si\''),
    174: ('papal-encyclical', 'Laudato Si\''),
    175: ('papal-encyclical', 'Laudato Si\''),
    176: ('papal-encyclical', 'Laudato Si\''),
    177: ('papal-encyclical', 'Laudato Si\''),
    178: ('papal-encyclical', 'Laudato Si\''),
    179: ('papal-encyclical', 'Laudato Si\''),
    180: ('papal-encyclical', 'Laudato Si\''),
    181: ('papal-encyclical', 'Laudato Si\''),
    182: ('papal-encyclical', 'Laudato Si\''),
    183: ('papal-encyclical', 'Laudato Si\''),
    184: ('papal-encyclical', 'Laudato Si\''),
    185: ('papal-encyclical', 'Laudato Si\''),
    186: ('papal-encyclical', 'Laudato Si\''),
    187: ('papal-encyclical', 'Laudato Si\''),
    188: ('papal-encyclical', 'Laudato Si\''),
    189: ('papal-encyclical', 'Laudato Si\''),
    190: ('papal-encyclical', 'Laudato Si\''),
    191: ('papal-encyclical', 'Laudato Si\''),
    192: ('leo-xiv', 'Message to UN General Assembly'),
    193: ('papal-encyclical', 'Laudato Si\''),
    194: ('papal-encyclical', 'Laudato Si\''),
    195: ('leo-xiv', 'Address to Pontifical Academy of Sciences'),
    196: ('papal-encyclical', 'Laudato Si\''),
    197: ('papal-encyclical', 'Laudato Si\''),
    198: ('papal-encyclical', 'Laudato Si\''),
    199: ('papal-encyclical', 'Laudato Si\''),
    200: ('papal-encyclical', 'Laudato Si\''),
    201: ('leo-xiv', 'Address to Diplomatic Corps'),
    202: ('vatican-ii', 'Gaudium et Spes'),
    203: ('vatican-ii', 'Gaudium et Spes'),
    204: ('vatican-ii', 'Gaudium et Spes'),
    205: ('vatican-ii', 'Gaudium et Spes'),
    206: ('papal-encyclical', 'Centesimus Annus'),
    207: ('papal-encyclical', 'Centesimus Annus'),
    208: ('papal-encyclical', 'Centesimus Annus'),
    209: ('papal-exhortation', 'Evangelii Gaudium'),
    210: ('papal-encyclical', 'Fratelli Tutti'),
    211: ('papal-encyclical', 'Fratelli Tutti'),
    212: ('papal-encyclical', 'Fratelli Tutti'),
    213: ('papal-encyclical', 'Fratelli Tutti'),
    214: ('papal-encyclical', 'Fratelli Tutti'),
    215: ('papal-encyclical', 'Fratelli Tutti'),
    216: ('papal-encyclical', 'Fratelli Tutti'),
    217: ('papal-encyclical', 'Fratelli Tutti'),
    218: ('papal-encyclical', 'Fratelli Tutti'),
    219: ('leo-xiv', 'Homily at Mass'),
    220: ('papal-encyclical', 'Fratelli Tutti'),
    221: ('papal-encyclical', 'Fratelli Tutti'),
    222: ('papal-encyclical', 'Fratelli Tutti'),
    223: ('papal-encyclical', 'Fratelli Tutti'),
    224: ('papal-encyclical', 'Humanae Vitae'),
}

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

    # Enrich footnotes
    enriched_footnotes = []
    for fn in doc['footnotes']:
        num = fn['number']
        category, source_title = FOOTNOTE_CATEGORIES.get(num, ('other', None))

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

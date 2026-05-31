#!/usr/bin/env python3
"""Parse the Vatican HTML of Magnifica Humanitas into structured JSON."""

import json
import re
import os
from html.parser import HTMLParser

SOURCE = os.path.join(os.path.dirname(__file__), '..', 'source', 'magnifica-humanitas.html')
OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw-document.json')


class MHParser(HTMLParser):
    """Parses Vatican HTML preserving inline formatting (italics, links, superscripts)."""

    # Tags whose open/close we preserve in the output
    INLINE_TAGS = {'i', 'em', 'sup'}

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current_text = ''
        self.tag_stack = []
        self.in_skip = False
        self._in_fn_link = False
        self._in_content_link = False
        self._content_link_href = ''
        self.current_footnote_markers = []

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        attrs_dict = dict(attrs)

        if tag in ('script', 'style', 'nav', 'header', 'noscript'):
            self.in_skip = True
            return

        if self.in_skip:
            return

        # Footnote reference links → insert placeholder, skip link text
        if tag == 'a' and attrs_dict.get('href', '').startswith('#_ftn'):
            fn_match = re.search(r'_ftn(\d+)', attrs_dict.get('href', ''))
            if fn_match:
                fn_num = int(fn_match.group(1))
                self.current_footnote_markers.append(fn_num)
                self.current_text += f'{{{{FN:{fn_num}}}}}'
                self._in_fn_link = True
            return

        # Content hyperlinks (pope names, encyclical titles) → preserve as <a>
        if tag == 'a' and not self._in_fn_link:
            href = attrs_dict.get('href', '')
            css_class = attrs_dict.get('class', '')
            if href and not href.startswith('#_ftn') and not href.startswith('#_edn') and 'cleaner' not in css_class:
                self._in_content_link = True
                self._content_link_href = href
                self.current_text += f'<a href="{href}" target="_blank" rel="noopener">'
            return

        # Inline formatting tags → preserve in output
        if tag in self.INLINE_TAGS:
            self.current_text += f'<{tag}>'
            return

        if tag == 'br':
            self.current_text += ' '

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        # Footnote link end
        if tag == 'a' and self._in_fn_link:
            self._in_fn_link = False
            return

        # Content link end
        if tag == 'a' and self._in_content_link:
            self._in_content_link = False
            self._content_link_href = ''
            self.current_text += '</a>'
            return

        if tag in ('script', 'style', 'nav', 'header', 'noscript'):
            self.in_skip = False
            return

        # Close inline tags
        if tag in self.INLINE_TAGS and not self.in_skip:
            self.current_text += f'</{tag}>'
            return

        # End of paragraph → save
        if tag == 'p':
            text = self.current_text.strip()
            # Collapse whitespace but preserve HTML tags
            text = re.sub(r'\s+', ' ', text)
            # Clean up empty italic tags like <i></i>
            text = re.sub(r'<i>\s*</i>', '', text)
            text = re.sub(r'<em>\s*</em>', '', text)
            if text and len(re.sub(r'<[^>]+>', '', text).strip()) > 5:
                self.paragraphs.append({
                    'raw_text': text,
                    'footnote_markers': list(self.current_footnote_markers),
                })
            self.current_text = ''
            self.current_footnote_markers = []

    def handle_data(self, data):
        if not self.in_skip and not self._in_fn_link:
            self.current_text += data

    def handle_entityref(self, name):
        if self.in_skip or self._in_fn_link:
            return
        if name == 'nbsp':
            self.current_text += ' '
        elif name == 'ldquo' or name == 'rdquo':
            self.current_text += '“' if name == 'ldquo' else '”'
        elif name == 'lsquo' or name == 'rsquo':
            self.current_text += '‘' if name == 'lsquo' else '’'
        elif name == 'mdash':
            self.current_text += '—'
        elif name == 'ndash':
            self.current_text += '–'
        else:
            self.current_text += f'&{name};'

    def handle_charref(self, name):
        if self.in_skip or self._in_fn_link:
            return
        try:
            if name.startswith('x'):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
            self.current_text += char
        except (ValueError, OverflowError):
            self.current_text += f'&#{name};'


def extract_footnotes(html):
    """Extract footnote texts from the endnotes section."""
    footnotes = {}
    fn_pattern = re.compile(
        r'<a[^>]*(?:name|id)=["\']_ftn(\d+)["\'][^>]*>.*?</a>(.*?)(?=<a[^>]*(?:name|id)=["\']_ftn\d+["\']|<div|</div|$)',
        re.DOTALL
    )
    ftn_section = re.search(r'<div[^>]*id=["\']ftn\d*["\'][^>]*>.*$', html, re.DOTALL)
    if not ftn_section:
        ftn_section_match = re.search(r'<a[^>]*name=["\']_ftn1["\'].*$', html, re.DOTALL)
        if ftn_section_match:
            section_text = ftn_section_match.group(0)
        else:
            return footnotes
    else:
        section_text = ftn_section.group(0)

    for match in fn_pattern.finditer(section_text):
        num = int(match.group(1))
        text = match.group(2)
        text = re.sub(r'<[^>]+>', '', text).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            footnotes[num] = text

    return footnotes


def extract_footnotes_simple(html):
    """Simpler footnote extraction — find all [N] patterns in endnotes area."""
    footnotes = {}
    lines = html.split('\n')
    in_endnotes = False
    current_num = None
    current_text = ''

    for line in lines:
        clean = re.sub(r'<[^>]+>', '', line).strip()
        if not clean:
            continue

        fn_start = re.match(r'^\[(\d+)\]\s*(.*)', clean)
        if fn_start:
            if current_num is not None and current_text.strip():
                footnotes[current_num] = current_text.strip()
            current_num = int(fn_start.group(1))
            current_text = fn_start.group(2)
            in_endnotes = True
        elif in_endnotes and current_num is not None:
            if re.match(r'^\d+\.\s', clean) and not re.match(r'^\[\d+\]', clean):
                pass
            current_text += ' ' + clean

    if current_num is not None and current_text.strip():
        footnotes[current_num] = current_text.strip()

    return footnotes


def identify_structure(paragraphs):
    """Identify section structure from paragraph content."""
    sections = []
    current_chapter = None
    current_section = None
    current_subsection = None

    chapter_patterns = [
        (r'^INTRODUCTION$', 'Introduction', 0),
        (r'^CHAPTER ONE\b', 'Chapter One: A Dynamic Approach Faithful to the Gospel', 1),
        (r'^CHAPTER TWO\b', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', 2),
        (r'^CHAPTER THREE\b', 'Chapter Three: Technology and Dominance — The Grandeur of Humanity in Light of the Promises of AI', 3),
        (r'^CHAPTER FOUR\b', 'Chapter Four: Safeguarding Humanity at a Time of Transformation — Truth, Work, Freedom', 4),
        (r'^CHAPTER FIVE\b', 'Chapter Five: The Culture of Power and the Civilization of Love', 5),
        (r'^CONCLUSION$', 'Conclusion', 6),
    ]

    section_headings = {
        'The res novae of our time': (0, 0),
        'Two biblical images': (0, 1),
        'Building for the common good': (0, 2),
        'Remaining human': (0, 3),
        'A Church journeying through human history': (1, 0),
        'The development of Social Doctrine from': (1, 1),
        'The foundations of Social Doctrine': (2, 0),
        'The principles of Social Doctrine': (2, 1),
        'Integral human development': (2, 2),
        'An examen for the Church': (2, 3),
        'The technocratic paradigm and digital power': (3, 0),
        'Artificial intelligence': (3, 1),
        'What must not be lost': (3, 2),
        'The authentic': (3, 3),
        'Two cities and two loves': (3, 4),
        'Truth as a common good': (4, 0),
        'The dignity of work at a time of digital transition': (4, 1),
        'Protecting freedom against dependencies and commercialization': (4, 2),
        'A shared responsibility': (4, 3),
        'The civilization of love in the digital age': (5, 0),
        'The culture of power': (5, 1),
        'Building the civilization of love': (5, 2),
        'The Word became flesh': (6, 0),
        'One body in Christ': (6, 1),
        'The construction site of our time': (6, 2),
        'The song of hope': (6, 3),
    }

    subsection_headings = {
        'The wisdom of the word of God': (1, 0, 0),
        'Social Doctrine as a shared discernment': (1, 0, 1),
        'The first stages of the Church': (1, 1, 0),
        'The years of the': (1, 1, 1),
        'The recent Magisterium': (1, 1, 2),
        'Interpreting history in the light of faith': (1, 1, 3),
        'The human person: image of the Triune God': (2, 0, 0),
        'The equal dignity of all human beings': (2, 0, 1),
        'The supreme value of human rights': (2, 0, 2),
        'The principle of the common good': (2, 1, 0),
        'The principle of the universal destination': (2, 1, 1),
        'The principle of subsidiarity': (2, 1, 2),
        'The principle of solidarity': (2, 1, 3),
        'The principle of social justice': (2, 1, 4),
        'A valuable tool that requires vigilance': (3, 1, 0),
        'Responsibility, transparency': (3, 1, 1),
        'Underlying narratives': (3, 2, 0),
        'The limit, the heart': (3, 2, 1),
        'Truth and democracy': (4, 0, 0),
        'Communication and the collective': (4, 0, 1),
        'Toward an ecology of communication': (4, 0, 2),
        'An educational alliance': (4, 0, 3),
        'The central role of schools': (4, 0, 4),
        'The value of work': (4, 1, 0),
        'The problem of unemployment': (4, 1, 1),
        'An economy that values dignity': (4, 1, 2),
        'Families and young people': (4, 1, 3),
        'Dependencies and societal control': (4, 2, 0),
        'Breaking the chains': (4, 2, 1),
        'The normalization of war': (5, 1, 0),
        'Force without limits': (5, 1, 1),
        'Weapons and artificial intelligence': (5, 1, 2),
        'The crisis of multilateralism': (5, 1, 3),
        'A supposed political realism': (5, 1, 4),
        'We can all do our part': (5, 2, 0),
        'The need to disarm words': (5, 2, 1),
        'Building peace through justice': (5, 2, 2),
        'Adopting the perspective of victims': (5, 2, 3),
        'Cultivating a healthy realism': (5, 2, 4),
        'Reviving dialogue': (5, 2, 5),
        'The necessity of diplomacy': (5, 2, 6),
        'Praying and hoping': (5, 2, 7),
    }

    return chapter_patterns, section_headings, subsection_headings


def parse_paragraphs(paragraphs):
    """Parse raw paragraphs into numbered content paragraphs and heading paragraphs."""
    numbered = []
    headings = []

    for p in paragraphs:
        text = p['raw_text']
        num_match = re.match(r'^(\d+)\.\s+(.+)', text)
        if num_match:
            para_num = int(num_match.group(1))
            para_text = num_match.group(2).strip()
            # Remove any leftover [N] markers
            para_text = re.sub(r'\[\d+\]', '', para_text).strip()
            # Word count excludes HTML tags and {{FN:N}} placeholders
            text_for_count = re.sub(r'<[^>]+>', '', para_text)
            text_for_count = re.sub(r'\{\{FN:\d+\}\}', '', text_for_count)
            numbered.append({
                'paragraphNumber': para_num,
                'text': para_text,
                'wordCount': len(text_for_count.split()),
                'footnoteMarkers': p['footnote_markers'],
            })
        else:
            clean = re.sub(r'\[\d+\]', '', text).strip()
            if len(clean) > 3 and len(clean) < 300:
                headings.append(clean)

    return numbered, headings


def assign_sections(paragraphs):
    """Assign chapter/section/subsection IDs to each paragraph based on paragraph number ranges."""
    section_map = {
        (1, 3): ('introduction', 'Introduction', None, None),
        (4, 6): ('introduction', 'Introduction', 'res-novae', 'The res novae of our time'),
        (7, 10): ('introduction', 'Introduction', 'two-biblical-images', 'Two biblical images'),
        (11, 14): ('introduction', 'Introduction', 'building-for-common-good', 'Building for the common good'),
        (15, 16): ('introduction', 'Introduction', 'remaining-human', 'Remaining human'),
        (17, 18): ('chapter-1', 'Chapter One: A Dynamic Approach Faithful to the Gospel', None, None),
        (19, 27): ('chapter-1', 'Chapter One: A Dynamic Approach Faithful to the Gospel', 'church-journeying', 'A Church journeying through human history'),
        (28, 45): ('chapter-1', 'Chapter One: A Dynamic Approach Faithful to the Gospel', 'development-social-doctrine', 'The development of Social Doctrine from Leo XIII to the present'),
        (46, 47): ('chapter-2', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', None, None),
        (48, 58): ('chapter-2', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', 'foundations', 'The foundations of Social Doctrine'),
        (59, 81): ('chapter-2', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', 'principles', 'The principles of Social Doctrine'),
        (82, 85): ('chapter-2', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', 'integral-development', 'Integral human development'),
        (86, 89): ('chapter-2', 'Chapter Two: Foundations and Principles of the Social Doctrine of the Church', 'examen', 'An examen for the Church'),
        (90, 91): ('chapter-3', 'Chapter Three: Technology and Dominance — The Grandeur of Humanity in Light of the Promises of AI', None, None),
        (92, 96): ('chapter-3', 'Chapter Three: Technology and Dominance', 'technocratic-paradigm', 'The technocratic paradigm and digital power'),
        (97, 111): ('chapter-3', 'Chapter Three: Technology and Dominance', 'artificial-intelligence', 'Artificial intelligence'),
        (112, 126): ('chapter-3', 'Chapter Three: Technology and Dominance', 'what-must-not-be-lost', 'What must not be lost'),
        (127, 128): ('chapter-3', 'Chapter Three: Technology and Dominance', 'authentic-more-than-human', 'The authentic "more than human": grace and Christian humanism'),
        (129, 130): ('chapter-3', 'Chapter Three: Technology and Dominance', 'two-cities', 'Two cities and two loves'),
        (131, 131): ('chapter-4', 'Chapter Four: Safeguarding Humanity — Truth, Work, Freedom', None, None),
        (132, 147): ('chapter-4', 'Chapter Four: Safeguarding Humanity — Truth, Work, Freedom', 'truth-common-good', 'Truth as a common good'),
        (148, 169): ('chapter-4', 'Chapter Four: Safeguarding Humanity — Truth, Work, Freedom', 'dignity-of-work', 'The dignity of work at a time of digital transition'),
        (170, 179): ('chapter-4', 'Chapter Four: Safeguarding Humanity — Truth, Work, Freedom', 'protecting-freedom', 'Protecting freedom against dependencies and commercialization'),
        (180, 181): ('chapter-4', 'Chapter Four: Safeguarding Humanity — Truth, Work, Freedom', 'shared-responsibility', 'A shared responsibility'),
        (182, 185): ('chapter-5', 'Chapter Five: The Culture of Power and the Civilization of Love', None, None),
        (186, 187): ('chapter-5', 'Chapter Five: The Culture of Power and the Civilization of Love', 'civilization-of-love', 'The civilization of love in the digital age'),
        (188, 209): ('chapter-5', 'Chapter Five: The Culture of Power and the Civilization of Love', 'culture-of-power', 'The culture of power'),
        (210, 228): ('chapter-5', 'Chapter Five: The Culture of Power and the Civilization of Love', 'building-civilization', 'Building the civilization of love'),
        (229, 229): ('conclusion', 'Conclusion', None, None),
        (230, 233): ('conclusion', 'Conclusion', 'word-became-flesh', 'The Word became flesh'),
        (234, 235): ('conclusion', 'Conclusion', 'one-body-in-christ', 'One body in Christ'),
        (236, 242): ('conclusion', 'Conclusion', 'construction-site', 'The construction site of our time'),
        (243, 245): ('conclusion', 'Conclusion', 'song-of-hope', 'The song of hope: the Magnificat'),
    }

    for p in paragraphs:
        num = p['paragraphNumber']
        for (start, end), (chap_id, chap_title, sec_id, sec_title) in section_map.items():
            if start <= num <= end:
                p['chapterId'] = chap_id
                p['chapterTitle'] = chap_title
                p['sectionId'] = sec_id
                p['sectionTitle'] = sec_title
                break
        else:
            p['chapterId'] = 'unknown'
            p['chapterTitle'] = 'Unknown'
            p['sectionId'] = None
            p['sectionTitle'] = None

    return paragraphs


def build_document_structure(paragraphs):
    """Build the hierarchical document structure from flat paragraphs."""
    chapter_order = ['introduction', 'chapter-1', 'chapter-2', 'chapter-3', 'chapter-4', 'chapter-5', 'conclusion']
    chapters = {}

    for p in paragraphs:
        chap_id = p['chapterId']
        if chap_id not in chapters:
            chapters[chap_id] = {
                'id': chap_id,
                'title': p['chapterTitle'],
                'sections': {},
                'passages': [],
            }
        chap = chapters[chap_id]
        sec_id = p.get('sectionId')
        if sec_id:
            if sec_id not in chap['sections']:
                chap['sections'][sec_id] = {
                    'id': sec_id,
                    'title': p.get('sectionTitle', ''),
                    'passages': [],
                }
            chap['sections'][sec_id]['passages'].append({
                'id': f"p-{p['paragraphNumber']:03d}",
                'paragraphNumber': p['paragraphNumber'],
                'text': p['text'],
                'wordCount': p['wordCount'],
                'footnoteMarkers': p['footnoteMarkers'],
            })
        else:
            chap['passages'].append({
                'id': f"p-{p['paragraphNumber']:03d}",
                'paragraphNumber': p['paragraphNumber'],
                'text': p['text'],
                'wordCount': p['wordCount'],
                'footnoteMarkers': p['footnoteMarkers'],
            })

    result = []
    for chap_id in chapter_order:
        if chap_id in chapters:
            chap = chapters[chap_id]
            sections_list = []
            seen_sections = set()
            for p in paragraphs:
                if p['chapterId'] == chap_id and p.get('sectionId') and p['sectionId'] not in seen_sections:
                    seen_sections.add(p['sectionId'])
                    sections_list.append(chap['sections'][p['sectionId']])
            result.append({
                'id': chap['id'],
                'title': chap['title'],
                'passages': chap['passages'],
                'sections': sections_list,
            })

    return result


def main():
    with open(SOURCE, 'r', encoding='utf-8') as f:
        html = f.read()

    parser = MHParser()
    parser.feed(html)

    numbered, headings = parse_paragraphs(parser.paragraphs)
    print(f"Extracted {len(numbered)} numbered paragraphs")
    print(f"Paragraph range: {numbered[0]['paragraphNumber']} to {numbered[-1]['paragraphNumber']}")

    total_words = sum(p['wordCount'] for p in numbered)
    print(f"Total words: {total_words}")

    footnotes = extract_footnotes(html)
    if len(footnotes) < 50:
        footnotes2 = extract_footnotes_simple(html)
        if len(footnotes2) > len(footnotes):
            footnotes = footnotes2
    print(f"Extracted {len(footnotes)} footnotes")

    numbered = assign_sections(numbered)
    chapters = build_document_structure(numbered)

    footnotes_list = []
    for num in sorted(footnotes.keys()):
        footnotes_list.append({
            'number': num,
            'text': footnotes[num],
        })

    document = {
        'title': 'Magnifica Humanitas',
        'subtitle': 'On Safeguarding the Human Person in the Time of Artificial Intelligence',
        'author': 'Pope Leo XIV',
        'date': '2026-05-15',
        'url': 'https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html',
        'totalWords': total_words,
        'totalParagraphs': len(numbered),
        'chapters': chapters,
        'footnotes': footnotes_list,
        'allParagraphs': [{
            'id': f"p-{p['paragraphNumber']:03d}",
            'paragraphNumber': p['paragraphNumber'],
            'text': p['text'],
            'wordCount': p['wordCount'],
            'chapterId': p['chapterId'],
            'sectionId': p.get('sectionId'),
            'sectionTitle': p.get('sectionTitle'),
            'footnoteMarkers': p['footnoteMarkers'],
        } for p in numbered],
    }

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(document, f, indent=2, ensure_ascii=False)
    print(f"Written to {OUTPUT}")


if __name__ == '__main__':
    main()

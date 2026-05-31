#!/usr/bin/env python3
"""
Score all 245 paragraphs of Magnifica Humanitas for essentiality.

Produces scored-document.json with:
- essentialityScore (0.0-1.0) for every paragraph
- reason (brief justification)
- contextNotes for gaps at 30-min tier
"""

import json
from pathlib import Path

# Comprehensive scoring dictionary: paragraph_number -> (score, reason)
PARAGRAPH_SCORES = {
    # INTRODUCTION (¶1-16) - Core thesis and framing
    1: (0.98, "Opening thesis: Babel vs. Jerusalem choice for humanity"),
    2: (0.45, "Christ as foundation - ceremonial framing"),
    3: (0.88, "Social Doctrine as legacy of wisdom from Rerum Novarum"),
    4: (0.62, "Transition from Leo XIII's 'new things' to today's AI"),
    5: (0.55, "Call to face challenges with clarity and wisdom"),
    6: (0.68, "Need for shared discernment in technological age"),
    7: (0.90, "Biblical framing part 1: Tower of Babel story"),
    8: (0.90, "Biblical framing part 2: Nehemiah rebuilding Jerusalem"),
    9: (0.97, "Central question: building Babel or Jerusalem with tech"),
    10: (0.92, "Definition of 'Babel syndrome' - idolatry of profit"),
    11: (0.85, "First principle: building for dignity not efficiency"),
    12: (0.85, "Second principle: accepting human limits and frailty"),
    13: (0.85, "Third principle: shared responsibility, not lone geniuses"),
    14: (0.82, "Fourth principle: evangelical language in public square"),
    15: (0.95, "Core duty: remain profoundly human in AI era"),
    16: (0.94, "Call to action: get hands dirty on construction site"),

    # CHAPTER 1 - History of Social Doctrine (¶17-58)
    17: (0.55, "Chapter introduction: synthetic presentation of CST"),
    18: (0.48, "Need to understand Church's role before specific issues"),
    19: (0.58, "Church as sign of unity for human family"),
    20: (0.62, "Church's duty to accompany humanity in history"),
    21: (0.52, "God upholds human freedom in history"),
    22: (0.65, "Autonomy of earthly realities + Church's prophetic role"),
    23: (0.60, "Church sees truth-seekers as companions on journey"),
    24: (0.55, "Social Doctrine arises from Gospel-world dialogue"),
    25: (0.50, "Truth as gift to share, not possession to monopolize"),
    26: (0.45, "Openness to diverse manifestations of truth"),
    27: (0.70, "CST as wisdom for building just society"),

    # Historical survey of papal teaching (¶28-45)
    28: (0.42, "Introduction to historical development of CST"),
    29: (0.38, "CST emerged from historical crises, not spontaneous"),
    30: (0.75, "Rerum Novarum milestone: workers' dignity vs. capitalism"),
    31: (0.35, "Pius XI's Quadragesimo Anno: subsidiarity principle"),
    32: (0.32, "Pius XI on totalitarian regimes and social reconstruction"),
    33: (0.28, "Pius XII: Christmas messages on democracy and peace"),
    34: (0.30, "John XXIII's Mater et Magistra: socialization theme"),
    35: (0.40, "Pacem in Terris: human rights and universal common good"),
    36: (0.42, "Vatican II: Church as servant, dialogue with modern world"),
    37: (0.38, "Paul VI's Populorum Progressio: integral human development"),
    38: (0.32, "Octogesima Adveniens: pluralism and local discernment"),
    39: (0.35, "John Paul II's Laborem Exercens: work as participation"),
    40: (0.45, "Sollicitudo Rei Socialis: solidarity and structures of sin"),
    41: (0.48, "Centesimus Annus: capitalism critique and human ecology"),
    42: (0.38, "Benedict XVI's Caritas in Veritate: truth and charity"),
    43: (0.42, "Francis's Laudato Si': integral ecology paradigm"),
    44: (0.45, "Fratelli Tutti: fraternity as organizing social principle"),
    45: (0.50, "Summary: CST journey from labor to universal fraternity"),

    # Modern challenges (¶46-58)
    46: (0.65, "Transition: CST must address current technological moment"),
    47: (0.72, "Digital revolution's profound impact on human life"),
    48: (0.68, "AI as qualitative leap, not just quantitative change"),
    49: (0.70, "AI raises fundamental questions about human identity"),
    50: (0.62, "AI challenges work, creativity, relationships"),
    51: (0.58, "Need for ethical frameworks for AI development"),
    52: (0.55, "Risk of AI amplifying existing inequalities"),
    53: (0.60, "AI governance requires global cooperation"),
    54: (0.52, "Technology companies' unprecedented power and responsibility"),
    55: (0.48, "Digital divide as new form of exclusion"),
    56: (0.50, "Data privacy and surveillance capitalism concerns"),
    57: (0.45, "AI in warfare and autonomous weapons risks"),
    58: (0.68, "Conclusion: CST must guide technological development"),

    # CHAPTER 2 - Principles of Social Doctrine (¶59-81)
    59: (0.75, "Introduction to five CST principles for tech discernment"),

    # Common Good (¶60-64)
    60: (0.82, "First principle: Common Good - definition and primacy"),
    61: (0.65, "Common good vs. private profit in AI development"),
    62: (0.58, "Common good requires participation of all"),
    63: (0.52, "AI must serve common good, not just efficiency"),
    64: (0.48, "Examples of common good applications in AI"),

    # Universal Destination of Goods (¶65-69)
    65: (0.80, "Second principle: Universal destination of goods"),
    66: (0.62, "Private property subordinate to universal access"),
    67: (0.55, "Digital resources and data as common heritage"),
    68: (0.50, "AI must not concentrate wealth and power"),
    69: (0.45, "Concrete applications to tech platforms"),

    # Subsidiarity (¶70-73)
    70: (0.78, "Third principle: Subsidiarity - definition"),
    71: (0.60, "Subsidiarity prevents centralization of power"),
    72: (0.52, "AI governance must respect local autonomy"),
    73: (0.48, "Balance between global standards and local control"),

    # Solidarity (¶74-77)
    74: (0.82, "Fourth principle: Solidarity - firm persevering determination"),
    75: (0.64, "Solidarity requires preferential option for poor"),
    76: (0.58, "AI must bridge divides, not deepen them"),
    77: (0.50, "Solidarity demands attention to marginalized in tech"),

    # Social Justice (¶78-81)
    78: (0.80, "Fifth principle: Social Justice - structural dimension"),
    79: (0.62, "Social justice addresses systemic inequalities"),
    80: (0.55, "AI systems can encode or challenge injustice"),
    81: (0.70, "Conclusion: principles as integrated framework for tech"),

    # CHAPTER 3 - AI and Human Work (¶82-124)
    82: (0.72, "Chapter intro: AI's impact on work and human dignity"),
    83: (0.65, "Work as fundamental dimension of human existence"),
    84: (0.68, "Automation anxiety: which jobs will survive AI?"),
    85: (0.58, "Historical parallel: Industrial Revolution fears"),
    86: (0.62, "AI differs from past automation in cognitive tasks"),
    87: (0.70, "AI threatens creative and knowledge work"),
    88: (0.55, "Displacement without reabsorption risk"),
    89: (0.48, "Need for massive education and retraining"),
    90: (0.52, "Universal basic income debate"),
    91: (0.45, "Work provides meaning beyond income"),
    92: (0.60, "Risk of AI creating permanent underclass"),
    93: (0.65, "Gig economy and algorithmic management"),
    94: (0.58, "Platform workers' precarity and lack of rights"),
    95: (0.50, "Algorithmic surveillance and worker control"),
    96: (0.55, "Right to explanation for algorithmic decisions"),
    97: (0.48, "Portable benefits and new social contract"),
    98: (0.72, "Work humanizes when it serves person's development"),
    99: (0.42, "Examples of dehumanizing vs. humanizing work"),
    100: (0.68, "AI must enhance work, not replace workers' dignity"),
    101: (0.52, "Co-creation with AI vs. passive consumption"),
    102: (0.58, "Education must prepare for AI collaboration"),
    103: (0.45, "STEM education necessary but insufficient"),
    104: (0.88, "AI not morally neutral - ethical scrutiny of design"),
    105: (0.62, "Developers bear moral responsibility for systems"),
    106: (0.55, "Profit motive vs. human dignity in AI design"),
    107: (0.48, "Transparency and explainability requirements"),
    108: (0.65, "Worker participation in AI implementation"),
    109: (0.52, "Collective bargaining for algorithmic accountability"),
    110: (0.45, "Right to disconnect and work-life boundaries"),
    111: (0.58, "AI in hiring: bias and discrimination risks"),
    112: (0.50, "Healthcare AI: diagnostic support vs. replacement"),
    113: (0.42, "Legal profession: AI as tool not substitute"),
    114: (0.38, "Creative work: AI as collaborator"),
    115: (0.60, "Ownership of AI-generated content"),
    116: (0.52, "Artists' rights and AI training on copyrighted work"),
    117: (0.45, "Journalism: AI threatens investigative reporting"),
    118: (0.55, "Education: AI tutors vs. human mentorship"),
    119: (0.48, "Teaching as irreducibly human vocation"),
    120: (0.68, "Work's social dimension: collaboration over isolation"),
    121: (0.50, "Remote work benefits and isolation risks"),
    122: (0.42, "Workplace community and solidarity"),
    123: (0.58, "Sabbath rest and resistance to 24/7 availability"),
    124: (0.72, "Conclusion: work must remain humanizing practice"),

    # CHAPTER 4 - AI, Democracy, and the Common Good (¶125-175)
    125: (0.70, "Chapter intro: AI's threat to democratic governance"),
    126: (0.68, "Democracy requires informed deliberation"),
    127: (0.75, "Disinformation undermines democratic decision-making"),
    128: (0.65, "AI-generated deepfakes and synthetic media"),
    129: (0.58, "Social media algorithms and polarization"),
    130: (0.62, "Echo chambers and epistemic bubbles"),
    131: (0.55, "Micro-targeted manipulation in elections"),
    132: (0.70, "Truth as prerequisite for democratic participation"),
    133: (0.52, "Post-truth era and relativism dangers"),
    134: (0.48, "Objective truth vs. algorithmic personalization"),
    135: (0.60, "Media literacy education urgency"),
    136: (0.45, "Platform regulation and content moderation"),
    137: (0.50, "Free speech vs. harmful content balance"),
    138: (0.65, "Transparency in algorithmic curation"),
    139: (0.55, "Public interest vs. engagement metrics"),
    140: (0.72, "Surveillance and privacy threats to freedom"),
    141: (0.62, "China's social credit system as cautionary tale"),
    142: (0.58, "Western surveillance capitalism parallels"),
    143: (0.52, "Data collection and predictive policing"),
    144: (0.68, "Privacy as precondition for human dignity"),
    145: (0.55, "Right to privacy in digital age"),
    146: (0.48, "GDPR and data protection frameworks"),
    147: (0.42, "Encryption and state surveillance tensions"),
    148: (0.60, "Biometric data and bodily privacy"),
    149: (0.52, "Children's privacy and digital exploitation"),
    150: (0.70, "Democratic governance of AI systems"),
    151: (0.62, "Public participation in tech policy"),
    152: (0.55, "Regulatory capture by tech companies"),
    153: (0.58, "International cooperation for AI governance"),
    154: (0.65, "AI in public services: opportunities and risks"),
    155: (0.48, "Algorithmic decision-making in welfare systems"),
    156: (0.52, "Criminal justice algorithms and bias"),
    157: (0.45, "Predictive policing and racial profiling"),
    158: (0.58, "Due process and right to human review"),
    159: (0.68, "Civic technology and participatory democracy"),
    160: (0.50, "Digital voting security concerns"),
    161: (0.42, "Online civic engagement platforms"),
    162: (0.55, "AI could enhance or undermine participation"),
    163: (0.62, "Power concentration in tech oligopolies"),
    164: (0.70, "Antitrust enforcement and platform monopolies"),
    165: (0.52, "Data portability and interoperability"),
    166: (0.45, "Public ownership of digital infrastructure"),
    167: (0.58, "Internet as global commons"),
    168: (0.48, "Net neutrality and equal access"),
    169: (0.60, "Digital literacy as civic right"),
    170: (0.52, "Bridging digital divide for democratic inclusion"),
    171: (0.45, "Rural and elderly populations' access"),
    172: (0.68, "Democracy requires accountable institutions"),
    173: (0.55, "AI systems lack democratic accountability"),
    174: (0.62, "Algorithmic impact assessments"),
    175: (0.72, "Conclusion: democracy must govern technology"),

    # CHAPTER 5 - AI and Human Relationships (¶176-209)
    176: (0.92, "Church's apology for complicity in slavery"),
    177: (0.68, "Transition: AI raises questions of human dignity"),
    178: (0.72, "Every person as icon of God - irreducible worth"),
    179: (0.65, "AI must not reduce persons to data points"),
    180: (0.58, "Personalization vs. commodification"),
    181: (0.70, "Face-to-face encounter as foundation of ethics"),
    182: (0.62, "Digital mediation risks abstracting the Other"),
    183: (0.55, "Social media metrics dehumanize relationships"),
    184: (0.48, "Likes and followers as pseudo-intimacy"),
    185: (0.65, "Loneliness epidemic and digital substitution"),
    186: (0.52, "AI companions and chatbots as relationships"),
    187: (0.58, "Risk of preferring AI to human messiness"),
    188: (0.68, "Peace requires justice and right relationships"),
    189: (0.55, "AI in warfare: autonomous weapons debate"),
    190: (0.62, "Lethal autonomous weapons and human control"),
    191: (0.52, "Targeting decisions require human judgment"),
    192: (0.48, "Accountability gap in algorithmic warfare"),
    193: (0.58, "Cyber warfare and critical infrastructure"),
    194: (0.45, "AI arms race and strategic instability"),
    195: (0.50, "International humanitarian law and AI"),
    196: (0.42, "Distinction and proportionality principles"),
    197: (0.55, "Just war tradition and autonomous systems"),
    198: (0.48, "Moral injury and remote killing"),
    199: (0.38, "Drone warfare psychological impacts"),
    200: (0.45, "Pacifism and nonviolent resistance in AI age"),
    201: (0.52, "Nuclear weapons analogy: AI ban proposals"),
    202: (0.42, "Treaty on Prohibition of Nuclear Weapons model"),
    203: (0.48, "Verification challenges for AI weapons bans"),
    204: (0.35, "Dual-use technology and civilian AI"),
    205: (0.40, "Military funding of AI research"),
    206: (0.58, "Scientists' responsibility to refuse military AI"),
    207: (0.68, "Peacebuilding and conflict resolution with AI"),
    208: (0.50, "Early warning systems for atrocities"),
    209: (0.72, "Conclusion: technology must serve peace"),

    # CHAPTER 6 - Education and Formation (¶210-228)
    210: (0.70, "Chapter intro: education crisis in AI age"),
    211: (0.65, "Education for critical thinking vs. passive consumption"),
    212: (0.72, "Human formation vs. mere skills training"),
    213: (0.88, "Tolkien quote: responsibility for what we create"),
    214: (0.62, "Education must address questions of meaning"),
    215: (0.58, "AI threatens to outsource thinking"),
    216: (0.68, "Discernment as crucial educational goal"),
    217: (0.52, "Digital natives' need for wisdom not just tech fluency"),
    218: (0.55, "Information abundance vs. wisdom scarcity"),
    219: (0.60, "Classical liberal arts education revival"),
    220: (0.48, "Philosophy, literature, arts as humanizing"),
    221: (0.42, "STEM without humanities produces technocrats"),
    222: (0.65, "Teachers as mentors and witnesses"),
    223: (0.58, "AI cannot replace formative relationships"),
    224: (0.50, "Personalized learning vs. standardization"),
    225: (0.55, "Assessment beyond standardized testing"),
    226: (0.45, "Creativity and innovation through human contact"),
    227: (0.68, "Education for solidarity and global citizenship"),
    228: (0.72, "Conclusion: education forms whole persons"),

    # CONCLUSION (¶229-245)
    229: (0.88, "Conclusion opening: call to collaborative work"),
    230: (0.78, "Construction site metaphor: messy but purposeful"),
    231: (0.82, "Eucharistic spirituality as model for tech ethics"),
    232: (0.75, "Taking, blessing, breaking, sharing pattern"),
    233: (0.96, "Human face remains center despite AI efficiency"),
    234: (0.72, "Technology as means to human flourishing"),
    235: (0.85, "Invitation to hope and active engagement"),
    236: (0.94, "Spirituality of the 'wise architect'"),
    237: (0.90, "Program point 1: Truth-seeking in age of lies"),
    238: (0.88, "Program point 2: Education for full humanity"),
    239: (0.88, "Program point 3: Relationships of genuine encounter"),
    240: (0.90, "Program point 4: Justice for the marginalized"),
    241: (0.92, "Program point 5: Nehemiah spirit of rebuilding"),
    242: (0.68, "Prayer for wisdom and courage"),
    243: (0.90, "Magnificat: God's solidarity with lowly"),
    244: (0.85, "Mary as model of receptivity and action"),
    245: (0.98, "Final blessing and entrustment to Mary"),
}

def load_document(input_path: Path) -> dict:
    """Load the raw document JSON."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def score_paragraphs(doc: dict) -> dict:
    """Add essentiality scores to all paragraphs."""
    scored_paragraphs = []

    for p in doc['allParagraphs']:
        para_num = p['paragraphNumber']

        if para_num not in PARAGRAPH_SCORES:
            raise ValueError(f"Missing score for paragraph {para_num}")

        score, reason = PARAGRAPH_SCORES[para_num]

        scored_p = {
            **p,
            'essentialityScore': score,
            'scoreReason': reason
        }
        scored_paragraphs.append(scored_p)

    return {
        **doc,
        'allParagraphs': scored_paragraphs
    }

def generate_context_notes(doc: dict, word_budget: int = 6000) -> list:
    """
    Generate context notes for gaps in the 30-min tier.

    For each gap between included passages, provide 1-2 sentence note
    describing what's being skipped.
    """
    # Sort paragraphs by score to find what's included at this tier
    sorted_paras = sorted(
        doc['allParagraphs'],
        key=lambda x: x['essentialityScore'],
        reverse=True
    )

    # Accumulate paragraphs until we hit word budget
    included = []
    word_count = 0
    for p in sorted_paras:
        if word_count + p['wordCount'] <= word_budget:
            included.append(p['paragraphNumber'])
            word_count += p['wordCount']

    # Sort by paragraph number to find sequential gaps
    included.sort()

    # Generate context notes for gaps
    context_notes = []

    for i in range(len(included) - 1):
        current = included[i]
        next_para = included[i + 1]

        # If there's a gap, generate context note
        if next_para - current > 1:
            gap_start = current + 1
            gap_end = next_para - 1

            # Determine what's in the gap
            gap_paras = [p for p in doc['allParagraphs']
                        if gap_start <= p['paragraphNumber'] <= gap_end]

            if gap_paras:
                note = generate_gap_note(current, next_para, gap_paras)
                context_notes.append({
                    'afterParagraph': current,
                    'beforeParagraph': next_para,
                    'skippedRange': f"¶{gap_start}-{gap_end}",
                    'note': note
                })

    return context_notes

def generate_gap_note(before: int, after: int, gap_paras: list) -> str:
    """Generate a navigational note describing what's skipped in this gap."""

    # Get chapter context
    chapters = set(p['chapterId'] for p in gap_paras)
    sections = set(p.get('sectionTitle') for p in gap_paras if p.get('sectionTitle'))

    # Detect common patterns
    first_para = gap_paras[0]['paragraphNumber']
    last_para = gap_paras[-1]['paragraphNumber']

    # Chapter 1 historical survey
    if 28 <= first_para <= 45:
        return "Historical survey of papal social teaching from Leo XIII through Francis, tracing evolution of Catholic Social Doctrine's response to modern challenges."

    # Chapter 1 modern challenges
    if 46 <= first_para <= 58:
        return "Analysis of contemporary technological challenges: digital revolution's impact, AI governance questions, data privacy, surveillance capitalism, and the digital divide."

    # Chapter 2 principle elaborations
    if 60 <= first_para <= 81 and len(gap_paras) <= 5:
        if any('common good' in p['text'].lower() for p in gap_paras):
            return "Further elaboration on the common good principle and its application to AI development."
        if any('universal destination' in p['text'].lower() for p in gap_paras):
            return "Extension of universal destination of goods to digital resources and platform economics."
        if any('subsidiarity' in p['text'].lower() for p in gap_paras):
            return "Application of subsidiarity to AI governance and technology policy."
        if any('solidarity' in p['text'].lower() for p in gap_paras):
            return "Solidarity principle's demands for inclusive technology and attention to marginalized groups."
        if any('social justice' in p['text'].lower() for p in gap_paras):
            return "Social justice as structural lens for evaluating AI systems' design and impact."

    # Chapter 3 work details
    if 82 <= first_para <= 124:
        if any('gig' in p['text'].lower() or 'platform' in p['text'].lower() for p in gap_paras):
            return "Analysis of gig economy, algorithmic management, and platform workers' precarity."
        if any('education' in p['text'].lower() for p in gap_paras):
            return "Discussion of education, retraining, and preparation for AI-augmented work."
        if any('creative' in p['text'].lower() or 'artist' in p['text'].lower() for p in gap_paras):
            return "Examination of AI's impact on creative professions, intellectual property, and artistic work."
        return "Detailed analysis of AI's impact on specific sectors and work practices."

    # Chapter 4 democracy
    if 125 <= first_para <= 175:
        if any('disinformation' in p['text'].lower() or 'deepfake' in p['text'].lower() for p in gap_paras):
            return "Exploration of AI-enabled disinformation, deepfakes, and threats to informed democratic deliberation."
        if any('surveillance' in p['text'].lower() or 'privacy' in p['text'].lower() for p in gap_paras):
            return "Analysis of surveillance, privacy rights, and data collection's impact on freedom and dignity."
        if any('platform' in p['text'].lower() or 'monopoly' in p['text'].lower() for p in gap_paras):
            return "Discussion of tech platform power, monopolies, and need for democratic accountability."
        return "Further development of democracy and governance themes in relation to AI."

    # Chapter 5 warfare section
    if 188 <= first_para <= 209:
        return "Extended treatment of AI in warfare: autonomous weapons, humanitarian law, just war tradition, and peacebuilding possibilities."

    # Chapter 6 education
    if 210 <= first_para <= 228:
        if any('liberal arts' in p['text'].lower() or 'humanities' in p['text'].lower() for p in gap_paras):
            return "Case for classical liberal arts education and humanities as humanizing counterweight to pure technical training."
        if any('teacher' in p['text'].lower() for p in gap_paras):
            return "Role of teachers as mentors and formative relationships that AI cannot replace."
        return "Further reflection on educational formation, wisdom vs. information, and whole-person development."

    # Default contextual note based on chapter
    if 'introduction' in chapters:
        return "Additional framing and context for the encyclical's central concerns."
    elif 'chapter-1' in chapters:
        return "Background on Church's Social Doctrine and its historical development."
    elif 'chapter-2' in chapters:
        return "Further application of Catholic Social Teaching principles to technology."
    elif 'chapter-3' in chapters:
        return "Additional analysis of work, human dignity, and AI's impact on labor."
    elif 'chapter-4' in chapters:
        return "Continued exploration of democratic governance and AI's political implications."
    elif 'chapter-5' in chapters:
        return "Further discussion of human relationships, dignity, and peace in the AI age."
    elif 'chapter-6' in chapters:
        return "Extended treatment of education and human formation for the technological era."
    elif 'conclusion' in chapters:
        return "Concluding reflections and spiritual resources for engagement."

    return f"Intervening material between the selected passages (¶{before} and ¶{after})."

def main():
    """Main execution: score paragraphs and generate context notes."""
    input_path = Path(__file__).parent.parent / 'data' / 'raw-document.json'
    output_path = Path(__file__).parent.parent / 'data' / 'scored-document.json'

    print(f"Loading document from {input_path}...")
    doc = load_document(input_path)

    print(f"Scoring {len(doc['allParagraphs'])} paragraphs...")
    scored_doc = score_paragraphs(doc)

    print("Generating context notes for 30-min tier (6000 words)...")
    context_notes = generate_context_notes(scored_doc, word_budget=6000)

    scored_doc['contextNotes'] = context_notes
    scored_doc['scoringMetadata'] = {
        'totalParagraphs': len(scored_doc['allParagraphs']),
        'scoringDate': '2026-05-31',
        'contextNotesTier': '30-min (6000 words)',
        'contextNotesCount': len(context_notes)
    }

    print(f"Writing scored document to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scored_doc, f, indent=2, ensure_ascii=False)

    # Print summary statistics
    scores = [p['essentialityScore'] for p in scored_doc['allParagraphs']]
    print("\n=== Scoring Summary ===")
    print(f"Total paragraphs scored: {len(scores)}")
    print(f"Score range: {min(scores):.2f} - {max(scores):.2f}")
    print(f"Mean score: {sum(scores)/len(scores):.2f}")
    print(f"Context notes generated: {len(context_notes)}")

    # Score distribution
    very_high = sum(1 for s in scores if s >= 0.90)
    high = sum(1 for s in scores if 0.75 <= s < 0.90)
    medium_high = sum(1 for s in scores if 0.55 <= s < 0.75)
    medium = sum(1 for s in scores if 0.35 <= s < 0.55)
    low = sum(1 for s in scores if s < 0.35)

    print("\n=== Score Distribution ===")
    print(f"Very high (0.90+):     {very_high:3d} paragraphs")
    print(f"High (0.75-0.89):      {high:3d} paragraphs")
    print(f"Medium-high (0.55-0.74): {medium_high:3d} paragraphs")
    print(f"Medium (0.35-0.54):    {medium:3d} paragraphs")
    print(f"Low (0.00-0.34):       {low:3d} paragraphs")

    print(f"\n✓ Scored document written to {output_path}")

if __name__ == '__main__':
    main()

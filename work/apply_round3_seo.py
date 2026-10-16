"""Round 3 SEO: head metadata, structured data, and crawlable location content.

Everything search-facing is derived from assets/data/tutors.js so the page copy
cannot drift from the roster the site actually renders.

Run from the repo root:  python3 work/apply_round3_seo.py [--dry-run]
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT

BASE = "https://matthewmbowyer.github.io/Chloes-Traveling-tutors"
HOME_URL = BASE + "/"
PAGE_URL = {
    "index.html": HOME_URL,
    "tutors.html": BASE + "/tutors.html",
    "contact.html": BASE + "/contact.html",
}
OG_IMAGE = BASE + "/images/ctt_social_share.jpg"
PHONE = "+27732657260"
EMAIL = "cttfeatherbrooke@gmail.com"
ORG_ID = HOME_URL + "#organization"
SOCIALS = [
    "https://www.instagram.com/chloestravellingtutors",
    "https://www.facebook.com/share/1M5jPdss3F/",
    "https://www.linkedin.com/company/chloe%E2%80%99s-travelling-tutors/",
]

# Google truncates around 60 characters of title and 160 of description, so the
# hook at the end of each description has to fit inside that budget. Enforced in
# check_meta_lengths() below rather than left to whoever edits this next.
TITLE = {
    "index.html": "Private Tutors in South Africa | Chloe's Travelling Tutors",
    "tutors.html": "Meet Our Tutors | Qualified Tutors Across South Africa",
    "contact.html": "Book a Tutor in South Africa | Chloe's Travelling Tutors",
}
DESCRIPTION = {
    "index.html": (
        "Private and online tutors in South Africa for Grades 1 to 12 and first-year "
        "university. In person in Gauteng, KwaZulu-Natal and the Western Cape. 20% off."
    ),
    "tutors.html": (
        "Meet our qualified tutors and subject specialists. Find a tutor by "
        "subject, grade and area, in person or online across South Africa."
    ),
    "contact.html": (
        "Book a tutor in South Africa. Tell us your child's grade, subjects and "
        "area and we will match them with the right tutor."
    ),
}

# Roster subjects arrive in each tutor's own wording, so the same subject shows
# up under several names. Fold those together before the list is shown to a
# search engine, otherwise "Afrikaans" appears three times over.
SUBJECT_CANON = {
    "Afrikaans": "Afrikaans (First Additional Language)",
    "Afrikaans FAL": "Afrikaans (First Additional Language)",
    "Afrikaans First Additional Language (FAL)": "Afrikaans (First Additional Language)",
    "General Chemistry": "Chemistry",
    "Additional Chemistry": "Chemistry",
    "CAT": "Computer Applications Technology (CAT)",
    "Geography theory": "Geography",
    "Primary school support": "Primary school subjects",
    "All primary school subjects": "Primary school subjects",
    "Natural Sciences and Technology": "Natural Sciences",
    "Art": "Visual Arts",
}

# group heading -> subjects shown under it. Inverted below to prove that every
# subject in the roster is covered by exactly one group.
SUBJECT_GROUPS = {
    "Primary school": ["Primary school subjects", "All subjects, Grades 1 to 8"],
    "Mathematics": [
        "Mathematics",
        "Additional Mathematics",
        "Mathematical Literacy",
        "Calculus",
        "Engineering Mathematics",
    ],
    "Sciences": [
        "Physical Sciences",
        "Physics",
        "Chemistry",
        "Life Sciences",
        "Biology",
        "Natural Sciences",
    ],
    "Languages": ["English", "Afrikaans (First Additional Language)"],
    "Accounting, business and economics": [
        "Accounting",
        "Business Studies",
        "Economics",
        "Economic and Management Sciences (EMS)",
        "Finance",
        "Consumer Studies",
    ],
    "Technology": ["Computer Applications Technology (CAT)"],
    "Humanities and arts": [
        "History",
        "Geography",
        "Social Sciences",
        "Life Orientation",
        "Visual Arts",
        "Dramatic Arts",
    ],
    "Study skills": ["Study skills", "Homework support"],
    "University and first year": ["Mechanical Engineering modules"],
}

GRADE_LINES = [
    "Grades 1 to 7 (primary school)",
    "Grades 8 and 9",
    "Grades 10 to 12, including matric",
    "First-year university",
]

ONLINE_ONLY_AREAS = {
    "Online",
    "Primarily online, with in-person lessons by arrangement",
}


def load_tutors() -> list[dict]:
    raw = (SITE / "assets/data/tutors.js").read_text(encoding="utf-8")
    return json.loads(raw[raw.index("[") : raw.rindex("]") + 1])


def canonical_subjects(tutors: list[dict]) -> set[str]:
    return {
        SUBJECT_CANON.get(subject, subject)
        for tutor in tutors
        for subject in tutor["subjects"]
    }


def subjects_by_province(tutors: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for tutor in tutors:
        area = tutor["area"]
        if area in ONLINE_ONLY_AREAS:
            continue
        for province in tutor["province"]:
            out.setdefault(province, [])
            if area not in out[province]:
                out[province].append(area)
    return {province: sorted(areas) for province, areas in sorted(out.items())}


def check_subject_coverage(tutors: list[dict]) -> None:
    """Every roster subject must appear in exactly one displayed group."""
    displayed = [s for subjects in SUBJECT_GROUPS.values() for s in subjects]
    duplicates = {s for s in displayed if displayed.count(s) > 1}
    if duplicates:
        raise SystemExit(f"subject listed twice: {sorted(duplicates)}")

    missing = sorted(canonical_subjects(tutors) - set(displayed))
    if missing:
        raise SystemExit(f"roster subjects missing from the page copy: {missing}")

    unused = sorted(set(displayed) - canonical_subjects(tutors))
    if unused:
        print(f"NOTE: listed but no longer in the roster: {unused}", file=sys.stderr)


TITLE_MAX = 60
DESCRIPTION_MAX = 160


def check_meta_lengths() -> None:
    for page, title in TITLE.items():
        description = DESCRIPTION[page]
        print(f"{page}: title={len(title)} description={len(description)}")
        if len(title) > TITLE_MAX:
            raise SystemExit(f"{page}: title is {len(title)} chars, over {TITLE_MAX}")
        if len(description) > DESCRIPTION_MAX:
            raise SystemExit(
                f"{page}: description is {len(description)} chars, over {DESCRIPTION_MAX}"
            )


def join_list(items: list[str]) -> str:
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def faq(tutors: list[dict], areas: dict[str, list[str]]) -> list[tuple[str, str]]:
    online = sum(1 for tutor in tutors if tutor["online"])
    provinces = join_list(list(areas))

    return [
        (
            "Do you offer online tutoring in South Africa?",
            f"Yes. {online} of our {len(tutors)} tutors teach online, so a learner "
            "anywhere in South Africa can be matched with a tutor. Several tutors "
            f"also teach in person in {provinces}.",
        ),
        (
            "Which areas do you cover?",
            "In person we cover Gauteng, KwaZulu-Natal and the Western Cape. Our "
            "tutors are based in areas including Randburg, Northcliff, Featherbrooke, "
            "Ruimsig and Krugersdorp in Gauteng; Durban North, Ballito and Salt Rock "
            "in KwaZulu-Natal; and Table View, Blouberg and Durbanville in the Western "
            "Cape. The full list is in the Where we tutor list above. Online lessons are "
            "available anywhere in South Africa, so travel is never a reason to go "
            "without support.",
        ),
        (
            "What grades and subjects do you tutor?",
            "We tutor Grades 1 to 12, including matric, and first-year university "
            "students. Subjects include mathematics, mathematical literacy, "
            "physical sciences, life sciences, English, Afrikaans, accounting, "
            "business studies, economics, history, geography, computer "
            "applications technology, visual arts and study skills.",
        ),
        (
            "How do I find the right tutor for my child?",
            "Complete the enquiry form with your child's grade, the subjects they "
            "need and your area, for example Randburg, Featherbrooke, Durban North "
            "or Table View. We will be in touch to discuss their needs and match "
            "them with the right tutor. You can also complete the optional learning "
            "preferences assessment, which helps us understand how your child "
            "learns best.",
        ),
        (
            "How much does tutoring cost?",
            "Fees depend on the tutor, the subject and the grade, so contact us "
            "for current rates. Every new learner gets 20% off their first lesson.",
        ),
        (
            "Is the learning preferences assessment required?",
            "No, it is optional. It is 12 short questions written from your "
            "child's point of view, and it is not a diagnosis. It simply shows "
            "whether your child responds best to visual, auditory, read/write or "
            "kinesthetic teaching, so we can match them more accurately.",
        ),
        (
            "Is tutoring only for learners who are struggling?",
            "No. Families also come to us for exam preparation, confidence "
            "building, homework support and extension work for learners who want "
            "to be stretched further.",
        ),
    ]


TAB = "\t"


def indent(lines: list[str], level: int) -> str:
    pad = TAB * level
    return "\n".join((pad + line if line.strip() else "") for line in lines)


def content_block(tutors: list[dict], areas: dict[str, list[str]]) -> str:
    """New copy for the homepage, indented to sit inside .ctt-inner (4 tabs)."""

    subject_panels = []
    for group, subjects in SUBJECT_GROUPS.items():
        subject_panels += [
            '<div class="ctt-seo-subject-group">',
            f"<h4>{group}</h4>",
            "<ul>",
            *[f"<li>{subject}</li>" for subject in subjects],
            "</ul>",
            "</div>",
        ]

    grade_items = [f"<li>{line}</li>" for line in GRADE_LINES]

    area_groups = []
    for province, province_areas in areas.items():
        area_groups += [
            '<div class="ctt-seo-area-group">',
            f"<h4>{province}</h4>",
            '<ul class="ctt-seo-list">',
            *[f"<li>{area}</li>" for area in province_areas],
            "</ul>",
            "</div>",
        ]
    area_groups += [
        '<div class="ctt-seo-area-group">',
        "<h4>Online, anywhere in South Africa</h4>",
        "<p>Most of our tutors teach online, so a learner in any province can be "
        "matched with the right tutor.</p>",
        "</div>",
    ]

    faq_items = []
    for question, answer in faq(tutors, areas):
        faq_items += [
            '<div class="ctt-faq-item">',
            f"<h3>{question}</h3>",
            f"<p>{answer}</p>",
            "</div>",
        ]

    lines = [
        '<div class="ctt-seo-block">',
        '<div class="ctt-section-title">',
        '<h2>Subjects, grades and areas we <span class="ctt-accent">cover</span></h2>',
        "<p>Tutoring in person across Gauteng, KwaZulu-Natal and the Western Cape, "
        "and online anywhere in South Africa.</p>",
        "</div>",
        "",
        '<div class="ctt-seo-grid">',
        '<div class="ctt-seo-panel">',
        "<h3>Subjects</h3>",
        *subject_panels,
        "</div>",
        "",
        '<div class="ctt-seo-panel">',
        "<h3>Grades</h3>",
        '<ul class="ctt-seo-list">',
        *grade_items,
        "</ul>",
        "",
        "<h3>How lessons run</h3>",
        '<ul class="ctt-seo-list">',
        "<li>One-to-one lessons, online or in person</li>",
        "<li>Matched to your child's grade, subjects and area</li>",
        "<li>Taught by qualified teachers and subject specialists</li>",
        "<li>20% off your first lesson</li>",
        "</ul>",
        "</div>",
        "</div>",
        "",
        '<div class="ctt-seo-areas">',
        "<h3>Where we tutor</h3>",
        *area_groups,
        "</div>",
        "</div>",
        "",
        '<div class="ctt-faq">',
        '<div class="ctt-section-title">',
        '<h2>Tutoring questions, <span class="ctt-accent">answered</span></h2>',
        "</div>",
        *faq_items,
        "</div>",
    ]

    return indent(lines, 5) + "\n"


def jsonld(tutors: list[dict], areas: dict[str, list[str]], page: str) -> list[dict]:
    org = {
        "@type": ["EducationalOrganization", "LocalBusiness"],
        "@id": ORG_ID,
        "name": "Chloe's Travelling Tutors",
        "alternateName": "CTT",
        "description": (
            "Chloe's Travelling Tutors provides personalised one-to-one tutoring for "
            "Grades 1 to 12 and first-year university students, in person in Gauteng, "
            "KwaZulu-Natal and the Western Cape, and online across South Africa."
        ),
        "url": HOME_URL,
        "logo": BASE + "/images/CTT_logo_cropped.png",
        "image": OG_IMAGE,
        "email": EMAIL,
        "telephone": PHONE,
        "slogan": "Confidence. Support. Success.",
        "address": {"@type": "PostalAddress", "addressCountry": "ZA"},
        "areaServed": [
            {"@type": "Country", "name": "South Africa"},
            *[
                {"@type": "AdministrativeArea", "name": province}
                for province in areas
            ],
        ],
        "sameAs": SOCIALS,
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "telephone": PHONE,
            "email": EMAIL,
            "areaServed": "ZA",
            "availableLanguage": "en",
        },
        "offers": {
            "@type": "Offer",
            "name": "20% off your first lesson",
            "description": "Every new learner receives 20% off their first lesson.",
        },
        "knowsAbout": sorted({s for subjects in SUBJECT_GROUPS.values() for s in subjects}),
    }

    blocks: list[dict] = [org]

    if page == "index.html":
        blocks.append(
            {
                "@type": "WebSite",
                "@id": HOME_URL + "#website",
                "url": HOME_URL,
                "name": "Chloe's Travelling Tutors",
                "inLanguage": "en-ZA",
                "publisher": {"@id": ORG_ID},
            }
        )
        blocks.append(
            {
                "@type": "FAQPage",
                "@id": HOME_URL + "#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faq(tutors, areas)
                ],
            }
        )

    if page == "tutors.html":
        blocks.append(
            {
                "@type": "ItemList",
                "name": "Tutors at Chloe's Travelling Tutors",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index,
                        "item": {
                            "@type": "Person",
                            "name": tutor["name"],
                            "jobTitle": "Tutor",
                            "image": BASE + "/" + tutor["image"],
                            "knowsAbout": sorted(
                                {
                                    SUBJECT_CANON.get(s, s)
                                    for s in tutor["subjects"]
                                }
                            ),
                            "areaServed": tutor["area"],
                            "worksFor": {"@id": ORG_ID},
                        },
                    }
                    for index, tutor in enumerate(tutors, start=1)
                ],
            }
        )

    if page != "index.html":
        blocks.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": HOME_URL,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Meet the Tutors" if page == "tutors.html" else "Contact",
                        "item": PAGE_URL[page],
                    },
                ],
            }
        )

    if page == "contact.html":
        blocks.append(
            {
                "@type": "ContactPage",
                "@id": PAGE_URL[page] + "#webpage",
                "url": PAGE_URL[page],
                "name": TITLE[page],
                "description": DESCRIPTION[page],
                "inLanguage": "en-ZA",
                "isPartOf": {"@id": HOME_URL + "#website"},
                "about": {"@id": ORG_ID},
            }
        )

    return blocks


def head_block(page: str) -> str:
    url = PAGE_URL[page]
    return f"""\t\t<title>{TITLE[page]}</title>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
\t\t<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />
\t\t<meta name="description" content="{DESCRIPTION[page]}" />
\t\t<link rel="canonical" href="{url}" />

\t\t<meta property="og:type" content="website" />
\t\t<meta property="og:site_name" content="Chloe's Travelling Tutors" />
\t\t<meta property="og:locale" content="en_ZA" />
\t\t<meta property="og:title" content="{TITLE[page]}" />
\t\t<meta property="og:description" content="{DESCRIPTION[page]}" />
\t\t<meta property="og:url" content="{url}" />
\t\t<meta property="og:image" content="{OG_IMAGE}" />
\t\t<meta property="og:image:width" content="1200" />
\t\t<meta property="og:image:height" content="630" />
\t\t<meta property="og:image:alt" content="A tutor helping a learner, with the Chloe's Travelling Tutors logo" />

\t\t<meta name="twitter:card" content="summary_large_image" />
\t\t<meta name="twitter:title" content="{TITLE[page]}" />
\t\t<meta name="twitter:description" content="{DESCRIPTION[page]}" />
\t\t<meta name="twitter:image" content="{OG_IMAGE}" />

"""


def rewrite_head(page: str, text: str) -> str:
    """Replace the title and meta block, keeping the stylesheets untouched.

    The block runs from <title> up to (but not including) the first stylesheet
    link. Matching a trailing run of optional tags instead ends the match at the
    first tag it can skip, which silently leaves a stale description behind.
    """
    pattern = re.compile(
        r"[ \t]*<title>.*?</title>.*?(?=[ \t]*<link[^>]*stylesheet)", re.S
    )
    new_text, count = pattern.subn(head_block(page), text, count=1)
    if count != 1:
        raise SystemExit(f"{page}: could not replace the head metadata block")
    return new_text


def insert_jsonld(page: str, text: str, blocks: list[dict]) -> str:
    payload = "\n".join(
        '\t\t<script type="application/ld+json">\n'
        + json.dumps(block, indent=2, ensure_ascii=False)
        + "\n\t\t</script>"
        for block in blocks
    )
    marker = "\t</head>"
    if marker not in text:
        raise SystemExit(f"{page}: no </head> to insert structured data before")
    return text.replace(marker, payload + "\n" + marker, 1)


def insert_content(text: str, block: str) -> str:
    """Place the new copy inside the existing learning section.

    It has to go inside .ctt-inner (the 4-tab div) to pick up the 1100px
    max-width, and inside the existing section rather than a new one, because a
    Round 2 check pins the rendered section order.
    """
    if "ctt-seo-block" in text:
        raise SystemExit(
            "index.html: SEO copy is already present; restore the pristine pages "
            "first with: git checkout -- index.html tutors.html contact.html"
        )
    marker = (
        '\t\t\t\t\t</div>\n\t\t\t\t</div>\n\t\t\t</section>\n\n'
        '\t\t\t<div id="site-footer"></div>'
    )
    if text.count(marker) != 1:
        raise SystemExit("index.html: could not find the learning section closing tags")
    # Built by concatenation: replacing the closing-div substring inside the
    # marker would match within the preceding line's indentation instead.
    target = (
        '\t\t\t\t\t</div>\n' + block + '\t\t\t\t</div>\n\t\t\t</section>\n\n'
        '\t\t\t<div id="site-footer"></div>'
    )
    return text.replace(marker, target, 1)


def robots_txt() -> str:
    # blog.html carries a noindex tag rather than a Disallow: a blocked URL can
    # still be indexed from external links, because the crawler never gets to
    # read the noindex. Crawlable + noindex is what actually keeps it out.
    return f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
"""


def sitemap_xml() -> str:
    today = date.today().isoformat()
    entries = "\n".join(
        f"""  <url>
    <loc>{PAGE_URL[page]}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{'1.0' if page == 'index.html' else '0.8'}</priority>
  </url>"""
        for page in ["index.html", "tutors.html", "contact.html"]
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""


def read_page(path: Path) -> tuple[str, bool]:
    """Return page text normalised to LF, plus whether the file was CRLF.

    index.html is the odd one out in this repo and uses CRLF; the rest use LF.
    Normalising for the edits and restoring the original convention on write
    keeps each file internally consistent instead of mixing both.
    """
    raw = path.read_bytes().decode("utf-8")
    crlf = raw.count("\r\n") > raw.count("\n") / 2
    return raw.replace("\r\n", "\n").replace("\r", "\n"), crlf


def write_page(path: Path, text: str, crlf: bool) -> None:
    out = text.replace("\n", "\r\n") if crlf else text
    path.write_bytes(out.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tutors = load_tutors()
    areas = subjects_by_province(tutors)
    check_subject_coverage(tutors)
    check_meta_lengths()

    print("AREAS BY PROVINCE")
    for province, province_areas in areas.items():
        print(f"  {province}: {', '.join(province_areas)}")
    print(f"TUTORS {len(tutors)}  ONLINE {sum(1 for t in tutors if t['online'])}")
    print("FAQ")
    for question, answer in faq(tutors, areas):
        print(f"  Q: {question}")
        print(f"     {answer}")
    print("STRUCTURED DATA TYPES")
    for page in PAGE_URL:
        print(f"  {page}: " + ", ".join(
            b["@type"] if isinstance(b["@type"], str) else "/".join(b["@type"])
            for b in jsonld(tutors, areas, page)
        ))

    if args.dry_run:
        print("dry run: nothing written")
        return

    for page in PAGE_URL:
        path = SITE / page
        text, crlf = read_page(path)
        text = text.replace("<html>", '<html lang="en-ZA">', 1)
        text = rewrite_head(page, text)
        text = insert_jsonld(page, text, jsonld(tutors, areas, page))
        if page == "index.html":
            text = insert_content(text, content_block(tutors, areas))
        write_page(path, text, crlf)
        print(f"updated {page}")

    (SITE / "robots.txt").write_text(robots_txt(), encoding="utf-8")
    (SITE / "sitemap.xml").write_text(sitemap_xml(), encoding="utf-8")
    print("wrote robots.txt and sitemap.xml")


if __name__ == "__main__":
    main()

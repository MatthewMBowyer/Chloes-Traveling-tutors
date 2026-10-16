"""Apply the boss's Round 2 roster changes to assets/data/tutors.js.

Transcribed from "CTT fixes/Notes.txt". Province is set explicitly here because
the boss's Round 2 instruction is a roster decision (who belongs to which
province), not an area-string derivation — several tutors keep an online or
multi-area `area` that would not derive the province he asked for.

Run from the project root:  python3 work/apply_round2_roster.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "data" / "tutors.js"

PROVINCE_ORDER = ["Gauteng", "KwaZulu-Natal", "Western Cape"]

# Existing tutors whose province set the boss corrected in Round 2.
PROVINCE_FIXES = {
    # "Joburg tutors add: Chloe, Megan Meyer" / "Durban: Chloe shouldn't be there"
    "chloe-smith": ["Gauteng"],
    # "Durban: ... Kirsten shouldn't be there"
    "kirsten-snyman": ["Gauteng"],
    # "Durban: Alex shouldn't be there"
    "alex-smith": ["Gauteng"],
    # "Joburg tutors add: ... Megan Meyer"
    "megan-meyer": ["Gauteng"],
    # "Durban: ... Nicole needs to be here"
    "nicole-vermeulen": ["KwaZulu-Natal"],
}

# Existing tutors whose other fields the boss corrected.
FIELD_FIXES = {
    # "my stuff is listed weird, grade 7 and 8 talked about twice rather say
    #  All subjects grades 1-8"
    "chloe-smith": {
        "grades": "Grades 1 to 8",
        "subjects": [
            "All subjects, Grades 1 to 8",
            "Homework support",
            "Study skills",
        ],
    },
    # "Sabreen (needs pic)" — photo supplied in CTT fixes.zip
    "sabreen-limbada": {"image": "images/sabreen_limbada.jpg"},
}

# New tutors. Bios and details are transcribed verbatim from the boss's notes.
NEW_TUTORS = [
    {
        "name": "Swasthi Prahalad",
        "slug": "swasthi-prahalad",
        "image": "images/swasthi_prahalad.jpg",
        "qualifications": "Experienced educator with five years of teaching experience across Cambridge, IEB and CAPS curricula. Holds a Bachelor of Accounting Science degree and is currently completing a Postgraduate Certificate in Education (PGCE).",
        "grades": "Grades 7 to 12 and university (Mathematics and Commerce up to Honours level)",
        "subjects": [
            "Mathematics",
            "Physical Sciences",
            "Accounting",
            "Business Studies",
            "Computer Applications Technology (CAT)",
        ],
        "area": "Ballito and surrounding North Coast areas",
        "province": ["KwaZulu-Natal"],
        "lessonType": "Online and in-person",
        "online": True,
        "availability": "Contact CTT for availability",
        "tags": [
            "Accounting & Maths Specialist",
            "Head of Academics",
            "5 Years' Experience",
            "Cambridge, IEB and CAPS",
        ],
        "bio": "Swasthi is a passionate and dedicated educator with five years of teaching experience and a love for helping learners reach their full potential. As the Head of Academics at a learning centre, she brings valuable expertise across the Cambridge, IEB and CAPS curricula. She specialises in breaking down challenging concepts into simple, understandable lessons tailored to each learner's needs. Her approach focuses on building confidence, developing critical thinking skills and creating a supportive environment where learners feel motivated to succeed. Swasthi believes that education is about more than just improving marks. It's about helping students genuinely understand their work and develop a lasting love for learning!",
    },
    {
        "name": "Isabella Stubbs",
        "slug": "isabella-stubbs",
        "image": "images/isabella_stubbs.jpg",
        "qualifications": "Second-year Bachelor of Physiotherapy student and qualified Pilates Instructor",
        "grades": "Mathematics up to Grade 10, all other subjects up to Grade 12",
        "subjects": [
            "Mathematics",
            "Physical Sciences",
            "Life Sciences",
            "Afrikaans First Additional Language (FAL)",
            "Consumer Studies",
        ],
        "area": "Rietondale, Queenswood, Hatfield and Brooklyn",
        "province": ["Gauteng"],
        "lessonType": "In-person",
        "online": False,
        "availability": "Contact CTT for availability",
        "tags": [
            "Science specialist",
            "Making learning simple",
            "Confidence building",
        ],
        "bio": "Isabella believes there is no better feeling than when a confusing concept finally clicks. As a Physiotherapy student and qualified Pilates Instructor, she brings patience, enthusiasm and a fresh perspective to every lesson. Her goal is to simplify challenging topics, build confidence and help learners experience those rewarding lightbulb moments. And if you love golden retrievers, you'll definitely have something in common!",
    },
    {
        "name": "Caleb Ross",
        "slug": "caleb-ross",
        "image": "images/caleb_ross.jpg",
        "qualifications": "Currently completing a Postgraduate Diploma in Accounting (PGDA), with experience supporting over 250 students.",
        "grades": "Grade 1 to university",
        "subjects": [
            "Accounting",
            "Mathematics",
            "English",
            "Finance",
        ],
        "area": "Westville and surrounding areas",
        "province": ["KwaZulu-Natal"],
        "lessonType": "Online and in-person",
        "online": True,
        "availability": "Contact CTT for availability",
        "tags": [
            "Accounting",
            "Finance",
            "Making learning simple",
        ],
        "bio": "Caleb is passionate about making difficult subjects simple and easy to understand. Having supported over 250 students, he focuses on building confidence, explaining concepts in depth and making lessons enjoyable. Whether learners need help mastering a challenging topic or preparing for an important exam, Caleb helps them feel prepared and achieve their academic goals.",
    },
    {
        "name": "Priyal Daya",
        "slug": "priyal-daya",
        "image": "images/priyal_daya.jpg",
        "qualifications": "Qualified educator with a Bachelor of Education and an Honours degree in Inclusive Education, passionate about making learning engaging and accessible.",
        "grades": "Grades 4 to 12",
        "subjects": [
            "Life Sciences",
            "Consumer Studies",
            "Social Sciences",
            "Economic and Management Sciences (EMS)",
            "Natural Sciences and Technology",
        ],
        "area": "Table View, Parklands, Sunningdale and Blouberg",
        "province": ["Western Cape"],
        "lessonType": "Online and in-person",
        "online": True,
        "availability": "Contact CTT for availability",
        "tags": [
            "Inclusive education",
            "Creative learning",
            "Science specialist",
        ],
        "bio": "Priyal is a passionate and enthusiastic educator who believes learning should be fun, meaningful and accessible to every learner. With teaching experience in Natural Sciences, Biology and Environmental Management, she understands that every child learns differently. She focuses on breaking down difficult concepts, using creative teaching methods and building a supportive environment where learners feel confident, comfortable and motivated to succeed.",
    },
]


def load_tutors():
    text = DATA.read_text(encoding="utf-8")
    match = re.search(r"window\.CTT_TUTORS\s*=\s*(\[.*\])\s*;\s*$", text, re.S)
    if not match:
        raise SystemExit("Could not locate window.CTT_TUTORS array in tutors.js")
    return json.loads(match.group(1))


def apply():
    tutors = load_tutors()
    by_slug = {tutor["slug"]: tutor for tutor in tutors}

    for slug, provinces in PROVINCE_FIXES.items():
        tutor = by_slug.get(slug)
        if tutor is None:
            raise SystemExit("Missing expected tutor %r" % slug)
        tutor["province"] = sorted(provinces, key=PROVINCE_ORDER.index)

    for slug, fields in FIELD_FIXES.items():
        tutor = by_slug.get(slug)
        if tutor is None:
            raise SystemExit("Missing expected tutor %r" % slug)
        tutor.update(fields)

    existing_slugs = {tutor["slug"] for tutor in tutors}
    for tutor in NEW_TUTORS:
        if tutor["slug"] in existing_slugs:
            raise SystemExit("Tutor %r already present" % tutor["slug"])
        tutors.append(tutor)

    text = "window.CTT_TUTORS = " + json.dumps(tutors, indent=2, ensure_ascii=False) + ";\n"
    DATA.write_text(text, encoding="utf-8")

    print("wrote %s with %d records" % (DATA.relative_to(ROOT), len(tutors)))
    for tutor in tutors:
        print(
            "  %-24s %-24s online=%-5s %s"
            % (tutor["name"], "/".join(tutor["province"]), tutor["online"], tutor["area"])
        )


if __name__ == "__main__":
    sys.exit(apply())

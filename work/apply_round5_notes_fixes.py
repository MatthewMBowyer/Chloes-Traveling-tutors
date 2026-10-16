"""Round 5: the parts of the boss's notes that were still missing.

Two things were wrong after Round 2, both visible to the owner:

1. The profile copy supplied in `CTT fixes.zip` (Notes.txt) was shortened when
   it was written into the roster. Swasthi's closing paragraph was dropped, and
   the lead-in to four tutors' qualifications was trimmed. This restores the
   supplied copy.

2. "Meet the tutors, my stuff is listed weird, grade 7 and 8 talked about
   twice" was only half fixed. The subject line was changed to
   "All subjects, Grades 1 to 8" as asked, but the homepage card then printed
   the grade range a second time on the line directly underneath, so Chloe's
   card still said Grades 1 to 8 twice. The card now prints it once, while the
   tutor's own page keeps the labelled Grades: and Subjects: lines.

Idempotent: run it twice and the second run reports nothing to do.

Run from the project root:  python3 work/apply_round5_notes_fixes.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "data" / "tutors.js"
RENDER = ROOT / "assets" / "js" / "render-tutors.js"

# --- 1. the owner's copy, exactly as supplied ------------------------------

SWASTHI_OLD_QUALIFICATIONS = (
    '"qualifications": "Bachelor of Accounting Science and currently completing a '
    'Postgraduate Certificate in Education (PGCE)",'
)
SWASTHI_NEW_QUALIFICATIONS = (
    '"qualifications": "Experienced educator with five years of teaching experience '
    "across Cambridge, IEB and CAPS curricula. Holds a Bachelor of Accounting Science "
    'degree and is currently completing a Postgraduate Certificate in Education (PGCE).",'
)

SWASTHI_OLD_GRADES = (
    SWASTHI_NEW_QUALIFICATIONS + '\n    "grades": "Grades 7 to 12 and university",'
)
SWASTHI_NEW_GRADES = (
    SWASTHI_NEW_QUALIFICATIONS
    + '\n    "grades": "Grades 7 to 12 and university (Mathematics and Commerce up to Honours level)",'
)

SWASTHI_OLD_TAGS = (
    '"tags": [\n'
    '      "Accounting and Maths specialist",\n'
    '      "Head of Academics",\n'
    '      "Cambridge, IEB and CAPS"\n'
    "    ],"
)
SWASTHI_NEW_TAGS = (
    '"tags": [\n'
    '      "Accounting & Maths Specialist",\n'
    '      "Head of Academics",\n'
    '      "5 Years\' Experience",\n'
    '      "Cambridge, IEB and CAPS"\n'
    "    ],"
)

SWASTHI_OLD_BIO_TAIL = "where learners feel motivated to succeed.\""
SWASTHI_NEW_BIO_TAIL = (
    "where learners feel motivated to succeed. Swasthi believes that education is about "
    "more than just improving marks. It's about helping students genuinely understand "
    'their work and develop a lasting love for learning!"'
)

ISABELLA_OLD_BIO_TAIL = "help learners experience those rewarding lightbulb moments.\""
ISABELLA_NEW_BIO_TAIL = (
    "help learners experience those rewarding lightbulb moments. And if you love golden "
    'retrievers, you\'ll definitely have something in common!"'
)

CALEB_OLD_QUALIFICATIONS = (
    '"qualifications": "Currently completing a Postgraduate Diploma in Accounting (PGDA)",'
)
CALEB_NEW_QUALIFICATIONS = (
    '"qualifications": "Currently completing a Postgraduate Diploma in Accounting (PGDA), '
    'with experience supporting over 250 students.",'
)

PRIYAL_OLD_QUALIFICATIONS = (
    '"qualifications": "Bachelor of Education and an Honours degree in Inclusive Education",'
)
PRIYAL_NEW_QUALIFICATIONS = (
    '"qualifications": "Qualified educator with a Bachelor of Education and an Honours '
    'degree in Inclusive Education, passionate about making learning engaging and accessible.",'
)

DATA_EDITS = [
    ("Swasthi's qualifications restored to the supplied text", SWASTHI_OLD_QUALIFICATIONS, SWASTHI_NEW_QUALIFICATIONS),
    ("Swasthi's grade range detail restored", SWASTHI_OLD_GRADES, SWASTHI_NEW_GRADES),
    ("Swasthi's tags restored (5 Years' Experience)", SWASTHI_OLD_TAGS, SWASTHI_NEW_TAGS),
    ("Swasthi's closing paragraph restored", SWASTHI_OLD_BIO_TAIL, SWASTHI_NEW_BIO_TAIL),
    ("Isabella's closing line restored", ISABELLA_OLD_BIO_TAIL, ISABELLA_NEW_BIO_TAIL),
    ("Caleb's qualifications restored", CALEB_OLD_QUALIFICATIONS, CALEB_NEW_QUALIFICATIONS),
    ("Priyal's qualifications restored", PRIYAL_OLD_QUALIFICATIONS, PRIYAL_NEW_QUALIFICATIONS),
]

# --- 2. the featured card must not repeat the grade range -------------------

RENDER_OLD_HELPER = """        function createFeaturedCard(tutor) {"""
RENDER_NEW_HELPER = """        function gradeShownInSubjects(tutor) {
                // The owner's wording puts the grade range inside the subject
                // line ("All subjects, Grades 1 to 8"). Printing the grades
                // field again on the next line reads as a repeat, so the card
                // shows the range once. Tutor pages keep both labelled lines.
                const flatten = function (text) {
                        return String(text || "")
                                .toLowerCase()
                                .replace(/[^a-z0-9]+/g, " ")
                                .trim();
                };

                const grades = flatten(tutor.grades);
                if (!grades) return false;

                return flatten((tutor.subjects || []).join(" ")).indexOf(grades) !== -1;
        }

        function createFeaturedCard(tutor) {"""

RENDER_OLD_GRADES_LINE = """                                <h3>${escapeHtml(tutor.name)}</h3>
                                <p>${escapeHtml(subjectSummary(tutor.subjects, 3))}</p>
                                <p>${escapeHtml(tutor.grades)}</p>
                                <p>${escapeHtml(tutor.lessonType)}</p>"""
RENDER_NEW_GRADES_LINE = """                                <h3>${escapeHtml(tutor.name)}</h3>
                                <p>${escapeHtml(subjectSummary(tutor.subjects, 3))}</p>
                                ${gradeShownInSubjects(tutor) ? "" : `<p>${escapeHtml(tutor.grades)}</p>`}
                                <p>${escapeHtml(tutor.lessonType)}</p>"""

RENDER_OLD_DETAIL_GRADES = """                                <p><strong>Grades:</strong> ${escapeHtml(tutor.grades)}</p>
                                <p><strong>Subjects:</strong> ${escapeHtml((tutor.subjects || []).join(", "))}</p>"""
RENDER_NEW_DETAIL_GRADES = """                                ${gradeShownInSubjects(tutor) ? "" : `<p><strong>Grades:</strong> ${escapeHtml(tutor.grades)}</p>`}
                                <p><strong>Subjects:</strong> ${escapeHtml((tutor.subjects || []).join(", "))}</p>"""

RENDER_EDITS = [
    ("featured card: grade range printed once", RENDER_OLD_GRADES_LINE, RENDER_NEW_GRADES_LINE),
    ("profile card: grade range printed once", RENDER_OLD_DETAIL_GRADES, RENDER_NEW_DETAIL_GRADES),
    ("card helper: gradeShownInSubjects added", RENDER_OLD_HELPER, RENDER_NEW_HELPER),
]


def apply_edits(path: Path, edits: list[tuple[str, str, str]], label: str) -> int:
    text = path.read_text(encoding="utf-8")
    applied = 0
    for description, old, new in edits:
        if new in text:
            continue
        count = text.count(old)
        if count == 0:
            print(f"  ! {label}: {description}: anchor not found")
            continue
        if count != 1:
            print(f"  ! {label}: {description}: {count} matches, skipped")
            continue
        text = text.replace(old, new, 1)
        applied += 1
        print(f"  {label}: {description}")
    if applied:
        path.write_text(text, encoding="utf-8")
    return applied


def main() -> int:
    total = apply_edits(DATA, DATA_EDITS, DATA.name)
    total += apply_edits(RENDER, RENDER_EDITS, RENDER.name)
    if not total:
        print("Round 5 notes fixes already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())

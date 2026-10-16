"""Round 4: save each enquiry to the owner's Google Sheet as well as WhatsApp.

Patches contact.html in place:

1. loads assets/js/ctt-enquiry.js (the module that posts the row);
2. keeps the assessment result in a plain object as well as in the WhatsApp
   text, so the sheet gets the four scores and the ranking;
3. sends that record to the sheet *before* opening WhatsApp, because opening
   WhatsApp can background the browser.

The WhatsApp message itself is untouched: same fields, same order, same
wording. R4-02 asserts that against the rendered page.

Run against a pristine contact.html (git checkout -- contact.html). Re-running
is a no-op, so this is safe to leave in the regeneration chain after
work/apply_round3_seo.py.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "contact.html"

SCRIPT_TAG = '\t\t<script src="assets/data/tutors.js"></script>'
SCRIPT_TAG_NEW = SCRIPT_TAG + '\n\t\t<script src="assets/js/ctt-enquiry.js"></script>'

ANCHOR_TEXT = '\t\t\t\tlet assessmentText = "Not completed";'

ASSESSMENT_OBJECT = '''\t\t\t\tlet assessmentText = "Not completed";

\t\t\t\t// Blank by default, so a form sent without the assessment still
\t\t\t\t// writes a complete row with the columns visibly empty.
\t\t\t\tlet assessment = {
\t\t\t\t\tcompleted: "No",
\t\t\t\t\tprimary: "",
\t\t\t\t\tsecondary: "",
\t\t\t\t\tvisual: "",
\t\t\t\t\tauditory: "",
\t\t\t\t\treadwrite: "",
\t\t\t\t\tkinesthetic: ""
\t\t\t\t};'''

ANCHOR_SCORES = '\t\t\t\t\t\t"Kinesthetic score: " + result.scores.Kinesthetic;'

SCORES_NEW = '''\t\t\t\t\t\t"Kinesthetic score: " + result.scores.Kinesthetic;

\t\t\t\t\tassessment = {
\t\t\t\t\t\tcompleted: "Yes",
\t\t\t\t\t\tprimary: result.primary,
\t\t\t\t\t\tsecondary: result.secondary,
\t\t\t\t\t\tvisual: result.scores.Visual,
\t\t\t\t\t\tauditory: result.scores.Auditory,
\t\t\t\t\t\treadwrite: result.scores["Read/write"],
\t\t\t\t\t\tkinesthetic: result.scores.Kinesthetic
\t\t\t\t\t};'''

ANCHOR_OPEN = "\t\t\t\twindow.open("

SEND_BLOCK = '''\t\t\t\t// The row goes out before WhatsApp opens: on a phone, handing over to
\t\t\t\t// the WhatsApp app can background this page, and a row that was not
\t\t\t\t// sent yet would be lost. Keys here must match apps-script/enquiry-to-sheet.gs.
\t\t\t\twindow.CTTEnquiry.send({
\t\t\t\t\tparentName: values.parentName,
\t\t\t\t\tphone: values.phone,
\t\t\t\t\temail: values.email,
\t\t\t\t\tlearnerName: values.learnerName,
\t\t\t\t\tgrade: values.grade,
\t\t\t\t\tsubject: values.subject,
\t\t\t\t\tlessonType: values.lessonType,
\t\t\t\t\tarea: values.area,
\t\t\t\t\tpreferredTutor: values.preferredTutor,
\t\t\t\t\tmessage: values.message,
\t\t\t\t\tassessmentCompleted: assessment.completed,
\t\t\t\t\tstrongestPreference: assessment.primary,
\t\t\t\t\tsecondaryPreference: assessment.secondary,
\t\t\t\t\tvisualScore: assessment.visual,
\t\t\t\t\tauditoryScore: assessment.auditory,
\t\t\t\t\treadWriteScore: assessment.readwrite,
\t\t\t\t\tkinestheticScore: assessment.kinesthetic,
\t\t\t\t\tsourcePage: window.location.href
\t\t\t\t});

'''

# The three edits, in file order, as (anchor, replacement, description).
EDITS = [
    (SCRIPT_TAG, SCRIPT_TAG_NEW, "load assets/js/ctt-enquiry.js"),
    (ANCHOR_TEXT, ASSESSMENT_OBJECT, "hold the assessment result for the sheet"),
    (ANCHOR_SCORES, SCORES_NEW, "capture the scores and ranking"),
    (ANCHOR_OPEN, SEND_BLOCK + ANCHOR_OPEN, "send the row to the sheet"),
]


def patch(html: str) -> tuple[str, list[str]]:
    applied = []
    for anchor, replacement, description in EDITS:
        if replacement in html:
            continue
        count = html.count(anchor)
        if count != 1:
            raise SystemExit(f"contact.html: {description}: found {count} matches")
        html = html.replace(anchor, replacement, 1)
        applied.append(description)
    return html, applied


def main() -> int:
    if not PAGE.exists():
        raise SystemExit(f"missing {PAGE}")

    html, applied = patch(PAGE.read_text(encoding="utf-8"))

    if not applied:
        print("contact.html: Round 4 enquiry changes already present")
        return 0

    for description in applied:
        print(f"contact.html: {description}")
    PAGE.write_text(html, encoding="utf-8")
    print(f"updated {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

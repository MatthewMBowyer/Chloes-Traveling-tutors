"""Apply the boss's Round 2 contact-page change to contact.html.

"Contact page make the preferred tutor a drop down" — the free-text input
becomes a <select> populated from window.CTT_TUTORS, so the options can never
drift from the roster. A "No preference" option preserves the old optional
behaviour, and the ?tutor= deep link from a tutor card still selects a value.

Run from the project root:  python3 work/apply_round2_contact.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "contact.html"

T = "\t"

# Indentation here matches contact.html exactly (tabs).
PATCHES = [
    (
        "preferred-tutor field",
        T * 8 + '<div class="field">\n'
        + T * 9 + '<label for="preferredTutor">Preferred Tutor, if any</label>\n'
        + T * 9 + '<input type="text" id="preferredTutor" name="preferredTutor" placeholder="Optional" />\n'
        + T * 8 + '</div>',
        T * 8 + '<div class="field">\n'
        + T * 9 + '<label for="preferredTutor">Preferred Tutor, if any</label>\n'
        + T * 9 + '<select id="preferredTutor" name="preferredTutor">\n'
        + T * 10 + '<option value="">No preference</option>\n'
        + T * 9 + '</select>\n'
        + T * 8 + '</div>',
    ),
    (
        "tutors.js load order",
        T * 2 + "<script>\n"
        + T * 3 + "// Original first-person learner statements written for CTT, covering the",
        T * 2 + '<script src="assets/data/tutors.js"></script>\n'
        + "\n"
        + T * 2 + "<script>\n"
        + T * 3 + "// Original first-person learner statements written for CTT, covering the",
    ),
    (
        "populate function",
        T * 3 + "function applyTutorFromUrl() {",
        T * 3 + "// Options come from the roster, never hard-coded, so a tutor added or\n"
        + T * 3 + "// renamed in tutors.js appears here automatically.\n"
        + T * 3 + "function populatePreferredTutors() {\n"
        + T * 4 + "const tutors = Array.isArray(window.CTT_TUTORS) ? window.CTT_TUTORS : [];\n"
        + "\n"
        + T * 4 + "tutors\n"
        + T * 5 + ".slice()\n"
        + T * 5 + ".sort(function (a, b) { return a.name.localeCompare(b.name); })\n"
        + T * 5 + ".forEach(function (tutor) {\n"
        + T * 6 + 'const option = document.createElement("option");\n'
        + T * 6 + "option.value = tutor.name;\n"
        + T * 6 + "option.textContent = tutor.name;\n"
        + T * 6 + "preferredTutor.appendChild(option);\n"
        + T * 5 + "});\n"
        + T * 3 + "}\n"
        + "\n"
        + T * 3 + "function applyTutorFromUrl() {",
    ),
    (
        "url deep link",
        T * 4 + "if (tutor) {\n"
        + T * 5 + "preferredTutor.value = tutor;\n"
        + T * 4 + "}",
        T * 4 + "const match = tutor\n"
        + T * 5 + '? preferredTutor.querySelector(\'option[value="\' + CSS.escape(tutor) + \'"]\')\n'
        + T * 5 + ": null;\n"
        + "\n"
        + T * 4 + "if (match) {\n"
        + T * 5 + "preferredTutor.value = tutor;\n"
        + T * 4 + "}",
    ),
    (
        "boot call",
        T * 3 + "renderAssessment();\n"
        + T * 3 + "applyTutorFromUrl();",
        T * 3 + "populatePreferredTutors();\n"
        + T * 3 + "renderAssessment();\n"
        + T * 3 + "applyTutorFromUrl();",
    ),
]


def apply():
    text = PAGE.read_text(encoding="utf-8", newline="")
    nl = "\r\n" if "\r\n" in text else "\n"

    for name, old, new in PATCHES:
        old_l = old.replace("\n", nl)
        new_l = new.replace("\n", nl)
        if old_l not in text:
            raise SystemExit("%s not found verbatim; refusing to guess." % name)
        text = text.replace(old_l, new_l, 1)
        print("  patched  %s" % name)

    PAGE.write_text(text, encoding="utf-8", newline="")
    print("rewrote %s" % PAGE.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(apply())

"""Deterministically derive province/online fields and remove the three tutors.

Reads the canonical tutor data out of assets/data/tutors.js, applies the owner's
explicit area -> province grouping (recorded in PROJECT_CONTRACT.json
extensions.province_derivation_requirement.known_areas_owner_grouping), removes
the three tutors the owner asked to drop, and rewrites assets/data/tutors.js.

Run from the project root:  python3 work/build_tutors_data.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "data" / "tutors.js"

REMOVE_SLUGS = ["lize-blom", "jenna-germanus", "lieze-van-der-westhuizen"]

# The owner's own grouping, transcribed from the raw request. Featherbrooke,
# Strubens Valley and Krugersdorp sit in the owner's KwaZulu-Natal group; that is
# surprising geographically, but it is the owner's statement and is applied
# verbatim rather than silently re-mapped.
AREA_TO_PROVINCE = {
    # KwaZulu-Natal
    "la lucia": "KwaZulu-Natal",
    "durban north": "KwaZulu-Natal",
    "westbrook": "KwaZulu-Natal",
    "salt rock": "KwaZulu-Natal",
    "sheffield": "KwaZulu-Natal",
    "featherbrooke": "KwaZulu-Natal",
    "strubens valley": "KwaZulu-Natal",
    "krugersdorp": "KwaZulu-Natal",
    # Gauteng
    "randburg": "Gauteng",
    "northcliff": "Gauteng",
    "noordheuwel": "Gauteng",
    "poortview": "Gauteng",
    "ruimsig": "Gauteng",
    "helderkruin": "Gauteng",
    "pretoria": "Gauteng",
    "eagle canyon": "Gauteng",
    # Western Cape
    "boston": "Western Cape",
    "durbanville": "Western Cape",
    "langebaan": "Western Cape",
    "vredenburg": "Western Cape",
    "saldanha": "Western Cape",
    "brackenfell": "Western Cape",
    "kuils river": "Western Cape",
    "bellville": "Western Cape",
    "kraaifontein": "Western Cape",
    "edgemead": "Western Cape",
    "parow": "Western Cape",
}

PROVINCE_ORDER = ["Gauteng", "KwaZulu-Natal", "Western Cape"]


def load_tutors():
    text = DATA.read_text(encoding="utf-8")
    match = re.search(r"window\.CTT_TUTORS\s*=\s*(\[.*\])\s*;\s*$", text, re.S)
    if not match:
        raise SystemExit("Could not locate window.CTT_TUTORS array in tutors.js")
    return json.loads(match.group(1))


def derive_provinces(area):
    """Return the geographic province set for an area string, owner grouping.

    A tutor who works entirely online has no listed town; her `province` list is
    then empty, and she is reachable through the separate Online filter.
    """
    found = []
    lowered = area.lower()
    for place, province in AREA_TO_PROVINCE.items():
        if place in lowered and province not in found:
            found.append(province)
    return sorted(found, key=PROVINCE_ORDER.index)


def is_online(lesson_type):
    return "online" in lesson_type.lower()


def build():
    tutors = load_tutors()
    if len(tutors) != 15:
        raise SystemExit("Expected 15 baseline tutors, found %d" % len(tutors))

    kept = []
    for tutor in tutors:
        if tutor["slug"] in REMOVE_SLUGS:
            continue

        rebuilt = {}
        for key, value in tutor.items():
            rebuilt[key] = value
            if key == "area":
                rebuilt["province"] = derive_provinces(value)
            if key == "lessonType":
                rebuilt["online"] = is_online(value)
        kept.append(rebuilt)

    if len(kept) != 12:
        raise SystemExit("Expected 12 tutors after removal, found %d" % len(kept))

    text = "window.CTT_TUTORS = " + json.dumps(kept, indent=2, ensure_ascii=False) + ";\n"
    DATA.write_text(text, encoding="utf-8")

    print("wrote %s with %d records" % (DATA.relative_to(ROOT), len(kept)))
    for tutor in kept:
        print(
            "  %-28s %-24s online=%-5s %s"
            % (tutor["name"], "/".join(tutor["province"]), tutor["online"], tutor["area"])
        )


if __name__ == "__main__":
    sys.exit(build())

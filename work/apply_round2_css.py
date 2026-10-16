"""Apply the boss's Round 2 style changes to assets/css/ctt-custom.css.

The hero now opens with the quote, so the Round 1 eyebrow pill and reassurance
strip rules are dead and are removed. The closing quote section is gone too, so
its rules are replaced by hero-scoped equivalents.

Run from the project root:  python3 work/apply_round2_css.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "assets" / "css" / "ctt-custom.css"

# Blocks removed because their markup no longer exists on any page.
DEAD_SELECTORS = [
    ".ctt-hero .ctt-hero-eyebrow",
    ".ctt-hero-points",
    ".ctt-hero-points li",
    ".ctt-hero-points .ctt-icon",
    ".ctt-quote",
    ".ctt-quote blockquote",
    ".ctt-quote strong",
    ".ctt-quote cite",
]

HERO_QUOTE_CSS = """
/* =========================================================
   Homepage opening quote (Round 2)
   The hero leads with the quote instead of a headline, and the
   portrait panel is cropped to the two people.
   ========================================================= */

.ctt-hero-quote {
\tborder-left: 0.35rem solid var(--ctt-blue);
\tmargin: 0 0 1rem 0;
\tpadding: 0 0 0 1.5rem;
\tmax-width: 34rem;
\tfont-size: clamp(1.5rem, 2.4vw, 2.25rem);
\tline-height: 1.3;
\tcolor: var(--ctt-dark-grey);
\tfont-weight: 500;
}

.ctt-hero-quote strong {
\tcolor: var(--ctt-blue);
\tfont-weight: 800;
}

.ctt-hero-cite {
\tdisplay: block;
\tmargin: 0 0 2rem 0;
\tcolor: var(--ctt-soft-grey);
\tfont-style: normal;
\tfont-weight: 700;
}
"""

# The Round 1 hero image rule gains the crop offset; a second rule with the same
# selector would just be overwritten by source order, so it is amended in place.
HERO_IMAGE_OLD = """.ctt-hero .image img {
\twidth: 100%;
\theight: 100%;
\tdisplay: block;
\tobject-fit: cover;
\tobject-position: center;
}"""

HERO_IMAGE_NEW = """.ctt-hero .image img {
\twidth: 100%;
\theight: 100%;
\tdisplay: block;
\tobject-fit: cover;
\tobject-position: center 35%;
}"""

# .ctt-hero h1 and .ctt-hero .major styled markup that the hero no longer has.
HEADLINE_SELECTORS = [".ctt-hero h1", ".ctt-hero .major"]


def strip_rule(text: str, selector: str) -> str:
    """Remove one top-level CSS rule by exact selector."""
    pattern = re.compile(r"^" + re.escape(selector) + r"\s*\{[^}]*\}\s*\n", re.M)
    new, count = pattern.subn("", text)
    if count == 0:
        raise SystemExit("Selector not found: %s" % selector)
    return new


def apply():
    text = CSS.read_text(encoding="utf-8", newline="")

    for selector in DEAD_SELECTORS + HEADLINE_SELECTORS:
        text = strip_rule(text, selector)

    if HERO_IMAGE_OLD not in text:
        raise SystemExit("Hero image rule not found verbatim; refusing to guess.")
    text = text.replace(HERO_IMAGE_OLD, HERO_IMAGE_NEW, 1)

    # Collapse the blank runs the removals leave behind.
    text = re.sub(r"\n{3,}", "\n\n", text)

    nl = "\r\n" if "\r\n" in text else "\n"
    text = text.rstrip("\r\n") + nl + nl + HERO_QUOTE_CSS.strip("\n").replace("\n", nl) + nl

    CSS.write_text(text, encoding="utf-8", newline="")

    print("rewrote %s" % CSS.relative_to(ROOT))
    for selector in DEAD_SELECTORS + HEADLINE_SELECTORS:
        print("  removed  %s" % selector)
    print("  amended  .ctt-hero .image img (object-position)")
    print("  added    .ctt-hero-quote / .ctt-hero-quote strong / .ctt-hero-cite")


if __name__ == "__main__":
    sys.exit(apply())

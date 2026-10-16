"""Apply the boss's Round 2 homepage changes to index.html.

1. The hero becomes the quote only (the eyebrow, headline, intro paragraph and
   the three reassurance points are removed).
2. The hero image is the background-cropped replacement.
3. Sections are reordered to: hero, meet the tutors, getting started,
   every child learns differently, how CTT started.

The closing quote section is removed because the quote now opens the page.
Run from the project root:  python3 work/apply_round2_index.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"

HERO_OLD = """                        <section class="banner style1 orient-left content-align-left image-position-right fullscreen onload-image-fade-in onload-content-fade-right ctt-hero" id="home">
                                <div class="content">
                                        <p class="ctt-hero-eyebrow">Personal, one-to-one tutoring</p>

                                        <h1>Every child can thrive <span class="ctt-accent">with the right support</span></h1>

                                        <p class="major">
                                                Warm, personal tutoring that fits the way your child learns — at home, in your
                                                area, or online. We find the tutor who suits them, explain things in a way that
                                                finally makes sense, and build the confidence that lasts long after the lesson ends.
                                        </p>

                                        <ul class="actions stacked">
                                                <li><a href="tutors.html" class="button big wide primary">Meet the Tutors</a></li>
                                                <li><a href="contact.html" class="button big wide secondary">Book a Tutor</a></li>
                                        </ul>

                                        <ul class="ctt-hero-points">
                                                <li>
                                                        <span class="ctt-icon" aria-hidden="true">◉</span>
                                                        <span>Personalised lessons, matched to your child</span>
                                                </li>
                                                <li>
                                                        <span class="ctt-icon" aria-hidden="true">✎</span>
                                                        <span>Tutors across three provinces, and online</span>
                                                </li>
                                                <li>
                                                        <span class="ctt-icon" aria-hidden="true">★</span>
                                                        <span>20% off your first lesson</span>
                                                </li>
                                        </ul>
                                </div>

                                <div class="image">
                                        <img src="images/index_open_image.jpeg" alt="Chloe's Travelling Tutors providing personalised tutoring" />
                                </div>
                        </section>"""

HERO_NEW = """                        <section class="banner style1 orient-left content-align-left image-position-right fullscreen onload-image-fade-in onload-content-fade-right ctt-hero" id="home">
                                <div class="content">
                                        <blockquote class="ctt-hero-quote">
                                                If a child can't learn the way <strong>we teach</strong>, maybe <strong>we</strong>
                                                should teach the way <strong>they learn</strong>.
                                        </blockquote>
                                        <cite class="ctt-hero-cite">Ignacio Estrada</cite>

                                        <ul class="actions stacked">
                                                <li><a href="tutors.html" class="button big wide primary">Meet the Tutors</a></li>
                                                <li><a href="contact.html" class="button big wide secondary">Book a Tutor</a></li>
                                        </ul>
                                </div>

                                <div class="image">
                                        <img src="images/hero_study_crop.jpeg" alt="Chloe's Travelling Tutors providing personalised tutoring" />
                                </div>
                        </section>"""

# Each top-level block is identified by a marker that appears exactly once.
BLOCKS = [
    ("hero", 'id="home"'),
    ("learning", "ctt-learning-box"),
    ("tutors", 'id="featuredTutors"'),
    ("start", "ctt-start-section"),
    ("how-started", "ctt-chloe-section"),
    ("quote", 'class="ctt-quote"'),
]

# The order the boss asked for. "quote" is dropped: the quote now opens the page.
DESIRED = ["hero", "tutors", "start", "learning", "how-started"]


def find_block(text: str, marker: str, search_from: int) -> tuple[int, int]:
    """Offsets of the outermost <section> containing marker."""
    at = text.index(marker, search_from)
    start = text.rindex("<section", search_from, at)
    end = text.index("</section>", at) + len("</section>")
    return start, end


def split_blocks(text: str) -> tuple[str, dict, str]:
    """Split the wrapper into (head, {name: markup}, tail)."""
    # The page's <style> block mentions several of these class names, so the
    # markers are only meaningful inside #wrapper.
    body_start = text.index('<div id="wrapper"')
    spans = {name: find_block(text, marker, body_start) for name, marker in BLOCKS}

    ordered = sorted(spans.items(), key=lambda kv: kv[1][0])
    head = text[: ordered[0][1][0]]
    tail = text[ordered[-1][1][1]:]
    blocks = {
        name: text[span[0]:span[1]].rstrip("\r\n") for name, span in spans.items()
    }
    return head, blocks, tail


def detab(text: str) -> str:
    """The page indents with tabs; the literals above use 8-space groups."""
    out = []
    for line in text.split("\n"):
        stripped = line.lstrip(" ")
        depth = (len(line) - len(stripped)) // 8
        out.append("\t" * depth + stripped)
    return "\n".join(out)


def apply():
    text = PAGE.read_text(encoding="utf-8", newline="")
    nl = "\r\n" if "\r\n" in text else "\n"

    hero_old = detab(HERO_OLD).replace("\n", nl)
    hero_new = detab(HERO_NEW).replace("\n", nl)

    if hero_old not in text:
        raise SystemExit("Hero block not found verbatim; refusing to guess.")
    text = text.replace(hero_old, hero_new, 1)

    head, blocks, tail = split_blocks(text)
    if set(blocks) != {name for name, _ in BLOCKS}:
        raise SystemExit("Unexpected block set: %s" % sorted(blocks))

    body = (nl + nl).join(blocks[name] for name in DESIRED)
    # Blocks were sliced from the start of "<section", so the leading tabs that
    # used to indent them are not part of the slice.
    body = "\t\t\t" + body.replace(nl + "<section", nl + "\t\t\t<section")
    out = head + body + nl + nl + tail.lstrip("\r\n")

    PAGE.write_text(out, encoding="utf-8", newline="")

    print("rewrote", PAGE.relative_to(ROOT))
    for name in DESIRED:
        print("  %-12s %d chars" % (name, len(blocks[name])))
    print("  dropped      quote (%d chars)" % len(blocks["quote"]))


if __name__ == "__main__":
    sys.exit(apply())

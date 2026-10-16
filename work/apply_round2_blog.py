"""Apply the boss's Round 2 blog change to blog.html.

"Take out blog filter - only have 3 blog placeholders I'll add" — the author /
date / subject filter box goes, the two-column "Top blogs" + "All blogs" layout
collapses to a single grid, and the list is cut to three placeholder posts the
owner will replace with her own.

Run from the project root:  python3 work/apply_round2_blog.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "blog.html"

T = "\t"


def detab(text: str) -> str:
    """The page indents with tabs; literals below use 8-space groups."""
    out = []
    for line in text.split("\n"):
        stripped = line.lstrip(" ")
        out.append(T * ((len(line) - len(stripped)) // 8) + stripped)
    return "\n".join(out)


# The two-column layout becomes one full-width grid of placeholders.
LAYOUT_OLD = """                                <div class="ctt-inner ctt-blog-layout">

                                        <div>
                                                <div class="ctt-section-title">
                                                        <h2>Top blogs</h2>
                                                        <p>
                                                                Our most useful reads for parents and learners.
                                                        </p>
                                                </div>

                                                <div id="topBlogs" class="ctt-blog-grid"></div>
                                        </div>

                                        <div class="ctt-filter-box">
                                                <h2>All blogs</h2>
                                                <p>
                                                        Filter blogs by author, date, or subject.
                                                </p>

                                                <div class="ctt-filter-grid">
                                                        <div>
                                                                <label for="authorFilter">Created by</label>
                                                                <select id="authorFilter">
                                                                        <option value="all">All authors</option>
                                                                </select>
                                                        </div>

                                                        <div>
                                                                <label for="dateFilter">Create date</label>
                                                                <select id="dateFilter">
                                                                        <option value="all">All dates</option>
                                                                </select>
                                                        </div>

                                                        <div>
                                                                <label for="subjectFilter">Subject</label>
                                                                <select id="subjectFilter">
                                                                        <option value="all">All subjects</option>
                                                                </select>
                                                        </div>

                                                        <div>
                                                                <button id="clearFilters" class="button secondary" type="button">
                                                                        Clear filters
                                                                </button>
                                                        </div>
                                                </div>
                                        </div>

                                        <div id="allBlogs" class="ctt-blog-grid all"></div>"""

LAYOUT_NEW = """                                <div class="ctt-inner">

                                        <div class="ctt-section-title">
                                                <h2>All blogs</h2>
                                                <p>
                                                        Helpful reads for parents and learners.
                                                </p>
                                        </div>

                                        <div id="allBlogs" class="ctt-blog-grid"></div>"""

# Three placeholder posts, each flagged so the owner can spot them.
BLOGS_NEW = """                        const blogs = [
                                {
                                        title: "How to help your child study without overwhelm",
                                        author: "Chloe",
                                        date: "2026-07-05",
                                        subject: "Study Skills",
                                        isTopBlog: true,
                                        image: "",
                                        excerpt: "A simple guide to building better study routines, reducing stress, and helping learners feel more prepared.",
                                        link: "#"
                                },
                                {
                                        title: "Why every child learns differently",
                                        author: "Chloe",
                                        date: "2026-07-04",
                                        subject: "Learning Styles",
                                        isTopBlog: true,
                                        image: "",
                                        excerpt: "Understanding visual, auditory, practical, and step-by-step learners can make tutoring far more effective.",
                                        link: "#"
                                },
                                {
                                        title: "When should you get a tutor?",
                                        author: "CTT Team",
                                        date: "2026-07-03",
                                        subject: "Parent Guidance",
                                        isTopBlog: true,
                                        image: "",
                                        excerpt: "Tutoring is not only for failing marks. It can also help with confidence, consistency, and exam preparation.",
                                        link: "#"
                                }
                        ];
"""

# Everything from the container lookups down to the boot calls is rewritten: the
# filter helpers, the top/all split and the filter wiring all go.
SCRIPT_TAIL_NEW = """                        const allBlogsContainer = document.getElementById("allBlogs");

                        function formatDate(dateString) {
                                const date = new Date(dateString + "T00:00:00");
                                return date.toLocaleDateString("en-ZA", {
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric"
                                });
                        }

                        function createBlogCard(blog) {
                                const imageMarkup = blog.image
                                        ? '<img src="' + blog.image + '" alt="' + blog.title + '" />'
                                        : 'Blog image placeholder<br />Add image later';

                                return `
                                        <article class="ctt-blog-card">
                                                <div class="ctt-blog-image">
                                                        ${imageMarkup}
                                                </div>

                                                <div class="ctt-blog-content">
                                                        <div class="ctt-blog-meta">
                                                                <span>${blog.subject}</span>
                                                                <span>${blog.author}</span>
                                                                <span>${formatDate(blog.date)}</span>
                                                        </div>

                                                        <h3>${blog.title}</h3>

                                                        <p class="ctt-blog-excerpt">
                                                                ${blog.excerpt}
                                                        </p>

                                                        <a href="${blog.link}" class="ctt-small-link">
                                                                Read blog
                                                        </a>
                                                </div>
                                        </article>
                                `;
                        }

                        allBlogsContainer.innerHTML = blogs.map(createBlogCard).join("");
                </script>"""

# Filter-only styles, plus the layout rule for the removed sidebar column.
CSS_RULES = [
    ".ctt-blog-layout",
    ".ctt-blog-grid.all",
    ".ctt-filter-box",
    ".ctt-filter-grid",
    ".ctt-filter-box label",
    ".ctt-empty-message",
]

# The responsive rule lists the removed selectors, so it is replaced wholesale.
MEDIA_OLD = """                        @media screen and (max-width: 980px) {
                                .ctt-blog-grid,
                                .ctt-blog-grid.all,
                                .ctt-filter-grid {
                                        grid-template-columns: 1fr;
                                }
                        }"""

MEDIA_NEW = """                        @media screen and (max-width: 980px) {
                                .ctt-blog-grid {
                                        grid-template-columns: 1fr;
                                }
                        }"""


def strip_rule(text: str, selector: str) -> str:
    # These rules live inside the page's <style> block, so they are indented.
    pattern = re.compile(
        r"^[ \t]*" + re.escape(selector) + r"\s*\{[^}]*\}\s*\n", re.M
    )
    new, count = pattern.subn("", text)
    if count == 0:
        raise SystemExit("CSS selector not found: %s" % selector)
    return new


def apply():
    text = PAGE.read_text(encoding="utf-8", newline="")
    nl = "\r\n" if "\r\n" in text else "\n"

    def sub(name, old, new, count=1):
        old_l = detab(old).replace("\n", nl)
        new_l = detab(new).replace("\n", nl)
        if old_l not in text:
            raise SystemExit("%s not found verbatim; refusing to guess." % name)
        print("  patched  %s" % name)
        return text.replace(old_l, new_l, count)

    text = sub("layout: two columns -> one grid", LAYOUT_OLD, LAYOUT_NEW)

    # The blogs array runs from "const blogs = [" to the closing "];".
    pattern = re.compile(r"^" + T * 3 + r"const blogs = \[.*?^\s*\];\n", re.S | re.M)
    text, n = pattern.subn(BLOGS_NEW.replace("\n", nl), text, count=1)
    if n != 1:
        raise SystemExit("blogs array not found")
    print("  patched  blogs array -> 3 placeholders")

    pattern = re.compile(
        r"^" + T * 3 + r"const topBlogsContainer.*?^\s*setupFilterEvents\(\);\n",
        re.S | re.M,
    )
    text, n = pattern.subn(SCRIPT_TAIL_NEW.replace("\n", nl), text, count=1)
    if n != 1:
        raise SystemExit("script tail not found")
    print("  patched  script: filter wiring removed")

    # The responsive rule is edited before the filter rules are stripped: one of
    # those selectors also appears inside it, and stripping first would mangle it.
    text = sub("responsive rule", MEDIA_OLD, MEDIA_NEW)

    for selector in CSS_RULES:
        text = strip_rule(text, selector)
        print("  removed  css %s" % selector)

    PAGE.write_text(text, encoding="utf-8", newline="")
    print("rewrote %s" % PAGE.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(apply())

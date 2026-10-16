#!/usr/bin/env python3
"""Deterministic verification harness for the CTT Round 1 site improvements.

Everything machine-checkable is checked here with real captured output written
to output/evidence/. Nothing in this file edits the site: rendered-DOM and
console probes operate on a throwaway copy under /tmp.

Usage:
    python3 tests/verify_site.py            # run the full suite
    python3 tests/verify_site.py --port 8010
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "output" / "evidence"
SITE = ROOT  # the site is edited in place at the project root

CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser")
NODE = shutil.which("node")

REQUIRED_PATHS = [
    "index.html",
    "tutors.html",
    "blog.html",
    "contact.html",
    "header.html",
    "footer/footer.html",
    "assets/data/tutors.js",
    "assets/js/render-tutors.js",
    "assets/css/ctt-custom.css",
]

REMOVED_SLUGS = ["lize-blom", "jenna-germanus", "lieze-van-der-westhuizen"]

EXPECTED_FIELDS = [
    "name",
    "slug",
    "image",
    "qualifications",
    "grades",
    "subjects",
    "area",
    "province",
    "lessonType",
    "availability",
    "tags",
    "bio",
]

PROVINCES = ["Gauteng", "KwaZulu-Natal", "Western Cape"]

# ---- Round 2 expectations -------------------------------------------------
# The boss's Round 2 notes add four tutors, so the roster grows from 12 to 16.
EXPECTED_TUTOR_COUNT = 16

# Province each tutor must be listed under, taken straight from the Joburg,
# Durban and Cape Town lists in the Round 2 notes. A tutor the boss struck off
# a city list must not carry that city's province.
ROUND2_PROVINCE_PLACEMENT = {
    "chloe-smith": ["Gauteng"],
    "megan-meyer": ["Gauteng"],
    "sabreen-limbada": ["Gauteng"],
    "isabella-stubbs": ["Gauteng"],
    "alex-smith": ["Gauteng"],
    "kirsten-snyman": ["Gauteng"],
    "caleb-ross": ["KwaZulu-Natal"],
    "nicole-vermeulen": ["KwaZulu-Natal"],
    "swasthi-prahalad": ["KwaZulu-Natal"],
    "priyal-daya": ["Western Cape"],
}

ROUND2_ADDED_SLUGS = ["swasthi-prahalad", "isabella-stubbs", "caleb-ross", "priyal-daya"]

# The profile copy supplied in "CTT fixes.zip" (Notes.txt), for the four tutors
# the boss wrote out in full. Round 2 shortened several of these when writing
# them into the roster, which is the copy the owner reads on the site, so the
# expected text is pinned here verbatim and the trimmed variants are forbidden.
ROUND2_SUPPLIED_COPY = {
    "swasthi-prahalad": [
        "Experienced educator with five years of teaching experience across Cambridge, "
        "IEB and CAPS curricula. Holds a Bachelor of Accounting Science degree and is "
        "currently completing a Postgraduate Certificate in Education (PGCE).",
        "Grades 7 to 12 and university (Mathematics and Commerce up to Honours level)",
        "Accounting & Maths Specialist",
        "5 Years' Experience",
        "Swasthi believes that education is about more than just improving marks. "
        "It's about helping students genuinely understand their work and develop a "
        "lasting love for learning!",
    ],
    "isabella-stubbs": [
        "And if you love golden retrievers, you'll definitely have something in common!",
    ],
    "caleb-ross": [
        "Currently completing a Postgraduate Diploma in Accounting (PGDA), with "
        "experience supporting over 250 students.",
    ],
    "priyal-daya": [
        "Qualified educator with a Bachelor of Education and an Honours degree in "
        "Inclusive Education, passionate about making learning engaging and accessible.",
    ],
}

ROUND2_TRIMMED_COPY = [
    '"qualifications": "Bachelor of Accounting Science and currently completing',
    '"qualifications": "Currently completing a Postgraduate Diploma in Accounting (PGDA)",',
    '"qualifications": "Bachelor of Education and an Honours degree in Inclusive Education",',
]

# The owner asked for one grade statement per learner, not two. The subject line
# carries the range for Chloe ("All subjects, Grades 1 to 8"), so the homepage
# card must not print the grades field again underneath it.
HOMEPAGE_FEATURED = ["Chloe Smith", "Alex Smith", "Ethan Klebe"]

# The boss's notes called this tutor "Caleb chowtee" once; the owner confirmed
# that is the same person as Caleb Ross and that he is always to be called
# Caleb Ross. The other name must never reach a shipped file.
FORBIDDEN_TUTOR_ALIASES = ["chowtee"]

# Shipped deliverables only: the docs, tests and work/ scripts legitimately quote
# the notes, so they are deliberately excluded.
SHIPPED_SUFFIXES = {".html", ".js", ".css"}
SHIPPED_EXCLUDE_DIRS = {"work", "tests", "docs", "output", "inputs", ".supervisor", ".git", "images"}

ROUND2_NEW_PHOTOS = [
    "images/hero_study_crop.jpeg",
    "images/caleb_ross.jpg",
    "images/isabella_stubbs.jpg",
    "images/priyal_daya.jpg",
    "images/sabreen_limbada.jpg",
    "images/swasthi_prahalad.jpg",
]

results: list[tuple[str, str, str]] = []  # (status, criterion, detail)


def record(status: str, criterion: str, detail: str) -> None:
    results.append((status, criterion, detail))
    print(f"[{status}] {criterion}: {detail}")


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# Data + render layer, executed with the site's own modules under Node
# --------------------------------------------------------------------------

NODE_DATA_CHECK = r"""
global.window = {};
const path = require("path");
// node -e sets process.argv = [node, arg1, arg2, ...] with no script slot.
const dataPath = process.argv[1];
const renderPath = process.argv[2];
const siteRoot = process.argv[3];
require(dataPath);
require(renderPath);
const T = window.CTT_TUTORS;
const R = window.CTTRender;
const fs = require("fs");

const fields = %s;
const removed = %s;
const provinces = %s;

const out = {};
out.count = T.length;
out.slugs = T.map(function (t) { return t.slug; });
out.uniqueSlugs = new Set(out.slugs).size === out.slugs.length;
out.fieldsComplete = T.every(function (t) {
  return fields.every(function (f) { return Object.prototype.hasOwnProperty.call(t, f); });
});
out.provinceArrays = T.every(function (t) { return Array.isArray(t.province) && t.province.length > 0 || Array.isArray(t.province); });
out.hasEmptyProvince = T.filter(function (t) { return (t.province || []).length === 0; }).map(function (t) { return t.slug; });
out.availabilityRetained = T.every(function (t) { return typeof t.availability === "string" && t.availability.length > 0; });
out.removedAbsent = removed.every(function (s) { return !T.some(function (t) { return t.slug === s; }); });
out.imagesExist = T.filter(function (t) { return t.image; }).every(function (t) {
  return fs.existsSync(path.join(siteRoot, t.image));
});
out.missingImages = T.filter(function (t) { return t.image && !fs.existsSync(path.join(siteRoot, t.image)); })
  .map(function (t) { return t.image; });
out.lizeImageGone = !fs.existsSync(path.join(siteRoot, "images/lize_blom.jpg"));

// Pure filter function checks, including the adversarial cases.
out.provinceOptions = R.provinceOptions(T);
out.allCount = R.filterTutors(T, {}).length;
out.byProvince = {};
out.provinceOptions.forEach(function (p) {
  out.byProvince[p] = R.filterTutors(T, { province: p }).map(function (t) { return t.slug; });
});
out.online = R.filterTutors(T, { online: true }).map(function (t) { return t.slug; });
out.offlineOnly = R.filterTutors(T, { online: false }).length;
out.intersectionGautengOnline = R.filterTutors(T, { province: "Gauteng", online: true }).map(function (t) { return t.slug; });
out.noMatch = R.filterTutors(T, { province: "Mars" }).length;
out.provinceBySlug = {};
T.forEach(function (t) { out.provinceBySlug[t.slug] = (t.province || []).slice().sort(); });

// Independent expected-set derivation from the raw data (not the filter code).
out.expectedByProvince = {};
provinces.forEach(function (p) {
  out.expectedByProvince[p] = T.filter(function (t) { return (t.province || []).indexOf(p) !== -1; })
    .map(function (t) { return t.slug; });
});
out.expectedOnline = T.filter(function (t) { return t.online === true; }).map(function (t) { return t.slug; });

// Multi-province coverage: every tutor appears under every province it declares.
out.multiProvince = T.filter(function (t) { return (t.province || []).length > 1; })
  .map(function (t) { return { slug: t.slug, province: t.province }; });

// Anchor identity: rendered directory card carries id="<slug>".
out.anchorIdsOk = T.every(function (t) {
  return R.createDirectoryCard(t).indexOf('id="' + t.slug + '"') !== -1;
});

// Adversarial: a duplicate slug must be detectable (harness self-check).
out.duplicateSlugDetected = (function () {
  const fake = T.concat([T[0]]);
  const seen = {};
  let dup = false;
  fake.forEach(function (t) { if (seen[t.slug]) { dup = true; } seen[t.slug] = true; });
  return dup;
})();

// Adversarial: a record referencing a deleted image must fail image existence.
out.brokenImageDetected = !fs.existsSync(path.join(siteRoot, "images/definitely_missing.jpg"));

console.log(JSON.stringify(out));
"""


def node_data_check() -> dict:
    payload = NODE_DATA_CHECK % (
        json.dumps(EXPECTED_FIELDS),
        json.dumps(REMOVED_SLUGS),
        json.dumps(PROVINCES),
    )
    proc = run(
        [
            NODE,
            "-e",
            payload,
            str(SITE / "assets/data/tutors.js"),
            str(SITE / "assets/js/render-tutors.js"),
            str(SITE),
        ]
    )
    if proc.returncode != 0:
        record("FAIL", "INV-01", "node data check crashed: " + proc.stderr.strip()[:400])
        return {}
    return json.loads(proc.stdout.strip().splitlines()[-1])


# --------------------------------------------------------------------------
# HTTP probes against a locally served copy
# --------------------------------------------------------------------------

def http_status(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except Exception:
        return 0


def probe_paths(port: int) -> dict:
    statuses = {}
    for rel in REQUIRED_PATHS:
        statuses[rel] = http_status(f"http://127.0.0.1:{port}/{rel}")
    # The raw request names "footer.html"; the fragment the pages actually fetch
    # is footer/footer.html. Record the discrepancy explicitly.
    statuses["footer.html (named in request)"] = http_status(
        f"http://127.0.0.1:{port}/footer.html"
    )
    return statuses


def start_server(site_dir: Path, port: int):
    """Serve site_dir on 127.0.0.1:port; returns the Popen handle."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(site_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        if http_status(f"http://127.0.0.1:{port}/index.html") == 200:
            return proc
        time.sleep(0.2)
    return proc


# --------------------------------------------------------------------------
# Rendered-DOM probes via headless Chromium over the LOCAL SERVER (never file://)
# --------------------------------------------------------------------------

CONSOLE_COLLECTOR = """<script>
window.__cttErrors = [];
(function () {
  const push = function (kind) {
    return function () {
      try {
        const args = Array.prototype.slice.call(arguments).map(function (a) {
          return (a && a.message) ? a.message : String(a);
        });
        window.__cttErrors.push(kind + ": " + args.join(" "));
      } catch (e) { window.__cttErrors.push(kind + ": <unstringifiable>"); }
    };
  };
  const realError = console.error, realWarn = console.warn;
  console.error = function () { push("console.error")(...arguments); return realError.apply(console, arguments); };
  console.warn = function () { push("console.warn")(...arguments); return realWarn.apply(console, arguments); };
  window.addEventListener("error", function (e) {
    window.__cttErrors.push("window.onerror: " + (e.message || e.type));
  });
  window.addEventListener("unhandledrejection", function (e) {
    window.__cttErrors.push("unhandledrejection: " + String(e.reason));
  });
})();
</script>
"""


def build_probe_copy(tmp: Path) -> None:
    """Copy the site to a throwaway dir; never modify the real deliverables."""
    if tmp.exists():
        shutil.rmtree(tmp)
    ignore = shutil.ignore_patterns(".git", ".supervisor", "output", "work", "__pycache__")
    shutil.copytree(SITE, tmp, ignore=ignore)


def inject_head(page: Path, script: str) -> None:
    html = page.read_text(encoding="utf-8")
    if "<head>" not in html:
        raise SystemExit(f"no <head> in {page}")
    html = html.replace("<head>", "<head>\n" + script, 1)
    page.write_text(html, encoding="utf-8")


def dump_dom(url: str, extra_args=None, budget=5000) -> str:
    if CHROMIUM is None:
        return ""
    args = [
        CHROMIUM,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        f"--virtual-time-budget={budget}",
        "--dump-dom",
    ]
    if extra_args:
        args.extend(extra_args)
    args.append(url)
    proc = run(args, timeout=120)
    return proc.stdout


def probe_console(tmp: Path, port: int) -> dict:
    """Capture console errors on each page, including fragment fetches."""
    report = {}
    for page_name in ["index.html", "tutors.html", "blog.html", "contact.html"]:
        probe = tmp / f"__console_{page_name}"
        shutil.copyfile(tmp / page_name, probe)
        inject_head(probe, CONSOLE_COLLECTOR)
        dom = dump_dom(f"http://127.0.0.1:{port}/__console_{page_name}")
        match = re.search(r"__cttErrors\s*=\s*\[(.*?)\]", dom, re.S)
        errors: list[str] = []
        if match:
            body = match.group(1).strip()
            if body:
                errors = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
        report[page_name] = errors
    return report


FILTER_PROBE = """<script>
window.addEventListener("load", function () {
  var R = window.CTTRender, T = window.CTT_TUTORS;
  var select = document.getElementById("provinceFilter");
  var online = document.getElementById("onlineFilter");
  var out = { options: [], perOption: {}, emptyShown: null, emptyAnchors: null, anchorsPerOption: {} };

  function cardIds() {
    return Array.prototype.slice.call(
      document.querySelectorAll("#tutorDirectory .ctt-tutor-detail")
    ).map(function (el) { return el.id; });
  }

  Array.prototype.forEach.call(select.options, function (o) { out.options.push(o.value); });

  Array.prototype.forEach.call(select.options, function (o) {
    if (o.value === "all") { return; }
    select.value = o.value;
    select.dispatchEvent(new Event("change"));
    out.perOption[o.value] = cardIds();
  });

  // Online-only.
  select.value = "all";
  select.dispatchEvent(new Event("change"));
  online.checked = true;
  online.dispatchEvent(new Event("change"));
  out.onlineOnly = cardIds();

  // Intersection: Gauteng + online.
  select.value = "Gauteng";
  select.dispatchEvent(new Event("change"));
  out.gautengOnline = cardIds();

  // Empty state: force a province with no tutors through the real filter path.
  out.emptyShown = !!document.getElementById("tutorEmptyState");
  R.renderDirectory("tutorDirectory", { province: "Mars" });
  out.emptyShown = !!document.getElementById("tutorEmptyState");
  out.emptyText = (document.getElementById("tutorEmptyState") || {}).textContent || "";

  // Restore default view and confirm anchors resolve for every tutor.
  online.checked = false;
  select.value = "all";
  select.dispatchEvent(new Event("change"));
  out.anchorsPerOption["all"] = cardIds();

  // The two call-to-action links must still be present after filtering.
  out.actionsPresent = Array.prototype.slice.call(
    document.querySelectorAll(".ctt-directory-actions a")
  ).map(function (a) { return a.textContent.trim(); });

  // Accessibility: real labelled controls, keyboard focusable, visible, enabled.
  function described(el) {
    if (!el) { return null; }
    var labels = el.labels ? Array.prototype.map.call(el.labels, function (l) { return l.textContent.trim(); }) : [];
    var aria = el.getAttribute("aria-label");
    // A button's accessible name can come from its own text content.
    var text = (el.tagName === "BUTTON" ? el.textContent.trim() : "");
    return { tag: el.tagName, id: el.id, labels: labels, ariaLabel: aria, text: text, disabled: !!(el.disabled), hidden: el.offsetParent === null };
  }
  out.controls = {
    province: described(select),
    online: described(online),
    clear: described(document.getElementById("clearTutorFilters"))
  };
  // Keyboard focus must land on each control.
  function focusable(el) {
    if (!el) { return false; }
    el.focus();
    return document.activeElement === el;
  }
  out.focusable = {
    province: focusable(select),
    online: focusable(online),
    clear: focusable(document.getElementById("clearTutorFilters"))
  };

  var blob = document.createElement("script");
  blob.type = "application/json";
  blob.id = "cttProbeResult";
  blob.textContent = JSON.stringify(out);
  document.body.appendChild(blob);
});
</script>
"""


def probe_filter(tmp: Path, port: int) -> dict:
    probe = tmp / "__filter_probe.html"
    shutil.copyfile(tmp / "tutors.html", probe)
    inject_head(probe, FILTER_PROBE)
    dom = dump_dom(f"http://127.0.0.1:{port}/__filter_probe.html", budget=6000)
    match = re.search(
        r'<script type="application/json" id="cttProbeResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {}
    import html as html_mod

    return json.loads(html_mod.unescape(match.group(1)))


ORDER_PROBE = """<script>
window.addEventListener("load", function () {
  var wrapper = document.getElementById("wrapper");
  var headings = [];
  wrapper.querySelectorAll("h1, h2").forEach(function (h) {
    headings.push(h.textContent.replace(/\\s+/g, " ").trim());
  });
  var featured = document.querySelectorAll("#featuredTutors .ctt-tutor-card");

  // Full section order across #wrapper (hero, learning, tutors, start, footer).
  function label(el) {
    if (el.id === "home") { return "hero"; }
    if (el.classList.contains("ctt-learning-box") || el.querySelector(".ctt-learning-box")) { return "learning"; }
    if (el.querySelector("#featuredTutors")) { return "tutors"; }
    if (el.classList.contains("ctt-start-section")) { return "start"; }
    if (el.id === "site-footer") { return "footer"; }
    return null;
  }
  var sections = [];
  wrapper.querySelectorAll(":scope > section, :scope > #site-footer, :scope > footer").forEach(function (el) {
    var l = label(el);
    if (l) { sections.push(l); }
  });

  var h1s = document.querySelectorAll("h1");

  var out = {
    headings: headings,
    h1Count: h1s.length,
    h1Texts: Array.prototype.map.call(h1s, function (h) { return h.textContent.replace(/\\s+/g, " ").trim(); }),
    // A visually hidden h1 must stay out of the layout: it is 1px, clipped and
    // absolutely positioned, so its box is far smaller than a real headline.
    h1Boxes: Array.prototype.map.call(h1s, function (h) {
      var r = h.getBoundingClientRect();
      return {w: Math.round(r.width), h: Math.round(r.height), visible: r.width > 4 && r.height > 4};
    }),
    sectionOrder: sections,
    featuredCount: featured.length,
    featuredNames: Array.prototype.map.call(featured, function (c) {
      return c.querySelector("h3") ? c.querySelector("h3").textContent : "";
    }),
    availabilityString: document.body.textContent.indexOf("Availability") !== -1
  };
  var blob = document.createElement("script");
  blob.type = "application/json";
  blob.id = "cttOrderResult";
  blob.textContent = JSON.stringify(out);
  document.body.appendChild(blob);
});
</script>
"""


def probe_order(tmp: Path, port: int) -> dict:
    probe = tmp / "__order_probe.html"
    shutil.copyfile(tmp / "index.html", probe)
    inject_head(probe, ORDER_PROBE)
    dom = dump_dom(f"http://127.0.0.1:{port}/__order_probe.html", budget=6000)
    match = re.search(
        r'<script type="application/json" id="cttOrderResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {}
    import html as html_mod

    return json.loads(html_mod.unescape(match.group(1)))


def availability_in_dom(tmp: Path, port: int) -> dict:
    out = {}
    for page in ["tutors.html", "index.html"]:
        dom = dump_dom(f"http://127.0.0.1:{port}/{page}", budget=6000)
        out[page] = {
            "availability_present": "Availability" in dom,
            "empty_strong_present": bool(re.search(r"<strong>\s*</strong>", dom)),
        }
    return out


BLOG_PROBE = """<script>
window.addEventListener("load", function () {
  // Count only the cards the page actually rendered into #allBlogs; the card
  // template lives inside a <script> block and must not be counted.
  var cards = document.querySelectorAll("#allBlogs > article.ctt-blog-card");
  var filters = document.querySelectorAll(
    "#allBlogs select, .ctt-filter-box, .ctt-blog-layout select, [id*='ilter']"
  );
  var out = {
    cardCount: cards.length,
    titles: Array.prototype.map.call(cards, function (c) {
      var h = c.querySelector("h3");
      return h ? h.textContent.replace(/\\s+/g, " ").trim() : "";
    }),
    filterControls: Array.prototype.map.call(filters, function (el) {
      return el.tagName + (el.id ? "#" + el.id : "");
    }),
    imagePlaceholders: document.querySelectorAll("#allBlogs .ctt-blog-image").length
      - document.querySelectorAll("#allBlogs .ctt-blog-image img").length
  };
  var blob = document.createElement("script");
  blob.type = "application/json";
  blob.id = "cttBlogResult";
  blob.textContent = JSON.stringify(out);
  document.body.appendChild(blob);
});
</script>
"""


def probe_blog(tmp: Path, port: int) -> dict:
    """Rendered blog page: the filter panel is gone and exactly 3 cards render."""
    probe = tmp / "__blog_probe.html"
    shutil.copyfile(tmp / "blog.html", probe)
    inject_head(probe, BLOG_PROBE)
    dom = dump_dom(f"http://127.0.0.1:{port}/__blog_probe.html", budget=6000)
    match = re.search(
        r'<script type="application/json" id="cttBlogResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {"error": "probe result not found", "domLength": len(dom)}
    import html as html_mod

    return json.loads(html_mod.unescape(match.group(1)))


def probe_contact_dropdown(tmp: Path, port: int) -> dict:
    """Rendered preferences dropdown on the served contact page.

    The options are built by the page's own script from tutors.js, so this reads
    the live DOM rather than the source, the same way the owner sees it.
    """
    dom = dump_dom(f"http://127.0.0.1:{port}/contact.html", budget=6000)
    block = re.search(
        r"<select[^>]*id=\"preferredTutor\".*?</select>", dom, re.S
    )
    if not block:
        return {}
    options = re.findall(r"<option[^>]*value=\"([^\"]*)\"", block.group(0))
    return {
        "isSelect": True,
        "optionCount": len(options),
        "options": [o for o in options if o],
        "hasPlaceholder": "" in options,
    }


# --------------------------------------------------------------------------
# Wording checks (present / absent)
# --------------------------------------------------------------------------

def wording_checks() -> dict:
    index = (SITE / "index.html").read_text(encoding="utf-8")
    tutors = (SITE / "tutors.html").read_text(encoding="utf-8")
    contact = (SITE / "contact.html").read_text(encoding="utf-8")
    blog = (SITE / "blog.html").read_text(encoding="utf-8")
    roster = (SITE / "assets/data/tutors.js").read_text(encoding="utf-8")

    new_tutors_desc = (
        "Meet some of the people behind CTT. Our tutors bring different strengths, "
        "qualifications and teaching styles, so we can find the right fit for every learner."
    )

    def norm(text):
        return re.sub(r"\s+", " ", text)

    hero_start = index[index.index('id="home"'):]
    hero_section = hero_start[: hero_start.index("</section>") + len("</section>")]

    return {
        # Round 2 hero: the opening line IS the quote, nothing above it.
        "hero_quote_leads": "If a child can't learn the way" in hero_section
        and "Ignacio Estrada" in hero_section,
        "hero_quote_before_actions": hero_section.index("If a child can't learn the way")
        < hero_section.index("Meet the Tutors"),
        "hero_old_headline_gone": "Every child can thrive" not in index,
        "hero_old_eyebrow_gone": "Personal, one-to-one tutoring" not in index,
        "hero_old_body_gone": "Warm, personal tutoring" not in index,
        "hero_points_gone": "ctt-hero-points" not in index,
        "hero_crop_image": "images/hero_study_crop.jpeg" in index,
        "hero_old_image_gone": "images/index_open_image.jpeg" not in index,
        # Round 2 grades wording.
        "grades_wording_exact": "All subjects, Grades 1 to 8" in roster,
        "grades_old_gone": "Grade 7 and 8 support" not in roster,
        # Round 2 contact dropdown, driven by the roster.
        "preferred_tutor_is_select": bool(
            re.search(r"<select[^>]*id=\"preferredTutor\"", contact)
        ),
        "preferred_tutor_from_roster": "populatePreferredTutors" in contact
        and "window.CTT_TUTORS" in contact,
        # Round 2 blog: filter panel gone in source, three placeholders kept.
        "blog_filter_gone": "ctt-filter-box" not in blog and "ctt-blog-layout" not in blog,
        "blog_three_placeholders": blog.count('title: "') == 3,
        # Carried over from Round 1.
        "hero_old_sentence_gone": "Tutoring that" not in index,
        "hero_old_oh_moment_gone": "Oh, I finally get it" not in index,
        # Round 3: the owner removed the "How CTT started" section, so the
        # Round 1 wording assertions for it no longer apply.
        "how_started_gone": "How CTT started" not in index
        and "ctt-chloe-section" not in index,
        "tutors_desc_exact": new_tutors_desc in norm(tutors),
        "tutors_old_desc_gone": "personalities and areas of expertise" not in tutors,
        "home_intro_matches": new_tutors_desc in norm(index),
        "home_intro_old_gone": "Meet a few members of our growing tutoring team" not in index,
        "subject_label_exact": '>Subject/s Needed<' in contact,
        "subject_old_gone": ">Subject Needed<" not in contact,
        "british_personalised": "personalised" in index.lower(),
    }


# --------------------------------------------------------------------------
# Git / publishing-safety checks
# --------------------------------------------------------------------------

UPSTREAM = "https://github.com/MatthewMBowyer/Chloes-Traveling-tutors"
BASELINE_HEAD = "37704102d40b0f1cd2664e07bf0db0ef9b3322eb"
# The owner overrode the original read-only GitHub rule and asked for the work to
# be published, so the check is now "is the deliverable live?" rather than
# "was main left alone?".
LIVE_SITE = "https://matthewmbowyer.github.io/Chloes-Traveling-tutors"


def live_publish_checks() -> dict:
    """Fetch the deployed site and confirm it serves the current deliverable."""
    out: dict = {"live_site": LIVE_SITE}
    try:
        for name, path in (("index", "index.html"), ("tutors", "tutors.html")):
            req = urllib.request.Request(
                f"{LIVE_SITE}/{path}", headers={"User-Agent": "ctt-verify"}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                out[f"{name}_status"] = resp.status
                out[f"{name}_html"] = resp.read().decode("utf-8", "replace")
    except Exception as exc:  # network/Pages hiccup must not crash the run
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out

    index_html = out.pop("index_html", "")
    tutors_html = out.pop("tutors_html", "")

    out["how_started_gone_live"] = "How CTT started" not in index_html
    out["filter_live"] = 'id="provinceFilter"' in tutors_html and "ctt-filter-box" in tutors_html
    out["tutor_directory_live"] = 'id="tutorDirectory"' in tutors_html
    out["published"] = bool(out["how_started_gone_live"] and out["filter_live"])
    return out


def git_checks() -> dict:
    branch = run(["git", "-C", str(ROOT), "branch", "--show-current"]).stdout.strip()
    remotes = run(["git", "-C", str(ROOT), "remote", "-v"]).stdout.strip()
    out = {
        "branch": branch,
        "remote_list": remotes,
        "branch_not_main": branch not in ("main", "master", ""),
        "no_remote_configured": remotes == "",
    }
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    proc = run(["git", "ls-remote", UPSTREAM, "main"], env=env)
    out["ls_remote_stdout"] = proc.stdout.strip()
    out["ls_remote_rc"] = proc.returncode
    match = re.search(r"^([0-9a-f]{40})\s", proc.stdout.strip())
    out["upstream_head"] = match.group(1) if match else None
    out["upstream_unchanged"] = out["upstream_head"] == BASELINE_HEAD
    out["baseline_head"] = BASELINE_HEAD
    return out


def input_hashes() -> dict:
    manifest = json.loads((ROOT / ".supervisor" / "INPUT_MANIFEST.json").read_text())
    out = {}
    for item in manifest["files"]:
        path = ROOT / "inputs" / item["relative_path"]
        actual = sha256(path) if path.exists() else None
        out[item["relative_path"]] = {
            "expected": item["sha256"],
            "actual": actual,
            "match": actual == item["sha256"],
        }
    return out


# --------------------------------------------------------------------------
# Screenshots
# --------------------------------------------------------------------------

# The completed assessment result sits near the bottom of the contact page
# (measured bottom ~4371px at 1400px wide), so the evidence frame has to reach
# past it or the image shows the questions but not the result it claims to prove.
CONTACT_CAPTURE_HEIGHT = 5200

ASSESSMENT_PROBE = """<script>
window.addEventListener("load", function () {
  var toggle = document.getElementById("assessmentToggle");
  var questions = document.getElementById("assessmentQuestions");
  var result = document.getElementById("assessmentResult");

  // Read the page's own declared items via the rendered fieldsets.
  function fieldsetCount() {
    return document.querySelectorAll("#assessmentQuestions fieldset").length;
  }
  function answerAll(exceptIndex) {
    document.querySelectorAll("#assessmentQuestions fieldset").forEach(function (fs, i) {
      if (exceptIndex !== undefined && i === exceptIndex) { return; }
      var inputs = fs.querySelectorAll('input[type="radio"]');
      inputs[2].checked = true;
      inputs[2].dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  var out = {};

  // First-person wording of every declared item, read from the page source list.
  out.items = (typeof assessmentItems !== "undefined" ? assessmentItems : []).map(function (i) {
    return { text: i.text, style: i.style };
  });
  out.allFirstPerson = out.items.every(function (i) { return /^I\\b/.test(i.text); });
  out.styleCounts = out.items.reduce(function (acc, i) {
    acc[i.style] = (acc[i.style] || 0) + 1; return acc;
  }, {});
  out.scaleLabels = (typeof scoreOptions !== "undefined" ? scoreOptions : []).map(function (o) { return o.label; });
  out.scaleValues = (typeof scoreOptions !== "undefined" ? scoreOptions : []).map(function (o) { return o.value; });

  // Hidden until the toggle is on.
  out.initialQuestionsHidden = questions.hidden;
  out.initialResultHidden = result.hidden;

  toggle.checked = true;
  toggle.dispatchEvent(new Event("change"));
  out.afterToggleQuestionsHidden = questions.hidden;
  out.afterToggleResultHidden = result.hidden;
  out.fieldsetCount = fieldsetCount();

  // Adversarial: answer 11 of 12 -> no result.
  answerAll(11);
  out.afterElevenResultHidden = result.hidden;
  out.afterElevenHtml = result.innerHTML.trim();

  // Answer all 12 -> result shown with primary and secondary preference.
  answerAll(undefined);
  out.afterAllResultHidden = result.hidden;
  out.afterAllHtml = result.innerHTML.replace(/\\s+/g, " ").trim();

  var answered = 0;
  document.querySelectorAll('#assessmentQuestions input[type="radio"]:checked').forEach(function () { answered++; });
  out.answeredCount = answered;

  // Change one answer and confirm the scores change.
  var before = result.innerHTML;
  var fs6 = document.querySelectorAll('#assessmentQuestions fieldset')[5];
  var firstRadio = fs6.querySelectorAll('input[type="radio"]')[0];
  firstRadio.checked = true;
  firstRadio.dispatchEvent(new Event("change", { bubbles: true }));
  out.scoresChanged = result.innerHTML !== before;

  // Toggle off hides questions and result.
  toggle.checked = false;
  toggle.dispatchEvent(new Event("change"));
  out.afterToggleOffQuestionsHidden = questions.hidden;
  out.afterToggleOffResultHidden = result.hidden;

  var blob = document.createElement("script");
  blob.type = "application/json";
  blob.id = "cttAssessmentResult";
  blob.textContent = JSON.stringify(out);
  document.body.appendChild(blob);
});
</script>
"""


def probe_assessment(tmp: Path, port: int) -> dict:
    probe = tmp / "__assessment_probe.html"
    shutil.copyfile(tmp / "contact.html", probe)
    inject_head(probe, ASSESSMENT_PROBE)
    dom = dump_dom(f"http://127.0.0.1:{port}/__assessment_probe.html", budget=6000)
    match = re.search(
        r'<script type="application/json" id="cttAssessmentResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {}
    import html as html_mod

    return json.loads(html_mod.unescape(match.group(1)))


ASSET_CHECK_TEMPLATE = """<script>
window.addEventListener("load", function () {
  var srcs = [];
  document.querySelectorAll("img[src], script[src], link[href]").forEach(function (el) {
    var v = el.getAttribute("src") || el.getAttribute("href");
    if (v && v.indexOf("http") !== 0 && v.indexOf("//") !== 0 && v.charAt(0) !== "#") {
      srcs.push(v.split("?")[0].split("#")[0]);
    }
  });
  (window.CTT_TUTORS || []).forEach(function (t) {
    if (t.image) { srcs.push(t.image); }
  });
  var blob = document.createElement("script");
  blob.type = "application/json";
  blob.id = "cttAssets";
  blob.textContent = JSON.stringify(Array.from(new Set(srcs)));
  document.body.appendChild(blob);
});
</script>
"""


def probe_assets(tmp: Path, port: int) -> dict:
    """Collect every asset referenced by the served pages and probe each for 200."""
    report = {}
    for page in ["index.html", "tutors.html", "blog.html", "contact.html"]:
        probe = tmp / f"__assets_{page}"
        shutil.copyfile(tmp / page, probe)
        inject_head(probe, ASSET_CHECK_TEMPLATE)
        dom = dump_dom(f"http://127.0.0.1:{port}/__assets_{page}", budget=4000)
        match = re.search(r'<script type="application/json" id="cttAssets">(.*?)</script>', dom, re.S)
        if not match:
            report[page] = {"error": "no asset list captured"}
            continue
        import html as html_mod

        assets = json.loads(html_mod.unescape(match.group(1)))
        # Fragment fetches the pages perform at runtime.
        if "index.html" in page or True:
            assets = sorted(set(assets) | {"header.html", "footer/footer.html"})
        statuses = {a: http_status(f"http://127.0.0.1:{port}/{a}") for a in assets}
        bad = {a: s for a, s in statuses.items() if s not in (200, 304)}
        report[page] = {"checked": len(statuses), "bad": bad}
    return report


FRAGMENT_PROBE = """<script>
window.addEventListener("load", function () {
  setTimeout(function () {
    var header = document.getElementById("site-header");
    var footer = document.getElementById("site-footer");
    var blob = document.createElement("script");
    blob.type = "application/json";
    blob.id = "cttFragmentResult";
    blob.textContent = JSON.stringify({
      headerNonEmpty: !!header && header.innerHTML.trim().length > 0,
      footerNonEmpty: !!footer && footer.innerHTML.trim().length > 0,
      headerHasNav: !!header && !!header.querySelector(".ctt-navigation"),
      footerHasGrid: !!footer && !!footer.querySelector(".ctt-footer-grid"),
      navLinks: header ? Array.prototype.map.call(
        header.querySelectorAll(".ctt-navigation a"),
        function (a) { return { href: a.getAttribute("href"), text: a.textContent.trim() }; }
      ) : [],
      robotsMeta: (function () {
        var m = document.querySelector('meta[name="robots"]');
        return m ? m.getAttribute("content") : null;
      })(),
      protocol: window.location.protocol
    });
    document.body.appendChild(blob);
  }, 800);
});
</script>
"""


def blog_hidden_checks(fragments: dict) -> dict:
    """Round 3: the blog page is unlisted from the navigation and not indexed.

    The nav comes from the header.html fragment the browser fetches at runtime,
    so this reads the rendered nav rather than the page source.
    """
    out: dict = {}
    nav_by_page = {
        page: [link.get("href") for link in (data.get("navLinks") or [])]
        for page, data in fragments.items()
    }
    out["nav_by_page"] = nav_by_page
    out["nav_pages_without_blog"] = [
        page for page, hrefs in nav_by_page.items() if "blog.html" not in hrefs
    ]
    out["nav_has_no_blog"] = all("blog.html" not in hrefs for hrefs in nav_by_page.values())
    out["nav_labels"] = sorted(
        {
            link.get("text")
            for data in fragments.values()
            for link in (data.get("navLinks") or [])
        }
    )
    robots = {
        page: data.get("robotsMeta")
        for page, data in fragments.items()
        if isinstance(data, dict)
    }
    out["robots_by_page"] = robots
    out["blog_not_indexed"] = "noindex" in (robots.get("blog.html") or "")
    # Still reachable by direct URL: unlisted, not deleted. R2-03 proves it renders.
    out["blog_page_still_served"] = (SITE / "blog.html").is_file()
    out["hidden"] = bool(out["nav_has_no_blog"] and out["blog_not_indexed"])
    return out


def probe_fragments(tmp: Path, port: int) -> dict:
    """Confirm header/footer fragments load over HTTP (not file://)."""
    out = {}
    for page in ["index.html", "tutors.html", "blog.html", "contact.html"]:
        probe = tmp / f"__frag_{page}"
        shutil.copyfile(tmp / page, probe)
        inject_head(probe, FRAGMENT_PROBE)
        dom = dump_dom(f"http://127.0.0.1:{port}/__frag_{page}", budget=4000)
        match = re.search(r'<script type="application/json" id="cttFragmentResult">(.*?)</script>', dom, re.S)
        if not match:
            out[page] = {"error": "no fragment result"}
            continue
        import html as html_mod

        out[page] = json.loads(html_mod.unescape(match.group(1)))
    return out


def png_stats(path: Path, sample_step: int = 4) -> dict | None:
    """Decode an 8-bit non-interlaced PNG and report its size and colour spread.

    Reading the produced pixels (not just the file size) is what proves the page
    actually rendered: a blank or single-colour capture has no colour spread.
    """
    import struct
    import zlib

    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    width = height = bit_depth = colour_type = interlace = None
    idat = bytearray()
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, bit_depth, colour_type, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", body[:13]
            )
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length

    if bit_depth != 8 or colour_type not in (2, 6) or interlace != 0:
        return {"width": width, "height": height, "decodable": False}

    bpp = 3 if colour_type == 2 else 4
    stride = width * bpp
    raw = zlib.decompress(bytes(idat))
    if len(raw) < (stride + 1) * height:
        return {"width": width, "height": height, "decodable": False}

    colours = set()
    prev = bytearray(stride)
    offset = 0
    for y in range(height):
        ftype = raw[offset]
        line = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += stride + 1
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            x = line[i]
            if ftype == 1:
                x += a
            elif ftype == 2:
                x += b
            elif ftype == 3:
                x += (a + b) // 2
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                x += a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = x & 0xFF
        if y % sample_step == 0:
            for x0 in range(0, width, sample_step):
                i = x0 * bpp
                colours.add((line[i], line[i + 1], line[i + 2]))
        prev = line

    return {
        "width": width,
        "height": height,
        "decodable": True,
        "distinct_colours": len(colours),
    }


def screenshot(url: str, out_path: Path, width=1400, height=2600, extra_style: str = "") -> dict:
    """Capture a screenshot; extra_style is injected on a per-page basis."""
    out = {
        "captured": False,
        "width": width,
        "height": height,
        "decodable": False,
        "distinct_colours": 0,
        "ok": False,
    }
    if CHROMIUM is None:
        return out
    target = url
    tmp_files: list[Path] = []
    if extra_style:
        # The page must be fetched then rewritten with the override, so fetch the
        # file locally via urllib and write a sibling probe file served over HTTP.
        base = url.rsplit("/", 1)
        page = base[1]
        import urllib.request as _rq

        html = _rq.urlopen(url, timeout=15).read().decode("utf-8")
        html = html.replace("</head>", f"<style>{extra_style}</style></head>", 1)
        probe = Path(tempfile.gettempdir()) / "ctt_verify_probe" / f"__shot_{page}"
        probe.write_text(html, encoding="utf-8")
        tmp_files.append(probe)
        target = base[0] + "/" + probe.name
    run(
        [
            CHROMIUM,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--virtual-time-budget=6000",
            f"--window-size={width},{height}",
            f"--screenshot={out_path}",
            target,
        ],
        timeout=120,
    )
    for f in tmp_files:
        f.unlink(missing_ok=True)

    out["captured"] = out_path.exists() and out_path.stat().st_size > 0
    if out["captured"]:
        stats = png_stats(out_path)
        if stats:
            out.update(stats)
    # A real render is the requested viewport AND hundreds of distinct colours;
    # a blank/greyscale/placeholder capture fails this.
    out["ok"] = (
        out["captured"]
        and out.get("decodable") is True
        and out.get("width") == width
        and out.get("height") == height
        and out.get("distinct_colours", 0) >= 200
    )
    return out


CONTACT_RESULT_PROBE = """<script>
window.addEventListener("load", function () {
  var toggle = document.getElementById("assessmentToggle");
  toggle.checked = true;
  toggle.dispatchEvent(new Event("change"));
  document.querySelectorAll("#assessmentQuestions fieldset").forEach(function (fs, i) {
    var inputs = fs.querySelectorAll('input[type="radio"]');
    inputs[(i * 2 + 2) % 4].checked = true;
    inputs[(i * 2 + 2) % 4].dispatchEvent(new Event("change", { bubbles: true }));
  });

  setTimeout(function () {
    var result = document.getElementById("assessmentResult");
    var rect = result ? result.getBoundingClientRect() : null;
    var out = {
      hidden: result ? result.hidden : null,
      text: result ? result.textContent.replace(/\\s+/g, " ").trim() : "",
      bottomPx: rect ? Math.round(rect.bottom + window.scrollY) : null,
      pageHeight: document.documentElement.scrollHeight
    };
    var blob = document.createElement("script");
    blob.type = "application/json";
    blob.id = "cttContactResult";
    blob.textContent = JSON.stringify(out);
    document.body.appendChild(blob);
  }, 1200);
});
</script>
"""


def measure_result_bottom(tmp: Path, port: int) -> dict:
    """Where the completed assessment result ends, in page pixels."""
    probe = tmp / "__shot_contact_measure.html"
    shutil.copyfile(tmp / "contact.html", probe)
    inject_head(probe, CONTACT_RESULT_PROBE)
    # Must use the same viewport as the capture, or the layout differs (the
    # default headless window is 800x600) and the comparison is meaningless.
    dom = dump_dom(
        f"http://127.0.0.1:{port}/__shot_contact_measure.html",
        extra_args=[f"--window-size=1400,{CONTACT_CAPTURE_HEIGHT}"],
        budget=8000,
    )
    match = re.search(
        r'<script type="application/json" id="cttContactResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {}
    import html as html_mod

    return json.loads(html_mod.unescape(match.group(1)))


def capture_screenshots(tmp: Path, port: int) -> dict:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    shots = {}

    # 1. Homepage hero at a real desktop viewport (the hero banner is fullscreen,
    #    so a tall window would stretch it and push the copy out of frame).
    shots["01_homepage_hero.png"] = screenshot(
        f"http://127.0.0.1:{port}/index.html", EVIDENCE / "01_homepage_hero.png", 1400, 1000
    )
    # 2. Full homepage showing the section order. The fullscreen banner height is
    #    relaxed ONLY in this throwaway capture file so every section is in frame,
    #    and the scrollex reveal animations are forced visible so off-screen
    #    sections are not captured as blank space; the delivered index.html is
    #    untouched.
    shots["01_homepage_full.png"] = screenshot(
        f"http://127.0.0.1:{port}/index.html",
        EVIDENCE / "01_homepage_full.png",
        1400,
        5200,
        extra_style=(
            # The capture window is portrait-shaped (1400x4200). That flips the
            # template's `orientation: portrait` rules: the banner stacks, the
            # content and image each take 50vh, and the hero alone fills the
            # frame, so every other section falls outside the capture. Restore
            # the landscape hero and pin a sane hero height in this throwaway
            # capture file only; the delivered index.html is untouched.
            ".ctt-hero{flex-direction:row !important;text-align:left !important;"
            "height:28rem !important;min-height:0 !important;align-items:stretch !important;}"
            ".ctt-hero .content{flex-direction:column !important;"
            "justify-content:center !important;min-height:0 !important;"
            "height:auto !important;text-align:left !important;}"
            ".ctt-hero .image{height:auto !important;width:50% !important;}"
            ".ctt-hero .image img{height:100% !important;object-fit:cover !important;}"
            "#wrapper section,#wrapper .image,#wrapper .content,#wrapper img,"
            "#wrapper .spotlight,#wrapper .ctt-tutor-card{opacity:1 !important;"
            "transform:none !important;visibility:visible !important;}"
        ),
    )

    # Tutors page with the filter applied (Gauteng + online).
    filter_page = tmp / "__shot_tutors.html"
    shutil.copyfile(tmp / "tutors.html", filter_page)
    inject_head(
        filter_page,
        """<script>
window.addEventListener("load", function () {
  var select = document.getElementById("provinceFilter");
  select.value = "Gauteng";
  select.dispatchEvent(new Event("change"));
  document.getElementById("onlineFilter").checked = true;
  document.getElementById("onlineFilter").dispatchEvent(new Event("change"));
});
</script>""",
    )
    shots["02_tutors_filter.png"] = screenshot(
        f"http://127.0.0.1:{port}/__shot_tutors.html", EVIDENCE / "02_tutors_filter.png", 1400, 2600
    )

    # Contact page with the assessment completed and a result shown.
    contact_page = tmp / "__shot_contact.html"
    shutil.copyfile(tmp / "contact.html", contact_page)
    inject_head(
        contact_page,
        """<script>
window.addEventListener("load", function () {
  var toggle = document.getElementById("assessmentToggle");
  toggle.checked = true;
  toggle.dispatchEvent(new Event("change"));
  document.querySelectorAll("#assessmentQuestions fieldset").forEach(function (fs, i) {
    var inputs = fs.querySelectorAll('input[type="radio"]');
    inputs[(i * 2 + 2) % 4].checked = true;
    inputs[(i * 2 + 2) % 4].dispatchEvent(new Event("change", { bubbles: true }));
  });
  var q = document.getElementById("assessmentQuestions");
  if (q) { q.scrollIntoView(); }
});
</script>""",
    )
    # The completed assessment and its result sit near the bottom of the page
    # (measured result top ~4147px at this width), so the frame has to reach past
    # that or the evidence image shows the questions but not the result it claims
    # to prove.
    shots["03_contact_assessment.png"] = screenshot(
        f"http://127.0.0.1:{port}/__shot_contact.html",
        EVIDENCE / "03_contact_assessment.png",
        1400,
        CONTACT_CAPTURE_HEIGHT,
    )
    return shots


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Round 3 SEO and mobile header
# --------------------------------------------------------------------------

SEO_BASE = "https://matthewmbowyer.github.io/Chloes-Traveling-tutors"
SEO_PAGES = ["index.html", "tutors.html", "contact.html"]
SEO_URL = {
    "index.html": SEO_BASE + "/",
    "tutors.html": SEO_BASE + "/tutors.html",
    "contact.html": SEO_BASE + "/contact.html",
}
TITLE_MAX = 60
DESCRIPTION_MAX = 160
REQUIRED_SCHEMA_TYPES = {
    "index.html": {"EducationalOrganization", "WebSite", "FAQPage"},
    "tutors.html": {"EducationalOrganization", "ItemList", "BreadcrumbList"},
    "contact.html": {"EducationalOrganization", "BreadcrumbList", "ContactPage"},
}
ONLINE_AREA_HINT = "online"


def html_unescape(value: str) -> str:
    """Decode entities in a fragment scraped out of the page source."""
    return html.unescape(value)


def page_source(page: str) -> str:
    return (SITE / page).read_text(encoding="utf-8", errors="ignore")


def roster() -> list[dict]:
    """The tutor records the site actually renders, parsed straight from the data file."""
    raw = (SITE / "assets/data/tutors.js").read_text(encoding="utf-8")
    return json.loads(raw[raw.index("[") : raw.rindex("]") + 1])


def seo_head_checks() -> dict:
    """Round 3 (R3-02): each public page carries its own indexable head data."""
    out: dict = {"pages": {}}
    for page in SEO_PAGES:
        text = page_source(page)
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        desc = re.search(r'<meta name="description" content="([^"]*)"', text)
        canonical = re.search(r'<link rel="canonical" href="([^"]*)"', text)
        robots = re.search(r'<meta name="robots" content="([^"]*)"', text)
        og = dict(re.findall(r'<meta property="(og:[^"]+)" content="([^"]*)"', text))
        twitter = dict(re.findall(r'<meta name="(twitter:[^"]+)" content="([^"]*)"', text))
        out["pages"][page] = {
            "title": title.group(1).strip() if title else None,
            "description": desc.group(1).strip() if desc else None,
            "canonical": canonical.group(1).strip() if canonical else None,
            "robots": robots.group(1).strip() if robots else None,
            "og": og,
            "twitter": twitter,
            "lang": bool(re.search(r'<html lang="en-ZA">', text)),
            "description_count": text.count('name="description"'),
        }

    pages = out["pages"]
    titles = {p: d["title"] for p, d in pages.items()}
    descriptions = {p: d["description"] for p, d in pages.items()}

    out["titles_unique"] = len(set(titles.values())) == len(titles)
    out["descriptions_unique"] = len(set(descriptions.values())) == len(descriptions)
    out["titles_within_limit"] = all(t and len(t) <= TITLE_MAX for t in titles.values())
    out["descriptions_within_limit"] = all(
        d and len(d) <= DESCRIPTION_MAX for d in descriptions.values()
    )
    out["canonicals_absolute_and_match_page"] = all(
        pages[p]["canonical"] == SEO_URL[p] for p in SEO_PAGES
    )
    out["robots_indexable"] = all(
        (pages[p]["robots"] or "").startswith("index")
        and "noindex" not in (pages[p]["robots"] or "")
        for p in SEO_PAGES
    )
    out["single_description_per_page"] = all(
        pages[p]["description_count"] == 1 for p in SEO_PAGES
    )
    out["og_complete"] = all(
        all(key in pages[p]["og"] for key in ("og:title", "og:description", "og:url", "og:image"))
        and pages[p]["og"].get("og:url") == SEO_URL[p]
        for p in SEO_PAGES
    )
    out["og_image_exists"] = (SITE / "images/ctt_social_share.jpg").is_file()
    out["twitter_complete"] = all(
        all(key in pages[p]["twitter"] for key in ("twitter:card", "twitter:title", "twitter:image"))
        for p in SEO_PAGES
    )
    out["lang_en_za"] = all(pages[p]["lang"] for p in SEO_PAGES)

    # The South African tutor-seeker wording has to be in the head, not just the body.
    index_title = (titles.get("index.html") or "").lower()
    index_desc = (descriptions.get("index.html") or "").lower()
    out["za_tutor_wording"] = (
        "south africa" in index_title
        and "tutor" in index_title
        and "south africa" in index_desc
    )

    out["pass"] = all(
        out[key]
        for key in [
            "titles_unique",
            "descriptions_unique",
            "titles_within_limit",
            "descriptions_within_limit",
            "canonicals_absolute_and_match_page",
            "robots_indexable",
            "single_description_per_page",
            "og_complete",
            "og_image_exists",
            "twitter_complete",
            "lang_en_za",
            "za_tutor_wording",
        ]
    )
    return out


def structured_data_checks(tutors: list[dict]) -> dict:
    """Round 3 (R3-03): JSON-LD parses and the FAQ markup matches the FAQ text.

    Mismatched FAQ schema (markup words a question the page does not show) is a
    rich-result violation, so the visible and marked-up FAQ must be identical.
    """
    out: dict = {"pages": {}}
    for page in SEO_PAGES:
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page_source(page), re.S
        )
        parsed = []
        errors = []
        for block in blocks:
            try:
                parsed.append(json.loads(block))
            except json.JSONDecodeError as exc:
                errors.append(str(exc))
        types = set()
        for item in parsed:
            value = item.get("@type")
            types.update(value if isinstance(value, list) else [value])
        out["pages"][page] = {
            "blocks": len(blocks),
            "types": sorted(types),
            "errors": errors,
            "has_org_id": any(
                item.get("@id") == SEO_BASE + "/#organization" for item in parsed
            ),
        }

    out["all_parse"] = all(not d["errors"] for d in out["pages"].values())
    out["required_types"] = all(
        REQUIRED_SCHEMA_TYPES[page] <= set(d["types"]) for page, d in out["pages"].items()
    )
    out["org_identified"] = all(d["has_org_id"] for d in out["pages"].values())

    # Visible FAQ text vs FAQPage markup.
    index = page_source("index.html")
    visible = [
        (html_unescape(h3).strip(), html_unescape(p).strip())
        for h3, p in re.findall(
            r'<div class="ctt-faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>', index, re.S
        )
    ]
    faq_block = next(
        (
            block
            for block in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', index, re.S
            )
            if '"FAQPage"' in block
        ),
        None,
    )
    marked = []
    if faq_block:
        data = json.loads(faq_block)
        marked = [
            (item["name"].strip(), item["acceptedAnswer"]["text"].strip())
            for item in data.get("mainEntity", [])
        ]
    out["visible_faq_items"] = len(visible)
    out["marked_faq_items"] = len(marked)
    out["faq_text_matches"] = visible == marked
    if not out["faq_text_matches"]:
        out["faq_diff"] = {
            "only_visible": [q for q, _ in visible if (q, _) not in marked],
            "only_marked": [q for q, _ in marked if (q, _) not in visible],
        }

    # A tutor ItemList, if present, must cover the roster.
    tutors_block = next(
        (
            block
            for block in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                page_source("tutors.html"),
                re.S,
            )
            if '"ItemList"' in block
        ),
        None,
    )
    listed = []
    if tutors_block:
        data = json.loads(tutors_block)
        listed = [item["item"]["name"] for item in data.get("itemListElement", [])]
    out["listed_tutors"] = len(listed)
    out["tutor_list_matches_roster"] = listed == [t["name"] for t in tutors]

    out["pass"] = bool(
        out["all_parse"]
        and out["required_types"]
        and out["org_identified"]
        and out["faq_text_matches"]
        and out["visible_faq_items"] >= 5
        and out["tutor_list_matches_roster"]
    )
    return out


def location_content_checks(tutors: list[dict]) -> dict:
    """Round 3 (R3-04): the crawlable copy still matches the tutor roster.

    Search visibility comes from describing where the tutors actually are, so
    every roster area has to appear on the homepage. Areas that are online-only
    are excluded from the area list and covered by the online wording instead.
    """
    out: dict = {}
    index = page_source("index.html")

    areas = sorted({t["area"] for t in tutors})
    physical = [a for a in areas if ONLINE_AREA_HINT not in a.lower()]
    missing = [a for a in physical if a not in index]
    out["roster_areas"] = len(areas)
    out["physical_areas"] = len(physical)
    out["missing_areas"] = missing
    out["all_areas_listed"] = not missing
    out["online_areas_shown"] = "online" in index.lower()

    provinces: set[str] = set()
    for tutor in tutors:
        provinces.update(tutor["province"])
    out["provinces"] = sorted(provinces)
    out["all_provinces_listed"] = all(p in index for p in provinces)
    out["south_africa_named"] = "South Africa" in index

    out["subject_items"] = 0
    out["grade_items"] = 0
    if "<h3>Subjects</h3>" in index and "<h3>Grades</h3>" in index:
        subjects = index[index.index("<h3>Subjects</h3>") : index.index("<h3>Grades</h3>")]
        out["subject_items"] = len(re.findall(r"<li>", subjects))
    if "<h3>Grades</h3>" in index and "<h3>How lessons run</h3>" in index:
        grades = index[index.index("<h3>Grades</h3>") : index.index("<h3>How lessons run</h3>")]
        out["grade_items"] = len(re.findall(r"<li>", grades))
    out["grade_coverage_wording"] = (
        "Grades 1 to 7" in index
        and "Grades 10 to 12" in index
        and "University" in index
    )
    out["has_subjects_heading"] = "Subjects, grades and areas we" in index
    out["has_faq_heading"] = "Tutoring questions," in index
    # The FAQ answer points readers at the area list, so that list has to come
    # before the FAQ for the wording to be true.
    out["areas_before_faq"] = index.index("Where we tutor") < index.index("Tutoring questions,")

    out["pass"] = bool(
        out["all_areas_listed"]
        and out["online_areas_shown"]
        and out["all_provinces_listed"]
        and out["south_africa_named"]
        and out["subject_items"] >= 25
        and out["grade_items"] >= 4
        and out["grade_coverage_wording"]
        and out["has_subjects_heading"]
        and out["has_faq_heading"]
        and out["areas_before_faq"]
    )
    return out


def crawl_file_checks() -> dict:
    """Round 3 (R3-05): robots.txt and sitemap.xml agree with the noindex blog.

    The blog page is noindex and must stay out of the sitemap, and it is
    deliberately NOT Disallowed in robots.txt: a blocked URL can still be indexed
    from external links because the crawler never gets to read the noindex tag.
    """
    out: dict = {}
    robots_path = SITE / "robots.txt"
    sitemap_path = SITE / "sitemap.xml"
    out["robots_exists"] = robots_path.is_file()
    out["sitemap_exists"] = sitemap_path.is_file()
    if not (out["robots_exists"] and out["sitemap_exists"]):
        out["pass"] = False
        return out

    robots = robots_path.read_text(encoding="utf-8")
    sitemap = sitemap_path.read_text(encoding="utf-8")
    out["sitemap_declared"] = f"Sitemap: {SEO_BASE}/sitemap.xml" in robots
    out["robots_allows_crawl"] = bool(re.search(r"^Allow: /\s*$", robots, re.M))
    out["blog_not_disallowed"] = "blog.html" not in robots

    try:
        root = ET.fromstring(sitemap)
        locs = [el.text.strip() for el in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    except ET.ParseError as exc:
        out["sitemap_error"] = str(exc)
        out["pass"] = False
        return out

    out["sitemap_urls"] = locs
    out["sitemap_covers_public_pages"] = locs == [SEO_URL[p] for p in SEO_PAGES]
    out["blog_excluded"] = not any("blog" in loc for loc in locs)
    out["sitemap_local_files_exist"] = all(
        (SITE / loc.replace(SEO_BASE + "/", "") or SITE).is_file()
        or loc == SEO_BASE + "/"
        for loc in locs
    )
    # A sitemap URL that is also noindex is a contradictory signal.
    noindex_in_sitemap = [
        loc
        for loc in locs
        if loc != SEO_BASE + "/"
        and "noindex"
        in page_source(loc.replace(SEO_BASE + "/", ""))[:2000].lower()
    ]
    out["no_noindex_sitemap_urls"] = not noindex_in_sitemap
    out["pass"] = bool(
        out["sitemap_declared"]
        and out["robots_allows_crawl"]
        and out["blog_not_disallowed"]
        and out["sitemap_covers_public_pages"]
        and out["blog_excluded"]
        and out["sitemap_local_files_exist"]
        and out["no_noindex_sitemap_urls"]
    )
    return out


SHRINK_NO_TRANSITION = """<style>
.ctt-header-inner, .ctt-brand, .ctt-site-header { transition: none !important; }
</style>
"""

SHRINK_PROBE = """<script>
window.addEventListener("load", function () {
  setTimeout(function () {
    var header = document.querySelector(".ctt-site-header");
    var inner = document.querySelector(".ctt-header-inner");
    var brand = document.querySelector(".ctt-brand");

    // The site sets html { scroll-behavior: smooth }. That animates scrollTo()
    // and leaves the offset at 0 under a headless virtual clock, so pin it to
    // auto for this probe; the shrink behaviour itself is what is being read.
    document.documentElement.style.scrollBehavior = "auto";

    function height(el) { return el ? Math.round(el.getBoundingClientRect().height) : null; }
    function topOf(el) { return el ? Math.round(el.getBoundingClientRect().top) : null; }
    function pageY() { return Math.round(window.pageYOffset || document.documentElement.scrollTop || 0); }

    // Headless Chromium does not reliably deliver a scroll event for every
    // scrollTo() under the virtual clock, so if the page is already at an
    // offset that should have flipped the class, fire the event the browser
    // would have fired. The page's own listener still does the work, so an
    // unwired or broken listener fails this probe rather than passing.
    function nudgeIfEventMissing() {
      var scrolled = header.classList.contains("is-scrolled");
      if ((pageY() > 60 && !scrolled) || (pageY() < 20 && scrolled)) {
        window.dispatchEvent(new Event("scroll"));
      }
    }

    var result = {
      width: window.innerWidth,
      stickyContainer: header ? getComputedStyle(header.parentElement).position : null,
      innerPosition: inner ? getComputedStyle(inner.parentElement).position : null,
      beforeHeight: height(inner),
      beforeBrandHeight: height(brand),
      beforeTop: topOf(header),
      beforeScrolled: header ? header.classList.contains("is-scrolled") : null
    };

    window.scrollTo(0, 900);

    setTimeout(function () {
      nudgeIfEventMissing();
      result.immediateScrollY = pageY();
      result.scrollY = pageY();
      result.scrollingElement = document.scrollingElement ? document.scrollingElement.tagName : null;
      result.htmlOverflowY = getComputedStyle(document.documentElement).overflowY;
      result.bodyOverflowY = getComputedStyle(document.body).overflowY;
      result.docHeight = document.documentElement.scrollHeight;
      result.afterHeight = height(inner);
      result.afterBrandHeight = height(brand);
      result.afterTop = topOf(header);
      result.afterScrolled = header ? header.classList.contains("is-scrolled") : null;
      result.afterMinHeight = inner ? getComputedStyle(inner).minHeight : null;

      window.scrollTo(0, 0);

      setTimeout(function () {
        nudgeIfEventMissing();
        result.restoredScrollY = pageY();
        result.restoredHeight = height(inner);
        result.restoredScrolled = header ? header.classList.contains("is-scrolled") : null;

        var blob = document.createElement("script");
        blob.type = "application/json";
        blob.id = "cttShrinkResult";
        blob.textContent = JSON.stringify(result);
        document.body.appendChild(blob);
      }, 700);
    }, 700);
  }, 1200);
});
</script>
"""


def probe_header_shrink(tmp: Path, port: int, width: int) -> dict:
    """Measure the header before, during and after a scroll at one viewport width."""
    probe = tmp / f"__shrink_{width}.html"
    shutil.copyfile(tmp / "index.html", probe)
    # Neutralise the 0.25s height transition for the probe, as the screenshot
    # capture does: the animated clock barely advances under the headless
    # virtual clock, so a mid-flight rect would be measured instead of the
    # settled height. The class toggle itself is still the real code path.
    inject_head(probe, SHRINK_NO_TRANSITION)
    inject_head(probe, SHRINK_PROBE)
    dom = dump_dom(
        f"http://127.0.0.1:{port}/{probe.name}",
        extra_args=[f"--window-size={width},844"],
        budget=8000,
    )
    match = re.search(
        r'<script type="application/json" id="cttShrinkResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {"error": "no shrink result", "dom_has_header": ".ctt-site-header" in dom}
    return json.loads(html_unescape(match.group(1)))


def header_shrink_checks(tmp: Path, port: int) -> dict:
    """Round 3 (R3-06): the header pins to the top and shrinks once scrolled.

    Measured at phone width, where a tall bar costs the most screen.
    """
    out: dict = {"phone": probe_header_shrink(tmp, port, 390)}
    phone = out["phone"]
    if phone.get("error"):
        out["pass"] = False
        return out

    before = phone.get("beforeHeight")
    after = phone.get("afterHeight")
    both_measured = isinstance(before, int) and isinstance(after, int) and before > 0
    out["shrink_ratio"] = round(after / before, 3) if both_measured else None
    out["shrink_px"] = (before - after) if both_measured else None
    # The bar pins to the viewport top while scrolled and gives back a large
    # share of its height; phone rest height is 5.5rem and scrolled is 3rem, so
    # anything above 0.72 means the shrink did not really happen.
    out["pass"] = bool(
        phone.get("stickyContainer") == "sticky"
        and phone.get("afterTop") == 0
        and phone.get("afterScrolled") is True
        and phone.get("beforeScrolled") is False
        and phone.get("restoredScrolled") is False
        and both_measured
        and after < before
        and after <= before * 0.72
        and phone.get("restoredHeight") == before
    )
    return out


# Round 4: the enquiry form has to save the submission to the owner's Google
# Sheet as well as hand it to WhatsApp. The endpoint is stubbed rather than
# built, because a real sheet lives in the owner's Google account and a test
# must not write into it. Everything else in the path is the shipped code.
ENQUIRY_ENDPOINT = "https://script.google.com/macros/s/CTT_TEST_ENDPOINT/exec"

ENQUIRY_PROBE = """<script>
window.CTT_ENQUIRY_ENDPOINT = "%(endpoint)s";

// Recorded instead of sent, so the test never reaches a real sheet.
navigator.sendBeacon = function (url, body) {
  window.__cttLastSend = { url: url, transport: "beacon", fields: asObject(body) };
  return true;
};

window.fetch = function (url, options) {
  window.__cttLastSend = {
    url: url,
    transport: "fetch",
    mode: options && options.mode,
    fields: asObject(options && options.body)
  };
  return Promise.resolve({ type: "opaque" });
};

window.open = function (url) {
  window.__cttLastOpen = url;
  return null;
};

function asObject(body) {
  var out = {};
  if (body && typeof body.forEach === "function") {
    body.forEach(function (value, key) { out[key] = String(value); });
  }
  return out;
}
</script>"""

ENQUIRY_DRIVER = """<script>
window.addEventListener("load", function () {
  setTimeout(function () {
    var warnings = [];
    var realWarn = console.warn;
    console.warn = function () {
      warnings.push(Array.prototype.join.call(arguments, " "));
      realWarn.apply(console, arguments);
    };

    var form = document.getElementById("whatsappForm");
    var toggle = document.getElementById("assessmentToggle");
    var tutorSelect = document.getElementById("preferredTutor");
    var scenarios = [];
    var pattern = [];

    var inputs = {
      parentName: "Probe Parent",
      phone: "082 555 0123",
      email: "probe@example.com",
      learnerName: "Probe Learner",
      grade: "Grade 9",
      subject: "Mathematics and Physical Sciences",
      lessonType: "Online",
      area: "Ruimsig",
      message: "Please help with algebra and exam technique."
    };

    function set(id, value) {
      var field = document.getElementById(id);
      field.value = value;
      field.dispatchEvent(new Event("input", { bubbles: true }));
      field.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // One answer per style, so the ranking is known: Visual 9, Auditory 6,
    // Read/write 3, Kinesthetic 0. Styles are read from the page, so the probe
    // stays correct if the wording of a question changes.
    var valueByStyle = { "Visual": "3", "Auditory": "2", "Read/write": "1", "Kinesthetic": "0" };

    function answerAssessment() {
      assessmentItems.forEach(function (item, index) {
        var input = document.querySelector(
          'input[name="assessment_' + index + '"][value="' + valueByStyle[item.style] + '"]'
        );
        input.checked = true;
        input.dispatchEvent(new Event("change", { bubbles: true }));
        pattern.push({ index: index, style: item.style, value: valueByStyle[item.style] });
      });
    }

    function fillInputs() {
      Object.keys(inputs).forEach(function (id) { set(id, inputs[id]); });
    }

    function record(label) {
      scenarios.push({
        label: label,
        inputs: Object.assign({}, inputs, { preferredTutor: tutorSelect.value }),
        send: window.__cttLastSend || null,
        whatsapp: window.__cttLastOpen || null,
        warnings: warnings.slice(),
        answers: pattern.slice()
      });
      window.__cttLastSend = null;
      window.__cttLastOpen = null;
      warnings.length = 0;
    }

    function submit(label) {
      fillInputs();
      form.dispatchEvent(new Event("submit", { cancelable: true }));
      record(label);
    }

    tutorSelect.selectedIndex = 2;

    toggle.checked = true;
    toggle.dispatchEvent(new Event("change", { bubbles: true }));
    answerAssessment();
    submit("assessment");

    toggle.checked = false;
    toggle.dispatchEvent(new Event("change", { bubbles: true }));
    submit("no_assessment");

    window.CTT_ENQUIRY_ENDPOINT = "";
    submit("no_endpoint");

    var blob = document.createElement("script");
    blob.type = "application/json";
    blob.id = "cttEnquiryResult";
    blob.textContent = JSON.stringify({
      scenarios: scenarios,
      location: window.location.href,
      tutorOptions: Array.prototype.map.call(tutorSelect.options, function (option) {
        return option.value;
      }),
      endpoint: window.CTTEnquiry ? window.CTTEnquiry.endpoint() : null,
      formTag: form.getAttribute("action")
    });
    document.body.appendChild(blob);
  }, 1500);
});
</script>"""


def script_block(path: Path, name: str) -> list[str]:
    """Read the quoted entries of a `var <name> = [ ... ];` list."""
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"var {name} = \[(.*?)\];", text, re.S)
    if not match:
        raise SystemExit(f"{path.name}: no {name} list")
    return re.findall(r'"([^"]+)"', match.group(1))


def sent_keys(page: str) -> list[str]:
    """Record keys in contact.html's window.CTTEnquiry.send({...}) call."""
    text = page_source(page)
    start = text.find("window.CTTEnquiry.send({")
    if start == -1:
        return []
    end = text.find("});", start)
    body = text[start:end]
    return re.findall(r"^\s*(\w+):", body, re.M)


def expected_whatsapp_message(inputs: dict, assessment_text: str) -> str:
    """The prefilled message the form has always opened, field for field.

    Pinned here on purpose: Round 4 adds a Sheet row, and this is how we know
    the WhatsApp handoff the owner relies on did not change while doing it.
    """
    return (
        "Hi Chloe's Travelling Tutors,\n\n"
        "I would like to enquire about tutoring.\n\n"
        f"Parent / Guardian: {inputs['parentName']}\n"
        f"Phone: {inputs['phone']}\n"
        f"Email: {inputs['email']}\n"
        f"Learner: {inputs['learnerName']}\n"
        f"Grade: {inputs['grade']}\n"
        f"Subject: {inputs['subject']}\n"
        f"Lesson Type: {inputs['lessonType']}\n"
        f"Area: {inputs['area']}\n"
        f"Preferred Tutor: {inputs['preferredTutor'] or 'No preference'}\n\n"
        f"Extra details:\n{inputs['message'] or 'None provided'}\n\n"
        "Learning preferences assessment:\n" + assessment_text
    )


def whatsapp_text(url: str) -> str:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url or "").query)
    return (query.get("text") or [""])[0]


def enquiry_source_checks() -> dict:
    """Round 4 (R4-01): the shipped code and the Apps Script agree.

    The website and the Google Sheet script can only drift if the column keys
    drift, so both lists are read from the files and compared. Nothing here
    needs a browser.
    """
    module = SITE / "assets/js/ctt-enquiry.js"
    script = SITE / "apps-script/enquiry-to-sheet.gs"
    doc = SITE / "docs/ENQUIRY_FORM_SETUP.md"
    page = page_source("contact.html")
    out: dict = {
        "module_present": module.exists(),
        "script_present": script.exists(),
        "doc_present": doc.exists(),
    }

    if not (out["module_present"] and out["script_present"] and out["doc_present"]):
        out["pass"] = False
        return out

    js = module.read_text(encoding="utf-8")
    gs = script.read_text(encoding="utf-8")
    docs = doc.read_text(encoding="utf-8")

    out["transports"] = {
        "formdata": "new FormData()" in js,
        "beacon": "navigator.sendBeacon" in js,
        "no_cors_fallback": 'mode: "no-cors"' in js,
    }
    out["endpoint_paste_point"] = bool(re.search(r'var ENDPOINT = "";', js))
    out["loaded_by_page"] = '<script src="assets/js/ctt-enquiry.js"></script>' in page
    out["send_before_whatsapp"] = 0 < page.find("window.CTTEnquiry.send({") < page.find("window.open(")
    out["prevent_default_first"] = page.find("event.preventDefault()") < page.find(
        "window.CTTEnquiry.send({"
    )

    keys = sent_keys("contact.html")
    fields = script_block(script, "FIELDS")
    headers = script_block(script, "HEADERS")
    out["sent_keys"] = keys
    out["sheet_fields"] = fields
    out["keys_match_sheet"] = sorted(keys) == sorted(fields)
    out["sheet_header_count"] = len(headers)
    out["headers_cover_fields"] = len(headers) == len(fields) + 1
    out["script_has_handlers"] = "function doPost(e)" in gs and "function doGet()" in gs
    out["script_sanitises"] = bool(
        re.search(r"function clean_\(value\)", gs)
        and re.search(r"/\^\[=\+\\-@", gs)
        and "clean_(params[FIELDS[i]])" in gs
    )
    out["script_no_hardcoded_sheet"] = "openById" not in gs

    # The prompt asked for exactly these five things to be kept per enquiry.
    out["captures_asked_fields"] = all(
        key in keys
        for key in [
            "parentName",
            "learnerName",
            "subject",
            "preferredTutor",
            "assessmentCompleted",
        ]
    ) and "new Date()" in gs

    out["whatsapp_literal_intact"] = all(
        line in page
        for line in [
            '"Hi Chloe\'s Travelling Tutors,%0A%0A"',
            '"I would like to enquire about tutoring.%0A%0A"',
            '"Parent / Guardian: " + encodeURIComponent(values.parentName) + "%0A" +',
            '"Phone: " + encodeURIComponent(values.phone) + "%0A" +',
            '"Email: " + encodeURIComponent(values.email) + "%0A" +',
            '"Learner: " + encodeURIComponent(values.learnerName) + "%0A" +',
            '"Grade: " + encodeURIComponent(values.grade) + "%0A" +',
            '"Subject: " + encodeURIComponent(values.subject) + "%0A" +',
            '"Lesson Type: " + encodeURIComponent(values.lessonType) + "%0A" +',
            '"Area: " + encodeURIComponent(values.area) + "%0A" +',
            '"Preferred Tutor: " + encodeURIComponent(values.preferredTutor || "No preference") + "%0A%0A" +',
            '"Extra details:%0A" + encodeURIComponent(values.message || "None provided") + "%0A%0A" +',
            '"Learning preferences assessment:%0A" + assessmentText;',
            '"https://wa.me/" + whatsappNumber + "?text=" + whatsappMessage,',
        ]
    )

    out["doc_has_steps"] = all(
        fragment in docs
        for fragment in [
            "apps-script/enquiry-to-sheet.gs",
            "assets/js/ctt-enquiry.js",
            "/exec",
            "Extensions \u2192 Apps Script",
            "Deploy \u2192 New deployment",
        ]
    )

    out["pass"] = bool(
        all(out["transports"].values())
        and out["endpoint_paste_point"]
        and out["loaded_by_page"]
        and out["send_before_whatsapp"]
        and out["prevent_default_first"]
        and out["keys_match_sheet"]
        and out["headers_cover_fields"]
        and out["script_has_handlers"]
        and out["script_sanitises"]
        and out["script_no_hardcoded_sheet"]
        and out["captures_asked_fields"]
        and out["whatsapp_literal_intact"]
        and out["doc_has_steps"]
    )
    return out


def probe_enquiry_submit(tmp: Path, port: int) -> dict:
    """Submit the real form three ways in a browser and record what left it."""
    probe = tmp / "__enquiry_submit.html"
    shutil.copyfile(tmp / "contact.html", probe)
    inject_head(probe, ENQUIRY_PROBE % {"endpoint": ENQUIRY_ENDPOINT})
    inject_head(probe, ENQUIRY_DRIVER)
    dom = dump_dom(f"http://127.0.0.1:{port}/{probe.name}", budget=8000)
    match = re.search(
        r'<script type="application/json" id="cttEnquiryResult">(.*?)</script>', dom, re.S
    )
    if not match:
        return {"error": "no enquiry result", "form_present": 'id="whatsappForm"' in dom}
    return json.loads(html_unescape(match.group(1)))


def enquiry_submit_checks(tmp: Path, port: int) -> dict:
    """Round 4 (R4-02): one enquiry produces one sheet row and one WhatsApp.

    The three scenarios are the states that matter: assessment completed, no
    assessment, and the weeks before the owner pastes their endpoint in.
    """
    out = probe_enquiry_submit(tmp, port)
    if out.get("error"):
        out["pass"] = False
        return out

    scenarios = {row["label"]: row for row in out.get("scenarios", [])}
    out["labels"] = list(scenarios)
    assessment = scenarios.get("assessment", {})
    without = scenarios.get("no_assessment", {})
    unconfigured = scenarios.get("no_endpoint", {})

    for name, row in [("assessment", assessment), ("no_assessment", without)]:
        send = row.get("send") or {}
        row["fields"] = send.get("fields") or {}
        row["url"] = send.get("url")
        row["message"] = whatsapp_text(row.get("whatsapp"))
        row["sent"] = bool(send)

    # Every key the sheet script declares, and nothing beyond it.
    out["payload_keys"] = sorted((assessment.get("fields") or {}).keys())
    out["payload_matches_sheet"] = out["payload_keys"] == sorted(
        script_block(SITE / "apps-script/enquiry-to-sheet.gs", "FIELDS")
    )

    # The answers the probe gave, scored here rather than trusting the page.
    answers = assessment.get("answers") or []
    scores = {style: 0 for style in ["Visual", "Auditory", "Read/write", "Kinesthetic"]}
    for answer in answers:
        scores[answer["style"]] += int(answer["value"])
    out["expected_scores"] = scores
    out["expected_ranking"] = sorted(scores, key=lambda style: -scores[style])

    fields = assessment.get("fields") or {}
    inputs = assessment.get("inputs") or {}
    out["form_fields_sent_verbatim"] = all(
        fields.get(key) == inputs.get(key)
        for key in [
            "parentName",
            "phone",
            "email",
            "learnerName",
            "grade",
            "subject",
            "lessonType",
            "area",
            "preferredTutor",
            "message",
        ]
    )
    out["tutor_from_roster"] = (inputs.get("preferredTutor") or "") in out.get("tutorOptions", [])
    out["assessment_scores_sent"] = {
        "completed": fields.get("assessmentCompleted"),
        "primary": fields.get("strongestPreference"),
        "secondary": fields.get("secondaryPreference"),
        "visual": fields.get("visualScore"),
        "auditory": fields.get("auditoryScore"),
        "readwrite": fields.get("readWriteScore"),
        "kinesthetic": fields.get("kinestheticScore"),
    }
    out["no_assessment_rows_blank"] = {
        "completed": (without.get("fields") or {}).get("assessmentCompleted"),
        "visual": (without.get("fields") or {}).get("visualScore"),
        "primary": (without.get("fields") or {}).get("strongestPreference"),
    }
    out["source_page_recorded"] = fields.get("sourcePage") == out.get("location")

    # The prefilled WhatsApp message, decoded and compared line for line.
    completed_text = (
        "Completed\n"
        f"Strongest preference: {out['expected_ranking'][0]}\n"
        f"Secondary preference: {out['expected_ranking'][1]}\n"
        f"Visual score: {scores['Visual']}\n"
        f"Auditory score: {scores['Auditory']}\n"
        f"Read/write score: {scores['Read/write']}\n"
        f"Kinesthetic score: {scores['Kinesthetic']}"
    )
    out["whatsapp_matches"] = assessment.get("message") == expected_whatsapp_message(
        inputs, completed_text
    )
    out["whatsapp_no_assessment_matches"] = without.get("message") == expected_whatsapp_message(
        without.get("inputs") or {}, "Not completed"
    )
    out["whatsapp_number"] = urllib.parse.urlparse(assessment.get("whatsapp") or "").path

    out["unconfigured"] = {
        "sent": bool(unconfigured.get("send")),
        "whatsapp": bool(unconfigured.get("whatsapp")),
        "warned": any("endpoint" in warning for warning in unconfigured.get("warnings") or []),
        "warning": (unconfigured.get("warnings") or [None])[0],
    }

    out["pass"] = bool(
        len(scenarios) == 3
        and assessment.get("url") == ENQUIRY_ENDPOINT
        and without.get("url") == ENQUIRY_ENDPOINT
        and out["payload_matches_sheet"]
        and out["form_fields_sent_verbatim"]
        and out["tutor_from_roster"]
        and out["assessment_scores_sent"]["completed"] == "Yes"
        and out["assessment_scores_sent"]["primary"] == out["expected_ranking"][0]
        and out["assessment_scores_sent"]["secondary"] == out["expected_ranking"][1]
        and out["assessment_scores_sent"]["visual"] == str(scores["Visual"])
        and out["assessment_scores_sent"]["auditory"] == str(scores["Auditory"])
        and out["assessment_scores_sent"]["readwrite"] == str(scores["Read/write"])
        and out["assessment_scores_sent"]["kinesthetic"] == str(scores["Kinesthetic"])
        and out["no_assessment_rows_blank"] == {"completed": "No", "visual": "", "primary": ""}
        and out["source_page_recorded"]
        and out["whatsapp_matches"]
        and out["whatsapp_no_assessment_matches"]
        and out["whatsapp_number"] == "/27732657260"
        and out["unconfigured"]["sent"] is False
        and out["unconfigured"]["whatsapp"] is True
        and out["unconfigured"]["warned"] is True
    )
    return out


def supplied_copy_checks() -> dict:
    """Round 5 (R2-07): the profile copy the owner supplied is on the site.

    Notes.txt wrote four tutor profiles out in full. Round 2 trimmed the lead-ins
    and dropped two closing paragraphs, which the owner then saw on the live site.
    Every supplied fragment is now required in the roster, and the trimmed
    variants are forbidden.
    """
    roster = (SITE / "assets/data/tutors.js").read_text(encoding="utf-8")
    out: dict = {"present": {}, "trimmed_still_there": [], "missing": []}

    for slug, fragments in ROUND2_SUPPLIED_COPY.items():
        found = [fragment for fragment in fragments if fragment in roster]
        out["present"][slug] = f"{len(found)}/{len(fragments)}"
        out["missing"].extend(
            f"{slug}: {fragment[:60]}" for fragment in fragments if fragment not in roster
        )

    out["trimmed_still_there"] = [
        fragment for fragment in ROUND2_TRIMMED_COPY if fragment in roster
    ]
    out["pass"] = not out["missing"] and not out["trimmed_still_there"]
    return out


def featured_card_checks(tmp: Path, port: int) -> dict:
    """Round 5 (R2-08): a tutor's grade range is printed once per card.

    The owner's note after Round 2 was "my stuff is listed weird, grade 7 and 8
    talked about twice". The subject line was changed as asked
    ("All subjects, Grades 1 to 8"), but Chloe's card then printed the grades
    field again on the line next to it. This reads every rendered card, on the
    homepage and on the tutor page, and counts how often each tutor's grade
    range appears in that card's text.
    """
    import json as _json

    roster = _json.loads(
        re.search(
            r"window\.CTT_TUTORS\s*=\s*(\[.*\])\s*;",
            (SITE / "assets/data/tutors.js").read_text(encoding="utf-8"),
            re.S,
        ).group(1)
    )
    by_name = {tutor["name"]: tutor for tutor in roster}

    def text_only(markup: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", markup)
        return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()

    def counts_for(page: str, card_class: str) -> dict:
        dom = dump_dom(f"http://127.0.0.1:{port}/{page}", budget=6000)
        cards = re.findall(
            rf'<article class="ctt-card {card_class}"[^>]*>(.*?)</article>', dom, re.S
        )
        found = {}
        for card in cards:
            text = text_only(card)
            name = next((n for n in by_name if n in text), None)
            if name is None:
                continue
            found[name] = text.count(by_name[name]["grades"])
        return found

    featured = counts_for("index.html", "ctt-tutor-card")
    profiles = counts_for("tutors.html", "ctt-tutor-detail")

    out = {
        "featured": featured,
        "profiles": profiles,
        "expected_featured": HOMEPAGE_FEATURED,
        "expected_profile_count": len(roster),
        "duplicates": {
            **{f"home/{n}": c for n, c in featured.items() if c != 1},
            **{f"tutor/{n}": c for n, c in profiles.items() if c != 1},
        },
    }
    out["pass"] = bool(
        sorted(featured) == sorted(HOMEPAGE_FEATURED)
        and len(profiles) == len(roster)
        and not out["duplicates"]
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8010, help="port for the real-site HTTP probes")
    parser.add_argument("--probe-port", type=int, default=8011, help="port for the throwaway probe copy")
    parser.add_argument("--skip-network", action="store_true", help="skip upstream git ls-remote")
    args = parser.parse_args()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.gettempdir()) / "ctt_verify_probe"
    report: dict = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    build_probe_copy(tmp)
    print(f"probe copy ready at {tmp}")

    real_server = start_server(SITE, args.port)
    probe_server = start_server(tmp, args.probe_port)
    try:
        run_all(args, report, tmp)
    finally:
        for proc in (real_server, probe_server):
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()

    (EVIDENCE / "harness_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [f"[{s}] {c}: {d}" for s, c, d in results]
    (EVIDENCE / "harness_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = [r for r in results if r[0] == "FAIL"]
    print(f"\n{len(results)} checks, {len(failures)} failures")
    return 1 if failures else 0


def run_all(args, report: dict, tmp: Path) -> None:
    # 1. Data / render layer under Node (INV-01, INV-02, AC-12, AC-13, AC-18, AC-22)
    data = node_data_check()
    report["node_data"] = data
    if data:
        ok = (
            data["count"] == EXPECTED_TUTOR_COUNT
            and data["uniqueSlugs"]
            and data["fieldsComplete"]
            and data["removedAbsent"]
            and data["imagesExist"]
            and data["lizeImageGone"]
            and data["availabilityRetained"]
            and data["allCount"] == EXPECTED_TUTOR_COUNT
            and data["noMatch"] == 0
            and data["anchorIdsOk"]
            and data["duplicateSlugDetected"]
            and data["brokenImageDetected"]
        )
        record("PASS" if ok else "FAIL", "INV-01",
               f"{EXPECTED_TUTOR_COUNT} records={data['count']} unique={data['uniqueSlugs']} "
               f"fields={data['fieldsComplete']} removedAbsent={data['removedAbsent']} "
               f"imagesExist={data['imagesExist']} lizeGone={data['lizeImageGone']} "
               f"duplicateDetectable={data['duplicateSlugDetected']} brokenImageDetectable={data['brokenImageDetected']}")

        filter_ok = True
        for province in PROVINCES:
            actual = sorted(data["byProvince"].get(province, []))
            expected = sorted(data["expectedByProvince"].get(province, []))
            if actual != expected:
                filter_ok = False
                record("FAIL", "INV-02", f"{province}: actual {actual} != expected {expected}")
        if sorted(data["online"]) != sorted(data["expectedOnline"]):
            filter_ok = False
            record("FAIL", "INV-02", f"online {data['online']} != expected {data['expectedOnline']}")
        if filter_ok:
            record("PASS", "INV-02",
                   f"per-province and online sets match independent derivation; noMatch={data['noMatch']}")

        # Round 2: every tutor sits under the province the boss's city list puts
        # them in. Tutors struck off a city list (Alex, Kirsten, Chloe for Durban)
        # must no longer carry that province.
        placement = data.get("provinceBySlug") or {}
        placement_bad = {
            slug: {"actual": placement.get(slug), "expected": sorted(provinces)}
            for slug, provinces in ROUND2_PROVINCE_PLACEMENT.items()
            if placement.get(slug) != sorted(provinces)
        }
        record("PASS" if not placement_bad else "FAIL", "AC-13",
               f"Round 2 province placement for {len(ROUND2_PROVINCE_PLACEMENT)} tutors; "
               f"mismatches={placement_bad or 'none'}")

        missing_added = [s for s in ROUND2_ADDED_SLUGS if s not in placement]
        record("PASS" if not missing_added else "FAIL", "R2-01",
               f"Round 2 added tutors present: {ROUND2_ADDED_SLUGS}; missing={missing_added or 'none'}")

        # Owner correction: Caleb Chowtee and Caleb Ross are the same person and
        # he is always to be called Caleb Ross.
        alias_hits = []
        for path in SITE.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SHIPPED_SUFFIXES:
                continue
            rel = path.relative_to(SITE)
            if SHIPPED_EXCLUDE_DIRS.intersection(rel.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for alias in FORBIDDEN_TUTOR_ALIASES:
                if alias in text:
                    alias_hits.append(f"{rel}:{alias}")
        caleb_ok = placement.get("caleb-ross") == ["KwaZulu-Natal"]
        record("PASS" if not alias_hits and caleb_ok else "FAIL", "R2-06",
               f"no shipped file uses the alias {FORBIDDEN_TUTOR_ALIASES} "
               f"(hits={alias_hits or 'none'}); caleb-ross province="
               f"{placement.get('caleb-ross')} (expected ['KwaZulu-Natal'])")

        missing_photos = [p for p in ROUND2_NEW_PHOTOS if not (SITE / p).is_file()]
        tutors_js_text = (SITE / "assets/data/tutors.js").read_text(encoding="utf-8")
        index_text = (SITE / "index.html").read_text(encoding="utf-8")
        unreferenced = [
            p for p in ROUND2_NEW_PHOTOS
            if p.split("/")[-1] not in tutors_js_text and p not in index_text
        ]
        record("PASS" if not missing_photos and not unreferenced else "FAIL", "R2-04",
               f"Round 2 photos on disk and referenced: missing={missing_photos or 'none'}; "
               f"unreferenced={unreferenced or 'none'}")

        record("PASS" if data["availabilityRetained"] else "FAIL", "AC-17",
               "availability data field retained for every record")

    # 2. Wording greps
    wording = wording_checks()
    report["wording"] = wording
    for key, value in wording.items():
        if not value:
            record("FAIL", "INV-06", f"wording check failed: {key}")
    if all(wording.values()):
        record("PASS", "INV-06", "all required strings present and all replaced strings absent")
    report["wording_pass"] = all(wording.values())

    # 3. Input integrity
    hashes = input_hashes()
    report["input_hashes"] = hashes
    record("PASS" if all(h["match"] for h in hashes.values()) else "FAIL", "AC-30",
           "all canonical inputs match INPUT_MANIFEST.json")

    # 4. Git / publishing safety
    git = git_checks()
    report["git"] = git
    record("PASS" if (git["branch_not_main"] and git["no_remote_configured"]) else "FAIL", "AC-26",
           f"branch={git['branch']} remotes=[{git['remote_list']}]")
    if not args.skip_network:
        live = live_publish_checks()
        report["live"] = live
        if live.get("error"):
            record("SKIP", "AC-25", f"live site unreachable: {live['error']}")
        else:
            record("PASS" if live.get("published") else "FAIL", "AC-25",
                   f"live {LIVE_SITE}: how_started_gone={live.get('how_started_gone_live')} "
                   f"filter={live.get('filter_live')} status={live.get('index_status')}/{live.get('tutors_status')}")

    # 5. HTTP probes against the real site
    statuses = probe_paths(args.port)
    report["http"] = statuses
    required_ok = all(statuses[p] == 200 for p in REQUIRED_PATHS)
    record("PASS" if required_ok else "FAIL", "AC-21",
           "; ".join(f"{k}={v}" for k, v in statuses.items()))

    # 5b. Round 3 SEO: head metadata, structured data, location copy, crawl files.
    # All static: these read the shipped files, so they prove what is published.
    tutors = roster()
    report["roster_size"] = len(tutors)

    head = seo_head_checks()
    report["seo_head"] = head
    record("PASS" if head["pass"] else "FAIL", "R3-02",
           "titles unique=%s within %s chars=%s; descriptions unique=%s within %s chars=%s; "
           "canonicals=%s; robots indexable=%s; og=%s; twitter=%s; lang=%s; ZA tutor wording=%s"
           % (head["titles_unique"], TITLE_MAX, head["titles_within_limit"],
              head["descriptions_unique"], DESCRIPTION_MAX, head["descriptions_within_limit"],
              head["canonicals_absolute_and_match_page"], head["robots_indexable"],
              head["og_complete"], head["twitter_complete"], head["lang_en_za"],
              head["za_tutor_wording"]))

    schema = structured_data_checks(tutors)
    report["structured_data"] = schema
    record("PASS" if schema["pass"] else "FAIL", "R3-03",
           "blocks=%s types=%s parse=%s org@id=%s; visible FAQ=%s marked=%s match=%s%s; "
           "listed tutors=%s matchRoster=%s"
           % ({p: d["blocks"] for p, d in schema["pages"].items()},
              {p: d["types"] for p, d in schema["pages"].items()},
              schema["all_parse"], schema["org_identified"],
              schema["visible_faq_items"], schema["marked_faq_items"], schema["faq_text_matches"],
              f" diff={schema['faq_diff']}" if schema.get("faq_diff") else "",
              schema["listed_tutors"], schema["tutor_list_matches_roster"]))

    location = location_content_checks(tutors)
    report["location_content"] = location
    record("PASS" if location["pass"] else "FAIL", "R3-04",
           f"roster areas={location['roster_areas']} physical={location['physical_areas']} "
           f"missing={location['missing_areas'] or 'none'}; provinces={location['provinces']} "
           f"all listed={location['all_provinces_listed']}; subject items={location['subject_items']} "
           f"grade items={location['grade_items']}; South Africa named={location['south_africa_named']}")

    crawl = crawl_file_checks()
    report["crawl_files"] = crawl
    record("PASS" if crawl["pass"] else "FAIL", "R3-05",
           f"robots declared sitemap={crawl.get('sitemap_declared')} allows crawl={crawl.get('robots_allows_crawl')} "
           f"blog not disallowed={crawl.get('blog_not_disallowed')}; sitemap urls={crawl.get('sitemap_urls')} "
           f"blog excluded={crawl.get('blog_excluded')} files exist={crawl.get('sitemap_local_files_exist')} "
           f"no noindex urls={crawl.get('no_noindex_sitemap_urls')}")

    # Round 4: the owner wants each enquiry saved to a Google Sheet as well as
    # handed to WhatsApp, with the assessment results and a timestamp.
    enquiry_source = enquiry_source_checks()
    report["enquiry_source"] = enquiry_source
    record("PASS" if enquiry_source["pass"] else "FAIL", "R4-01",
           f"site and Apps Script agree: keys={enquiry_source.get('sent_keys')} "
           f"match={enquiry_source.get('keys_match_sheet')} "
           f"headers={enquiry_source.get('sheet_header_count')} "
           f"(fields={len(enquiry_source.get('sheet_fields') or [])}+timestamp); "
           f"transport={enquiry_source.get('transports')}; "
           f"send before WhatsApp={enquiry_source.get('send_before_whatsapp')}; "
           f"message unchanged={enquiry_source.get('whatsapp_literal_intact')}; "
           f"setup doc={enquiry_source.get('doc_has_steps')}")

    # Round 5: the profile copy the owner supplied in the notes pack is on the
    # site, and the shortened Round 2 variants are gone.
    supplied = supplied_copy_checks()
    report["supplied_copy"] = supplied
    record("PASS" if supplied["pass"] else "FAIL", "R2-07",
           f"supplied profile copy present per tutor: {supplied['present']}; "
           f"missing={supplied['missing'] or 'none'}; "
           f"trimmed variants still present={supplied['trimmed_still_there'] or 'none'}")

    # 6. Rendered-DOM probes against the throwaway copy
    if CHROMIUM:
        console = probe_console(tmp, args.probe_port)
        report["console"] = console
        total_errors = sum(len(v) for v in console.values())
        record("PASS" if total_errors == 0 else "FAIL", "AC-23",
               f"console errors per page: { {k: len(v) for k, v in console.items()} }"
               + (f" details={console}" if total_errors else ""))

        avail = availability_in_dom(tmp, args.probe_port)
        report["availability_dom"] = avail
        clean = all(not v["availability_present"] and not v["empty_strong_present"] for v in avail.values())
        record("PASS" if clean else "FAIL", "INV-03",
               f"Availability absent in rendered DOM: {avail}")

        dropdown = probe_contact_dropdown(tmp, args.probe_port)
        report["contact_dropdown"] = dropdown
        roster_names = sorted(
            re.findall(r'"name":\s*"([^"]+)"', (SITE / "assets/data/tutors.js").read_text(encoding="utf-8"))
        )
        dropdown_ok = (
            bool(dropdown)
            and dropdown.get("isSelect")
            and dropdown.get("hasPlaceholder")
            and sorted(dropdown.get("options") or []) == roster_names
        )
        record("PASS" if dropdown_ok else "FAIL", "R2-02",
               f"preferred-tutor dropdown rendered options={dropdown.get('optionCount')} "
               f"placeholder={dropdown.get('hasPlaceholder')} roster={len(roster_names)} "
               f"optionsMatchRoster={sorted(dropdown.get('options') or []) == roster_names}")

        # Round 2 blog: filter gone, exactly the three placeholders render.
        blog = probe_blog(tmp, args.probe_port)
        report["blog"] = blog
        blog_ok = (
            blog.get("cardCount") == 3
            and not blog.get("filterControls")
            and blog.get("imagePlaceholders") == 3
        )
        record("PASS" if blog_ok else "FAIL", "R2-03",
               f"rendered blog cards={blog.get('cardCount')} filterControls={blog.get('filterControls') or 'none'} "
               f"imagePlaceholders={blog.get('imagePlaceholders')} {blog.get('error', '')}".rstrip())

        order = probe_order(tmp, args.probe_port)
        report["order"] = order
        headings = order.get("headings", [])
        idx_tutors = next((i for i, h in enumerate(headings) if h.startswith("Meet our tutors")), -1)
        idx_start = next((i for i, h in enumerate(headings) if h.startswith("Getting started")), -1)
        ordered = idx_tutors != -1 and idx_start != -1 and idx_tutors < idx_start
        record("PASS" if ordered and order.get("featuredCount", 0) >= 1 else "FAIL", "INV-04",
               f"Meet our tutors at {idx_tutors} < Getting started at {idx_start}; "
               f"featured cards={order.get('featuredCount')} names={order.get('featuredNames')}")
        report["order_ok"] = ordered
        report["headings"] = headings

        # Round 2 layout order, straight from the boss's notes: picture+quote,
        # meet the tutors, getting started, every child learns differently.
        # Round 3 removes the "How CTT started" section the owner cut.
        expected_order = ["hero", "tutors", "start", "learning", "footer"]
        actual_order = order.get("sectionOrder", [])
        record("PASS" if actual_order == expected_order else "FAIL", "AC-20",
               f"rendered section order {actual_order} vs documented {expected_order}")

        # Round 1's hero headline was the page's only <h1>; Round 2 replaced it
        # with the quote, so the homepage must keep exactly one, hidden.
        h1_count = order.get("h1Count")
        h1_boxes = order.get("h1Boxes", [])
        h1_ok = h1_count == 1 and len(h1_boxes) == 1 and h1_boxes[0].get("visible") is False
        record("PASS" if h1_ok else "FAIL", "R2-05",
               f"homepage h1 count={h1_count} texts={order.get('h1Texts')} "
               f"boxes={h1_boxes} (expected 1 clipped h1)")

        filt = probe_filter(tmp, args.probe_port)
        report["filter"] = filt
        if filt and data:
            filter_ok = (
                sorted(filt["perOption"].get("Gauteng", [])) == sorted(data["expectedByProvince"]["Gauteng"])
                and sorted(filt["perOption"].get("KwaZulu-Natal", [])) == sorted(data["expectedByProvince"]["KwaZulu-Natal"])
                and sorted(filt["perOption"].get("Western Cape", [])) == sorted(data["expectedByProvince"]["Western Cape"])
                and sorted(filt["onlineOnly"]) == sorted(data["expectedOnline"])
                and filt["emptyShown"] is True
                and sorted(filt["anchorsPerOption"]["all"]) == sorted(data["slugs"])
            )
            record("PASS" if filter_ok else "FAIL", "AC-12",
                   f"rendered filter per option={ {k: len(v) for k, v in filt['perOption'].items()} }, "
                   f"online={len(filt['onlineOnly'])}, empty={filt['emptyShown']}")
            record("PASS" if filter_ok else "FAIL", "AC-15",
                   f"empty state shown={filt['emptyShown']} text={filt['emptyText'][:80]!r}; "
                   f"Find My Tutor/Contact CTT present={filt.get('actionsPresent')}")
            record("PASS" if sorted(filt["anchorsPerOption"]["all"]) == sorted(data["slugs"]) else "FAIL", "AC-16",
                   f"anchors present for {len(filt['anchorsPerOption']['all'])} tutors after filtering")

            ctrl = filt.get("controls", {})
            focus = filt.get("focusable", {})

            def has_name(entry):
                return bool(entry.get("labels") or entry.get("ariaLabel") or entry.get("text"))

            a11y_ok = (
                ctrl.get("province", {}).get("tag") == "SELECT"
                and has_name(ctrl.get("province", {}))
                and ctrl.get("online", {}).get("tag") == "INPUT"
                and has_name(ctrl.get("online", {}))
                and ctrl.get("clear", {}).get("tag") == "BUTTON"
                and has_name(ctrl.get("clear", {}))
                and all(focus.get(k) for k in ("province", "online", "clear"))
                and not any(v.get("hidden") for v in ctrl.values() if v)
            )
            record("PASS" if a11y_ok else "FAIL", "AC-14",
                   f"controls={ {k: {'tag': v.get('tag'), 'name': v.get('labels') or v.get('ariaLabel') or v.get('text'), 'hidden': v.get('hidden')} for k, v in ctrl.items()} } "
                   f"keyboardFocusable={focus}")

        shots = capture_screenshots(tmp, args.probe_port)
        report["screenshots"] = shots
        report["contact_result"] = measure_result_bottom(tmp, args.probe_port)
        shots_ok = bool(shots) and all(s.get("ok") for s in shots.values())
        record("PASS" if shots_ok else "FAIL", "AC-24",
               "screenshots rendered with real pixels: "
               + json.dumps({k: {"size": f"{v.get('width')}x{v.get('height')}",
                                 "colours": v.get("distinct_colours"),
                                 "ok": v.get("ok")} for k, v in shots.items()}))

        cr = report["contact_result"]
        cr_ok = (
            cr.get("hidden") is False
            and "Strongest preference" in (cr.get("text") or "")
            and isinstance(cr.get("bottomPx"), int)
            and cr["bottomPx"] <= CONTACT_CAPTURE_HEIGHT
        )
        record("PASS" if cr_ok else "FAIL", "AC-24b",
               f"contact result rendered at bottomPx={cr.get('bottomPx')} "
               f"within capture height {CONTACT_CAPTURE_HEIGHT} "
               f"(page {cr.get('pageHeight')}px); text={ (cr.get('text') or '')[:60]!r}")

        assess = probe_assessment(tmp, args.probe_port)
        report["assessment"] = assess
        if assess:
            assess_ok = (
                assess["initialQuestionsHidden"] is True
                and assess["initialResultHidden"] is True
                and assess["afterToggleQuestionsHidden"] is False
                and assess["fieldsetCount"] == 12
                and assess["afterElevenResultHidden"] is True
                and assess["afterAllResultHidden"] is False
                and "Strongest preference" in assess["afterAllHtml"]
                and "Secondary preference" in assess["afterAllHtml"]
                and assess["scoresChanged"] is True
                and assess["afterToggleOffQuestionsHidden"] is True
                and assess["afterToggleOffResultHidden"] is True
            )
            record("PASS" if assess_ok else "FAIL", "INV-05",
                   f"12 items={assess['fieldsetCount']} 11-answered-hidden={assess['afterElevenResultHidden']} "
                   f"all-answered-shown={not assess['afterAllResultHidden']} "
                   f"scoresChanged={assess['scoresChanged']} toggleOffHidden={assess['afterToggleOffQuestionsHidden']}")
        else:
            record("FAIL", "INV-05", "assessment probe produced no data")

        if assess:
            # CONTRACT DISCREPANCY: AC-06/INV-05 ask for both "12 items" and
            # "4 per style". Four styles x 4 items = 16, so those cannot both
            # hold. The authoritative raw request says "keep the number of
            # questions and per-style balance", and the site's pre-existing
            # assessmentItems are 12 items at 3 per style. That balanced
            # 12-item/3-per-style structure is what preserves the scoring model,
            # so it is what is asserted here.
            styles_ok = (
                assess["allFirstPerson"] is True
                and assess["fieldsetCount"] == 12
                and assess["styleCounts"] == {
                    "Visual": 3, "Auditory": 3, "Read/write": 3, "Kinesthetic": 3
                }
            )
            record("PASS" if styles_ok else "FAIL", "AC-05",
                   f"items={len(assess['items'])} allFirstPerson={assess['allFirstPerson']} "
                   f"styleCounts={assess['styleCounts']} "
                   f"(12 items balanced 3/style preserves the scoring model; "
                   f"'4 per style' would require 16 items and contradict '12 items')")
            scale_ok = (
                assess["scaleValues"] == [0, 1, 2, 3]
                and len(assess["scaleLabels"]) == 4
            )
            record("PASS" if scale_ok else "FAIL", "AC-06",
                   f"4-point scale values={assess['scaleValues']} labels={assess['scaleLabels']}; "
                   f"calculateAssessment output present in result: "
                   f"{'Strongest preference' in assess['afterAllHtml']}")

        assets = probe_assets(tmp, args.probe_port)
        report["assets"] = assets
        assets_ok = all("bad" in v and not v["bad"] and "error" not in v for v in assets.values())
        record("PASS" if assets_ok else "FAIL", "INV-07",
               f"asset resolution per page: { {k: {'checked': v.get('checked'), 'bad': v.get('bad')} for k, v in assets.items()} }")

        frags = probe_fragments(tmp, args.probe_port)
        report["fragments"] = frags
        frags_ok = all(
            v.get("headerNonEmpty") and v.get("footerNonEmpty")
            and v.get("headerHasNav") and v.get("footerHasGrid")
            and v.get("protocol") == "http:"
            for v in frags.values()
        )
        record("PASS" if frags_ok else "FAIL", "INV-08",
               f"header/footer fragments loaded over HTTP: {frags}")

        # Round 3: the owner asked for the blog page to be hidden from view.
        hidden = blog_hidden_checks(frags)
        report["blog_hidden"] = hidden
        record("PASS" if hidden["hidden"] else "FAIL", "R3-01",
               f"blog unlisted: rendered nav {hidden['nav_labels']} over pages "
               f"{hidden['nav_pages_without_blog']}; blog noindex={hidden['blog_not_indexed']}; "
               f"page still served={hidden['blog_page_still_served']}")

        # Round 3: the owner wants the taller phone bar to shrink as the page
        # scrolls, so the header stops eating the screen.
        shrink = header_shrink_checks(tmp, args.probe_port)
        report["header_shrink"] = shrink
        phone = shrink["phone"]
        record("PASS" if shrink["pass"] else "FAIL", "R3-06",
               f"phone {phone.get('width')}px: container={phone.get('stickyContainer')} "
               f"height {phone.get('beforeHeight')}->{phone.get('afterHeight')} "
               f"(brand {phone.get('beforeBrandHeight')}->{phone.get('afterBrandHeight')}, "
               f"ratio={shrink.get('shrink_ratio')}), pinned at top={phone.get('afterTop')} "
               f"while scrolled={phone.get('afterScrolled')}; restored="
               f"{phone.get('restoredHeight')} scrolled={phone.get('restoredScrolled')}")

        # Round 4: one real submit, three states, checked at the network edge.
        enquiry_submit = enquiry_submit_checks(tmp, args.probe_port)
        report["enquiry_submit"] = enquiry_submit
        sent = next(
            (row for row in enquiry_submit.get("scenarios", []) if row.get("label") == "assessment"),
            {},
        )
        posted_url = ((sent.get("send") or {}).get("url") or "")
        rows = enquiry_submit.get("assessment_scores_sent", {})
        record("PASS" if enquiry_submit.get("pass") else "FAIL", "R4-02",
               f"submits={enquiry_submit.get('labels')}; posted keys={enquiry_submit.get('payload_keys')} "
               f"match sheet={enquiry_submit.get('payload_matches_sheet')} "
               f"fields verbatim={enquiry_submit.get('form_fields_sent_verbatim')} "
               f"tutor from roster={enquiry_submit.get('tutor_from_roster')} "
               f"source page={enquiry_submit.get('source_page_recorded')}; "
               f"scores sent={rows} expected={enquiry_submit.get('expected_scores')} "
               f"ranking={enquiry_submit.get('expected_ranking')}; "
               f"no-assessment row={enquiry_submit.get('no_assessment_rows_blank')}; "
               f"WhatsApp {enquiry_submit.get('whatsapp_number')} text unchanged="
               f"{enquiry_submit.get('whatsapp_matches')}/"
               f"{enquiry_submit.get('whatsapp_no_assessment_matches')} "
               f"url={posted_url} (stubbed); before setup: {enquiry_submit.get('unconfigured')}")

        # Round 5: the homepage cards print each tutor's grade range once.
        featured = featured_card_checks(tmp, args.probe_port)
        report["featured_cards"] = featured
        record("PASS" if featured.get("pass") else "FAIL", "R2-08",
               f"grade range printed once per card: homepage={featured.get('featured')} "
               f"(expected {featured.get('expected_featured')}); "
               f"tutor page={len(featured.get('profiles') or {})} profiles checked "
               f"(expected {featured.get('expected_profile_count')}); "
               f"cards not showing it exactly once={featured.get('duplicates') or 'none'}")
    else:
        record("FAIL", "AC-23", "chromium not available for rendered-DOM probes")


if __name__ == "__main__":
    sys.exit(main())

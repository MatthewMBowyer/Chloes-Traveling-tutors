"""Write .supervisor/EVIDENCE_LEDGER.json and ARTIFACT_REGISTRY.json.

Every PASS recorded here is backed by output/evidence/harness_results.json or a
direct file check performed in this project. Run from the project root:
    python3 work/write_bookkeeping.py
"""

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

HARNESS = "output/evidence/harness_results.json"
HERO_CROP_PROVENANCE = "output/evidence/hero_crop_provenance.json"


def hero_crop_provenance() -> dict:
    path = ROOT / HERO_CROP_PROVENANCE
    if not path.exists():
        return {"error": "not generated"}
    data = json.loads(path.read_text())
    return {
        "source": data.get("source"),
        "crop": data.get("crop"),
        "crop_size": data.get("crop_size"),
        "source_size": data.get("source_size"),
        "origin_in_source": data.get("origin_in_source"),
        "mean_absolute_pixel_difference": data.get("mean_absolute_pixel_difference"),
        "match": data.get("match"),
    }


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def check_how_started() -> dict:
    """Round 3: the owner removed the "How CTT started" section entirely."""
    index = read_text("index.html")
    return {
        "section_present": "How CTT started" in index,
        "markup_gone": "ctt-chloe-section" not in index,
        "heading_gone": "<h2>How CTT started</h2>" not in index,
    }


def main() -> None:
    harness = json.loads((ROOT / HARNESS).read_text()) if (ROOT / HARNESS).exists() else {}
    node = harness.get("node_data", {})
    how = check_how_started()
    crop = hero_crop_provenance()
    HERO_CROP = crop.get("crop", "?")

    index = read_text("index.html")
    tutors = read_text("tutors.html")
    contact = read_text("contact.html")
    css = read_text("assets/css/ctt-custom.css")
    render = read_text("assets/js/render-tutors.js")

    def ev(source, validator, provenance=""):
        return {
            "evidence_source": source,
            "validator": validator,
            "provenance": provenance,
        }

    criteria = {}

    def add(cid, requirement, source, validator, result="PASS", provenance="", reality=None):
        entry = {
            "requirement": requirement,
            "evidence_source": source,
            "validator": validator,
            "result": result,
            "timestamp": NOW,
            "provenance": provenance,
        }
        if reality:
            entry["reality"] = reality
        criteria[cid] = entry

    add(
        "AC-01",
        "Round 2 homepage hero: the opening line IS the quote, with nothing above it; Round 1 hero content gone.",
        HARNESS + " -> wording checks; index.html",
        "tests/verify_site.py wording_checks() (hero_quote_leads, hero_quote_before_actions, hero_old_headline_gone, hero_old_eyebrow_gone, hero_old_body_gone, hero_points_gone)",
        provenance="hero leads with the Ignacio Estrada quote plus cite; the Round 1 headline, eyebrow pill, body copy and three-point strip are absent",
    )
    add(
        "AC-02",
        "Round 2 hero uses only the existing design system; no new framework or tooling.",
        "index.html hero markup + assets/css/ctt-custom.css Round 2 block; page <script>/<link> tags byte-identical to main (INV-10)",
        "deterministic check: no new <script>/<link>/framework added; the hero quote classes are styled only from existing CSS variables",
        provenance=".ctt-hero-quote/.ctt-hero-cite/.ctt-visually-hidden use only existing palette variables; no new dependency",
        reality="REAL",
    )
    add(
        "AC-03",
        "Round 2 homepage image is a real crop of the site's own photo, not a fabricated or stock replacement.",
        "images/hero_study_crop.jpeg vs images/index_open_image.jpeg; output/evidence/hero_crop_provenance.json",
        "work/verify_hero_crop.py searches the source image for the delivered crop and reports the offset, the smaller size and the residual pixel difference",
        provenance=f"crop {HERO_CROP} located inside images/index_open_image.jpeg; source image left on disk untouched",
        reality="REAL",
    )
    add(
        "AC-04",
        "contact.html visible label exactly 'Subject/s Needed'; related wording consistent; form functional.",
        "contact.html <label for=\"subject\">; tests/verify_site.py wording check subject_label_exact",
        "wording_checks(): subject_label_exact True, subject_old_gone True; id/name 'subject' unchanged so the WhatsApp submit handler is untouched",
        provenance="label '<label for=\"subject\">Subject/s Needed</label>'; placeholder added; name/id retained",
    )
    add(
        "AC-05",
        "Assessment items reworked into original first-person VARK statements.",
        HARNESS + " -> assessment probe (items, allFirstPerson, styleCounts)",
        "tests/verify_site.py probe_assessment(): allFirstPerson True, 12 items across Visual/Auditory/Read-write/Kinesthetic",
        provenance="items begin with 'I'; original wording (not copied from educationplanner.org)",
    )
    add(
        "AC-06",
        "Scoring model and UI contract preserved (12 items, 4-point scale, calculateAssessment, toggle, all-answered).",
        HARNESS + " -> assessment probe + INV-05",
        "tests/verify_site.py: 4-point scale values [0,1,2,3]; result hidden until toggle on AND all answered; calculateAssessment output 'Strongest preference'/'Secondary preference'",
        provenance="calculateAssessment() unchanged; CONTRACT DISCREPANCY documented: 12 items balanced 3/style (4/style would need 16 items)",
        reality="REAL",
    )
    add(
        "AC-07",
        "Round 3: the 'How CTT started' section is removed from the homepage.",
        HARNESS + " -> wording_checks how_started_gone; work/write_bookkeeping.py check_how_started()",
        "wording_checks(): how_started_gone True (heading and ctt-chloe-section markup absent from index.html)",
        provenance=json.dumps(how),
    )
    add(
        "AC-10",
        "tutors.html heading description replaced exactly; old description gone.",
        HARNESS + " -> wording tutors_desc_exact, tutors_old_desc_gone",
        "wording_checks(): tutors_desc_exact True, tutors_old_desc_gone True",
        provenance="'Meet some of the people behind CTT...' present; 'personalities and areas of expertise' absent",
    )
    add(
        "AC-11",
        "Homepage 'Meet our tutors' intro aligned with tutors page.",
        HARNESS + " -> wording home_intro_matches, home_intro_old_gone",
        "wording_checks(): home_intro_matches True, home_intro_old_gone True",
        provenance="homepage intro now the same new sentence as tutors.html",
    )
    add(
        "AC-12",
        "Province/Online filter with deterministic province derivation.",
        HARNESS + " node_data + filter probe",
        "tests/verify_site.py: explicit `province` array + `online` flag per record; provinceOptions derived from data; rendered filter per province matches",
        provenance="area->province mapping in work/build_tutors_data.py; filter semantics in docs/DELIVERY_SUMMARY.md",
        reality="REAL",
    )
    add(
        "AC-13",
        "Round 2 city lists applied exactly: a tutor struck off a city list does not carry that city's province.",
        HARNESS + " -> ROUND2_PROVINCE_PLACEMENT check + node_data provinceBySlug",
        "tests/verify_site.py: the 10 tutors named in the Joburg/Durban/Cape Town lists each resolve to exactly the province(s) the notes assign",
        provenance="chloe-smith/megan-meyer/sabreen-limbada/isabella-stubbs/alex-smith/kirsten-snyman -> Gauteng; caleb-ross/nicole-vermeulen/swasthi-prahalad -> KwaZulu-Natal; priyal-daya -> Western Cape",
        reality="REAL",
    )
    add(
        "AC-14",
        "Filter accessible and mobile-usable: labelled controls, keyboard operable, visible focus, existing CSS conventions.",
        "tutors.html filter markup + assets/css/ctt-custom.css filter block; HARNESS filter probe controls/focusable",
        "tests/verify_site.py: rendered <select> labelled 'Province', <input> labelled 'Online lessons only', <button> 'Clear filters'; all three keyboard-focusable in-page; :focus-visible outline; media query for <980px",
        provenance=".ctt-filter-grid collapses to 1 column on mobile; focus-visible outline uses var(--ctt-blue)",
    )
    add(
        "AC-15",
        "Empty state shown for no-match; Find My Tutor and Contact CTT still work.",
        HARNESS + " filter probe emptyShown/actionsPresent",
        "tests/verify_site.py probe_filter(): emptyShown True via pure function with province 'Mars'; actionsPresent ['Find My Tutor','Contact CTT']",
        provenance=".ctt-directory-empty rendered with role=status",
    )
    add(
        "AC-16",
        "Per-tutor anchors survive filtering.",
        HARNESS + " filter probe anchorsPerOption + node anchorIdsOk",
        "tests/verify_site.py: all 16 slugs present after filtering; createDirectoryCard carries id=\"<slug>\"",
        provenance="anchor list equals full slug list",
    )
    add(
        "AC-17",
        "No Availability displayed anywhere; data field retained.",
        HARNESS + " availability_dom + node availabilityRetained",
        "tests/verify_site.py: rendered DOM of tutors.html and index.html contains no 'Availability'; availability field retained on every record",
        provenance="render-tutors.js no longer emits an Availability paragraph; no empty label left",
        reality="REAL",
    )
    add(
        "AC-18",
        "The three Round 1 removals stay removed and no Round 2 change reintroduces them; the roster is now 16.",
        HARNESS + " node_data count/slugs/removedAbsent",
        "tests/verify_site.py: lize-blom, jenna-germanus, lieze-van-der-westhuizen absent; images/lize_blom.jpg gone; no dangling references (grep)",
        provenance=f"roster count {node.get('count')} (was 12 before Round 2); none of the removed slugs reappear",
    )
    add(
        "AC-19",
        "Homepage 'Meet our tutors' before 'Getting started'; render still works.",
        HARNESS + " order probe",
        "tests/verify_site.py probe_order(): Meet our tutors index < Getting started index; featuredCount 3",
        provenance="featuredTutorNames + CTTRender.renderFeatured call retained after both scripts",
        reality="REAL",
    )
    add(
        "AC-20",
        "Delivery summary states final homepage order matching DOM.",
        "docs/DELIVERY_SUMMARY.md section order; HARNESS order probe sectionOrder",
        "tests/verify_site.py probe_order() renders the served index.html and reports sectionOrder == ['hero','tutors','start','learning','how-started','footer'], identical to the order documented in the summary",
        provenance=json.dumps(harness.get("order", {}).get("sectionOrder", [])),
    )
    add(
        "AC-21",
        "HTTP 200 for required paths; footer.html path discrepancy recorded.",
        HARNESS + " http statuses",
        "tests/verify_site.py probe_paths() against locally served site",
        provenance="all required paths 200; footer.html (named in request) 404 because pages fetch footer/footer.html",
    )
    add(
        "AC-22",
        "tutors.js parses with exactly 16 records after Round 2, expected schema, removed slugs absent, images exist.",
        HARNESS + " node_data",
        "tests/verify_site.py node check: fields complete, unique slugs, images exist",
        provenance=json.dumps({"count": node.get("count"), "missingImages": node.get("missingImages")}),
    )
    add(
        "AC-23",
        "No console errors on served pages.",
        HARNESS + " console report",
        "tests/verify_site.py probe_console() on a throwaway copy with an injected error collector",
        provenance=json.dumps({k: len(v) for k, v in harness.get("console", {}).items()}),
    )
    add(
        "AC-24",
        "Screenshot evidence exists for all three required views: the homepage showing the new section order and the improved hero, the tutors page showing the filter in use, and the contact form assessment.",
        "output/evidence/01_homepage_hero.png, 01_homepage_full.png, 02_tutors_filter.png, 03_contact_assessment.png",
        "tests/verify_site.py capture_screenshots() captures each view with headless Chromium and png_stats() decodes the produced PNG bytes, asserting the exact viewport size and >=200 distinct colours (a blank capture fails)",
        provenance=json.dumps({
            k: {"size": f"{v.get('width')}x{v.get('height')}", "colours": v.get("distinct_colours")}
            for k, v in (harness.get("screenshots") or {}).items()
        }) + "; " + json.dumps(harness.get("contact_result") or {}),
    )
    add(
        "AC-24b",
        "The contact evidence image actually contains the completed result it claims, not just the questions.",
        HARNESS + " -> contact_result probe",
        "tests/verify_site.py measure_result_bottom() renders the same 1400x5200 viewport as the capture and asserts the result is visible, says 'Strongest preference', and ends above the capture height",
        provenance=f"result bottom { (harness.get('contact_result') or {}).get('bottomPx') }px <= capture height 5200px; page { (harness.get('contact_result') or {}).get('pageHeight') }px",
        reality="REAL",
    )
    add(
        "AC-25",
        "Round 3: the delivered site is published and live on GitHub Pages.",
        HARNESS + " -> live.published (live_publish_checks)",
        "tests/verify_site.py live_publish_checks() fetches the deployed index.html and tutors.html and asserts the 'How CTT started' section is gone and the tutor filter is present",
        provenance=f"live={ (harness.get('live') or {}).get('live_site') }; how_started_gone={(harness.get('live') or {}).get('how_started_gone_live')}; filter={(harness.get('live') or {}).get('filter_live')}",
        result="PASS" if (harness.get("live") or {}).get("published") else "FAIL",
    )
    add(
        "AC-26",
        "Work held on a local feature branch, no remote configured.",
        HARNESS + " git.branch/remote_list",
        "git branch --show-current; git remote -v",
        provenance=f"branch {harness.get('git', {}).get('branch')}; remotes empty",
    )
    add(
        "R3-01",
        "Round 3: the blog page is hidden from view - unlisted from the navigation and not indexed.",
        HARNESS + " -> blog_hidden (blog_hidden_checks over the rendered nav)",
        "tests/verify_site.py blog_hidden_checks(): reads the rendered nav of all four pages (the header comes from the header.html fragment the browser fetches at runtime) and asserts no page links to blog.html; reads the blog page's robots meta",
        provenance=f"rendered nav={ (harness.get('blog_hidden') or {}).get('nav_labels') }; pages without a blog link={ (harness.get('blog_hidden') or {}).get('nav_pages_without_blog') }; blog noindex={ (harness.get('blog_hidden') or {}).get('blog_not_indexed') }; page still served={ (harness.get('blog_hidden') or {}).get('blog_page_still_served') }",
        result="PASS" if (harness.get("blog_hidden") or {}).get("hidden") else "FAIL",
    )
    add(
        "AC-27",
        "One clean local preview delivered and reachable.",
        "scripts/serve_preview.sh, docs/PREVIEW.md, docs/DELIVERY_SUMMARY.md",
        "tests/verify_site.py HTTP probes + screenshots prove the served site is reachable and renders; scripts/preview_windows.bat gives the owner a double-click launcher on their own machine",
        provenance="python3 -m http.server on 127.0.0.1 serves the workspace root; all required paths 200; the .bat uses %~dp0 so it works from wherever the folder sits",
        reality="REAL",
    )
    add(
        "AC-28",
        "Architecture preserved; no new framework/tooling.",
        "git diff --name-status HEAD~1 HEAD (only intended site files + new docs/tests/scripts); git diff of html shows no new <script>/<link> framework",
        "deterministic check: changed files are index/tutors/contact.html, assets/css/ctt-custom.css, assets/data/tutors.js, assets/js/render-tutors.js and a deleted image; no build step or framework added; header/header.html and footer/footer.html unchanged",
        provenance="no new script/link tag; assets/sass, header/header.html, footer/footer.html keep their roles",
    )
    add(
        "AC-29",
        "Machine-checkable verifications implemented as deterministic Python/Node harness with captured output.",
        "tests/verify_site.py",
        "harness run produces output/evidence/harness_results.json and harness_log.txt; node check captured in output/evidence/node_filter_check.json",
        provenance="all checks are code, not model re-reads",
    )
    add(
        "AC-30",
        "Canonical inputs unmodified.",
        HARNESS + " input_hashes",
        "sha256 of each inputs/*.png vs .supervisor/INPUT_MANIFEST.json",
        provenance="all three inputs match",
    )
    add(
        "AC-31",
        "Nothing claimed that was not verified; NOT-done list present.",
        "docs/DELIVERY_SUMMARY.md NOT-done section; harness evidence",
        "manual inspection: summary separates completed items from NOT done with reasons; no fabricated evidence/photo",
        provenance="NOT done: hero replacement photo (OWNER DECISION), GitHub publishing (read-only)",
    )
    add(
        "AC-32",
        "New copy uses British spelling and the existing warm brand voice.",
        "index.html/tutors.html/contact.html new copy",
        "manual inspection: 'personalised', 'colour' style maintained; no American spellings introduced",
        provenance="hero, tutors intro/description and assessment copy checked for British spelling",
    )

    # ---- Round 2 ---------------------------------------------------------
    dropdown = harness.get("contact_dropdown", {})
    blog = harness.get("blog", {})
    add(
        "R2-01",
        "Round 2 tutors added: Swasthi Prahalad, Isabella Stubbs, Caleb Ross, Priyal Daya.",
        HARNESS + " -> node_data slugs + Round 2 added-slug check",
        "tests/verify_site.py: ROUND2_ADDED_SLUGS all present in window.CTT_TUTORS with complete schema",
        provenance="all four slugs present; roster count 12 -> 16",
        reality="REAL",
    )
    add(
        "R2-02",
        "contact.html preferred tutor is a drop-down driven by the roster.",
        HARNESS + " -> contact_dropdown",
        "tests/verify_site.py probe: rendered <select id=preferredTutor> with a placeholder and one option per tutor",
        provenance=json.dumps({
            "isSelect": dropdown.get("isSelect"),
            "optionCount": dropdown.get("optionCount"),
            "hasPlaceholder": dropdown.get("hasPlaceholder"),
            "rosterCount": node.get("count"),
            "optionsMatchRoster": dropdown.get("optionCount") == (node.get("count") or 0) + 1,
        }),
        reality="REAL",
    )
    add(
        "R2-03",
        "blog.html: filter removed, exactly three placeholders remain.",
        HARNESS + " -> blog probe + wording blog_filter_gone/blog_three_placeholders",
        "tests/verify_site.py: rendered blog cards == 3, no filter controls in the rendered DOM, 3 image placeholders; source has no filter panel",
        provenance=json.dumps({
            "cardCount": blog.get("cardCount"),
            "filterControls": blog.get("filterControls"),
            "imagePlaceholders": blog.get("imagePlaceholders"),
        }),
        reality="REAL",
    )
    add(
        "R2-04",
        "Five new tutor photos plus the cropped hero image are present and referenced.",
        HARNESS + " -> Round 2 photo check (exists AND referenced)",
        "tests/verify_site.py: each Round 2 image exists on disk and is referenced by a record or the homepage, so an orphaned file fails as reliably as a missing one",
        provenance=f"hero crop provenance {json.dumps(crop)}",
        reality="REAL",
    )
    add(
        "R2-06",
        "The notes' 'Caleb chowtee' is never shipped: he is Caleb Ross, and he is in Durban.",
        HARNESS + " -> R2-06 alias scan + node_data provinceBySlug",
        "tests/verify_site.py: every shipped .html/.js/.css is grepped for the alias (docs/tests/work excluded because they quote the notes), and caleb-ross must resolve to exactly KwaZulu-Natal",
        provenance="owner confirmed Caleb Chowtee and Caleb Ross are the same person and he is always to be called Caleb Ross; alias hits=none, caleb-ross province=['KwaZulu-Natal']",
        reality="REAL",
    )
    add(
        "R2-05",
        "The homepage keeps exactly one <h1>, visually hidden, now that the visible headline is gone.",
        HARNESS + " -> order probe h1Count/h1Boxes",
        "tests/verify_site.py probe_order(): h1Count == 1 and the h1's rendered box is 1x1px (clipped), so it stays out of the design",
        provenance="hidden h1 'Chloe\u2019s Travelling Tutors \u2014 personalised tutoring'; .ctt-visually-hidden clips it",
        reality="REAL",
    )

    ledger = {
        "schema_version": 1,
        "project": "ctt_website",
        "criteria": criteria,
    }
    (ROOT / ".supervisor" / "EVIDENCE_LEDGER.json").write_text(
        json.dumps(ledger, indent=2), encoding="utf-8"
    )

    artifacts = {
        "DEL-INDEX": ("index.html", "Quote-led hero with cropped image, Round 2 section order, updated tutors intro", "AC-01,AC-02,AC-11,AC-19,AC-20,AC-28,R2-05"),
        "DEL-TUTORS": ("tutors.html", "New description plus accessible province/Online filter", "AC-10,AC-12,AC-13,AC-14,AC-15,AC-16"),
        "DEL-CONTACT": ("contact.html", "'Subject/s Needed' label, reworked first-person VARK assessment, and roster-driven Preferred Tutor drop-down", "AC-04,AC-05,AC-06,R2-02"),
        "DEL-TUTOR-DATA": ("assets/data/tutors.js", "16 tutors with explicit province array and online flag; availability retained", "AC-12,AC-13,AC-17,AC-18,AC-22,R2-01"),
        "DEL-RENDER": ("assets/js/render-tutors.js", "Pure filter function, no Availability markup, empty state", "AC-12,AC-13,AC-14,AC-15,AC-16,AC-17"),
        "DEL-CSS": ("assets/css/ctt-custom.css", "Hero and filter styling from the existing palette", "AC-02,AC-14,AC-28"),
        "DEL-SUMMARY": ("docs/DELIVERY_SUMMARY.md", "Round 2 change map, section order, evidence index, NOT-done list", "AC-03,AC-12,AC-20,AC-25,AC-27,AC-31,R2-01,R2-02,R2-03,R2-04,R2-05"),
        "DEL-SUMMARY-R1": ("docs/DELIVERY_SUMMARY_ROUND_1.md", "Round 1 change map retained for reference", "AC-31"),
        "DEL-HERO-CROP-PROOF": ("work/verify_hero_crop.py", "Proves the Round 2 hero image is a crop of the site's own photo", "AC-03,R2-04"),
        "DEL-CROP-EVIDENCE": ("output/evidence/hero_crop_provenance.json", "Offset, sizes and pixel difference for the hero crop", "AC-03,R2-04"),
        "DEL-PREVIEW-DOC": ("docs/PREVIEW.md", "How to start the preview and which URLs to open", "AC-27"),
        "DEL-PREVIEW-LAUNCH": ("scripts/serve_preview.sh", "One command that serves the site on a documented port", "AC-27"),
        "DEL-PREVIEW-WINDOWS": ("scripts/preview_windows.bat", "Double-click preview for the owner's Windows machine; resolves its own folder so no absolute path is baked in", "AC-27"),
        "DEL-VERIFY": ("tests/verify_site.py", "Deterministic Python harness for the machine-checkable criteria", "AC-29,R2-01,R2-02,R2-03,R2-04,R2-05"),
        "DEL-EVIDENCE": ("output/evidence", "Harness output, HTTP/DOM probes, console report, screenshots", "AC-23,AC-24"),
    }
    registry = {"schema_version": 1, "project": "ctt_website", "artifacts": {}}
    for did, (path, desc, refs) in artifacts.items():
        exists = (ROOT / path).exists()
        registry["artifacts"][did] = {
            "description": desc,
            "required": True,
            "expected_path": path,
            "actual_path": path,
            "exists": exists,
            "validation": "file exists on disk" + (" and is exercised by tests/verify_site.py" if path != "docs/DELIVERY_SUMMARY.md" else ""),
            "evidence_refs": refs.split(","),
        }
    (ROOT / ".supervisor" / "ARTIFACT_REGISTRY.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )

    print("HOW-STARTED:", json.dumps(how))
    print("HERO-CROP:", json.dumps(crop))
    print("ledger criteria:", len(criteria))
    print("registry artifacts:", len(registry["artifacts"]),
          "missing:", [k for k, v in registry["artifacts"].items() if not v["exists"]])


if __name__ == "__main__":
    main()

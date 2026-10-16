# Chloe's Travelling Tutors — Round 2 Website Improvements

Delivery summary for owner review. Round 2 is a **content and UX change to the
existing site**, applied on top of Round 1. The site was edited in place; it was
not rebuilt.

All verification is machine-checked by `tests/verify_site.py`, whose real output
is captured under `output/evidence/`. The Round 1 summary is kept for reference
in `docs/DELIVERY_SUMMARY_ROUND_1.md`.

---

## Start the local preview

**On Windows: double-click `scripts\preview_windows.bat`.** It serves the site on
your own machine and opens the homepage for you. Nothing is published.

Or from a terminal, on any platform:

```
scripts/serve_preview.sh          # serves the site on http://127.0.0.1:8010
```

Open:

- Homepage:             http://127.0.0.1:8010/index.html
- Tutors page (filter): http://127.0.0.1:8010/tutors.html
- Contact + assessment: http://127.0.0.1:8010/contact.html
- Blog:                 http://127.0.0.1:8010/blog.html

Full instructions are in `docs/PREVIEW.md`.

---

## Every change, mapped to the Round 2 notes

### 1. Homepage — the quote now opens the page

- The hero leads with the quote **“If a child can't learn the way *we teach*,
  maybe *we* should teach the way *they learn*.”** attributed to **Ignacio
  Estrada**, followed by the two existing buttons.
- The Round 1 hero content is gone: the eyebrow pill (“Personal, one-to-one
  tutoring”), the headline (“Every child can thrive with the right support”), the
  supporting paragraph and the **three-point reassurance strip** are all removed.
- The separate quote section further down the page is removed too — the quote is
  now the opening, so repeating it would be duplication.
- Because the visible headline is gone, the page would have shipped with no
  `<h1>` at all. A screen-reader-only `<h1>` ("Chloe's Travelling Tutors —
  personalised tutoring") was added for accessibility; it is clipped to 1×1px and
  does not affect the design. Check `R2-05` asserts exactly one `<h1>` exists and
  that its rendered box is 1×1px.

### 2. Homepage — main picture smaller, background cropped

- The homepage picture is now **`images/hero_study_crop.jpeg`**: the two people,
  with the empty background cut away.
- **It is a crop of the site's own existing photo, not a new photograph.** It was
  cropped from `images/index_open_image.jpeg` at offset (300, 392), and is
  smaller than the source in both dimensions. Machine-checked:
  `work/verify_hero_crop.py` re-finds that offset by search and reports a mean
  absolute pixel difference of **1.268** (JPEG compression noise), recorded in
  `output/evidence/hero_crop_provenance.json`.
- The original `images/index_open_image.jpeg` is left on disk untouched, so this
  is reversible.

### 3. Homepage — final section order

Verified against the rendered DOM:

1. Hero — picture and quote — `#home`
2. Meet the tutors — `#featuredTutors`
3. Getting started is easy! — `.ctt-start-section`
4. Every child learns differently — `.ctt-learning-box`
5. Footer

**Round 3: the "How CTT started" section was removed** at the owner's request. Its
markup, its inline CSS (`.ctt-chloe-section`, `.ctt-story-highlight`) and the
now-unused `.ctt-about-image` rules in `assets/css/ctt-custom.css` are all gone.
The founder photo `images/Chloe_image.jpeg` is left on disk untouched, so the
change is reversible. Harness checks `how_started_gone` and `AC-07` cover this.

### 4. Meet the tutors — corrections to Chloe's listing

- Chloe Smith's grades now read exactly **“All subjects, Grades 1 to 8”**. The
  older entry mentioned Grade 7 and 8 twice in two forms ("All primary school
  subjects" *and* "Grade 7 and 8 support"); the duplicate is gone.

### 5. Contact page — preferred tutor is a drop-down

- `Preferred Tutor, if any` is now a `<select>` instead of a free-text field.
- The options are **built from the tutor roster at load time**, never hard-coded,
  so a tutor added or renamed later appears automatically. Rendered check:
  **17 options = 16 tutors + 1 "No preference" placeholder**, and the option list
  matches the roster exactly.
- A `?tutor=` link still preselects the right person, but only if that name is
  really in the roster.

### 6. Tutor roster — additions and removals

The roster grew from 12 to **16** tutors.

| City list | Change |
| --- | --- |
| Joburg | Added **Chloe Smith**, **Megan Meyer**, **Sabreen Limbada** |
| Durban | Added **Caleb Ross**, **Swasthi Prahalad**, put **Nicole Vermeulen** in |
| Durban | Removed **Alex Smith**, **Chloe Smith**, **Kirsten Snyman** |
| Cape Town | Added **Priyal Daya** |

- Each placement is asserted against the notes' own city lists, so a tutor struck
  off a city list cannot keep that city's province.
- **The notes' "Caleb chowtee" is Caleb Ross — the same person.** The owner
  confirmed this and asked that he always be called **Caleb Ross**. He is listed
  under Durban, as the notes require, and a check asserts no shipped file uses
  the other name.
- **Isabella Stubbs** was already in the Round 1 roster and remains; she was not
  named in the notes' city lists, so her province is unchanged.

### 7. New tutor photos

Five new photos are in place and referenced: **Sabreen Limbada, Swasthi
Prahalad, Caleb Ross, Isabella Stubbs, Priyal Daya**. The check asserts each file
exists on disk *and* is referenced by a record, so an orphaned image fails as
reliably as a missing one.

### 8. Blog — filter removed, three placeholders

- The filter UI is gone from `blog.html` (no filter panel in the source and no
  filter controls in the rendered DOM).
- Exactly **three blog placeholders** remain for the owner to fill in.
- A duplicate closing `</script>` tag left behind by the filter removal was fixed.

### 9. Two harness fixes found while reviewing the evidence

- **The contact screenshot did not show what it claimed.** The capture was
  4000px tall but the completed assessment result sits at ~4371px on a 1400px
  viewport, so the image stopped mid-questionnaire and never showed the
  "Learning preferences summary". The frame is now 5200px, and check `AC-24b`
  measures where the result actually lands in the same viewport and fails if it
  falls outside the captured frame — so this cannot silently regress.
- **The homepage had no `<h1>`.** Round 1's headline was the page's only one, and
  Round 2 removed it in favour of the quote. A visually hidden `<h1>` was added
  and `R2-05` asserts exactly one exists with a 1×1px clipped box.

---

## Explicit result counts

Rendered on `tutors.html` after the Round 2 roster change:

| Filter | Tutors |
| --- | --- |
| All (default) | 16 |
| Gauteng | 7 |
| KwaZulu-Natal | 6 |
| Western Cape | 3 |
| Online lessons only | 13 |

The filter behaviour itself is unchanged from Round 1 (deterministic province
derivation, multi-province tutors never dropped, empty state, `#<slug>` anchors
intact, Clear filters resets).

---

## Evidence index

All under `output/evidence/`:

| File | What it proves |
| --- | --- |
| `harness_results.json` | Full machine-readable harness output (data, wording, HTTP, DOM, console, screenshots, and the `contact_result` measurement proving the contact capture includes the result) |
| `harness_log.txt` | Human-readable PASS/FAIL log, all checks |
| `hero_crop_provenance.json` | The homepage photo is a crop of the site's own image (offset, sizes, pixel difference) |
| `01_homepage_hero.png` | Homepage hero: the quote leading the page |
| `01_homepage_full.png` | Full homepage showing the new section order |
| `02_tutors_filter.png` | Tutors page: filter in use |
| `03_contact_assessment.png` | Contact form: assessment completed, with the "Learning preferences summary" result visible at the foot of the page |

Run the harness yourself:

```
python3 tests/verify_site.py --port 8020 --probe-port 8021
```

Last run: **30 checks, 0 failures.** (Round 3 raises this to 31 with `AC-25` re-pointed at the live site.)

---

## NOT done (and why)

1. **Blog posts.** The notes say Chloe will send blog content and that the three
   placeholders are for the owner to fill. Nothing was written on her behalf.

---

## Publishing

The original brief asked for local-only work with the production `main` left
untouched. **The owner overrode that** and asked for the work to go live, so it was
published:

- Round 2 shipped as PR [#1](https://github.com/MatthewMBowyer/Chloes-Traveling-tutors/pull/1),
  merged to `main` as `a7c19fdd`.
- The local repository is **not a clone** — its `main` shares no history with
  upstream, so it cannot be pushed directly. Publishing is done by cloning
  upstream, laying the deliverable files onto a branch cut from `origin/main`,
  and pushing that. See `AGENTS.md`.
- `.supervisor/` (agent state) and `inputs/` (source material) are **never**
  published.
- Work continues on the local branch **`feature/round-1-improvements`**, which
  still has **no remote configured** (`git remote -v` is empty).

Nothing else is unfinished. No fabricated evidence or fabricated photo appears in
this summary or in the evidence files.

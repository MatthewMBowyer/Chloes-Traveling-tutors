# AGENTS.md — CTT website (Round 2)

## What this project is
A static HTML/CSS/JS site (Chloe's Travelling Tutors) improved in place for the
owner's Round 1 and Round 2 content and UX changes. No build step; no framework.

Round 2 source of truth is the notes file recovered at
`/tmp/ctt_fixes/CTT fixes/Notes.txt` plus the five tutor photos beside it. That
path is outside the repo and not guaranteed to survive, so the checks in
`tests/verify_site.py` (`ROUND2_PROVINCE_PLACEMENT`, `ROUND2_ADDED_SLUGS`,
`ROUND2_NEW_PHOTOS`, `EXPECTED_TUTOR_COUNT`) are the durable record of what was
asked for.

## Hard constraints
- The site is **production-live** from `main` via GitHub Pages
  (`https://matthewmbowyer.github.io/Chloes-Traveling-tutors/`, source `main` at `/`).
  Merging to `main` publishes to the public site. The owner has explicitly asked for
  changes to go live, so the path is: push a branch, open a PR, merge it. Never
  force-push `main`.
- Work stays on the local branch `feature/round-1-improvements`. The local repo
  has **no remote configured** on purpose.
- **The local repo is not a clone, so it cannot be pushed.** Local `main` (`72ed3eb`)
  shares no history with upstream `main`; a push is rejected and a PR has no common
  ancestor. To publish: clone upstream into a temp dir, copy the deliverable files onto
  a branch cut from `origin/main`, and push that. Local `main`'s content is
  byte-identical to upstream except for `.supervisor/` and `inputs/`, which are local
  only and must not be published.
- Round 2 was published this way: PR #1, merge commit `a7c19fdd` on `main`.
- Round 3: PR #2, merge commit `933d018`.
- **Shipping gotcha that already bit once.** Build the file list from
  `git diff --name-status main -- . ':!.supervisor' ':!inputs' ':!ctt_verify_probe'`,
  NOT from `git status`. Round 2 shipped uncommitted changes only, so every file
  already committed on the feature branch was silently left out — including
  `tutors.html` and `assets/js/render-tutors.js` — and the tutor filter never
  reached the live site. Always diff against `main`, then confirm the pushed
  branch contains the files you expect (`git show :<path>`).
- Treat `inputs/` as immutable; write derived files under `work/` or the project
  output dirs.
- Never fabricate a photograph. When asked to change an image, crop or re-frame
  the site's own existing file and prove the provenance — see
  `work/verify_hero_crop.py`.

## Layout
- `index.html`, `tutors.html`, `contact.html`, `blog.html` — pages (edited in place)
- `assets/data/tutors.js` — `window.CTT_TUTORS` array; each record carries an
  explicit `province` array and a boolean `online` flag (plus the retained
  `availability` field). Areas→province mapping: `work/build_tutors_data.py`.
- `assets/js/render-tutors.js` — `window.CTTRender`, a pure module exposing
  `provinceOptions`, `filterTutors`, `createDirectoryCard`, `renderDirectory`,
  `renderFeatured`. Used by both the pages and the tests.
- `assets/css/ctt-custom.css` — palette variables (`--ctt-blue` etc.) and all
  custom classes.

## Commands
- Verify everything: `python3 tests/verify_site.py --port 8020 --probe-port 8021`
  (starts its own servers, writes `output/evidence/`).
- Preview: `scripts/serve_preview.sh` (default port 8010).
- Regenerate data/HTML/CSS patches: `work/*.py`, `work/gen_corpus_quality.js`.
- Bookkeeping: `python3 work/write_bookkeeping.py`.

## Notes
- Playwright is not installed; rendered-DOM and screenshot checks use headless
  Chromium (`--dump-dom` / `--screenshot`) against a throwaway copy in `/tmp`,
  never `file://` and never against the real deliverables.
- AC-24 screenshot evidence is content-based: `png_stats()` decodes the captured
  PNG bytes and asserts the exact viewport size and >=200 distinct colours, so a
  blank/placeholder capture fails. It does not merely check for a file.
- Screenshot colour counts vary run to run (font rasterisation); only the
  >=200-colour floor is asserted. Re-running the harness rewrites
  `output/evidence/*.png`, so re-run `work/write_bookkeeping.py` and commit both
  together, otherwise the ledger's AC-24 provenance drifts from the on-disk PNGs.
- **Screenshots are not the real site in one respect:** `--screenshot` needs a
  fixed window, and the full-homepage capture uses 1400x5200, which is
  *portrait*-shaped. That flips the template's `@media (orientation: portrait)`
  banner rules (content and image each 50vh, hero stacks), so the hero alone
  would fill the frame and hide every later section — the capture then looks
  blank below the fold while the site is fine. `screenshot()` takes an
  `extra_style` argument and the full-homepage capture uses it to pin the
  landscape hero. If a full-page shot ever goes blank again, suspect this before
  suspecting the page.

## Known contract contradiction
AC-06/INV-05 ask for both "12 items" and "4 per style" (4×4=16). The delivered
assessment is 12 items balanced 3 per style, matching the pre-existing site and
the authoritative raw request ("keep the number of questions and per-style
balance"). Documented in `docs/DELIVERY_SUMMARY.md`.

## Round 2 naming decision (resolved by the owner)
The notes list "Caleb chowtee" for Durban. The owner confirmed that is **Caleb
Ross** — the same person — and that he is **always to be called Caleb Ross**. He
is the tutor listed under Durban. Never ship the other name; `R2-06` greps every
shipped `.html`/`.js`/`.css` for it and also asserts `caleb-ross` is
KwaZulu-Natal. The docs, tests and `work/` scripts are excluded from that grep
because they legitimately quote the notes.

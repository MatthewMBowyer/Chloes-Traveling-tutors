# AGENTS.md ŌĆö CTT website (Round 2)

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
- Round 3: PR #2, merge commit `933d018` (hidden blog, then SEO/crawl files and
  the shrinking header, PRs #3/#4).
- Round 4: PR #5, the Google Sheet enquiry endpoint. The custom domain
  `chloestravellingtutors.com` now serves `main`, so the
  `matthewmbowyer.github.io/Chloes-Traveling-tutors/` URLs redirect to it; both
  work when checking what is live.
- Round 5: the two Round 2 items that had been missed — the trimmed tutor
  profile copy (Swasthi, Isabella, Caleb, Priyal) and the duplicated grade
  range on the cards. `docs/DELIVERY_SUMMARY_ROUND_5.md` and
  `docs/ROUND_2_NOTES_CHECKLIST.md`.
- **A "fix" is not done until the rendered page is checked, not just the source.**
  Round 2's grade-wording fix passed every source-level assertion while Chloe's
  card still read "All subjects, Grades 1 to 8" followed by "Grades 1 to 8" —
  the exact repeat the owner complained about. Source grep cannot see a card
  that is assembled by JavaScript. Checks `R2-07` and `R2-08` read the rendered
  DOM for this reason.
- **The owner's own photos and profile text are pinned in the harness.**
  `work/verify_tutor_photos.py` compares each site photo against the file in the
  owner's pack (mean absolute pixel difference, not a hash, because the site
  files were re-encoded). `ROUND2_SUPPLIED_COPY` in `tests/verify_site.py` holds
  the supplied sentences verbatim, so a later edit that trims them fails.
- **Correct publishing procedure for the current repo state.** `git diff main`
  in this repo is NOT the Round-3/4 change list: local `main` is the pre-Round-1
  template, so it lists every round at once, and the Round 3/4 work is
  uncommitted anyway. Build the change set from the tree instead:
  ```
  cd /tmp/ctt_upstream && git fetch origin --prune
  git checkout -B round-N-<slug> origin/main
  python3 /tmp/sync_publish.py          # copies the project tree, minus .git/.supervisor/inputs
  git status --short                    # this is the real change set
  ```
  then commit, push, `gh pr create --base main`, and `gh pr merge <n> --merge
  --delete-branch`. Before committing, confirm the list holds only intended
  files and that `.supervisor/`, `inputs/` and the temp sync scripts are absent.
  `gh` is authenticated as the owner, which is how the merges appear on GitHub.
- **The local repo's HEAD is deliberately left at the pristine template** (the
  working tree carries every round, uncommitted). `work/apply_round3_seo.py`
  then `work/apply_round4_enquiry.py` restore-and-reapply in that order, and both
  refuse to run twice: `git checkout -- index.html tutors.html contact.html`
  gives back the pages the generators expect. Committing those three pages here
  without rewriting the generators breaks that chain.
- **Shipping gotcha that already bit once.** Build the file list from
  `git diff --name-status main -- . ':!.supervisor' ':!inputs' ':!ctt_verify_probe'`,
  NOT from `git status`. Round 2 shipped uncommitted changes only, so every file
  already committed on the feature branch was silently left out ŌĆö including
  `tutors.html` and `assets/js/render-tutors.js` ŌĆö and the tutor filter never
  reached the live site. Always diff against `main`, then confirm the pushed
  branch contains the files you expect (`git show :<path>`).
- Treat `inputs/` as immutable; write derived files under `work/` or the project
  output dirs.
- Never fabricate a photograph. When asked to change an image, crop or re-frame
  the site's own existing file and prove the provenance ŌĆö see
  `work/verify_hero_crop.py`.

## Layout
- `index.html`, `tutors.html`, `contact.html`, `blog.html` ŌĆö pages (edited in place)
- `assets/data/tutors.js` ŌĆö `window.CTT_TUTORS` array; each record carries an
  explicit `province` array and a boolean `online` flag (plus the retained
  `availability` field). AreasŌåÆprovince mapping: `work/build_tutors_data.py`.
- `assets/js/render-tutors.js` ŌĆö `window.CTTRender`, a pure module exposing
  `provinceOptions`, `filterTutors`, `createDirectoryCard`, `renderDirectory`,
  `renderFeatured`. Used by both the pages and the tests.
- `assets/css/ctt-custom.css` ŌĆö palette variables (`--ctt-blue` etc.) and all
  custom classes.
- `assets/js/ctt-enquiry.js` Ś posts one enquiry row to the owner's Google Sheet
  (sendBeacon, `mode: "no-cors"` fetch fallback) before the form opens WhatsApp.
  The endpoint is the single `var ENDPOINT = ""` constant;
  `window.CTT_ENQUIRY_ENDPOINT` overrides it, which is how R4-02 tests the send
  path without touching a real sheet.
- `apps-script/enquiry-to-sheet.gs` Ś the Apps Script web app that appends the
  row. Bound to its own spreadsheet (no id, no secret in the repo). Its `FIELDS`
  list must equal the keys contact.html sends; R4-01 compares the two lists and
  fails on drift. Owner setup: `docs/ENQUIRY_FORM_SETUP.md`. **Until the owner
  deploys it and pastes the `/exec` URL, an enquiry is only ever delivered by
  WhatsApp, and the console says a row was skipped** Ś that is the expected state
  until they follow the doc, not a bug.
- `work/apply_round3_seo.py`, `work/make_og_image.py`,
  `work/apply_round4_enquiry.py` Ś generators for the Round 3 search content and
  the Round 4 enquiry wiring. Each refuses to run twice; see the publishing notes
  above for the restore-and-reapply order.

## Commands
- Verify everything: `python3 tests/verify_site.py --port 8020 --probe-port 8021`
  (starts its own servers, writes `output/evidence/`).
- Preview: `scripts/serve_preview.sh` (default port 8010).
- Regenerate data/HTML/CSS patches: `work/*.py`, `work/gen_corpus_quality.js`.
- Bookkeeping: `python3 work/write_bookkeeping.py`.

## Notes
- Round 3 and Round 4 added checks: R3-02..R3-06 (head metadata, JSON-LD, roster
  copy, robots/sitemap, shrinking header) and R4-01/R4-02 (enquiry source agrees
  with the Apps Script; a real submit in a browser posts every field and opens
  the unchanged WhatsApp message). Full suite is 38 checks.
- R4-02 stubs `navigator.sendBeacon`/`fetch`/`window.open` in the probe copy and
  points `window.CTT_ENQUIRY_ENDPOINT` at a fake URL: the real Sheet is in the
  owner's Google account and a test must never write into it. Everything else in
  the path is the shipped code.
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
  would fill the frame and hide every later section ŌĆö the capture then looks
  blank below the fold while the site is fine. `screenshot()` takes an
  `extra_style` argument and the full-homepage capture uses it to pin the
  landscape hero. If a full-page shot ever goes blank again, suspect this before
  suspecting the page.

## Known contract contradiction
AC-06/INV-05 ask for both "12 items" and "4 per style" (4├Ś4=16). The delivered
assessment is 12 items balanced 3 per style, matching the pre-existing site and
the authoritative raw request ("keep the number of questions and per-style
balance"). Documented in `docs/DELIVERY_SUMMARY.md`.

## Round 2 naming decision (resolved by the owner)
The notes list "Caleb chowtee" for Durban. The owner confirmed that is **Caleb
Ross** ŌĆö the same person ŌĆö and that he is **always to be called Caleb Ross**. He
is the tutor listed under Durban. Never ship the other name; `R2-06` greps every
shipped `.html`/`.js`/`.css` for it and also asserts `caleb-ross` is
KwaZulu-Natal. The docs, tests and `work/` scripts are excluded from that grep
because they legitimately quote the notes.

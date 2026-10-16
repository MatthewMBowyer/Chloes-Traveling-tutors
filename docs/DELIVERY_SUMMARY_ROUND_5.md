# Round 5 — the two fixes that had been missed

You were right that some things from "CTT fixes.zip" had not landed. Two had
not. Both are now fixed, and both now have an automatic check so they cannot
slip again.

**1. Chloe's grade range was printed twice.** Your note said *"my stuff is
listed weird, grade 7 and 8 talked about twice, rather say 'All subjects grades
1-8'."* The subjects line was changed as you asked, but then her card read
"All subjects, Grades 1 to 8" with "Grades 1 to 8" on the next line — the same
repeat you were pointing at. A tutor's grade range now appears once per card,
on the home page and on the tutor page.

**2. Some of the tutor profiles had been shortened.** The full profiles you
sent were trimmed when they were written onto the site. Restored:

- Swasthi — her full opening ("Experienced educator with five years' teaching
  experience…"), her grade range detail, the "5 Years' Experience" tag, and her
  closing paragraph ("education is about more than just improving marks").
- Isabella — her closing line about golden retrievers.
- Caleb — "with experience supporting over 250 students".
- Priyal — "Qualified educator with … passionate about making learning engaging
  and accessible".

The five photos are unchanged and were re-checked against your own files: each
site photo matches the one you sent, pixel for pixel after resizing.

Everything else in the notes pack was already in place. `docs/ROUND_2_NOTES_CHECKLIST.md`
lists every line of `Notes.txt` against the site and the check that holds it.

## Verification

`python3 tests/verify_site.py` — **40 checks, 0 failures**, including two new
ones: `R2-07` (supplied profile copy on the site) and `R2-08` (grade range
printed once per card, read from the rendered pages).

## Files changed this round

| File | Change |
| --- | --- |
| `assets/data/tutors.js` | Swasthi, Isabella, Caleb and Priyal copy restored |
| `assets/js/render-tutors.js` | Cards print the grade range once |
| `tests/verify_site.py` | `R2-07` and `R2-08` added |
| `docs/ROUND_2_NOTES_CHECKLIST.md` | New — every notes item against the site |
| `work/apply_round5_notes_fixes.py` | New — the patch, safe to re-run |
| `work/verify_tutor_photos.py` | New — proves the photos are yours |

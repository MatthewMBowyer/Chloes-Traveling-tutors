# Chloe's Travelling Tutors — Rounds 3 and 4

Short summary for owner review. Round 3 was the search and mobile-header notes;
Round 4 was the enquiry form. Both are **live** on the site. The Round 1 and
Round 2 summaries are kept in `docs/DELIVERY_SUMMARY_ROUND_1.md` and
`docs/DELIVERY_SUMMARY.md`.

Everything here is machine-checked by `tests/verify_site.py`, whose real output
is captured under `output/evidence/`. Full suite: **38 checks, 0 failures**.

---

## Round 3 — found in search, and a header that gets out of the way

- The blog page is hidden from the menu (done first, on its own).
- Each public page now has its own title, description, canonical link and
  social-share preview, all inside Google's length limits. A share image is
  included, so a link posted to WhatsApp shows a picture instead of a blank box.
- Search engines are told what the business is, where it works and what it
  teaches, and the homepage now carries plain readable copy about the subjects,
  grades, areas and common questions. Every one of those details is generated
  from the tutor list, so the page cannot claim a tutor or an area the site does
  not have.
- `robots.txt` and `sitemap.xml` were added. The hidden blog is kept out of the
  sitemap but is still readable by crawlers, so it can be un-hidden later without
  losing its history.
- On a phone, the header now sticks to the top and shrinks when you scroll, then
  returns to full size at the top. It gives back about 40% of its height.

## Round 4 — every enquiry saved, not just sent

The form already opened WhatsApp with the full message. Now the same enquiry is
also written as a row in a Google Sheet, before WhatsApp opens, so there is a
searchable record of who asked for what.

Each row holds: the time, parent or guardian, phone, email, learner, grade,
subject, lesson type, area, preferred tutor, message, the assessment scores and
strongest and second-strongest learning preference, and which page it came from.

**One step is yours, and it takes about five minutes:** create the Google Sheet
and publish the script that fills it. Step-by-step instructions, including what
to click and how to check it worked, are in `docs/ENQUIRY_FORM_SETUP.md`.

Until that is done the form behaves exactly as it did before — the enquiry still
arrives on WhatsApp, nothing is lost, and no error is shown to a parent.

## Check it yourself

Nothing is needed from a terminal. On Windows, double-click
`scripts\preview_windows.bat` in this folder: it serves the site on your own
machine and opens the homepage in your browser. Close the window to stop it.

The live site is <https://chloestravellingtutors.com/>.

Published as PR
[#4](https://github.com/MatthewMBowyer/Chloes-Traveling-tutors/pull/4) and PR
[#5](https://github.com/MatthewMBowyer/Chloes-Traveling-tutors/pull/5), both
merged to `main`, which is what the live site serves.

No fabricated evidence or photograph appears in this summary or in the evidence
files.

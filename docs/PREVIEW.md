# Local preview — Chloe's Travelling Tutors (Round 2)

This is a **local preview only**. Nothing has been published. The site is served
straight from this project workspace; no build step is involved.

## On Windows (double-click)

Double-click **`scripts\preview_windows.bat`**.

It serves the folder on your own machine and opens the homepage in your browser
at `http://127.0.0.1:8010/index.html`. Close the window (or press `Ctrl+C`) to
stop it. It needs Python on your PC — if it isn't installed the script says so
and links you to the download.

## On Mac or Linux, or by hand

From the project root:

```
scripts/serve_preview.sh
```

That serves the site at **http://127.0.0.1:8010** using Python's built-in HTTP
server. To use a different port:

```
scripts/serve_preview.sh 8085
```

Stop it with `Ctrl+C`.

Or without the script:

```
python3 -m http.server 8010 --bind 127.0.0.1
```

## Open these pages

| Page | URL | What to look at |
| --- | --- | --- |
| Homepage | http://127.0.0.1:8010/index.html | The **quote now opens the page**, with the smaller cropped picture beside it. Then **Meet our tutors**, **Getting started**, **Every child learns differently** |
| Tutors page | http://127.0.0.1:8010/tutors.html | The 16-tutor roster with the new people (Chloe, Megan Meyer, Sabreen, Caleb, Swasthi, Priyal), and the **Province / Online** filter. Try Gauteng, then tick "Online lessons only" to see the intersection; click **Clear filters** to reset |
| Contact | http://127.0.0.1:8010/contact.html | **Preferred Tutor** as a drop-down listing every tutor. Tick "Complete assessment", answer all 12 questions, and the learning-preferences summary appears |
| Blog | http://127.0.0.1:8010/blog.html | **Hidden from the navigation (Round 3).** Direct URL only. The filter is gone; **three placeholders** remain for you to fill in |

## What you should NOT see

- Nothing above the opening quote — no headline, no "Personal, one-to-one
  tutoring" pill, no three-point strip.
- No separate quote section further down the homepage; the quote opens the page.
- No blog filter panel.
- No "Availability" day/time on any tutor card or featured card.
- Lize Blom, Jenna Germanus and Lieze van der Westhuizen appear nowhere.

## Notes

- The pages fetch their header and footer fragments over HTTP, so please use the
  served URL (above), not a `file://` path.
- The homepage picture is a **crop of the existing site photo**, not a new one —
  see `output/evidence/hero_crop_provenance.json`.
- Full details of every change are in `docs/DELIVERY_SUMMARY.md`; the Round 1
  summary is in `docs/DELIVERY_SUMMARY_ROUND_1.md`.

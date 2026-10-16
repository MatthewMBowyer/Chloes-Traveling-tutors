# Round 2 notes — checked line by line

Every line of `CTT fixes/Notes.txt` from the owner's pack, with where it now
stands on the site and which check holds it. Written after the owner reported
that fixes had been missed; two of them had been: the tutor profile copy was
shortened when it was written into the roster, and the homepage cards printed a
tutor's grade range twice (the exact thing the notes complain about). Both are
fixed and both now have a check.

Checks run with `python3 tests/verify_site.py`. Suite: **40 checks, 0 failures.**

## Home page

| Note | Now | Check |
| --- | --- | --- |
| "Change the opening line to the quote." | The hero's first line is the Ignacio Estrada quote, above the buttons, with no headline above it. | `R2` wording: `hero_quote_leads`, `hero_quote_before_actions` |
| "Take out the extra info from warm…" | The Round 1 headline, eyebrow pill and warm supporting paragraph are gone from the source. | `hero_old_headline_gone`, `hero_old_eyebrow_gone`, `hero_old_body_gone` |
| "The main picture needs to be smaller cut out the tip background. Waistibg space" | Hero uses `images/hero_study_crop.jpeg`, a crop of the site's own photo with the background trimmed; no band of background at any edge. | `hero_crop_image`, `hero_old_image_gone`; provenance in `output/evidence/hero_crop_provenance.json` |
| "And take out those 3 points" | The three-point reassurance strip added in Round 1 is gone (`.ctt-hero-points` appears nowhere). | `hero_points_gone` |
| Layout: picture and quote / meet the tutors / getting started / every child learns differently | Rendered section order is exactly that; the search copy and FAQ sit after them. | `AC-20` |
| "my stuff is listed weird, grade 7 and 8 talked about twice rather say. All subjects grades 1-8." | The subjects line reads "All subjects, Grades 1 to 8" and the grade range is printed once per card, not twice. The old two-part grade wording is gone. | `grades_wording_exact`, `grades_old_gone`, `R2-08` |

## Contact page

| Note | Now | Check |
| --- | --- | --- |
| "make the preferred tutor a drop down" | `#preferredTutor` is a `<select>` populated from the roster: 16 tutors plus a "No preference" placeholder. | `R2-02`, `preferred_tutor_is_select`, `preferred_tutor_from_roster` |

## Tutor lists

| Note | Now | Check |
| --- | --- | --- |
| Joburg: add Chloe, Megan Meyer, Sabreen (needs pic) | All three are listed under Gauteng; Sabreen has the photo Chloe sent. | `AC-13`, `R2-01`, `R2-04` |
| Durban: Alex, Chloe and Kirsten should not be there | All three are Gauteng, not KwaZulu-Natal. | `AC-13` |
| Durban: add Caleb chowtee | Added as **Caleb Ross** under KwaZulu-Natal. The owner confirmed the two names are one person; the alias appears in no shipped file. | `R2-01`, `R2-06`, `AC-13` |
| Durban: Nicole needs to be here | Nicole Vermeulen is listed under KwaZulu-Natal. | `AC-13` |
| Durban: add Swashti Prahalad | Added as Swasthi Prahalad under KwaZulu-Natal. | `R2-01`, `AC-13` |
| Cape Town: add Priyal Daya | Added under the Western Cape. | `R2-01`, `AC-13` |

## Supplied profile copy and photos

| Note | Now | Check |
| --- | --- | --- |
| Full profiles for Swasthi, Isabella, Caleb and Priyal | Every supplied line is on the site: Swasthi's lead-in, grade detail, "5 Years' Experience", closing paragraph; Isabella's closing line; Caleb's and Priyal's lead-ins. The shortened Round 2 variants are gone. | `R2-07` |
| "Chloe will send stuff for … Sabreen pix" | Five photos are in place and referenced. Each was proven against the owner's own file rather than taken on trust: normalised to a common size, the mean absolute pixel difference from the supplied photo is under 1.1 out of 255. | `R2-04`; `work/verify_tutor_photos.py` |
| "Blogs" | Three blog placeholders, ready for Chloe to fill in. | `blog_three_placeholders` |

## Blog

| Note | Now | Check |
| --- | --- | --- |
| "Take out blog filter - only have 3 blog placeholders I'll add" | The filter panel and its layout are gone from the source and the rendered page; three cards remain, each with an image placeholder. The page is also hidden from the menu, as asked later. | `blog_filter_gone`, `R2-03`, `R3-01` |

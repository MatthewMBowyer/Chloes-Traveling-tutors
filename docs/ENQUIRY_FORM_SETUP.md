# Enquiry form → Google Sheet

Every enquiry already opens WhatsApp with the full message. This adds a second
copy of the same enquiry as a row in a Google Sheet, so you have a searchable
record of who asked for what and when.

Two parts:

1. a small script inside a Google Sheet that accepts a row (one-time setup,
   about five minutes, done once on the site's behalf);
2. the website, which posts the row before it opens WhatsApp. That part is
   already built and live; it does nothing until you paste the URL in step 5.

## One-time setup

1. Create the spreadsheet: go to <https://sheets.new>. Name it something like
   `CTT enquiries`.
2. In that sheet, open **Extensions → Apps Script**. A code editor opens with a
   placeholder function in it.
3. Select everything in the editor, delete it, and paste the whole contents of
   `apps-script/enquiry-to-sheet.gs` from this project. Click the save icon.
4. Click **Deploy → New deployment**. Choose type **Web app**, and set:
   - **Description**: `Enquiry endpoint`
   - **Execute as**: `Me`
   - **Who has access**: `Anyone`

   Click **Deploy**. Google will ask you to authorise: **Authorise access**,
   pick your account, then **Advanced → Go to … (unsafe)** and **Allow**. The
   "unsafe" wording is normal for a script Google has not reviewed; you wrote
   it, and it only appends rows to your own sheet.
5. Copy the **Web app URL** — it ends in `/exec` — and paste it into
   `assets/js/ctt-enquiry.js`, on the `var ENDPOINT = "";` line, between the
   quotes. It looks like
   `https://script.google.com/macros/s/AKfycb.../exec`.
6. Commit and publish that change the usual way, so the live site picks it up.

Until step 5 is done, enquiries still arrive by WhatsApp exactly as before, and
the browser console logs `no Google Sheet endpoint configured` when someone
submits.

## Checking it works

1. Paste the URL into a browser. You should see
   `CTT enquiry endpoint is live. Submissions will appear in this sheet.`
   That confirms the deployment is public and reachable.
2. Submit the contact form with a test enquiry. WhatsApp should open as usual,
   and within a few seconds a row should appear in the sheet, with the time,
   every field you filled in, and the learning-preference scores if you
   completed the assessment.
3. Delete the test row.

## If rows do not appear

- **Nothing at all, console says no endpoint configured** — step 5 was not
  published, or the URL was pasted outside the quotes.
- **Nothing at all, no console message** — check the URL ends in `/exec`, not
  `/dev`. `/dev` only works while you are signed in to Google.
- **The browser shows "Web app is not available"** — step 4 was deployed with
  **Who has access** set to something other than `Anyone`, or the deployment
  was not re-published after an edit.
- **You cannot read the reply in the browser console** — expected. The request
  is cross-origin, so the page cannot read the response. The Sheet is the
  confirmation.

## Notes

- The columns are fixed by `FIELDS` in `apps-script/enquiry-to-sheet.gs`. The
  website sends exactly those keys, and the test suite fails if the two lists
  drift apart, so a row can never silently lose a column.
- Field values are treated as text and truncated at 500 characters, and a value
  beginning with `=`, `+`, `-` or `@` is prefixed with an apostrophe, so a
  submission cannot make the sheet run it as a formula.
- The sheet holds parents' names, phone numbers and emails. Keep it private:
  don't share the sheet outside the business, and don't publish the endpoint URL
  anywhere except the site.
- The web app URL is not a secret (it is visible in the page source to anyone
  who looks), so the script also refuses submissions with no name and no phone
  number, so automated junk does not pad the sheet.

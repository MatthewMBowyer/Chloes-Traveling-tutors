/**
 * Chloe's Travelling Tutors — form submissions to Google Sheet.
 *
 * This file is not part of the website. It is the script you paste into the
 * Google Sheet that collects submissions. Step-by-step setup, including how to
 * publish the URL the website posts to, is in docs/ENQUIRY_FORM_SETUP.md.
 *
 * The script is bound to its own spreadsheet (Extensions > Apps Script from
 * inside the sheet), so there is no spreadsheet id to keep in this file.
 *
 * It writes three kinds of submission into three tabs of the same spreadsheet:
 *
 *   enquiries           the contact form        -> the first tab, columns unchanged
 *   tutor reviews       the tutor review forms  -> a "Tutor reviews" tab
 *   tutor applications  the Become a Tutor form -> a "Tutor applications" tab
 *
 * The kind is chosen by the single field `recordType`: "review" and
 * "tutorApplication" select the two new tabs, and anything else - including a
 * submission with no recordType at all - is treated as an enquiry, so the
 * contact form keeps working exactly as it always has.
 *
 * Columns are written in the order of the FIELDS list below, after the
 * timestamp. The website sends exactly these keys; tests/verify_site.py (R4-01
 * for the enquiry, R6-09 for all three) fails if the lists ever drift apart.
 */

var FIELDS = [
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
  "assessmentCompleted",
  "strongestPreference",
  "secondaryPreference",
  "visualScore",
  "auditoryScore",
  "readWriteScore",
  "kinestheticScore",
  "sourcePage"
];

var HEADERS = [
  "Submitted at",
  "Parent / Guardian",
  "Phone",
  "Email",
  "Learner",
  "Grade",
  "Subject/s needed",
  "Lesson type",
  "Area",
  "Preferred tutor",
  "Message",
  "Assessment completed",
  "Strongest preference",
  "Secondary preference",
  "Visual score",
  "Auditory score",
  "Read/write score",
  "Kinesthetic score",
  "Sent from"
];

// The single identifying field the script routes on.
var RECORD_TYPE_FIELD = "recordType";

// The tabs the two new kinds are written to. The enquiry tab is the first tab
// of the spreadsheet, exactly where it has always been.
var TAB_REVIEWS = "Tutor reviews";
var TAB_APPLICATIONS = "Tutor applications";

// Tutor reviews: the keys assets/js/ctt-tutor-review.js sends, in this order.
var REVIEW_FIELDS = [
  "recordType",
  "tutorName",
  "tutorSlug",
  "reviewerName",
  "reviewText",
  "rating",
  "sourcePage"
];

var REVIEW_HEADERS = [
  "Submitted at",
  "Record type",
  "Tutor",
  "Tutor slug",
  "Reviewer",
  "Review",
  "Rating",
  "Sent from"
];

// Tutor applications: the keys assets/js/ctt-tutor-application.js sends, in
// this order.
var APPLICATION_FIELDS = [
  "recordType",
  "fullName",
  "email",
  "phone",
  "universityQualification",
  "subjectsToTeach",
  "gradesToTeach",
  "teachingMode",
  "teachingArea",
  "reasonToTeach",
  "otherQuestions",
  "sourcePage"
];

var APPLICATION_HEADERS = [
  "Submitted at",
  "Record type",
  "Full name",
  "Email",
  "Phone",
  "University qualification",
  "Subjects to teach",
  "Grades to teach",
  "Teaching mode",
  "Area",
  "Why they want to teach",
  "Other questions",
  "Sent from"
];

var MAX_LENGTH = 500;

/**
 * Opening the page in a browser is how you confirm the web app is deployed and
 * still reachable from a phone.
 */
function doGet() {
  return ContentService
    .createTextOutput("CTT enquiry endpoint is live. Submissions will appear in this sheet.")
    .setMimeType(ContentService.MimeType.TEXT);
}

/**
 * The website posts one submission here per form and does not wait for or read
 * the reply, so this must never throw: an error would be invisible. A failed
 * write is reported in the log and in the JSON body.
 */
function doPost(e) {
  try {
    var params = readParams_(e);
    var kind = kindOf_(params);

    if (kind === "review") {
      if (!params.reviewerName && !params.reviewText) {
        return reply_({ ok: false, error: "empty submission, nothing written" });
      }
      writeRow_(sheetFor_(TAB_REVIEWS), REVIEW_FIELDS, REVIEW_HEADERS, params);
      return reply_({ ok: true });
    }

    if (kind === "tutorApplication") {
      if (!params.fullName) {
        return reply_({ ok: false, error: "empty submission, nothing written" });
      }
      writeRow_(sheetFor_(TAB_APPLICATIONS), APPLICATION_FIELDS, APPLICATION_HEADERS, params);
      return reply_({ ok: true });
    }

    // No recognised kind, so this is an enquiry, exactly as before. Junk
    // requests (bots, or an empty form) are not worth a row; a real enquiry
    // always has a name and a contact number.
    if (!params.parentName && !params.phone) {
      return reply_({ ok: false, error: "empty submission, nothing written" });
    }

    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    ensureHeaders_(sheet);

    var row = [new Date()];
    for (var i = 0; i < FIELDS.length; i++) {
      row.push(clean_(params[FIELDS[i]]));
    }
    sheet.appendRow(row);

    return reply_({ ok: true });
  } catch (error) {
    console.error("CTT submission failed: " + error);
    return reply_({ ok: false, error: String(error) });
  }
}

/**
 * The single field the script routes on. Only the two new kinds are named;
 * anything else - an enquiry, or a submission with no recordType at all - is an
 * enquiry, so nothing that already works can break.
 */
function kindOf_(params) {
  var recordType = params[RECORD_TYPE_FIELD];
  if (recordType === "review") return "review";
  if (recordType === "tutorApplication") return "tutorApplication";
  return "enquiry";
}

/**
 * The tab a kind belongs to. The two new tabs are created on first use, so the
 * owner never has to add them by hand.
 */
function sheetFor_(name) {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(name);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(name);
  }
  return sheet;
}

/**
 * Append one row, timestamp first, to a tab, writing that tab's header row the
 * first time the tab is used.
 */
function writeRow_(sheet, fields, headers, params) {
  ensureHeaders_(sheet, headers);

  var row = [new Date()];
  for (var i = 0; i < fields.length; i++) {
    row.push(clean_(params[fields[i]]));
  }
  sheet.appendRow(row);
}

/**
 * Form fields arrive in e.parameter for multipart posts. A urlencoded post is
 * parsed too, so the endpoint also works from curl while testing.
 */
function readParams_(e) {
  var params = {};

  if (e && e.parameter) {
    for (var key in e.parameter) {
      params[key] = e.parameter[key];
    }
  }

  if (e && e.postData && /urlencoded/i.test(e.postData.type || "")) {
    String(e.postData.contents).split("&").forEach(function (pair) {
      var split = pair.split("=");
      if (!split[0]) return;
      params[decodeURIComponent(split[0].replace(/\+/g, " "))] =
        decodeURIComponent(split.slice(1).join("=").replace(/\+/g, " "));
    });
  }

  return params;
}

/**
 * A text field in a Sheet is not safe as-is: a value starting with one of
 * = + - @ is treated as a formula, so a submission could make the sheet fetch
 * or reveal data. Prefixing keeps it as plain text.
 */
function clean_(value) {
  if (value === null || value === undefined) return "";

  var text = String(value)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "")
    .substring(0, MAX_LENGTH)
    .trim();

  if (/^[=+\-@\t\r]/.test(text)) {
    text = "'" + text;
  }

  return text;
}

/**
 * Write a header row once per tab. The enquiry tab is the first tab and keeps
 * its original 19 columns; each new tab gets its own header row the first time
 * a row is written to it.
 */
function ensureHeaders_(sheet, headers) {
  headers = headers || HEADERS;
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
  }
}

function reply_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

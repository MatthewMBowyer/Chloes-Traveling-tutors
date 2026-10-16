/**
 * Chloe's Travelling Tutors — enquiry form to Google Sheet.
 *
 * This file is not part of the website. It is the script you paste into the
 * Google Sheet that collects enquiries. Step-by-step setup, including how to
 * publish the URL the website posts to, is in docs/ENQUIRY_FORM_SETUP.md.
 *
 * The script is bound to its own spreadsheet (Extensions > Apps Script from
 * inside the sheet), so there is no spreadsheet id to keep in this file.
 *
 * Columns are written in the order of FIELDS below, after the timestamp. The
 * website sends exactly these keys; tests/verify_site.py (R4-01) fails if the
 * two lists ever drift apart.
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
 * The website posts one multipart form here per enquiry and does not wait for
 * or read the reply, so this must never throw: an error would be invisible.
 * A failed write is reported in the log and in the JSON body.
 */
function doPost(e) {
  try {
    var params = readParams_(e);

    // Junk requests (bots, or an empty form) are not worth a row. A real
    // enquiry always has a name and a contact number.
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
    console.error("CTT enquiry failed: " + error);
    return reply_({ ok: false, error: String(error) });
  }
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

function ensureHeaders_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Submitted at"].concat(HEADERS.slice(1)));
    sheet.setFrozenRows(1);
  }
}

function reply_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

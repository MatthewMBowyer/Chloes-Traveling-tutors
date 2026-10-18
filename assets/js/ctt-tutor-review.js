/**
 * Sends a tutor review to the owner's Google Sheet.
 *
 * A review is a name, the review text and a rating out of five. It travels the
 * same way as an enquiry, through window.CTTEnquiry (assets/js/ctt-enquiry.js),
 * and lands in its own tab of the same sheet. No account, no login, no email.
 *
 * The keys below are the contract with apps-script/enquiry-to-sheet.gs:
 * recordType, tutorName, tutorSlug, reviewerName, reviewText, rating,
 * sourcePage. Keep the two lists in step.
 */
(function () {
	"use strict";

	var NOTE_INVALID = "Please add your name, your review and a rating from 1 to 5.";
	var NOTE_SENT = "Thank you, your review has been sent.";
	var NOTE_FAILED = "Sorry, your review could not be sent just now. Please try again later.";

	function value(form, name) {
		var field = form.querySelector('[name="' + name + '"]');
		return field ? String(field.value || "").trim() : "";
	}

	function recordFor(form) {
		return {
			recordType: "review",
			tutorName: form.getAttribute("data-tutor-name") || "",
			tutorSlug: form.getAttribute("data-tutor-slug") || "",
			reviewerName: value(form, "reviewerName"),
			reviewText: value(form, "reviewText"),
			rating: value(form, "rating"),
			sourcePage: window.location.href
		};
	}

	// The same rule the required attributes express, applied to the record, so it
	// holds even when the submit event is dispatched directly.
	function complete(record) {
		return Boolean(
			record.reviewerName &&
			record.reviewText &&
			/^[1-5]$/.test(record.rating)
		);
	}

	function note(form, message) {
		var element = form.querySelector(".ctt-review-note");
		if (!element) return;
		element.textContent = message;
		element.hidden = false;
	}

	function onReviewSubmit(event) {
		var form = event.target;

		if (!form || !form.classList || !form.classList.contains("ctt-review-form")) {
			return;
		}

		event.preventDefault();

		var record = recordFor(form);

		if (!complete(record)) {
			note(form, NOTE_INVALID);
			return;
		}

		var sent = Boolean(window.CTTEnquiry && window.CTTEnquiry.send(record));

		if (sent) {
			form.reset();
			note(form, NOTE_SENT);
		} else {
			note(form, NOTE_FAILED);
		}
	}

	// The directory is rebuilt on every filter change, so the handler is bound to
	// the document and matches the review form that was actually submitted.
	document.addEventListener("submit", onReviewSubmit);
})();

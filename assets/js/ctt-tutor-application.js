/**
 * Sends a Become a Tutor application to the owner's Google Sheet, then hands it
 * to WhatsApp.
 *
 * The application travels the same way as an enquiry: window.CTTEnquiry
 * (assets/js/ctt-enquiry.js) posts one record to the same Apps Script, and the
 * applicant's own WhatsApp opens with the details prefilled.
 *
 * The keys below are the contract with apps-script/enquiry-to-sheet.gs. The
 * first key is the identifying field the Apps Script routes on, exactly as the
 * tutor review carries recordType "review":
 *
 *   recordType, fullName, email, phone, universityQualification,
 *   subjectsToTeach, gradesToTeach, teachingMode, teachingArea, reasonToTeach,
 *   otherQuestions, sourcePage
 *
 * Keep this list and the Apps Script's in step.
 */
(function () {
	"use strict";

	var WHATSAPP_NUMBER = "27732657260";
	var REQUIRED_NOTE =
		"Please add your name and surname, your university qualification, the " +
		"subjects and grades you teach, where you can teach, and why you want " +
		"to become a tutor.";

	function field(form, name) {
		return form.querySelector('[name="' + name + '"]');
	}

	function value(form, name) {
		var element = field(form, name);
		return element ? String(element.value || "").trim() : "";
	}

	function recordFor(form) {
		return {
			recordType: "tutorApplication",
			fullName: value(form, "fullName"),
			email: value(form, "email"),
			phone: value(form, "phone"),
			universityQualification: value(form, "universityQualification"),
			subjectsToTeach: value(form, "subjectsToTeach"),
			gradesToTeach: value(form, "gradesToTeach"),
			teachingMode: value(form, "teachingMode"),
			teachingArea: value(form, "teachingArea"),
			reasonToTeach: value(form, "reasonToTeach"),
			otherQuestions: value(form, "otherQuestions"),
			sourcePage: window.location.href
		};
	}

	// The same rule the required attributes express, applied to the record, so
	// it holds even when the submit event is dispatched directly.
	function complete(record) {
		return Boolean(
			record.fullName &&
			record.universityQualification &&
			record.subjectsToTeach &&
			record.gradesToTeach &&
			record.teachingMode &&
			record.teachingArea &&
			record.reasonToTeach
		);
	}

	function note(form, message) {
		var element = form.querySelector(".ctt-application-note");
		if (!element) return;
		element.textContent = message;
		element.hidden = false;
	}

	// The same handoff pattern the contact page uses: literal %0A line breaks
	// with each value percent-encoded, handed to wa.me.
	function whatsappMessage(record) {
		return (
			"Hi Chloe's Travelling Tutors,%0A%0A" +
			"I would like to apply to become a tutor.%0A%0A" +
			"Name and surname: " + encodeURIComponent(record.fullName) + "%0A" +
			"Email: " + encodeURIComponent(record.email) + "%0A" +
			"Phone: " + encodeURIComponent(record.phone) + "%0A" +
			"University qualification: " + encodeURIComponent(record.universityQualification) + "%0A" +
			"Subjects I want to teach: " + encodeURIComponent(record.subjectsToTeach) + "%0A" +
			"Grades I want to teach: " + encodeURIComponent(record.gradesToTeach) + "%0A" +
			"Where I can teach: " + encodeURIComponent(record.teachingMode) + "%0A" +
			"Area: " + encodeURIComponent(record.teachingArea) + "%0A%0A" +
			"Why I want to become a tutor:%0A" + encodeURIComponent(record.reasonToTeach) + "%0A%0A" +
			"Any other relevant questions:%0A" + encodeURIComponent(record.otherQuestions || "None provided") + "%0A%0A" +
			"I will send my matric certificate and driver's licence in this chat."
		);
	}

	function onSubmit(event) {
		var form = event.target;

		if (!form || form.id !== "tutorApplicationForm") {
			return;
		}

		event.preventDefault();

		var record = recordFor(form);

		if (!complete(record)) {
			note(form, REQUIRED_NOTE);
			return;
		}

		// The row goes out before WhatsApp opens: on a phone, handing over to
		// the WhatsApp app can background this page, and a row that was not
		// sent yet would be lost. Keys here must match the Apps Script.
		if (window.CTTEnquiry && window.CTTEnquiry.send) {
			window.CTTEnquiry.send(record);
		}

		window.open(
			"https://wa.me/" + WHATSAPP_NUMBER + "?text=" + whatsappMessage(record),
			"_blank",
			"noopener"
		);
	}

	document.addEventListener("submit", onSubmit);
})();

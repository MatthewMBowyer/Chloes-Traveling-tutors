/**
 * Sends each enquiry to the owner's Google Sheet before the WhatsApp handoff.
 *
 * Setup is one paste, once: deploy apps-script/enquiry-to-sheet.gs and put the
 * resulting /exec URL between the quotes below. Full steps, with screenshots
 * of what to click, are in docs/ENQUIRY_FORM_SETUP.md.
 *
 * If ENDPOINT is still empty the enquiry is not lost: the WhatsApp message
 * carries every field, and the browser console says a row was skipped.
 */
(function () {
	// Paste your Apps Script web app URL here, between the quotes. It looks
	// like https://script.google.com/macros/s/AKfycb.../exec
	var ENDPOINT = "";

	function endpoint() {
		// An override is accepted so the page can be pointed at a test endpoint
		// (or a replacement sheet) without editing this file.
		return window.CTT_ENQUIRY_ENDPOINT || ENDPOINT;
	}

	function send(record) {
		var url = endpoint();

		if (!url) {
			console.warn(
				"CTT enquiry: no Google Sheet endpoint configured, row not saved. " +
					"See docs/ENQUIRY_FORM_SETUP.md."
			);
			return false;
		}

		var body = new FormData();

		Object.keys(record).forEach(function (key) {
			body.append(key, record[key] === null || record[key] === undefined ? "" : String(record[key]));
		});

		// Opening WhatsApp can background the browser, so the row is sent with
		// sendBeacon where it exists: the browser delivers it even if the page
		// is discarded. The reply cannot be read either way (the endpoint is
		// cross-origin), so neither path confirms the write.
		try {
			if (navigator.sendBeacon && navigator.sendBeacon(url, body)) {
				return true;
			}
		} catch (error) {
			// Fall through to fetch.
		}

		try {
			fetch(url, { method: "POST", mode: "no-cors", body: body });
			return true;
		} catch (error) {
			console.error("CTT enquiry: could not reach the Google Sheet.", error);
			return false;
		}
	}

	window.CTTEnquiry = { send: send, endpoint: endpoint };
})();

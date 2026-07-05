document.addEventListener("DOMContentLoaded", function () {
	const footerTarget = document.getElementById("site-footer");

	if (!footerTarget) {
		return;
	}

	fetch("footer/footer.html")
		.then(function (response) {
			if (!response.ok) {
				throw new Error("Footer could not be loaded.");
			}

			return response.text();
		})
		.then(function (html) {
			footerTarget.innerHTML = html;
		})
		.catch(function (error) {
			console.error(error);
		});
});

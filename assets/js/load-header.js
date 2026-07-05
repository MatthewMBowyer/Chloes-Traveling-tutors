document.addEventListener("DOMContentLoaded", function () {
	const headerTarget = document.getElementById("site-header");

	if (!headerTarget) {
		return;
	}

	fetch("header/header.html")
		.then(function (response) {
			if (!response.ok) {
				throw new Error("Header could not be loaded.");
			}

			return response.text();
		})
		.then(function (html) {
			headerTarget.innerHTML = html;

			const currentFile = window.location.pathname.split("/").pop() || "index.html";
			const currentPage = currentFile.replace(".html", "");
			const links = headerTarget.querySelectorAll(".ctt-menu a");

			links.forEach(function (link) {
				const href = link.getAttribute("href");

				if (href === currentFile) {
					link.classList.add("active");
				}
			});

			if (currentPage === "index") {
				const homeLink = headerTarget.querySelector('[data-page="index"]');
				if (homeLink) {
					homeLink.classList.add("active");
				}
			}

			if (currentPage === "contact") {
				const contactLink = headerTarget.querySelector('[data-page="contact"]');
				if (contactLink) {
					contactLink.classList.add("active");
				}
			}
		})
		.catch(function (error) {
			console.error(error);
		});
});

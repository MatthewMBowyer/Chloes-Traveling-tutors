document.addEventListener("DOMContentLoaded", function () {
	const headerContainer = document.getElementById("site-header");

	if (!headerContainer) {
		return;
	}

	fetch("header.html")
		.then(function (response) {
			if (!response.ok) {
				throw new Error("Could not load header.html");
			}

			return response.text();
		})
		.then(function (headerHtml) {
			headerContainer.innerHTML = headerHtml;

			setupMobileNavigation();
			setActiveNavigationLink();
		})
		.catch(function (error) {
			console.error("Header loading error:", error);
		});
});

function setupMobileNavigation() {
	const menuToggle = document.getElementById("cttMenuToggle");
	const navigation = document.getElementById("cttNavigation");

	if (!menuToggle || !navigation) {
		return;
	}

	menuToggle.addEventListener("click", function () {
		const menuIsOpen = navigation.classList.toggle("is-open");

		menuToggle.classList.toggle("is-open", menuIsOpen);
		menuToggle.setAttribute("aria-expanded", String(menuIsOpen));
	});

	navigation.querySelectorAll("a").forEach(function (link) {
		link.addEventListener("click", function () {
			navigation.classList.remove("is-open");
			menuToggle.classList.remove("is-open");
			menuToggle.setAttribute("aria-expanded", "false");
		});
	});
}

function setActiveNavigationLink() {
	const currentPage =
		window.location.pathname.split("/").pop() || "index.html";

	document.querySelectorAll(".ctt-navigation a").forEach(function (link) {
		const linkPage = link.getAttribute("href");

		if (linkPage === currentPage) {
			link.classList.add("is-active");
			link.setAttribute("aria-current", "page");
		}
	});
}

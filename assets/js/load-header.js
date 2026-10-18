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
			setupShrinkOnScroll(headerContainer);
		})
		.catch(function (error) {
			console.error("Header loading error:", error);
		});
});

function setupMobileNavigation() {
	const menuToggle = document.getElementById("cttMenuToggle");
	const navigation = document.getElementById("cttNavigation");
	const header = document.querySelector(".ctt-site-header");

	if (!menuToggle || !navigation) {
		return;
	}

	menuToggle.addEventListener("click", function () {
		const menuIsOpen = navigation.classList.toggle("is-open");

		menuToggle.classList.toggle("is-open", menuIsOpen);
		menuToggle.setAttribute("aria-expanded", String(menuIsOpen));

		// The bar holds its full height while the menu is open, so the open
		// links are never clipped by a bar that shrank underneath them.
		if (header) {
			header.classList.toggle("is-menu-open", menuIsOpen);
		}
	});

	navigation.querySelectorAll("a").forEach(function (link) {
		link.addEventListener("click", function () {
			navigation.classList.remove("is-open");
			menuToggle.classList.remove("is-open");
			menuToggle.setAttribute("aria-expanded", "false");

			if (header) {
				header.classList.remove("is-menu-open");
			}
		});
	});
}

// Shrink the bar once the page has scrolled, so a phone screen is not eaten by
// a tall header. Two thresholds give hysteresis, which stops the bar flickering
// between sizes when the page jitters around one scroll position.
const SHRINK_AT = 60;
const EXPAND_AT = 20;

function setupShrinkOnScroll(headerContainer) {
	const header = headerContainer.querySelector(".ctt-site-header");

	if (!header) {
		return;
	}

	// Acting straight in the handler rather than deferring to
	// requestAnimationFrame: browsers already deliver scroll events at most once
	// per frame, and the work here is a single classList toggle, so deferring it
	// would only let the bar lag a frame behind the scroll.
	function update() {
		const y = window.pageYOffset || document.documentElement.scrollTop || 0;
		const isScrolled = header.classList.contains("is-scrolled");

		if (!isScrolled && y > SHRINK_AT) {
			header.classList.add("is-scrolled");
		} else if (isScrolled && y < EXPAND_AT) {
			header.classList.remove("is-scrolled");
		}
	}

	window.addEventListener("scroll", update, { passive: true });
	window.addEventListener("resize", update, { passive: true });

	// The page can load already scrolled (a refresh or a back navigation), so
	// run once instead of waiting for the first scroll event.
	update();
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

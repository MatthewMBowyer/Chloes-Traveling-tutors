(function () {
        "use strict";

        function escapeHtml(value) {
                return String(value ?? "")
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/"/g, "&quot;")
                        .replace(/'/g, "&#039;");
        }

        function subjectSummary(subjects, limit) {
                const values = Array.isArray(subjects) ? subjects : [];
                if (values.length <= limit) {
                        return values.join(", ");
                }
                return values.slice(0, limit).join(", ") + " and more";
        }

        function imageMarkup(tutor, className) {
                if (tutor.image) {
                        return `
                                <img
                                        src="${escapeHtml(tutor.image)}"
                                        alt="${escapeHtml(tutor.name)}"
                                        class="${className}"
                                        loading="lazy"
                                />
                        `;
                }

                const initials = tutor.name
                        .split(/\s+/)
                        .map(function (part) { return part.charAt(0); })
                        .slice(0, 2)
                        .join("");

                return `<div class="${className} ctt-tutor-fallback" aria-label="${escapeHtml(tutor.name)}">${escapeHtml(initials)}</div>`;
        }

        function createFeaturedCard(tutor) {
                return `
                        <article class="ctt-card ctt-tutor-card">
                                <div class="ctt-tutor-photo-wrap">
                                        ${imageMarkup(tutor, "ctt-tutor-photo")}
                                </div>

                                <h3>${escapeHtml(tutor.name)}</h3>
                                <p>${escapeHtml(subjectSummary(tutor.subjects, 3))}</p>
                                <p>${escapeHtml(tutor.grades)}</p>
                                <p>${escapeHtml(tutor.lessonType)}</p>

                                <a href="tutors.html#${escapeHtml(tutor.slug)}" class="ctt-small-link">
                                        View profile
                                </a>
                        </article>
                `;
        }

        function createDirectoryCard(tutor) {
                const tags = (tutor.tags || [])
                        .map(function (tag) {
                                return `<span class="ctt-badge">${escapeHtml(tag)}</span>`;
                        })
                        .join("");

                const provinces = Array.isArray(tutor.province) ? tutor.province.join(", ") : "";

                return `
                        <article class="ctt-card ctt-tutor-detail" id="${escapeHtml(tutor.slug)}">
                                <div class="ctt-tutor-detail-heading">
                                        <div class="ctt-tutor-photo-wrap">
                                                ${imageMarkup(tutor, "ctt-tutor-photo")}
                                        </div>

                                        <div>
                                                <h2>${escapeHtml(tutor.name)}</h2>
                                                <p class="ctt-tutor-qualification">${escapeHtml(tutor.qualifications)}</p>
                                        </div>
                                </div>

                                <div class="ctt-badge-row">${tags}</div>

                                <p><strong>Grades:</strong> ${escapeHtml(tutor.grades)}</p>
                                <p><strong>Subjects:</strong> ${escapeHtml((tutor.subjects || []).join(", "))}</p>
                                <p><strong>Lesson type:</strong> ${escapeHtml(tutor.lessonType)}</p>
                                <p><strong>Area:</strong> ${escapeHtml(tutor.area)}</p>
                                ${provinces ? `<p><strong>Province:</strong> ${escapeHtml(provinces)}</p>` : ""}

                                <p class="ctt-tutor-bio">${escapeHtml(tutor.bio)}</p>

                                <a
                                        href="contact.html?tutor=${encodeURIComponent(tutor.name)}"
                                        class="button primary ctt-tutor-enquire"
                                >
                                        Enquire about ${escapeHtml(tutor.name.split(" ")[0])}
                                </a>
                        </article>
                `;
        }

        // Pure, deterministic filter. A tutor is kept when every active condition
        // holds. Province matches when it is in the tutor's declared province set,
        // so a multi-province tutor survives under each of her provinces. The
        // Online condition matches the explicit `online` flag on the record.
        function filterTutors(tutors, options) {
                const list = Array.isArray(tutors) ? tutors : [];
                const selected = options || {};
                const province = selected.province || "all";
                const onlineOnly = selected.online === true;

                return list.filter(function (tutor) {
                        const provinces = Array.isArray(tutor.province) ? tutor.province : [];
                        const matchesProvince =
                                province === "all" || provinces.indexOf(province) !== -1;
                        const matchesOnline = !onlineOnly || tutor.online === true;
                        return matchesProvince && matchesOnline;
                });
        }

        // Province options come from the data itself, sorted for a stable order.
        function provinceOptions(tutors) {
                const list = Array.isArray(tutors) ? tutors : [];
                const seen = [];
                list.forEach(function (tutor) {
                        (Array.isArray(tutor.province) ? tutor.province : []).forEach(function (province) {
                                if (seen.indexOf(province) === -1) {
                                        seen.push(province);
                                }
                        });
                });
                return seen.sort();
        }

        function byName(a, b) {
                return a.name.localeCompare(b.name);
        }

        function emptyStateMarkup() {
                return `
                        <div class="ctt-directory-empty" id="tutorEmptyState" role="status">
                                <h3>No tutors match these filters yet</h3>
                                <p>
                                        Try choosing a different province, or clear the Online filter.
                                        You can also contact us and we will help find the right fit.
                                </p>
                        </div>
                `;
        }

        window.CTTRender = {
                renderFeatured: function (containerId, featuredNames) {
                        const container = document.getElementById(containerId);

                        if (!container || !Array.isArray(window.CTT_TUTORS)) {
                                return;
                        }

                        const names = featuredNames || [];
                        const tutors = names
                                .map(function (name) {
                                        return window.CTT_TUTORS.find(function (tutor) {
                                                return tutor.name === name;
                                        });
                                })
                                .filter(Boolean);

                        container.innerHTML = tutors.map(createFeaturedCard).join("");
                },

                renderDirectory: function (containerId, options) {
                        const container = document.getElementById(containerId);

                        if (!container || !Array.isArray(window.CTT_TUTORS)) {
                                return;
                        }

                        const matches = filterTutors(window.CTT_TUTORS, options).slice().sort(byName);

                        if (matches.length === 0) {
                                container.innerHTML = emptyStateMarkup();
                                return;
                        }

                        container.innerHTML = matches.map(createDirectoryCard).join("");
                },

                // Exposed so page wiring and the deterministic harness share one
                // implementation of the matching rules.
                filterTutors: filterTutors,
                provinceOptions: provinceOptions,
                createDirectoryCard: createDirectoryCard
        };
})();

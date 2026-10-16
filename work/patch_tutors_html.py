from pathlib import Path

p = Path('tutors.html')
s = p.read_text(encoding='utf-8')

old_desc = """\t\t\t\t\t\t<p>
\t\t\t\t\t\t\tOur tutors bring different qualifications, personalities and areas of expertise.
\t\t\t\t\t\t\tWe use your learner's needs, location, subjects and learning preferences to help find
\t\t\t\t\t\t\tthe right match.
\t\t\t\t\t\t</p>"""
new_desc = """\t\t\t\t\t\t<p>
\t\t\t\t\t\t\tMeet some of the people behind CTT. Our tutors bring different strengths,
\t\t\t\t\t\t\tqualifications and teaching styles, so we can find the right fit for every learner.
\t\t\t\t\t\t</p>"""
assert old_desc in s, "desc not found"
s = s.replace(old_desc, new_desc)

old_block = """\t\t\t\t\t<div id="tutorDirectory" class="ctt-tutor-directory"></div>"""
assert old_block in s, "directory block not found"
filter_box = """\t\t\t\t\t<div class="ctt-filter-box">
\t\t\t\t\t\t<h2>Find the right tutor</h2>
\t\t\t\t\t\t<p>
\t\t\t\t\t\t\tFilter our tutors by province, or show only tutors who teach online.
\t\t\t\t\t\t</p>

\t\t\t\t\t\t<div class="ctt-filter-grid">
\t\t\t\t\t\t\t<div>
\t\t\t\t\t\t\t\t<label for="provinceFilter">Province</label>
\t\t\t\t\t\t\t\t<select id="provinceFilter">
\t\t\t\t\t\t\t\t\t<option value="all">All provinces</option>
\t\t\t\t\t\t\t\t</select>
\t\t\t\t\t\t\t</div>

\t\t\t\t\t\t\t<div class="ctt-filter-toggle">
\t\t\t\t\t\t\t\t<input type="checkbox" id="onlineFilter" />
\t\t\t\t\t\t\t\t<label for="onlineFilter">Online lessons only</label>
\t\t\t\t\t\t\t</div>

\t\t\t\t\t\t\t<div>
\t\t\t\t\t\t\t\t<button id="clearTutorFilters" class="button secondary" type="button">
\t\t\t\t\t\t\t\t\tClear filters
\t\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>

\t\t\t\t\t\t<p id="tutorFilterSummary" class="ctt-filter-summary" role="status"></p>
\t\t\t\t\t</div>

\t\t\t\t\t<div id="tutorDirectory" class="ctt-tutor-directory"></div>"""
s = s.replace(old_block, filter_box)

old_script = """\t\t<script>
\t\t\tCTTRender.renderDirectory("tutorDirectory");
\t\t</script>"""
assert old_script in s, "script not found"
new_script = """\t\t<script>
\t\t\t(function () {
\t\t\t\tconst provinceFilter = document.getElementById("provinceFilter");
\t\t\t\tconst onlineFilter = document.getElementById("onlineFilter");
\t\t\t\tconst clearFilters = document.getElementById("clearTutorFilters");
\t\t\t\tconst summary = document.getElementById("tutorFilterSummary");

\t\t\t\tconst provinceLabels = {
\t\t\t\t\t"Gauteng": "Gauteng",
\t\t\t\t\t"KwaZulu-Natal": "KwaZulu-Natal",
\t\t\t\t\t"Western Cape": "Western Cape"
\t\t\t\t};

\t\t\t\t// Options come from the data, never hard-coded.
\t\t\t\tCTTRender.provinceOptions(window.CTT_TUTORS).forEach(function (province) {
\t\t\t\t\tconst option = document.createElement("option");
\t\t\t\t\toption.value = province;
\t\t\t\t\toption.textContent = provinceLabels[province] || province;
\t\t\t\t\tprovinceFilter.appendChild(option);
\t\t\t\t});

\t\t\t\tfunction currentOptions() {
\t\t\t\t\treturn {
\t\t\t\t\t\tprovince: provinceFilter.value,
\t\t\t\t\t\tonline: onlineFilter.checked
\t\t\t\t\t};
\t\t\t\t}

\t\t\t\tfunction updateSummary() {
\t\t\t\t\tconst options = currentOptions();
\t\t\t\t\tconst matches = CTTRender.filterTutors(window.CTT_TUTORS, options);
\t\t\t\t\tconst parts = [];

\t\t\t\t\tif (options.province !== "all") {
\t\t\t\t\t\tparts.push(provinceLabels[options.province] || options.province);
\t\t\t\t\t}

\t\t\t\t\tif (options.online) {
\t\t\t\t\t\tparts.push("online lessons");
\t\t\t\t\t}

\t\t\t\t\tconst scope = parts.length ? " for " + parts.join(" and ") : "";
\t\t\t\t\tsummary.textContent = matches.length + (matches.length === 1 ? " tutor" : " tutors") + scope + ".";
\t\t\t\t}

\t\t\t\tfunction applyFilters() {
\t\t\t\t\tCTTRender.renderDirectory("tutorDirectory", currentOptions());
\t\t\t\t\tupdateSummary();
\t\t\t\t}

\t\t\t\tprovinceFilter.addEventListener("change", applyFilters);
\t\t\t\tonlineFilter.addEventListener("change", applyFilters);

\t\t\t\tclearFilters.addEventListener("click", function () {
\t\t\t\t\tprovinceFilter.value = "all";
\t\t\t\t\tonlineFilter.checked = false;
\t\t\t\t\tapplyFilters();
\t\t\t\t});

\t\t\t\tapplyFilters();
\t\t\t})();
\t\t</script>"""
s = s.replace(old_script, new_script)
p.write_text(s, encoding='utf-8')
print("tutors.html updated")

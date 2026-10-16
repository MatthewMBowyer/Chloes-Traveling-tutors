/* Generate .supervisor/CORPUS_QUALITY.json for the tutor-record corpus.

The contract declares corpus applicability "none", but per-item quality evidence
across the whole tutor population is recorded anyway. All invariants are checked
against the live data and rendered card output.

    node work/gen_corpus_quality.js
*/

global.window = {};
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
require("../assets/data/tutors.js");
require("../assets/js/render-tutors.js");
const T = window.CTT_TUTORS;
const R = window.CTTRender;
const VALID = ["Gauteng", "KwaZulu-Natal", "Western Cape"];

const items = {};
T.forEach(function (t) {
  const card = R.createDirectoryCard(t);
  const provinceOk = Array.isArray(t.province)
    && t.province.every(function (p) { return VALID.indexOf(p) !== -1; });
  // Online-only tutors legitimately have an empty province set: they must still
  // be reachable (through the Online filter) and must not be silently dropped.
  const reachable = (t.province.length === 0)
    ? R.filterTutors(T, { online: true }).some(function (x) { return x.slug === t.slug; })
    : t.province.every(function (p) {
        return R.filterTutors(T, { province: p }).some(function (x) { return x.slug === t.slug; });
      });
  items[t.slug] = {
    name: t.name,
    card_has_slug_anchor: card.indexOf('id="' + t.slug + '"') !== -1,
    card_has_no_availability: card.indexOf("Availability") === -1,
    province_values_valid: provinceOk,
    online_flag_is_boolean: typeof t.online === "boolean",
    image_exists_on_disk: !t.image || fs.existsSync(path.join(ROOT, t.image)),
    reachable_in_filter: reachable,
    evidence: "id#" + t.slug + "; province=" + JSON.stringify(t.province)
      + "; online=" + t.online + "; image=" + t.image
      + (t.province.length ? "" : " (online-only: reachable via Online filter)"),
  };
});

const failed = Object.keys(items).filter(function (k) {
  const v = items[k];
  return !(v.card_has_slug_anchor && v.card_has_no_availability && v.province_values_valid
    && v.online_flag_is_boolean && v.image_exists_on_disk && v.reachable_in_filter);
});

fs.writeFileSync(path.join(ROOT, ".supervisor/CORPUS_QUALITY.json"), JSON.stringify({
  generation: 1,
  corpora: { "tutor-records": { items: items } },
  failed: failed.length,
  failed_identities: failed,
}, null, 2));
console.log("items", Object.keys(items).length, "failed", failed.length, failed);

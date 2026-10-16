"""Ad-hoc audit of rendered tutor cards, for the Round 2 notes review.

Serves the site and dumps the rendered DOM of tutors.html and index.html so the
card text can be read as a parent sees it.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import verify_site as vs  # noqa: E402


def strip(html: str) -> str:
    text = re.sub(r"<[^>]+>", "|", html)
    return re.sub(r"\s+", " ", text.replace("|", " ")).strip()


def main() -> int:
    server = vs.start_server(ROOT, 8999)
    try:
        import time

        time.sleep(1)
        dom = vs.dump_dom("http://127.0.0.1:8999/tutors.html", budget=6000)
        cards = re.findall(
            r'<article class="ctt-card ctt-tutor-detail"(.*?)</article>', dom, re.S
        )
        print(f"tutor cards rendered: {len(cards)}")
        for card in cards:
            name = re.search(r"<h2[^>]*>(.*?)</h2>", card, re.S)
            print("=" * 78)
            print("NAME:", strip(name.group(1)) if name else "?")
            print(strip(card)[:900])
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())

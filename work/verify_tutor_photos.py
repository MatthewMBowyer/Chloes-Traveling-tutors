"""Prove each new tutor photo on the site came from the photo Chloe sent.

The site stores JPEGs; the source pack holds JPEGs of the same pictures. A file
that was converted or resized will not hash-match, so this compares the picture
itself: both are normalised to a common size and the mean absolute pixel
difference is reported. A low difference means the same photograph; a poster or
a different person would not come close.
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("/tmp/ctt_fixes/CTT fixes")
SIZE = (256, 256)

PAIRS = [
    ("Sabreen Limbada", "images/sabreen_limbada.jpg", "Sabreen image.jpeg"),
    ("Swasthi Prahalad", "images/swasthi_prahalad.jpg", "Sw image.jpeg"),
    ("Caleb Ross", "images/caleb_ross.jpg", "caleb image.jpeg"),
    ("Isabella Stubbs", "images/isabella_stubbs.jpg", "Isabella image.jpeg"),
    ("Priyal Daya", "images/priyal_daya.jpg", "priyal image.jpeg"),
]


def normalised(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB").resize(SIZE, Image.LANCZOS)
    return image


def main() -> int:
    failures = 0
    for name, site_rel, source_name in PAIRS:
        site = ROOT / site_rel
        source = SOURCE / source_name
        if not site.exists() or not source.exists():
            print(f"[FAIL] {name}: missing file {site} {source}")
            failures += 1
            continue

        left, right = normalised(site), normalised(source)
        diff = ImageChops.difference(left, right)
        total = sum(sum(pixel) for pixel in diff.getdata())
        mean = total / (SIZE[0] * SIZE[1] * 3)
        site_size = Image.open(site).size
        source_size = Image.open(source).size
        ok = mean < 12
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}: site={site_size} source={source_size} "
            f"mean absolute pixel difference={mean:.2f}"
        )
        failures += 0 if ok else 1

    print(f"\n{len(PAIRS)} photos, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

"""Prove the Round 2 hero image is a crop of the site's own photo, not a new one.

The boss asked for the homepage picture to be smaller with the empty background
cut out. That must not mean swapping in a different (stock or fabricated)
photograph, so this search locates the delivered crop inside the pre-existing
`images/index_open_image.jpeg` and records the offset and residual difference.

Writes output/evidence/hero_crop_provenance.json. Run from the project root:
    python3 work/verify_hero_crop.py
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "images" / "index_open_image.jpeg"
CROP = ROOT / "images" / "hero_study_crop.jpeg"
OUT = ROOT / "output" / "evidence" / "hero_crop_provenance.json"

SEARCH_RADIUS = 40


def main() -> None:
    source = np.asarray(Image.open(SOURCE).convert("RGB")).astype(int)
    crop = np.asarray(Image.open(CROP).convert("RGB")).astype(int)
    crop_h, crop_w = crop.shape[:2]
    source_h, source_w = source.shape[:2]

    coarse_x = coarse_y = None
    best = None
    step = 8
    for y in range(0, source_h - crop_h + 1, step):
        for x in range(0, source_w - crop_w + 1, step):
            diff = np.abs(source[y:y + crop_h, x:x + crop_w] - crop).mean()
            if best is None or diff < best:
                best, coarse_x, coarse_y = diff, x, y

    best = None
    offset = (coarse_x, coarse_y)
    for y in range(max(0, coarse_y - SEARCH_RADIUS), min(source_h - crop_h, coarse_y + SEARCH_RADIUS) + 1):
        for x in range(max(0, coarse_x - SEARCH_RADIUS), min(source_w - crop_w, coarse_x + SEARCH_RADIUS) + 1):
            diff = np.abs(source[y:y + crop_h, x:x + crop_w] - crop).mean()
            if best is None or diff < best:
                best, offset = diff, (x, y)

    result = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_size": [source_w, source_h],
        "crop": str(CROP.relative_to(ROOT)),
        "crop_size": [crop_w, crop_h],
        "crop_is_smaller": crop_w < source_w and crop_h < source_h,
        "origin_in_source": list(offset),
        "mean_absolute_pixel_difference": round(float(best), 3),
        "match": bool(best is not None and best < 4.0),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

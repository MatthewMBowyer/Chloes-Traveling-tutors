"""Build the social share card (1200x630) used for the og:image / twitter:image.

Composed rather than cropped: the hero photo is a 822x1010 portrait, so a plain
1.91:1 crop of it would either cut the faces or need heavy upscaling. Instead the
photo is used whole down the right of a 1200x630 canvas and the left carries the
logo and the search-facing headline.

Run from the repo root:  python3 work/make_og_image.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "ctt_social_share.jpg"

W, H = 1200, 630
PHOTO_W = 580
TEAL = (0, 151, 178)
INK = (0, 0, 0)
GREY = (57, 57, 57)
FONT_DIR = Path("/usr/share/fonts/truetype/lato")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def soften_left_edge(photo: Image.Image, fade: int = 90) -> Image.Image:
    """Fade the photo's left edge into the white panel.

    A hard vertical seam looks like two pasted images; a short gradient reads as
    one card.
    """
    photo = photo.convert("RGBA")
    mask = Image.new("L", photo.size, 255)
    draw = ImageDraw.Draw(mask)

    for x in range(fade):
        draw.line([(x, 0), (x, photo.height)], fill=int(255 * (x / fade)))

    photo.putalpha(mask)
    return photo


def main() -> None:
    canvas = Image.new("RGB", (W, H), (255, 255, 255))

    # --- photo, right hand side -------------------------------------------------
    source = Image.open(ROOT / "images" / "hero_study_crop.jpeg")
    target_ratio = PHOTO_W / H
    crop_h = min(source.height, int(source.width / target_ratio))
    # Keep the top of the frame: both faces sit in the upper half of the source.
    crop_y = max(0, (source.height - crop_h) // 3)
    photo = source.crop((0, crop_y, source.width, crop_y + crop_h))
    photo = photo.resize((PHOTO_W, H), Image.LANCZOS)
    canvas.paste(soften_left_edge(photo), (W - PHOTO_W, 0), soften_left_edge(photo))

    draw = ImageDraw.Draw(canvas)

    # --- logo ------------------------------------------------------------------
    logo = Image.open(ROOT / "images" / "CTT_logo_cropped.png").convert("RGB")
    logo_w = 250
    logo = logo.resize((logo_w, int(logo.height * logo_w / logo.width)), Image.LANCZOS)
    canvas.paste(logo, (64, 58))

    # --- headline --------------------------------------------------------------
    draw.text((64, 292), "Private & online tutors", font=font("Lato-Black.ttf", 46), fill=INK)
    draw.text((64, 344), "across South Africa", font=font("Lato-Black.ttf", 46), fill=TEAL)

    draw.text(
        (64, 418),
        "Grades 1 to 12 and first-year university",
        font=font("Lato-Medium.ttf", 24),
        fill=GREY,
    )

    # --- offer pill ------------------------------------------------------------
    label = "20% off your first lesson"
    pill_font = font("Lato-Bold.ttf", 23)
    text_w = draw.textlength(label, font=pill_font)
    pill = (64, 464, int(64 + text_w + 56), 464 + 52)
    draw.rounded_rectangle(pill, radius=26, fill=TEAL)
    draw.text((pill[0] + 28, pill[1] + 13), label, font=pill_font, fill=(255, 255, 255))

    canvas.save(OUT, quality=88, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} {canvas.size}")


if __name__ == "__main__":
    main()

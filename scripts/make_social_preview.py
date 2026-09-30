"""Render docs/assets/social-preview.png to match social-preview.svg.

The SVG is the source of truth for the design. Social platforms do not render
SVG previews, so this draws the same 1200x630 card with Pillow using the
system Segoe UI / Consolas faces. It is a build-time helper, not a runtime
dependency: the committed PNG is what the site ships.
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "social-preview.png"

BG_A, BG_B, BG_C = (15, 23, 42), (17, 24, 39), (8, 12, 20)
CARD, CARD_EDGE = (11, 18, 32), (36, 48, 68)
TEXT, MUTED, DIM = (248, 250, 252), (148, 163, 184), (124, 139, 161)
CYAN, INDIGO, GREEN = (56, 189, 248), (129, 140, 248), (52, 211, 153)

SANS = "C:/Windows/Fonts/segoeui.ttf"
SANS_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"
MONO_BOLD = "C:/Windows/Fonts/consolab.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def lerp(a, b, t: float):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def gradient(w: int, h: int) -> Image.Image:
    """Diagonal two-stop gradient, matching the SVG's linearGradient."""
    base = Image.new("RGB", (w, h))
    px = base.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.55) + (y / h * 0.45)
            t = min(1.0, max(0.0, t))
            px[x, y] = BG_A if t < 0.55 else lerp(BG_B, BG_C, (t - 0.55) / 0.45)
    return base


def glow(img: Image.Image, cx: int, cy: int, r: int, colour, alpha: int) -> None:
    """Soft radial wash, standing in for the SVG's blurred ellipse."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    steps = 26
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(alpha * (1 - t) ** 2)
        rr = int(r * t)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*colour, a))
    img.alpha_composite(overlay)


def brand_text(d: ImageDraw.ImageDraw, x: int, y: int, text: str, f, size: int) -> None:
    """Draw text along the cyan -> indigo brand gradient."""
    tmp = Image.new("RGBA", (size * 26, int(size * 1.6)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((0, 0), text, font=f, fill=(255, 255, 255, 255))
    box = tmp.getbbox()
    if box is None:
        return
    crop = tmp.crop(box)
    grad = Image.new("RGB", crop.size)
    gp = grad.load()
    for i in range(crop.size[0]):
        col = lerp(CYAN, INDIGO, i / max(1, crop.size[0] - 1))
        for j in range(crop.size[1]):
            gp[i, j] = col
    crop.putalpha(crop.getchannel("A"))
    d._image.paste(grad.convert("RGBA"), (x, y), crop)


def pill(d: ImageDraw.ImageDraw, x, y, w, h, head, sub, head_col) -> None:
    d.rounded_rectangle([x, y, x + w, y + h], radius=12,
                        fill=CARD, outline=CARD_EDGE, width=2)
    d.text((x + 26, y + 20), head, font=font(MONO_BOLD, 20), fill=head_col)
    d.text((x + 26, y + 56), sub, font=font(MONO, 17), fill=DIM)


def main() -> int:
    if not OUT.parent.is_dir():
        print("assets directory missing", file=sys.stderr)
        return 1

    img = gradient(W, H).convert("RGBA")
    glow(img, 170, 120, 420, CYAN, 42)
    glow(img, 1060, 560, 440, INDIGO, 36)
    d = ImageDraw.Draw(img)

    # Logo mark
    d.rounded_rectangle([64, 52, 120, 108], radius=15, fill=(11, 15, 25),
                        outline=CYAN, width=2)
    lw = 4
    d.arc([72, 62, 100, 98], start=-70, end=70, fill=CYAN, width=lw)
    d.arc([84, 62, 112, 98], start=110, end=250, fill=INDIGO, width=lw)
    d.polygon([(84, 62), (92, 70), (84, 78)], fill=CYAN)
    d.polygon([(100, 82), (92, 90), (100, 98)], fill=INDIGO)
    d.ellipse([86, 74, 98, 86], fill=CYAN)

    brand_text(d, 140, 62, "MockRelay", font(SANS_BOLD, 46), 46)

    d.text((64, 168), "Record real HTTP traffic once.",
           font=font(SANS_BOLD, 43), fill=TEXT)
    d.text((64, 222), "Replay it locally whenever you want.",
           font=font(SANS_BOLD, 43), fill=TEXT)
    d.text((64, 288),
           "A local HTTP proxy with ranked fixture matching, redaction,"
           " and a CI-friendly CLI.",
           font=font(SANS, 21), fill=MUTED)

    pill(d, 64, 352, 520, 104,
         "$ mockrelay serve --mode record",
         "saved fixtures/gh/gh-get-016c60e26e39.json", CYAN)
    pill(d, 616, 352, 520, 104,
         "$ mockrelay serve --mode replay",
         "X-MockRelay-Score: 4000009", GREEN)

    d.rounded_rectangle([64, 500, 534, 562], radius=10, fill=(17, 28, 46),
                        outline=(43, 58, 82), width=2)
    d.text((90, 518), "$ pip install mockrelay", font=font(MONO_BOLD, 21),
           fill=(226, 232, 240))
    d.text((560, 524), "MIT licensed · Python 3.10+",
           font=font(SANS_BOLD, 18), fill=(100, 116, 139))

    img.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError, OSError):
            _s.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

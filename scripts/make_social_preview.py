"""Render docs/assets/social-preview.png to match social-preview.svg.

Social platforms do not render SVG, so this draws the same 1200x630 card with
Pillow. It is a build-time helper, not a runtime dependency: the committed PNG is
what the site ships. Run it after editing the SVG.
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "social-preview.png"

WHITE = (255, 255, 255)
INK = (26, 26, 26)
MUTED = (85, 85, 85)
RULE = (208, 208, 208)
PANEL = (246, 246, 246)
BORDER = (156, 156, 156)

SANS = "C:/Windows/Fonts/segoeui.ttf"
SANS_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def logo(d: ImageDraw.ImageDraw, x: int, y: int, s: int) -> None:
    """The relay mark, flat: a bordered square with two arcs and a dot."""
    d.rounded_rectangle([x, y, x + s, y + s], radius=s // 6,
                        fill=WHITE, outline=BORDER, width=2)
    w = max(2, s // 14)
    k = s / 64.0
    d.arc([x + 10 * k, y + 22 * k, x + 41 * k, y + 42 * k],
          start=-70, end=70, fill=INK, width=w)
    d.arc([x + 23 * k, y + 22 * k, x + 54 * k, y + 42 * k],
          start=110, end=250, fill=INK, width=w)
    d.polygon([(x + 24.8 * k, y + 44.8 * k), (x + 19.2 * k, y + 53 * k),
               (x + 24.8 * k, y + 61.2 * k)], fill=INK)
    d.polygon([(x + 39.2 * k, y + 20.8 * k), (x + 44.8 * k, y + 29 * k),
               (x + 39.2 * k, y + 37.2 * k)], fill=INK)
    d.ellipse([x + 28.4 * k, y + 28.4 * k, x + 35.6 * k, y + 35.6 * k], fill=INK)


def main() -> int:
    if not OUT.parent.is_dir():
        print("assets directory missing", file=sys.stderr)
        return 1

    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    d.rectangle([24, 24, W - 24, H - 24], outline=RULE, width=2)

    logo(d, 72, 72, 64)
    d.text((164, 82), "MockRelay", font=font(SANS_BOLD, 48), fill=INK)

    d.text((72, 172), "HTTP mocking and API record/replay",
           font=font(SANS_BOLD, 38), fill=INK)
    d.text((72, 224), "Record real traffic once. Replay it offline.",
           font=font(SANS_BOLD, 38), fill=INK)
    d.text((72, 288),
           "A local HTTP proxy for API testing, integration tests, and CI.",
           font=font(SANS, 24), fill=MUTED)

    d.rectangle([72, 368, 1128, 486], fill=PANEL, outline=RULE, width=2)
    d.text((100, 396), "$ mockrelay serve --mode record",
           font=font(MONO, 23), fill=INK)
    d.text((100, 436), "$ mockrelay serve --mode replay     X-MockRelay-Match: exact",
           font=font(MONO, 23), fill=INK)

    d.text((72, 528),
           "Ranked fixture matching \u00b7 secrets redacted to {{SECRET}} \u00b7 no network in replay",
           font=font(SANS, 22), fill=MUTED)
    d.text((72, 566),
           "Python 3.10+ \u00b7 one dependency (PyYAML) \u00b7 MIT",
           font=font(SANS, 22), fill=MUTED)

    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError, OSError):
            _s.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

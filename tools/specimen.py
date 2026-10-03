# Prerequisite: fonttools must be able to draw glyphs (its Cython pens
# accelerate cu2qu, but the pure-Python fallback is used otherwise).
"""
Render a specimen sheet from the compiled fonts.

Every glyph, side by side, plus the character set and a tabular-figure check.
Handy for eyeballing a weight change without opening a font editor:

    python tools/specimen.py
    python tools/specimen.py --out /tmp/specimen.png --weight Medium
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from monochrome import layout  # noqa: E402
from monochrome.builder import build_font  # noqa: E402
from monochrome.metrics import WEIGHTS, WEIGHTS_BY_NAME  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("This tool needs Pillow: pip install pillow")


MARGIN = 32
LABEL_H = 28


def load(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def draw_specimen(font_path: Path, out: Path, size: int, width: int = 1600) -> None:
    """Render every glyph of ``font_path`` in a grid about ``width`` px across."""
    font = load(font_path, size)
    names = list(layout.GLYPH_ORDER)

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    def as_char(name: str) -> str:
        """Turn a glyph name into a character the cmap already knows."""
        cp = layout.CODEPOINTS.get(name)
        if cp is None:
            return "?"
        return chr(cp)

    entries = []
    for name in names:
        char = as_char(name)
        box = probe.textbbox((0, 0), char, font=font)
        # textbbox is (x0, y0, x1, y1); y0 is usually negative (ascender overhang)
        entries.append((name, char, box))

    cell_w = max(b[2] - b[0] for _, _, b in entries) + 24
    cell_h = max(b[3] - b[1] for _, _, b in entries) + 24
    cols = max(1, min(len(entries), width // cell_w))
    rows = (len(names) + cols - 1) // cols

    width = MARGIN * 2 + cols * cell_w
    height = MARGIN * 2 + rows * (cell_h + LABEL_H)

    img = Image.new("RGB", (width, height), "#111111")
    draw = ImageDraw.Draw(img)
    label = load(font_path, 13)

    for i, (name, char, box) in enumerate(entries):
        r, c = divmod(i, cols)
        x = MARGIN + c * cell_w
        y = MARGIN + r * (cell_h + LABEL_H)
        # shift by the glyph's own left/top offset so the grid stays aligned
        draw.text((x - box[0], y - box[1]), char, font=font, fill="#f0f0f0")
        draw.text((x, y + cell_h), name[:8], font=label, fill="#666666")

    img.save(out)
    print(f"Wrote {out}  ({len(names)} glyphs, {font_path.name})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "specimen.png")
    ap.add_argument("--size", type=int, default=48, help="glyph size in px")
    ap.add_argument("--width", type=int, default=1600, help="target sheet width in px")
    ap.add_argument("--weight", default="Regular", choices=[w.style for w in WEIGHTS])
    ap.add_argument("--font", type=Path, help="use an existing .ttf instead of building")
    args = ap.parse_args(argv)

    if args.font:
        font_path = args.font
    else:
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        font_path = build_font(WEIGHTS_BY_NAME[args.weight.lower()], tmp, ("ttf",))[0]

    draw_specimen(font_path, args.out, args.size, args.width)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

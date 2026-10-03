#!/usr/bin/env python3
"""Generate a self-contained HTML specimen for the compiled fonts.

Everything is inlined (the fonts become base64 data URIs), so the result is a
single file that opens from disk, works offline, and can be attached to a
release without a web server or any external request.

    python tools/html_specimen.py
    python tools/html_specimen.py --out /tmp/specimen.html --weight medium

Only needs fonttools-free stdlib plus the compiled fonts themselves - unlike
``tools/specimen.py`` (which rasterises a PNG sheet with Pillow) there is no
image library involved, so this runs anywhere.
"""

from __future__ import annotations

import argparse
import base64
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from monochrome.metrics import VERSION, WEIGHTS, WEIGHTS_BY_NAME  # noqa: E402

DEFAULT_OUT = ROOT / "monochrome-aviation-specimen.html"

# Every character the family maps, grouped for display. Kept in sync with
# monochrome/layout.py - an unmapped character would render as .notdef here,
# which is exactly the kind of thing this page is for catching.
CHARSET = [
    ("Capitals", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ("Lowercase", "abcdefghijklmnopqrstuvwxyz"),
    ("Figures (tabular)", "0123456789"),
    ("Punctuation", ".,:;!?'\"-–—/()+=_&@"),
    ("Symbols", "°←↑→↓✈"),
]

# Copy this typeface was actually drawn for. Nothing here may use a character
# outside CHARSET, or it falls back to .notdef.
SAMPLES = [
    ("Flight level", "FL350"),
    ("Heading", "270"),
    ("Squawk", "7700"),
    ("Runway", "RWY 18L"),
    ("Temperature", "-54°C"),
    ("Speed", "M0.79 → 250 KT"),
    ("Aircraft", "✈ A320 / B738 / E190"),
    ("Phraseology", "Cleared to land, runway one eight left"),
]

PANGRAM = "The quick brown fox jumps over 0770"

CSS = """
:root { color-scheme: dark; }
body {
  margin: 0; padding: 3rem 2rem 6rem;
  background: #0d0f11; color: #e8eaed;
  font-family: "Monochrome Aviation", ui-monospace, monospace;
}
.wrap { max-width: 60rem; margin: 0 auto; }
h1 { font-size: 2rem; margin: 0 0 .25rem; letter-spacing: .01em; }
h1 span { color: #7d848c; font-size: 1rem; font-weight: 400; }
p.lede { color: #9aa1a9; margin: 0 0 3rem; font-size: .95rem; line-height: 1.6; }
h2 {
  font-size: .75rem; text-transform: uppercase; letter-spacing: .14em;
  color: #7d848c; font-weight: 400;
  margin: 3.5rem 0 1rem; padding-bottom: .5rem;
  border-bottom: 1px solid #22262a;
}
.row { display: flex; flex-wrap: wrap; gap: 1.5rem 2.5rem; margin: 1.25rem 0; }
.swatch { flex: 1 1 18rem; min-width: 0; }
.k { color: #6b7178; font-size: .7rem; letter-spacing: .1em; text-transform: uppercase; }
.v { line-height: 1.25; margin-top: .2rem; overflow-wrap: anywhere; }
.glyphs span { display: inline-block; margin: 0 .18em; }
.weights .v { font-size: 2.5rem; line-height: 1.1; }
figure { margin: 0 0 1.5rem; }
figcaption { color: #6b7178; font-size: .7rem; letter-spacing: .1em; }
footer { margin-top: 4rem; color: #6b7178; font-size: .78rem; line-height: 1.7; }
a { color: #8ab4f8; }
code { color: #9aa1a9; }
table { border-collapse: collapse; width: 100%; font-size: .82rem; }
td, th { text-align: left; padding: .35rem .6rem .35rem 0; border-bottom: 1px solid #1c2024; }
th { color: #6b7178; font-weight: 400; }
"""


def data_uri(path: Path) -> str:
    """Inline a font file as a base64 data URI."""
    mime = "font/woff2" if path.suffix == ".woff2" else "font/ttf"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def face_rules(fonts_dir: Path, weights) -> str:
    """One @font-face per weight, pointing at the inlined WOFF2."""
    rules = []
    for w in weights:
        path = fonts_dir / f"{w.filename}.woff2"
        if not path.exists():
            print(f"warning: {path.name} missing, skipping {w.style}", file=sys.stderr)
            continue
        rules.append(
            "@font-face{"
            "font-family:'Monochrome Aviation';"
            "font-style:normal;"
            f"font-weight:{w.us_weight_class};"
            f"src:url({data_uri(path)}) format('woff2');"
            "font-display:swap;}"
        )
    return "\n".join(rules)


def _swatch(label: str, body: str, cls: str = "") -> str:
    return (
        f'<div class="swatch"><div class="k">{html.escape(label)}</div>'
        f'<div class="v {cls}">{body}</div></div>'
    )


def samples_block() -> str:
    """Realistic aviation strings, laid out as a wrapping grid."""
    rows = [
        _swatch(label, html.escape(text))
        for label, text in SAMPLES
    ]
    return f'<div class="row">{"".join(rows)}</div>'


def charset_block() -> str:
    """Every mapped character, grouped by category."""
    rows = [
        _swatch(
            label,
            "".join(f"<span>{html.escape(ch)}</span>" for ch in chars),
            "glyphs",
        )
        for label, chars in CHARSET
    ]
    return f'<div class="row">{"".join(rows)}</div>'


def sizes_block() -> str:
    """The same line at decreasing sizes, to check hinting-ish legibility."""
    figures = [
        f'<figure><figcaption>{size}px</figcaption>'
        f'<div style="font-size:{size}px;line-height:1.25">{html.escape(PANGRAM)}</div>'
        f"</figure>"
        for size in (64, 40, 26, 18, 13)
    ]
    return "".join(figures)


def build(fonts_dir: Path, out: Path, weights) -> Path:
    """Render the specimen to ``out`` and return the path written."""
    faces = face_rules(fonts_dir, weights)
    if not faces:
        raise SystemExit(f"no compiled fonts in {fonts_dir} - run `python build.py` first")

    big = "".join(
        _swatch(f"{w.style} / {w.us_weight_class}", "HAMBURGEFONSIV", "big")
        for w in weights
    )
    rows = "".join(
        f"<tr><td>{html.escape(w.style)}</td><td>{w.stroke:g} units</td>"
        f"<td>{w.us_weight_class}</td><td><code>{w.filename}.ttf</code></td></tr>"
        for w in weights
    )

    out.write_text(
        f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monochrome Aviation — specimen</title>
<style>
{faces}
{CSS}</style>
<div class="wrap">

<h1>Monochrome Aviation <span>version {VERSION}</span></h1>
<p class="lede">A minimal, fully rounded monoline sans, drawn for aviation
displays. Every terminal and corner is round at every weight, and the figures
are tabular, so flight levels and headings stack in clean columns.</p>

<h2>Weights</h2>
<div class="row weights">{big}</div>

<h2>In context</h2>
{samples_block()}

<h2>Character set</h2>
{charset_block()}

<h2>Sizes</h2>
{sizes_block()}

<h2>Files</h2>
<table><tr><th>Weight</th><th>Stroke</th><th>Class</th><th>Filename</th></tr>{rows}</table>

<footer>
Licensed under <a href="https://creativecommons.org/licenses/by-nd/4.0/">CC BY-ND 4.0</a>.
This page embeds the fonts as data URIs, so it renders offline with no network
access.<br>
Generated from source — edit a skeleton in <code>monochrome/glyphs/</code> and rebuild.
</footer>
</div>
""",
        encoding="utf-8",
    )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fonts", type=Path, default=ROOT / "fonts", help="directory holding the compiled fonts")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="HTML file to write")
    ap.add_argument("--weight", action="append", metavar="NAME",
                    help="restrict to a weight, repeatable (default: all)")
    args = ap.parse_args(argv)

    weights = WEIGHTS
    if args.weight:
        weights = tuple(WEIGHTS_BY_NAME[n.lower()] for n in args.weight)

    path = build(args.fonts, args.out, weights)
    print(f"Wrote {path}  ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# Monochrome Aviation

A minimal, fully rounded monoline sans, drawn for aviation displays.

Every glyph is a **centre-line skeleton** — straight lines, true circular arcs,
smooth Hermite curves — that gets stroked with round caps and round joins. Because
the round joins are baked into the outline at build time, every terminal and
corner is perfectly round at every weight. Strokes are merged with skia-pathops
and converted to TrueType quadratics.

The font is generated from source, so the repository *is* the design: edit a
skeleton, rebuild, and the `.ttf` follows.

```
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
a b c d e f g h i j k l m n o p q r s t u v w x y z
0 1 2 3 4 5 6 7 8 9   ! ? , : ; ' " - – — / ( ) + = ° _  ← ↑ → ↓ ✈
```

## Quick start

```bash
pip install -r requirements.txt   # or: pip install -e .
python build.py                   # writes ./fonts
```

Or, if installed as a package:

```bash
monochrome-build
python -m monochrome
```

Output lands in `fonts/`:

| File | Weight | `usWeightClass` |
|---|---|---|
| `monochrome-aviation-light.ttf` / `.woff2` | Light | 300 |
| `monochrome-aviation.ttf` / `.woff2` | Regular | 400 |
| `monochrome-aviation-medium.ttf` / `.woff2` | Medium | 500 |

`fonts/` is committed, not ignored — the typeface is the deliverable, and most
people want the `.ttf` rather than the generator. A tag like `v3.0.0` rebuilds
every weight in CI, checks it against what is committed, and attaches the fonts
plus a specimen to a [release](https://github.com/Frqme21/monochrome-font/releases).

### Options

```bash
python build.py --weights regular        # one weight (case-insensitive)
python build.py --format ttf             # skip the woff2 pass
python build.py --out /tmp/out           # elsewhere
python build.py --help
```

## Using the font

Web:

```css
@font-face {
  font-family: "Monochrome Aviation";
  src: url("fonts/monochrome-aviation.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}
```

Desktop:

```bash
cp fonts/monochrome-aviation.ttf ~/.local/share/fonts/
fc-cache -f
```

## Character set

- `A`–`Z`, `a`–`z`
- `0`–`9`, **tabular** — one shared advance width, each figure optically centred,
  so flight levels (`FL350`), headings (`270`) and squawk codes (`7700`) stack
  in clean columns
- Punctuation: `. , : ; ! ? - – — / ( ) + = ° ' " _`
- Arrows: `← ↑ → ↓` (U+2190–2193)
- Airliner silhouette: `✈` (U+2708)

Both ASCII and no-break space map to `space`. Anything unmapped draws as
`.notdef`.

## Layout

```
monochrome/
├── metrics.py      vertical metrics, weight table, and the Frame that solves
│                   centre lines from a stroke width
├── skeleton.py     Sk - the path builder (M/L/Q/C/Z, arc, poly, hermite, mapped)
├── primitives.py   the drawing vocabulary (line, circle, pill, rot180, mirror_x…)
├── glyph.py        Glyph - stroked skeletons plus filled dots
├── glyphs/         the actual letterforms, one module per category
│   ├── base.py       shared sub-drawings (bowl, s-curve, dot)
│   ├── caps.py       A–Z
│   ├── lowercase.py  a–z
│   ├── figures.py    0–9
│   ├── punctuation.py
│   └── aviation.py   arrows and the airliner
├── layout.py       names, codepoints, sidebearing classes, kern pairs
├── outline.py      skeleton → stroked → merged → TrueType quadratics
├── builder.py      glyph order, metrics, name/OS2/gasp/GPOS tables, output
└── cli.py          argument parsing and the progress output

tests/              142 tests, no network, ~1s
tools/
├── specimen.py     contact sheet of every glyph as a PNG (needs Pillow)
├── html_specimen.py  self-contained HTML specimen, fonts inlined as data URIs
└── verify_fonts.py   assert two builds agree; used by the release workflow
```

The data flows one way:

```
metrics.Frame  ──▶  glyphs/*.draw(f)  ──▶  outline.outline()  ──▶  builder  ──▶  .ttf / .woff2
   (stroke)            (skeletons)            (stroked outline)      (tables)
```

`Frame` is what makes the family weight-consistent: glyph modules read
pre-solved landmarks (`f.cap`, `f.bowl_r`, `f.dot_r`) instead of doing arithmetic
on raw metrics, so changing a weight is a one-line change in `metrics.py` and
every glyph follows.

## How a glyph is defined

Nothing in `glyphs/` is an outline. A glyph is a list of skeletons to stroke,
plus a list of skeletons to fill:

```python
G["H"] = Glyph([line(0, B, 0, T), line(460, B, 460, T), line(0, M, 460, M)])
```

Symmetry is structural, not drawn twice — `u` is `n` rotated, `9` is `6` rotated,
and the other arrows are one arrow mirrored and turned:

```python
G["u"]   = Glyph([rot180(p, ra, (XT + B) / 2.0) for p in arch(ra)])
G["nine"] = Glyph([rot180(p, r6, M) for p in six])
G["arrowleft"] = Glyph([mirror_x(shaft, 280), mirror_x(head, 280)])
```

A stroke may carry a width multiplier, which is how the airliner gets a heavier
fuselage without a second drawing:

```python
G["airplane"] = Glyph([
    (line(0, -90, 0, 640), 1.55),      # fuselage
    (line(0, 470, -380, 170), 1.25),   # wings
])
```

### Dots are filled, not stroked

`.`, `i`, `:` and friends are filled circles. A filled circle is a cleaner
outline than a round cap on a zero-length line, and it keeps the optical size of
the period stable as weight increases.

## Spacing and kerning

Sidebearings are per *class*, not per glyph — a flat bar needs less air than a
stem, which needs less than a diagonal tip:

```python
EDGE = {"s": 72, "r": 52, "f": 46, "d": 20}   # stem, round, flat, diagonal
SIDES = {"A": "dd", "H": "ss", "O": "rr", "T": "ff", ...}
```

That keeps a line of text evenly spaced without hand-nudging 87 glyphs.

Kerning is a plain table in `layout.py`, compiled to a GPOS `kern` feature:

```python
KERN = (("A", "V", -55), ("T", "a", -45), ("L", "T", -70), ...)
```

If the feature compiler ever rejects the data, the build logs it and continues —
kerning is a nicety and should never block a release.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

142 tests, no network, roughly a second. They cover the design space (strokes
land inside the declared metrics at every weight), the skeleton primitives (arcs
stay on their radius, rounded corners stay inside their segments), the compiled
binaries (cmap coverage, `hmtx` agrees with `glyf`, figures are tabular and
centred, no cubic segments survive, every contour is wound the same way, heavier
weights carry more ink), and the CLI.

`layout.check_coverage()` runs on every build: if a glyph is drawn without a
codepoint, a codepoint has no glyph, or a kern pair names a glyph that no longer
exists, the build stops with a specific message instead of quietly shipping a
font with a hole in it.

## Tools

```bash
python tools/specimen.py                  # contact sheet → specimen.png
python tools/specimen.py --weight medium --size 96
python tools/html_specimen.py             # offline HTML specimen, fonts inlined

python build.py --out /tmp/fresh          # build a second copy to compare against
python tools/verify_fonts.py fonts /tmp/fresh
```

`verify_fonts.py` is what the release workflow runs to prove the committed
binaries still match the source. Two builds of identical source differ in
exactly four bytes — the `head` timestamps and the checksum that follows from
them — so everything else is compared directly, and a stale artifact fails the
build instead of shipping.

## Adding a character

1. Draw it in the matching `glyphs/` module, add it to that module's `draw()`
   return.
2. Add its name to the right list in `layout.py` (`UPPERCASE`, `LOWERCASE`,
   `FIGURES`, `PUNCTUATION`, `SYMBOLS`) and its codepoint to `EXTRA_CODEPOINTS`.
3. Give it a sidebearing class in `SIDES` unless it is round on both sides (then
   it defaults to `rr`).
4. Add kern pairs in `KERN` if it needs them.
5. `python build.py` — `check_coverage()` will tell you if you missed a step.

The name lists are **frozen order**, not alphabetical: the builder writes glyphs
in that order, and the glyph order is part of the font's binary identity.
Reordering renumbers every glyph and changes the shipped files for no visual
gain. `test_design.py` asserts the drawn set matches the declared order, so a new
character cannot be added without being placed.

## Known quirks

Two oddities are inherited from the original build and deliberately preserved, so
the shipped binaries stay byte-identical. Both are noted at their definitions:

- **`head` timestamps.** `created`/`modified` are stamped at build time, so two
  builds of the same source differ in those four bytes (and in
  `checkSumAdjustment`). Everything else — every glyph outline, metric and table
  — is reproducible.
- **`.notdef` left sidebearing** is a fixed `60` at all weights, so it does not
  equal the outline's actual `xMin` at Light and Medium. Nothing shifts, because
  the advance is fixed too. `monochrome/layout.py:NOTDEF_LSB` explains how to
  derive it if you would rather it matched.

## License

**CC BY-ND 4.0** — [Creative Commons Attribution-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nd/4.0/)

You are free to share this font and this source code, including commercially,
as long as you credit the author and link to the license. **No derivatives:**
you may not publish a modified version — a redrawn glyph, a new weight, a
subset, or a renamed repackage. (Formatting the source for readability, or
building it with a different toolchain, is not a derivative.)

The fonts in `fonts/` and this source code are covered by the same license.
Attribution should name the author and point at the project URL.

Note that this licence blocks the two things most font projects want to allow:
subsetting (a common workflow — shipping a smaller character set to save bytes)
and adding weights or italics. If you later want those permitted, the
[OFL 1.1](https://openfontlicense.org/) is the usual choice for typefaces.

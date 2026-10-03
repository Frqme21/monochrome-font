"""Compile a set of glyph outlines into a TrueType font.

This module owns the parts of a font that are not glyphs: glyph order, advance
widths and sidebearings, vertical metrics, the name table, and kerning.
"""

from __future__ import annotations

import os
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from pathops import Path as SkPath

from . import layout
from .glyph import Glyph
from .layout import DIGITS, edges, kern_feature
from .metrics import CAP, FAMILY, UPM, VERSION, WEIGHTS, Weight, XH
from .outline import outline, outline_glyphs, to_ttglyph
from .skeleton import Sk

#: Vertical metrics of the compiled font, in font units.
#:
#: The design lines run from ASC to DESC, but a font also has to leave room for
#: accents and for the overshoot of the round shapes, so the public metrics are
#: looser than the drawing area.
TYPO_ASCENT = 820
TYPO_DESCENT = -260
LINE_GAP = 0
WIN_ASCENT = 950
WIN_DESCENT = 320

#: Formats written for each weight.
DEFAULT_FORMATS = ("ttf", "woff2")

#: Where ``python -m monochrome`` writes by default.
DEFAULT_OUTDIR = Path(__file__).resolve().parent.parent / "fonts"


# --------------------------------------------------------------------------
# Horizontal metrics
# --------------------------------------------------------------------------
def figure_advance(paths: dict[str, SkPath]) -> int:
    """The shared advance width of the tabular figures.

    Figures are as wide as the widest of them plus a fixed amount of optical air,
    and every figure is then centred inside it - so ``1``, ``7`` and ``0`` sit in
    the same column.
    """
    widest = 0.0
    for name in DIGITS:
        xmin, _, xmax, _ = paths[name].bounds or (0.0, 0.0, 0.0, 0.0)
        widest = max(widest, xmax - xmin)
    return int(round(widest + 2 * layout.FIGURE_AIR))


def notdef_glyph(stroke: float) -> Glyph:
    """``.notdef``: the hollow rounded box that shows for a missing glyph."""
    return Glyph([Sk().poly([(90, 40), (90, 660), (470, 660), (470, 40)], r=60, closed=True)])


def place(name: str, path: SkPath, dig_adv: int) -> tuple[float, int, int]:
    """Work out ``(dx, advance, lsb)`` for one glyph.

    ``dx`` moves the outline into place, ``advance`` is the cell width and
    ``lsb`` must end up equal to the placed outline's ``xMin``.

    Figures are centred in the shared tabular cell; every other glyph gets its
    sidebearing class.  A glyph with no ink (an empty path) is placed at the
    origin rather than crashing on a null bounding box.
    """
    if path.bounds is None:
        # No ink: place at the origin instead of tripping over a null bbox.
        xmin = xmax = 0.0
    else:
        xmin, _, xmax, _ = path.bounds

    if name in DIGITS:
        dx = (dig_adv - (xmax - xmin)) / 2.0 - xmin
        return dx, dig_adv, dx + xmin

    left, right = edges(name)
    advance = int(round(xmax - xmin + left + right))
    dx = left - xmin
    return dx, advance, float(left)


# --------------------------------------------------------------------------
# Font assembly
# --------------------------------------------------------------------------
def build_font(
    weight: Weight,
    outdir: Path | str = DEFAULT_OUTDIR,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
) -> list[Path]:
    """Compile one weight and write it out.

    Args:
        weight: which member of the family to build.
        outdir: directory to write into; created if missing.
        formats: subset of ``("ttf", "woff2")``.

    Returns:
        The paths written, in the order they were written.
    """
    from .glyphs import design

    glyphs = design(weight.stroke)
    layout.check_coverage(glyphs)
    paths = outline_glyphs(glyphs, weight.stroke)

    glyph_order = [".notdef", "space", *glyphs]
    compiled: dict[str, object] = {}
    metrics: dict[str, tuple[int, int]] = {}
    dig_adv = figure_advance(paths)

    for name, path in paths.items():
        dx, advance, lsb = place(name, path, dig_adv)
        compiled[name] = to_ttglyph(path, dx)
        metrics[name] = (advance, int(round(lsb)))

    # .notdef is a fixed shape, so it is stroked thinner than the text.
    compiled[".notdef"] = to_ttglyph(outline(notdef_glyph(weight.stroke), weight.stroke * 0.7))
    metrics[".notdef"] = (layout.NOTDEF_ADVANCE, layout.NOTDEF_LSB)
    compiled["space"] = TTGlyphPen(None).glyph()
    metrics["space"] = (layout.SPACE_ADVANCE, 0)

    # Codepoint -> glyph name, plus the two space characters mapped to `space`.
    charmap = {0x20: "space", 0xA0: "space", **layout.CHARS}

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(charmap)
    fb.setupGlyf(compiled)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=TYPO_ASCENT, descent=TYPO_DESCENT, lineGap=LINE_GAP)
    setup_names(fb, weight)
    setup_os2(fb, weight)
    fb.setupPost(keepGlyphNames=True)
    setup_gasp(fb)
    setup_kerning(fb)

    written = write(fb, weight, outdir, formats)
    return written


def setup_names(fb: FontBuilder, weight: Weight) -> None:
    """Write the name table.

    Quirk kept from the original build: name ID 2 is always "Regular" and ID 1
    carries the style for the non-Regular weights.  That is the pre-RIBBI
    convention, kept so the shipped binaries stay byte-identical.  Apps that read
    name IDs 16/17 get the correct modern grouping: family, then subfamily.
    """
    full = f"{FAMILY} {weight.style}"
    is_regular = weight.style == "Regular"
    fb.setupNameTable({
        "familyName": FAMILY if is_regular else full,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{full}:{VERSION}",
        "fullName": full,
        "version": f"Version {VERSION}",
        "psName": full.replace(" ", "-"),
        "typographicFamily": FAMILY,
        "typographicSubfamily": weight.style,
    })


def setup_os2(fb: FontBuilder, weight: Weight) -> None:
    """Write the OS/2 table (the metrics browsers and design tools read)."""
    fb.setupOS2(
        sTypoAscender=TYPO_ASCENT,
        sTypoDescender=TYPO_DESCENT,
        sTypoLineGap=LINE_GAP,
        usWinAscent=WIN_ASCENT,
        usWinDescent=WIN_DESCENT,
        sxHeight=XH,
        sCapHeight=CAP,
        usWeightClass=weight.us_weight_class,
        usWidthClass=5,
        fsType=0,
    )


def setup_gasp(fb: FontBuilder) -> None:
    """Enable grid fitting, symmetric smoothing and grayscale AA at all sizes.

    The range covers every size from 0 to 0xFFFF, so no size is left to default.
    This is a monoline with round joins and no hinting program; symmetric
    smoothing is what keeps those joins smooth at small sizes.
    """
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    fb.font["gasp"] = gasp


def setup_kerning(fb: FontBuilder) -> None:
    """Compile the kern feature into GPOS.

    Kerning is a nicety, not a requirement: if the feature compiler rejects the
    data the font is still worth shipping, so a failure is reported and ignored
    rather than killing the build.
    """
    try:
        fb.addOpenTypeFeatures(kern_feature())
    except Exception as exc:  # noqa: BLE001 - never block the build on kerning
        print(f"  (kerning skipped: {exc})")


def write(
    fb: FontBuilder,
    weight: Weight,
    outdir: Path | str,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
) -> list[Path]:
    """Save the compiled font in each requested format.

    WOFF2 needs the optional ``brotli`` package; if it is missing the TTF is
    still written and the WOFF2 is reported as skipped.
    """
    os.makedirs(outdir, exist_ok=True)
    base = Path(outdir) / weight.filename
    written: list[Path] = []

    if "ttf" in formats:
        path = base.with_suffix(".ttf")
        fb.font.save(str(path))
        written.append(path)
    if "woff2" in formats:
        path = base.with_suffix(".woff2")
        try:
            fb.font.flavor = "woff2"
            fb.font.save(str(path))
        except Exception as exc:  # noqa: BLE001 - brotli is an optional extra
            print(f"  (woff2 skipped: {exc})")
        else:
            written.append(path)
    return written


def build_all(
    outdir: Path | str = DEFAULT_OUTDIR,
    weights: tuple[Weight, ...] = WEIGHTS,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
) -> list[Path]:
    """Build every weight, returning all paths written."""
    written: list[Path] = []
    for weight in weights:
        written.extend(build_font(weight, outdir, formats))
    return written

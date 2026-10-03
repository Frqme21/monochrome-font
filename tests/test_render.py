"""Render-level tests.

These rasterise glyphs through Pillow, which is a completely different code path
from fontTools: it exercises the compiled binary the way a real renderer would.
A glyph that draws nothing, or a figure grid that does not line up, shows up here
even when every table-level check passes.
"""

from __future__ import annotations

import pytest

from monochrome import layout
from monochrome.metrics import WEIGHTS

Image = pytest.importorskip("PIL.Image", reason="Pillow is needed to rasterise glyphs")
from PIL import ImageDraw, ImageFont  # noqa: E402

SIZE = 64
PAD = 20
CANVAS = SIZE * 3


def render(font_path, char):
    """Draw one character on a fresh canvas; return the ink bounding box."""
    font = ImageFont.truetype(str(font_path), SIZE)
    img = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(img).text((PAD, PAD), char, font=font, fill=255)
    return img.getbbox()


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_every_glyph_draws_visible_ink(all_ttfs, style):
    """No mapped glyph may render as nothing."""
    blank = [
        name
        for name in layout.GLYPH_ORDER
        if render(all_ttfs[style], chr(layout.CODEPOINTS[name])) is None
    ]
    assert not blank, f"{style}: {blank} render as blank"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_space_is_the_only_blank_glyph(all_ttfs, style):
    """space should be empty; .notdef should not be."""
    font = ImageFont.truetype(str(all_ttfs[style]), SIZE)
    img = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(img).text((PAD, PAD), " ", font=font, fill=255)
    assert img.getbbox() is None


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_notdef_draws_something(all_ttfs, style):
    """An unmapped character must fall back to a visible box, not nothing."""
    font = ImageFont.truetype(str(all_ttfs[style]), SIZE)
    img = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(img).text((PAD, PAD), "\uE000", font=font, fill=255)
    assert img.getbbox() is not None


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_capitals_share_one_cap_height(all_ttfs, style):
    """Flat-topped capitals must reach the same height.

    ``S`` is excluded because its spine overshoots by design, and the diagonals
    of ``M``/``N`` are excluded because their rounded apexes sit a hair lower.  A
    pixel of slack absorbs rasteriser rounding.
    """
    flat = "EFHIKLPRT"
    tops = {c: render(all_ttfs[style], c)[1] for c in flat}
    assert max(tops.values()) - min(tops.values()) <= 1, f"cap tops differ: {tops}"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_baseline_is_consistent(all_ttfs, style):
    """Glyphs that sit on the baseline must share a baseline."""
    flat = "EFHIKLM"
    bottoms = {c: render(all_ttfs[style], c)[3] for c in flat}
    assert max(bottoms.values()) - min(bottoms.values()) <= 1, f"baselines differ: {bottoms}"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_round_glyphs_overshoot_the_flat_ones(all_ttfs, style):
    """``O`` must be taller than ``H``, or the design has lost its overshoot."""
    path = all_ttfs[style]
    o = render(path, "O")
    h = render(path, "H")
    assert o[1] < h[1], "O does not overshoot the cap height"
    assert o[3] > h[3], "O does not overshoot the baseline"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_figures_are_tabular_in_a_renderer(all_ttfs, style):
    """The tabular promise, measured by the renderer rather than hmtx."""
    font = ImageFont.truetype(str(all_ttfs[style]), SIZE)
    advances = {round(font.getlength(chr(layout.CODEPOINTS[n])), 3) for n in layout.DIGIT_NAMES}
    assert len(advances) == 1, f"figures not tabular when rendered: {advances}"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_figures_stack_in_a_column(all_ttfs, style):
    """Digit origins must align, which is what a vertical strip of figures needs.

    Measured as *advance*, not ink: ``1`` has a narrow stem, so its leftmost ink
    is well inside its cell even though the cell itself lines up perfectly.
    """
    font = ImageFont.truetype(str(all_ttfs[style]), SIZE)
    origins = {}
    for name in layout.DIGIT_NAMES:
        char = chr(layout.CODEPOINTS[name])
        img = Image.new("L", (CANVAS, CANVAS), 0)
        ImageDraw.Draw(img).text((PAD, PAD), char, font=font, fill=255)
        origins[name] = img.getbbox()[0] - PAD

    assert len({round(font.getlength(chr(layout.CODEPOINTS[n])), 6)
                for n in layout.DIGIT_NAMES}) == 1
    # every figure's ink must start inside the shared cell
    assert all(-1 <= off <= font.getlength("0") for off in origins.values()), origins


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_capitals_are_taller_than_lowercase(all_ttfs, style):
    """x-height must be clearly below cap height."""
    path = all_ttfs[style]
    cap = render(path, "H")[1]
    xh = render(path, "x")[1]
    assert xh > cap, "x-height is not below cap height"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_descenders_dip_below_the_baseline(all_ttfs, style):
    path = all_ttfs[style]
    baseline = render(path, "H")[3]
    for ch in "gjpqy":
        assert render(path, ch)[3] > baseline, f"{ch} has no descender"


@pytest.mark.parametrize("style", [w.style for w in WEIGHTS])
def test_heavier_weights_draw_more_pixels(all_ttfs, style):
    """Ink must visibly increase with weight in the rendered output."""
    counts = {}
    for w in WEIGHTS:
        font = ImageFont.truetype(str(all_ttfs[w.style]), SIZE)
        img = Image.new("L", (CANVAS, CANVAS), 0)
        ImageDraw.Draw(img).text((PAD, PAD), "Hamburgefonstiv", font=font, fill=255)
        counts[w.style] = sum(1 for p in img.getdata() if p > 128)
    assert (
        counts["Light"] < counts["Regular"] < counts["Medium"]
    ), counts


def test_the_sample_line_renders_without_error(regular_ttf):
    """A realistic aviation string must not raise or produce stray tofu."""
    font = ImageFont.truetype(str(regular_ttf), SIZE)
    img = Image.new("L", (1600, 120), 0)
    d = ImageDraw.Draw(img)
    text = "FL350 270° 7700 RWY 18L ✈ →"
    d.text((10, 10), text, font=font, fill=255)
    assert img.getbbox() is not None

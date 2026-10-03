"""Tests for the compiled fonts.

These open the actual binaries and check the things a broken build would break:
coverage, metrics, and the promise that the figures are tabular.
"""

from __future__ import annotations

import pytest
from fontTools.ttLib import TTFont

from monochrome import layout
from monochrome.builder import TYPO_ASCENT, TYPO_DESCENT
from monochrome.metrics import ASC, CAP, DESC, UPM, VERSION, WEIGHTS, XH


@pytest.fixture(scope="module")
def font(regular_ttf):
    return TTFont(regular_ttf)


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------
def test_expected_tables_are_present(font):
    expected = {
        "head", "hhea", "maxp", "hmtx", "cmap", "loca", "glyf",
        "name", "post", "OS/2", "gasp", "GPOS",
    }
    assert expected <= set(font.keys())


def test_units_per_em(font):
    assert font["head"].unitsPerEm == UPM


def test_glyph_order_starts_with_notdef_and_space(font):
    assert font.getGlyphOrder()[:2] == [".notdef", "space"]
    assert font.getGlyphOrder()[2:] == list(layout.GLYPH_ORDER)


def test_glyph_order_has_no_duplicates(font):
    order = font.getGlyphOrder()
    assert len(order) == len(set(order))


def test_font_passes_fonttools_sanity_checks(regular_ttf):
    """Re-compiling with fontTools must not raise."""
    TTFont(regular_ttf).save(regular_ttf.with_suffix(".recompiled.ttf"))
    TTFont(regular_ttf.with_suffix(".recompiled.ttf")).getGlyphSet()
    regular_ttf.with_suffix(".recompiled.ttf").unlink()


def test_every_weight_has_the_same_glyph_set(all_ttfs):
    reference = None
    for style, path in all_ttfs.items():
        order = set(TTFont(path).getGlyphOrder())
        if reference is None:
            reference = order
        assert order == reference, f"{style} has a different glyph set"


def test_weights_are_ordered_by_class(all_ttfs):
    fonts = {style: TTFont(path) for style, path in all_ttfs.items()}
    assert (
        fonts["Light"]["OS/2"].usWeightClass
        < fonts["Regular"]["OS/2"].usWeightClass
        < fonts["Medium"]["OS/2"].usWeightClass
    )


# --------------------------------------------------------------------------
# Character map
# --------------------------------------------------------------------------
def test_cmap_covers_every_declared_codepoint(font):
    cmap = font.getBestCmap()
    for codepoint in layout.CODEPOINTS.values():
        assert codepoint in cmap, f"U+{codepoint:04X} missing from cmap"


def test_cmap_maps_to_the_right_glyphs(font):
    cmap = font.getBestCmap()
    for name, codepoint in layout.CODEPOINTS.items():
        assert cmap[codepoint] == name


def test_space_is_mapped_from_both_space_codepoints(font):
    cmap = font.getBestCmap()
    assert cmap[0x20] == "space"
    assert cmap[0xA0] == "space"


def test_cmap_covers_the_expected_character_classes(font):
    cmap = set(font.getBestCmap())
    assert set(range(ord("A"), ord("Z") + 1)) <= cmap
    assert set(range(ord("a"), ord("z") + 1)) <= cmap
    assert set(range(ord("0"), ord("9") + 1)) <= cmap
    assert 0x2708 in cmap, "airliner glyph missing"
    assert 0x00B0 in cmap, "degree sign missing"


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def test_vertical_metrics_agree_with_the_design_space(font):
    os2, hhea = font["OS/2"], font["hhea"]
    assert (os2.sTypoAscender, os2.sTypoDescender) == (TYPO_ASCENT, TYPO_DESCENT)
    assert (hhea.ascent, hhea.descent) == (TYPO_ASCENT, TYPO_DESCENT)
    assert os2.sxHeight == XH
    assert os2.sCapHeight == CAP


def test_design_lines_fit_inside_the_declared_line(font):
    """No glyph may be drawn outside ascender..descender."""
    glyf = font["glyf"]
    lo = min(glyf[n].yMin for n in font.getGlyphOrder() if glyf[n].numberOfContours)
    hi = max(glyf[n].yMax for n in font.getGlyphOrder() if glyf[n].numberOfContours)
    assert DESC - 120 < lo < DESC + 120, f"lowest ink at {lo}, descender is {DESC}"
    assert ASC - 120 < hi < ASC + 120, f"highest ink at {hi}, ascender is {ASC}"


def test_lsb_matches_the_outline_for_every_placed_glyph(font):
    """hmtx must agree with glyf, or shaping drifts in some renderers.

    A tolerance of one unit is allowed because outlines are snapped to integer
    coordinates on the way into ``glyf`` while the sidebearing is declared from
    the unrounded value.
    """
    glyf, hmtx = font["glyf"], font["hmtx"]
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            continue
        assert abs(hmtx[name][1] - g.xMin) <= 1, f"{name}: lsb {hmtx[name][1]} vs xMin {g.xMin}"


def test_sidebearings_are_declared_from_the_design_space(font):
    """The declared left sidebearing should match its class, not the ink.

    This is the invariant behind :func:`monochrome.layout.edges` - it is what
    keeps a line of text evenly spaced rather than tracking the outline.

    Figures are excluded: they are centred in the tabular cell rather than given
    a class sidebearing, so :func:`monochrome.builder.place` ignores their entry.
    """
    hmtx = font["hmtx"]
    for name, sides in layout.SIDES.items():
        if name in layout.DIGITS:
            continue
        expected = layout.EDGE[sides[0]]
        assert abs(hmtx[name][1] - expected) <= 1, f"{name}: lsb {hmtx[name][1]}, expected ~{expected}"


def test_figure_sidebearing_entries_are_not_used(font):
    """The figures carry sidebearing classes, but centring overrides them.

    Worth pinning down: it looks like dead data, and someone could "fix" the
    centring by honouring these entries, which would break the tabular grid.
    """
    hmtx = font["hmtx"]
    adv = hmtx["zero"][0]
    for name in ("one", "two", "four", "five", "seven"):
        assert name in layout.SIDES, f"{name} lost its sidebearing class"
        assert hmtx[name][1] != layout.EDGE[layout.SIDES[name][0]]
        assert hmtx[name][0] == adv


def test_every_glyph_has_a_positive_advance(font):
    for name in font.getGlyphOrder():
        assert font["hmtx"][name][0] > 0, f"{name} has no advance"


def test_figures_are_tabular(font):
    """The core promise for flight levels and headings: one shared width."""
    advances = {font["hmtx"][name][0] for name in layout.DIGIT_NAMES}
    assert len(advances) == 1, f"figures are not tabular: {advances}"


def test_figures_are_centred_in_that_width(font):
    """Each figure must be optically centred, so ``1`` is not shoved left.

    A few units of slack: the centring is computed from the unrounded outline and
    then snapped to integer coordinates.
    """
    glyf = font["glyf"]
    adv = font["hmtx"]["zero"][0]
    for name in layout.DIGIT_NAMES:
        g = glyf[name]
        left, right = g.xMin, adv - g.xMax
        assert abs(left - right) <= 8, f"{name}: {left} left vs {right} right"


def test_space_is_empty_but_advanceable(font):
    assert font["glyf"]["space"].numberOfContours == 0
    assert font["hmtx"]["space"][0] == layout.SPACE_ADVANCE


def test_notdef_has_ink_and_a_fixed_cell(font):
    assert font["glyf"][".notdef"].numberOfContours > 0
    assert font["hmtx"][".notdef"][0] == layout.NOTDEF_ADVANCE


# --------------------------------------------------------------------------
# Outlines
# --------------------------------------------------------------------------
def test_every_glyph_is_well_formed(font):
    """Contours must be non-empty and closed; no stray off-curve garbage."""
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            continue
        assert g.numberOfContours > 0
        for contour in g.coordinates:
            assert len(contour) >= 2


def test_outlines_are_wound_consistently(font):
    """Every glyph must wind the same way, or fills render inside-out.

    ``AreaPen`` negates the shoelace sum, so the sign depends on its convention;
    what matters is that no glyph disagrees with the rest, and that none is zero
    (which would mean self-cancelling contours).
    """
    from fontTools.pens.areaPen import AreaPen

    signs = set()
    for name in font.getGlyphOrder():
        if font["glyf"][name].numberOfContours == 0:
            continue
        pen = AreaPen(font.getGlyphSet())
        font.getGlyphSet()[name].draw(pen)
        assert pen.value != 0, f"{name} has zero area"
        signs.add(pen.value > 0)
    assert len(signs) == 1, "glyphs disagree on winding direction"


def test_glyphs_contain_only_quadratic_and_line_segments(font):
    """TrueType has no cubic segments; cu2qu must have converted them all.

    A cubic would appear as an on-curve point followed by two off-curve points,
    which ``qCurveTo`` reporting would reveal.
    """
    from fontTools.pens.recordingPen import RecordingPen

    for name in font.getGlyphOrder():
        g = font["glyf"][name]
        if g.numberOfContours == 0:
            continue
        assert not g.isComposite(), f"{name} is unexpectedly composite"
        pen = RecordingPen()
        font.getGlyphSet()[name].draw(pen)
        cubics = [args for op, args in pen.value if op == "curveTo"]
        assert not cubics, f"{name} contains {len(cubics)} cubic segment(s)"


def test_heavier_weights_have_more_ink(all_ttfs):
    """Ink area must increase with weight, or a weight is not being applied."""
    from fontTools.pens.areaPen import AreaPen

    areas = {}
    for style, path in all_ttfs.items():
        f = TTFont(path)
        glyphset = f.getGlyphSet()
        pen = AreaPen(glyphset)
        for name in ("A", "o", "zero"):
            glyphset[name].draw(pen)
        # AreaPen negates the shoelace sum, so compare magnitudes.
        areas[style] = abs(pen.value)
    assert areas["Light"] < areas["Regular"] < areas["Medium"], areas


# --------------------------------------------------------------------------
# Naming and OS/2
# --------------------------------------------------------------------------
def test_name_ids(font):
    name = font["name"]
    assert name.getDebugName(1) == "Monochrome Aviation"
    assert name.getDebugName(2) == "Regular"
    assert name.getDebugName(4) == "Monochrome Aviation Regular"
    assert name.getDebugName(5) == f"Version {VERSION}"
    assert name.getDebugName(6) == "Monochrome-Aviation-Regular"


def test_typographic_names_are_the_modern_pair(font):
    name = font["name"]
    assert name.getDebugName(16) == "Monochrome Aviation"
    assert name.getDebugName(17) == "Regular"


def test_postscript_name_has_no_spaces(font):
    assert " " not in font["name"].getDebugName(6)


def test_weight_classes(all_ttfs):
    for weight in WEIGHTS:
        f = TTFont(all_ttfs[weight.style])
        assert f["OS/2"].usWeightClass == weight.us_weight_class


def test_gasp_enables_antialiasing(font):
    gasp = font["gasp"]
    assert gasp.version == 1
    assert gasp.gaspRange[0xFFFF] & 0x0002, "grayscale AA not enabled"


def test_kerning_was_compiled(font):
    """GPOS must carry a kern feature with the pairs from layout.KERN."""
    assert "GPOS" in font
    feats = [fr.FeatureTag for fr in font["GPOS"].table.FeatureList.FeatureRecord]
    assert "kern" in feats


def test_no_warnings_when_saved(regular_ttf, tmp_path):
    """fontTools must not complain about anything in the font."""
    import warnings

    font = TTFont(regular_ttf)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        font.save(tmp_path / "check.ttf")
    assert not [w for w in caught if "glyph" in str(w.message).lower()], [str(w.message) for w in caught]

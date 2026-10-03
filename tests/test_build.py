"""Tests for the build pipeline and the command line.

The point of these is that a broken *build* (as opposed to a broken design) is
caught before it reaches ``fonts/``.
"""

from __future__ import annotations

import contextlib
import io

import pytest
from fontTools.pens.ttGlyphPen import TTGlyphPen

from monochrome import layout
from monochrome.builder import (
    DEFAULT_OUTDIR,
    build_all,
    build_font,
    figure_advance,
    place,
)
from monochrome.cli import main, parse_args
from monochrome.metrics import WEIGHTS
from monochrome.outline import outline, sanitize_path, to_ttglyph


# --------------------------------------------------------------------------
# Outlining
# --------------------------------------------------------------------------
def test_sanitize_does_not_mutate_its_input():
    """sanitize_path copies; the caller's path must be reusable."""
    from monochrome.primitives import circle

    original = circle(0, 0, 50).to_skia()
    before = str(original)
    sanitize_path(original)
    assert str(original) == before


def test_outline_of_empty_glyph_has_no_ink():
    """An empty glyph yields an empty path (skia reports a null bbox)."""
    from monochrome.glyph import Glyph

    empty = outline(Glyph(), 84)
    assert list(empty.bounds) == [0.0, 0.0, 0.0, 0.0]
    assert TTGlyphPen(None).glyph() is not None
    assert to_ttglyph(empty).numberOfContours == 0


def test_outline_is_stroked_wider_for_a_bigger_weight():
    from monochrome.glyph import Glyph
    from monochrome.primitives import line

    glyph = Glyph([line(0, 0, 500, 0)])
    thin = outline(glyph, 60)
    thick = outline(glyph, 120)
    assert (thick.bounds[3] - thick.bounds[1]) > (thin.bounds[3] - thin.bounds[1])


def test_stroke_multiplier_thickens_only_that_stroke():
    """The airliner leans on this; if it broke, the silhouette would go flat."""
    from monochrome.glyph import Glyph
    from monochrome.primitives import line

    glyph = Glyph([line(0, 0, 500, 0), (line(0, 0, 500, 300), 1.5)])
    xmin, ymin, xmax, ymax = outline(glyph, 84).bounds
    plain = Glyph([line(0, 0, 500, 0), line(0, 0, 500, 300)])
    _, pymin, _, pymax = outline(plain, 84).bounds
    # the second stroke is heavier, so it overshoots further vertically
    assert ymax > pymax and ymin < pymin


def test_figure_advance_is_shared_and_wider_than_the_widest_figure(designs):
    from monochrome.outline import outline_glyphs

    paths = outline_glyphs(designs[84], 84)
    adv = figure_advance(paths)
    for name in layout.DIGITS:
        xmin, _, xmax, _ = paths[name].bounds
        assert xmax - xmin < adv


def test_place_centres_figures_and_spaces_letters():
    from monochrome.outline import outline_glyphs
    from monochrome.glyphs import design

    paths = outline_glyphs(design(84), 84)
    adv = figure_advance(paths)

    dx, advance, lsb = place("zero", paths["zero"], adv)
    assert advance == adv
    _, _, lsb_letter = place("A", paths["A"], adv)
    assert lsb_letter == layout.EDGE[layout.SIDES["A"][0]]


def test_place_survives_an_empty_glyph():
    """A glyph with no ink must not crash the build.

    skia-pathops reports the bounds of an empty path as all zeros rather than
    ``None``, so this pins the behaviour the builder actually has to cope with.
    """
    from pathops import Path as SkPath

    empty = SkPath()
    assert empty.bounds == (0.0, 0.0, 0.0, 0.0)

    dx, advance, lsb = place("A", empty, 600)
    assert advance > 0
    assert dx == lsb == layout.EDGE[layout.SIDES["A"][0]]


def test_place_survives_a_null_bbox(monkeypatch):
    """Guard the ``None`` branch too, in case pathops ever changes."""
    from pathops import Path as SkPath

    empty = SkPath()
    monkeypatch.setattr(type(empty), "bounds", property(lambda self: None))
    assert empty.bounds is None

    dx, advance, lsb = place("zero", empty, 600)
    assert (advance, lsb) == (600, 300)
    assert dx == 300


# --------------------------------------------------------------------------
# build_font
# --------------------------------------------------------------------------
def test_build_font_writes_both_formats(tmp_path):
    written = build_font(WEIGHTS[1], tmp_path, ("ttf", "woff2"))
    assert [p.name for p in written] == [
        "monochrome-aviation.ttf",
        "monochrome-aviation.woff2",
    ]
    assert all(p.exists() and p.stat().st_size > 0 for p in written)


def test_woff2_is_really_woff2(tmp_path):
    """A woff2 must carry the wOF2 signature, not be a renamed ttf."""
    written = build_font(WEIGHTS[1], tmp_path, ("woff2",))
    assert written[0].read_bytes()[:4] == b"wOF2"


def test_ttf_is_really_ttf(tmp_path):
    written = build_font(WEIGHTS[1], tmp_path, ("ttf",))
    assert written[0].read_bytes()[:4] in (b"\x00\x01\x00\x00", b"true")


def test_build_font_creates_the_output_directory(tmp_path):
    out = tmp_path / "nested" / "deeper"
    assert not out.exists()
    build_font(WEIGHTS[1], out, ("ttf",))
    assert out.is_dir()


def test_build_all_writes_every_weight(tmp_path):
    written = build_all(tmp_path, WEIGHTS, ("ttf",))
    assert len(written) == len(WEIGHTS)
    assert {p.stem for p in written} == {w.filename for w in WEIGHTS}


def test_weights_have_distinct_strokes_and_filenames():
    assert len({w.stroke for w in WEIGHTS}) == len(WEIGHTS)
    assert len({w.filename for w in WEIGHTS}) == len(WEIGHTS)
    assert len({w.style for w in WEIGHTS}) == len(WEIGHTS)


def test_weight_classes_are_ascending():
    classes = [w.us_weight_class for w in WEIGHTS]
    assert classes == sorted(classes)


def test_regular_has_the_unsuffixed_filename():
    """The most commonly installed weight must not be called "-regular"."""
    regular = next(w for w in WEIGHTS if w.style == "Regular")
    assert regular.filename == "monochrome-aviation"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def test_cli_builds_the_default_weights(tmp_path, capsys):
    assert main(["--out", str(tmp_path), "-q"]) == 0
    assert {p.name for p in tmp_path.iterdir()} == {
        "monochrome-aviation-light.ttf",
        "monochrome-aviation-light.woff2",
        "monochrome-aviation.ttf",
        "monochrome-aviation.woff2",
        "monochrome-aviation-medium.ttf",
        "monochrome-aviation-medium.woff2",
    }


def test_cli_selects_a_single_weight(tmp_path):
    assert main(["--out", str(tmp_path), "--weights", "medium", "-q"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "monochrome-aviation-medium.ttf",
        "monochrome-aviation-medium.woff2",
    ]


def test_cli_weight_names_are_case_insensitive(tmp_path):
    assert main(["--out", str(tmp_path), "--weights", "REGULAR", "-q"]) == 0
    assert (tmp_path / "monochrome-aviation.ttf").exists()


def test_cli_selects_a_single_format(tmp_path):
    assert main(["--out", str(tmp_path), "--weights", "light", "--format", "ttf", "-q"]) == 0
    assert [p.suffix for p in tmp_path.iterdir()] == [".ttf"]


def test_cli_rejects_an_unknown_weight(tmp_path):
    with pytest.raises(SystemExit):
        parse_args(["--weights", "black"])


def test_cli_rejects_an_unknown_format(tmp_path):
    with pytest.raises(SystemExit):
        parse_args(["--format", "otf"])


def test_cli_default_outdir_is_the_fonts_folder():
    assert DEFAULT_OUTDIR.name == "fonts"
    assert DEFAULT_OUTDIR.is_dir()


def test_cli_quiet_suppresses_progress(tmp_path, capsys):
    main(["--out", str(tmp_path), "-q"])
    assert capsys.readouterr().out == ""


def test_cli_reports_errors_without_a_traceback(tmp_path, capsys):
    """A failure must exit 1 with a message, not raise."""
    unwritable = tmp_path / "file-not-a-dir"
    unwritable.write_text("not a directory")
    code = main(["--out", str(unwritable / "fonts"), "-q"])
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_cli_defaults_to_every_weight():
    assert parse_args([]).weights is None, "default should be resolved in main(), not parsed"


def test_cli_help_does_not_dump_repr_objects():
    """The --help default must be readable, not a NamedTuple repr."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            parse_args(["--help"])
    except SystemExit:
        pass
    out = buf.getvalue()
    assert "Weight(style=" not in out, "help text is leaking the NamedTuple repr"
    assert "default: all" in out


def test_cli_does_not_mutate_the_default_weight_list():
    """Building must not be able to corrupt the module-level WEIGHTS."""
    before = tuple(WEIGHTS)
    main(["--out", "/tmp/opencode/cli-mutation-check", "-q"])
    assert WEIGHTS == before

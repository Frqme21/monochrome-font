"""Tests for ``tools/verify_fonts.py``.

The release workflow gates on this tool, so its verdict has to be trustworthy:
it must pass on two builds of identical source (despite the differing ``head``
timestamp) and it must actually catch drift in an outline or in the metrics.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent


def _load_verify_fonts():
    """Import the tool by path - ``tools/`` is not a package."""
    spec = importlib.util.spec_from_file_location(
        "verify_fonts", ROOT / "tools" / "verify_fonts.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_fonts = _load_verify_fonts()


@pytest.fixture(scope="module")
def second_build(tmp_path_factory):
    """A second, independent build of every weight."""
    from monochrome.builder import build_all
    from monochrome.metrics import WEIGHTS

    out = tmp_path_factory.mktemp("rebuild")
    build_all(out, WEIGHTS, ("ttf",))
    return out


def _edit_copy(source: Path, tmp_path: Path, edit) -> Path:
    """Copy a font, hand the open TTFont to ``edit``, and save it back."""
    path = tmp_path / source.name
    shutil.copy(source, path)
    font = TTFont(path)
    edit(font)
    font.save(path)
    return path


def _shift_h(font: TTFont) -> None:
    """Move glyph ``H`` up 7 units, leaving every other glyph alone."""
    glyphs = font.getGlyphSet()
    pen = TTGlyphPen(glyphs)
    glyphs["H"].draw(TransformPen(pen, (1, 0, 0, 1, 0, 7)))
    font["glyf"]["H"] = pen.glyph()


def _widen_h(font: TTFont) -> None:
    """Give ``H`` 3 more units of advance, leaving the outline untouched."""
    advance, lsb = font["hmtx"]["H"]
    font["hmtx"]["H"] = (advance + 3, lsb)


# --------------------------------------------------------------------------
def test_two_builds_of_the_same_source_agree(built_dir, second_build):
    """The head timestamp differs between builds and must not be counted."""
    assert verify_fonts.verify(built_dir, second_build) == []


def test_an_empty_directory_is_not_silently_a_pass(tmp_path):
    assert verify_fonts.verify(tmp_path, tmp_path) == [f"no .ttf files found in {tmp_path}"]


def test_a_missing_rebuild_is_reported(built_dir, tmp_path):
    problems = verify_fonts.verify(built_dir, tmp_path / "nowhere")
    assert problems
    assert all("missing from" in p for p in problems)


def test_a_shifted_glyph_is_caught(tmp_path, regular_ttf):
    edited = _edit_copy(regular_ttf, tmp_path, _shift_h)
    problems = verify_fonts.verify(tmp_path, regular_ttf.parent)
    assert problems == [f"{edited.name}: glyph 'H' outline differs"]


def test_a_changed_advance_is_caught(tmp_path, regular_ttf):
    """Metrics drift without any outline change still has to fail."""
    edited = _edit_copy(regular_ttf, tmp_path, _widen_h)
    problems = verify_fonts.verify(tmp_path, regular_ttf.parent)
    assert problems == [f"{edited.name}: metrics (hmtx) differ"]


def test_glyph_order_drift_is_caught(tmp_path, regular_ttf):
    """Reordering renumbers every glyph, which changes the binary."""

    def swap_first_two(font: TTFont) -> None:
        order = font.getGlyphOrder()
        order[0], order[1] = order[1], order[0]
        font.setGlyphOrder(order)

    edited = _edit_copy(regular_ttf, tmp_path, swap_first_two)
    problems = verify_fonts.verify(tmp_path, regular_ttf.parent)
    assert problems == [f"{edited.name}: glyph order differs"]


def test_cli_exit_codes(built_dir, second_build, tmp_path, capsys):
    assert verify_fonts.main([str(built_dir), str(second_build)]) == 0
    assert "match the source" in capsys.readouterr().out

    assert verify_fonts.main([str(built_dir), str(tmp_path / "nowhere")]) == 1
    assert "difference" in capsys.readouterr().err
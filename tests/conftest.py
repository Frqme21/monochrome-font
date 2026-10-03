"""Shared fixtures.

The fonts are built once per session into a temporary directory and reused, so
the test suite pays for a compile only once.
"""

from __future__ import annotations

import pytest

from monochrome.builder import build_all
from monochrome.glyphs import design
from monochrome.metrics import WEIGHTS

STROKES = tuple(w.stroke for w in WEIGHTS)


@pytest.fixture(scope="session")
def built_dir(tmp_path_factory):
    """A directory containing every weight as ``.ttf``."""
    out = tmp_path_factory.mktemp("fonts")
    build_all(out, WEIGHTS, ("ttf",))
    return out


@pytest.fixture(scope="session")
def regular_ttf(built_dir):
    """Path to the compiled Regular TTF."""
    return built_dir / "monochrome-aviation.ttf"


@pytest.fixture(scope="session")
def all_ttfs(built_dir):
    """Path to every compiled TTF, keyed by style name."""
    return {w.style: built_dir / f"{w.filename}.ttf" for w in WEIGHTS}


@pytest.fixture(scope="session")
def designs():
    """Every weight's glyph designs, keyed by stroke width."""
    return {stroke: design(stroke) for stroke in STROKES}

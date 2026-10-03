"""Monochrome Aviation - a minimal, fully rounded monoline sans.

Every glyph is drawn as a centre-line skeleton (lines, true circular arcs,
smooth Hermite curves) and then stroked with round caps and round joins, so
every terminal and corner is perfectly round at any weight.  The strokes are
merged with skia-pathops and converted to TrueType quadratics.

    pip install -e .
    python -m monochrome

Outputs (in ./fonts):
    monochrome-aviation-light.ttf / .woff2
    monochrome-aviation.ttf       / .woff2   (Regular)
    monochrome-aviation-medium.ttf / .woff2

Character set: A-Z, a-z, 0-9 (tabular, for flight levels and headings),
common punctuation, the degree sign, arrows and an airliner glyph (U+2708).
"""

from __future__ import annotations

from .builder import build_all, build_font
from .glyph import Glyph
from .glyphs import design
from .metrics import FAMILY, UPM, VERSION, WEIGHTS, Frame, Weight

__all__ = [
    "FAMILY",
    "UPM",
    "VERSION",
    "WEIGHTS",
    "Frame",
    "Glyph",
    "Weight",
    "build_all",
    "build_font",
    "design",
]

__version__ = "3.0.0"

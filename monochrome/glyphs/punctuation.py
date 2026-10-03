"""Punctuation and the symbols a cockpit display actually needs.

Dots are filled rather than stroked: a filled circle is a cleaner outline than
a round cap on a zero-length line, and it is what keeps the optical size of
``.`` stable as the weight grows.
"""

from __future__ import annotations

from ..glyph import Glyph
from ..metrics import OS, Frame
from ..primitives import circle, line
from ..skeleton import Sk
from .base import dot


def draw(f: Frame) -> dict[str, Glyph]:
    """Build the punctuation for the frame's stroke width."""
    T, B = f.cap, f.base
    XT = f.x_top
    dy = f.dot_r
    """Every dot sits on the baseline - they are periods by default."""
    y_colon = XT - OS
    """The upper dot of ``:`` and ``;``."""

    tail = line(0, dy, -42, -105)
    """The tail of ``,`` and ``;``."""
    cross = line(0, 300, 250, 300)
    """The hyphen, on the maths axis."""

    G: dict[str, Glyph] = {}

    G["period"] = Glyph([], [dot(f, 0, dy)])
    G["comma"] = Glyph([tail], [dot(f, 0, dy)])
    G["colon"] = Glyph([], [dot(f, 0, dy), dot(f, 0, y_colon)])
    G["semicolon"] = Glyph([tail], [dot(f, 0, dy), dot(f, 0, y_colon)])
    G["exclam"] = Glyph([line(0, T, 0, 255)], [dot(f, 0, dy)])

    # question - a bowl leaving on the tangent into a short stem
    rq = 160
    cyq = T + OS - rq
    G["question"] = Glyph([
        Sk().arc(rq, cyq, rq, 165, -45).L(rq, cyq - rq * 1.41),
    ], [dot(f, rq, dy)])

    G["hyphen"] = Glyph([cross])
    G["endash"] = Glyph([line(0, 300, 400, 300)])
    G["emdash"] = Glyph([line(0, 300, 740, 300)])
    G["slash"] = Glyph([line(0, -70, 340, T + 40)])

    # parentheses - the left one is a slice of a very large circle so the
    # curvature at text sizes matches the weight of the glyphs it brackets
    pr = 640
    pa = 34
    G["parenleft"] = Glyph([Sk().arc(pr, 300, pr, 180 - pa, 180 + pa)])
    G["parenright"] = Glyph([Sk().arc(0, 300, pr, 360 - pa, 360 + pa)])

    G["plus"] = Glyph([line(0, 330, 360, 330), line(180, 150, 180, 510)])
    G["equal"] = Glyph([line(0, 400, 360, 400), line(0, 250, 360, 250)])

    # degree - a small circle riding at cap height
    G["degree"] = Glyph([circle(0, T - 60, 62)])
    G["quotesingle"] = Glyph([line(0, T, 0, T - 170)])
    G["quotedbl"] = Glyph([line(0, T, 0, T - 170), line(135, T, 135, T - 170)])
    G["underscore"] = Glyph([line(0, -110, 500, -110)])

    return G

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

    # ----------------------------------------------------------------------
    # at / ampersand
    #
    # Both are the most structurally involved punctuation here, and both reuse
    # the geometry of letters that already exist: the outer ring of ``at`` is
    # the same stadium as ``O`` with a bite taken out of its lower right, and
    # ``ampersand`` is the two-bowls-plus-leg construction that geometric sans
    # serifs use.  ``outline`` unions the sub-strokes, so where they overlap
    # they fuse into one contour instead of showing a seam.
    # ----------------------------------------------------------------------
    G["at"] = _at(f)
    G["ampersand"] = _ampersand(f)

    return G


def _at(f: Frame) -> Glyph:
    """``@`` - an ``O`` open at the lower right, a small bowl, and a tail.

    The outer ring is the ``O`` stadium (same 510-unit width, same cap height
    and overshoot) traced from a terminal on the right side, up and around the
    top, down the left and under the bottom, stopping short of the lower right
    so the tail has somewhere to land.
    """
    a = 255
    hgt = (f.cap - f.base) + 2 * OS
    d = hgt / 2.0 - a
    top_cy, bot_cy = f.cap_mid + d, f.cap_mid - d

    outer = (
        Sk().M(2 * a, f.cap_mid - 50)          # free terminal, right side
        .L(2 * a, top_cy)
        .arc(a, top_cy, a, 0, 180)            # over the top
        .L(0, bot_cy)
        .arc(a, bot_cy, a, 180, 330)          # under the bottom, stopping short
    )

    # The bowl is the 'a' inside the ring: smaller than half the ring so a
    # healthy counter survives at every weight, and set a little below centre
    # because the open quadrant at the lower right needs the extra room.
    br, bcx, bcy = 96, 228, f.cap_mid - 18
    bowl = circle(bcx, bcy, br)

    # The tail leaves the bowl low on its right, dips under the chord, and
    # rises to meet the ring on the tangent at the ring's open end. Ending on
    # the tangent is what fuses the two into one continuous stroke.
    tail = Sk().hermite([
        (bcx + br * 0.7071, bcy - br * 0.7071, 0.94, -0.34),
        (a + a * 0.8660, bot_cy - a * 0.5, 1, 0.58),
    ])

    return Glyph([outer, bowl, tail])


def _ampersand(f: Frame) -> Glyph:
    """``&`` - a small upper bowl, a large lower bowl, and the leg between them.

    The two-bowls-plus-diagonal-leg construction that geometric sans serifs
    use.  What makes it read as ``&`` rather than as ``8`` is the white gap
    between the leg and the upper bowl, so the leg is aimed past that bowl
    rather than through it.
    """
    # Tangency and the OS overshoot are not independent: they are the same
    # equation, which is why the radii have to sum to (T - B) / 2 + OS. Writing
    # the bowl heights out as constants instead lets them drift apart as the
    # stroke grows, and the glyph stops reading at the weights it was not tuned
    # for.
    #
    #     (T + OS - r_upper) - r_upper  ==  (B - OS + r_lower) + r_lower
    #   =>  r_upper + r_lower  ==  (T - B) / 2 + OS
    budget = (f.cap - f.base) / 2.0 + OS
    r_upper = budget * 0.33
    r_lower = budget - r_upper
    cx_upper, cx_lower = 170, 225

    y_upper = f.cap + OS - r_upper
    y_lower = f.base - OS + r_lower

    upper = circle(cx_upper, y_upper, r_upper)
    lower = circle(cx_lower, y_lower, r_lower)

    # The leg is a straight diagonal, not a Hermite: over a chord this long the
    # automatic handle length balloons wherever the tangent is not parallel to
    # the chord, which turns the leg into a lobe.  It starts well inside the
    # lower bowl so the union has no seam.
    leg = line(
        cx_lower + 0.50 * r_lower,
        y_lower + 0.38 * r_lower,
        cx_lower + 1.05 * r_lower,
        f.cap + OS - 23,
    )
    return Glyph([lower, upper, leg])

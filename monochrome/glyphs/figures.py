"""Figures ``0``-``9``.

All ten figures share one advance width (they are tabular), so flight levels,
headings and squawk codes stay in vertical columns when they are stacked.  The
builder centres each one inside that shared width; this module only draws the
ink.  Curved figures are drawn as tangent-joined arcs rather than fudge-rounded
polygons, so ``2``, ``5`` and ``3`` stay true circles where it shows.
"""

from __future__ import annotations

from math import cos, radians, sin

from ..glyph import Glyph
from ..metrics import OS, Frame
from ..primitives import circle, line, pill, rot180, tangent_angle
from ..skeleton import Sk

#: Order the figures are emitted in.  Frozen: the builder uses the design order
#: as the TrueType glyph order, and changing it would renumber every glyph in
#: the shipped binaries.  ``nine`` deliberately precedes ``eight``.
ORDER = ("zero", "one", "two", "three", "four", "five", "six", "nine", "eight", "seven")


def draw(f: Frame) -> dict[str, Glyph]:
    """Build the ten figures for the frame's stroke width."""
    T, B, M = f.cap, f.base, f.cap_mid
    hgt = T - B + 2 * OS
    tot = hgt / 2.0
    """Half the full figure height - the radius budget for a stacked bowl."""

    G: dict[str, Glyph] = {}

    # 0 - the only figure as wide as the capitals
    G["zero"] = Glyph([pill(205, M, 410, hgt)])

    # 1 - a flag, then the stem
    G["one"] = Glyph([Sk().poly([(-150, T - 150), (0, T), (0, B)])])

    # 2 - a bowl that leaves on the tangent, then a flat base
    r2 = 172
    cx2, cy2 = r2 + 10, T + OS - r2
    th2 = tangent_angle(cx2, cy2, r2, 0, B, True)
    while th2 >= 160:
        th2 -= 360
    G["two"] = Glyph([Sk().arc(cx2, cy2, r2, 160, th2).L(0, B).L(2 * r2 + 10, B)])

    # 3 - two open bowls meeting on a short horizontal bar
    r31 = 150
    r32 = tot - r31
    cx3 = r32
    ytop3 = T + OS - r31
    ym3 = T + OS - 2 * r31
    G["three"] = Glyph([
        Sk().arc(cx3, ytop3, r31, 152, -90).L(cx3 - 105, ym3),
        Sk().M(cx3 - 105, ym3).L(cx3, ym3).arc(cx3, B - OS + r32, r32, 90, -152),
    ])

    # 4 - an open triangle closed by a full-height stem
    y4 = B + (T - B) * 0.31
    G["four"] = Glyph([
        Sk().poly([(300, T), (0, y4), (390, y4)]),
        line(300, T, 300, B),
    ])

    # 5 - a flat top, a stem down to the bowl, then the bowl on a tangent
    rb = 192
    cb = 0.766 * rb + 22
    cyb = B - OS + rb
    ys5 = cyb + rb * sin(radians(140))
    x5 = cb + rb * cos(radians(140))
    G["five"] = Glyph([Sk().M(x5 + 310, T).L(x5, T).L(x5, ys5).arc(cb, cyb, rb, 140, -152)])

    # 6 - a closed lower bowl with a stem rising out of its left
    r6 = 190
    cy6 = B - OS + r6
    cy6t = T + OS - r6
    six = [circle(r6, cy6, r6), Sk().M(0, cy6).L(0, cy6t).arc(r6, cy6t, r6, 180, 38)]
    G["six"] = Glyph(six)
    # 9 - 6 turned the other way
    G["nine"] = Glyph([rot180(p, r6, M) for p in six])

    # 8 - two bowls, the upper one tighter than the lower
    r81 = 148
    r82 = tot - r81
    G["eight"] = Glyph([circle(r82, T + OS - r81, r81), circle(r82, B - OS + r82, r82)])

    G["seven"] = Glyph([Sk().poly([(0, T), (400, T), (130, B)])])

    return G

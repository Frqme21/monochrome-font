"""Ready-made skeleton primitives and transforms.

These are the vocabulary the glyph modules are written in: a handful of strokes
(line, circle, stadium) and a handful of symmetric operations (shift, mirror,
rotate) that let one drawing stand in for several letters.
"""

from __future__ import annotations

from math import acos, atan2, cos, degrees, hypot, sin

from .skeleton import Sk


# --------------------------------------------------------------------------
# Transforms - keep the skeleton a skeleton
# --------------------------------------------------------------------------
def shift(sk: Sk, dx: float = 0.0, dy: float = 0.0) -> Sk:
    """Translate ``sk`` by ``(dx, dy)``."""
    return sk.mapped(lambda x, y: (x + dx, y + dy))


def rot180(sk: Sk, cx: float, cy: float) -> Sk:
    """Rotate ``sk`` 180 degrees about ``(cx, cy)``.

    Used to build ``u`` from ``n``, ``9`` from ``6`` and ``9``/``6`` without
    hand-drawing a second time.
    """
    return sk.mapped(lambda x, y: (2 * cx - x, 2 * cy - y))


def mirror_x(sk: Sk, cx: float) -> Sk:
    """Mirror ``sk`` about the vertical axis ``x = cx``."""
    return sk.mapped(lambda x, y: (2 * cx - x, y))


def rot90(sk: Sk, cx: float, cy: float, ccw: bool = True) -> Sk:
    """Rotate ``sk`` a quarter turn about ``(cx, cy)``."""
    if ccw:
        return sk.mapped(lambda x, y: (cx - (y - cy), cy + (x - cx)))
    return sk.mapped(lambda x, y: (cx + (y - cy), cy - (x - cx)))


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------
def line(x1: float, y1: float, x2: float, y2: float) -> Sk:
    """A single straight stroke."""
    return Sk().M(x1, y1).L(x2, y2)


def circle(cx: float, cy: float, r: float) -> Sk:
    """A closed full circle, drawn as four true quarter arcs."""
    return Sk().arc(cx, cy, r, 0, 360).Z()


def pill(cx: float, cy: float, w: float, hgt: float) -> Sk:
    """Closed stadium with straight vertical sides and semicircular ends."""
    a, b = w / 2.0, hgt / 2.0
    s = Sk().M(cx + a, cy - (b - a))
    s.L(cx + a, cy + (b - a))
    s.arc(cx, cy + (b - a), a, 0, 180)
    s.L(cx - a, cy - (b - a))
    s.arc(cx, cy - (b - a), a, 180, 360)
    return s.Z()


def tangent_angle(cx: float, cy: float, r: float, px: float, py: float, cw: bool) -> float:
    """Angle in degrees on a circle whose travel tangent passes through ``P``.

    This is how a stroke leaves a bowl and runs off to a baseline (the ``2`` and
    ``5``) without the join kinking: the arc is solved for the tangent line
    instead of being eyeballed at a fixed angle.
    """
    dx, dy = px - cx, py - cy
    d = hypot(dx, dy)
    phi = atan2(dy, dx)
    delta = acos(min(1.0, r / d))
    for sgn in (1, -1):
        th = phi + sgn * delta
        qx, qy = cx + r * cos(th), cy + r * sin(th)
        ux, uy = (sin(th), -cos(th)) if cw else (-sin(th), cos(th))
        if (px - qx) * ux + (py - qy) * uy > 0:
            return degrees(th)
    return degrees(phi)


__all__ = [
    "circle",
    "line",
    "mirror_x",
    "pill",
    "rot90",
    "rot180",
    "shift",
    "tangent_angle",
]

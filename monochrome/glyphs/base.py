"""Shared sub-drawings used by several glyph modules.

These are the shapes that appear across families of letters: the bowl that
closes ``B``/``D``/``P``, the spine of ``S``, the dot used for every
punctuation mark.
"""

from __future__ import annotations

from ..metrics import OS, Frame
from ..primitives import circle
from ..skeleton import Sk

# Sentinel radius meaning "round this corner as far as the bowl allows".
FULL_ROUND = 999


def bowl(x0: float, ytop: float, ybot: float, xr: float, r: float) -> Sk:
    """A closed bowl: left edge at ``x0``, right edge at ``xr``.

    ``r`` is the radius of the two right-hand corners; it is clamped so it can
    never exceed half the bowl height, which lets callers pass :data:`FULL_ROUND`
    for a fully round right side.
    """
    r = min(r, (ytop - ybot) / 2.0)
    s = Sk().M(x0, ybot).L(x0, ytop).L(xr - r, ytop)
    s.arc(xr - r, ytop - r, r, 90, 0)
    s.L(xr, ybot + r)
    s.arc(xr - r, ybot + r, r, 0, -90)
    return s.Z()


def s_curve(x0: float, y0: float, w: float, y1: float) -> Sk:
    """The spine of ``S``/``s``: a double curve between two levels.

    ``y0`` is the lower level, ``y1`` the upper one, ``w`` the width.  The
    overshoot at both ends plus the tangent list is what gives ``S`` its
    spine - straight in the middle, turning tightly at the top and bottom.
    """
    hh = y1 - y0
    xl, xr, xc = x0, x0 + w, x0 + w / 2.0
    yt, yb, ym = y1 + OS, y0 - OS, (y0 + y1) / 2.0
    return Sk().hermite([
        (xr - 0.015 * w, yt - 0.17 * hh, -0.55, 1.0),
        (xc, yt, -1, 0),
        (xl, ym + 0.24 * hh, 0, -1),
        (xc, ym, 1, -0.42),
        (xr, ym - 0.24 * hh, 0, -1),
        (xc, yb, -1, 0),
        (xl + 0.015 * w, yb + 0.17 * hh, -0.55, 1.0),
    ])


def dot(f: Frame, x: float, y: float) -> Sk:
    """A filled round dot of the frame's dot radius."""
    return circle(x, y, f.dot_r)

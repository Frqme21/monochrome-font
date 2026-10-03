"""Capitals, ``A``-``Z``.

The capitals are the widest part of the design, so they set the proportions
everything else is fitted into.  Heights come from the frame; widths are
hard-coded advance values in the same units.
"""

from __future__ import annotations

from ..glyph import Glyph
from ..metrics import OS, Frame
from ..primitives import line, pill
from ..skeleton import Sk
from .base import FULL_ROUND, bowl, s_curve


def draw(f: Frame) -> dict[str, Glyph]:
    """Build the 26 capitals for the frame's stroke width."""
    T, B, M = f.cap, f.base, f.cap_mid

    # Geometry shared by the round capitals (C, G, O, Q).
    a = 255
    x_mid = M
    hgt = T - B + 2 * OS
    d = hgt / 2.0 - a

    # Shared horizontal landmarks.
    y_top_bowl = M + 14
    """Where ``B`` splits into its two bowls."""
    y_bowl = B + (T - B) * 0.42
    """Where the bowl of ``P``/``R`` and the arms of ``Y`` land."""
    y_knee = B + (T - B) * 0.40
    """Where the arm of ``K`` meets the stem."""

    G: dict[str, Glyph] = {}

    # A - two diagonals plus a low crossbar that clears the apex
    w = 590
    cx = w / 2.0
    yb = B + (T - B) * 0.29
    lx = cx * (yb - B) / (T - B)
    G["A"] = Glyph([line(0, B, cx, T).L(w, B), line(lx, yb, w - lx, yb)])

    # B - two stacked bowls, the lower one reaching slightly wider
    G["B"] = Glyph([bowl(0, T, y_top_bowl, 400, FULL_ROUND),
                    bowl(0, y_top_bowl, B, 435, FULL_ROUND)])

    # C - a broken circle, open on the right
    G["C"] = Glyph([
        Sk().arc(a, x_mid + d, a, 40, 180)
        .L(0, x_mid - d)
        .arc(a, x_mid - d, a, 180, 320)
    ])

    # D - one big bowl
    G["D"] = Glyph([bowl(0, T, B, 440, 250)])

    # E / F - squared spine with a mitred middle arm
    G["E"] = Glyph([Sk().poly([(385, T), (0, T), (0, B), (385, B)], r=85),
                    line(0, M, 335, M)])
    G["F"] = Glyph([Sk().poly([(385, T), (0, T), (0, B)], r=85),
                    line(0, M, 335, M)])

    # G - like C, closed off by a horizontal spur
    g = (Sk().arc(a, x_mid + d, a, 40, 180)
         .L(0, x_mid - d)
         .arc(a, x_mid - d, a, 180, 360))
    g.L(2 * a, M - 22).L(a + 10, M - 22)
    G["G"] = Glyph([g])

    # H - two stems and a crossbar on the midline
    G["H"] = Glyph([line(0, B, 0, T), line(460, B, 460, T), line(0, M, 460, M)])
    G["I"] = Glyph([line(0, B, 0, T)])
    # J - stem with a left hook that swings below the baseline
    G["J"] = Glyph([Sk().M(330, T).L(330, B + 150).arc(180, B + 150, 150, 0, -170)])

    # K - stem, arm up to the right, leg kicked out past the arm
    G["K"] = Glyph([line(0, B, 0, T),
                    line(360, T, 0, y_knee),
                    line(360 - 0.42 * 360, T - 0.42 * (T - y_knee), 370, B)])
    G["L"] = Glyph([Sk().poly([(0, T), (0, B), (360, B)], r=85)])
    # M / N - the diagonal runs down to a point just above the baseline
    G["M"] = Glyph([Sk().poly([(0, B), (0, T), (320, B + (T - B) * 0.2), (640, T), (640, B)])])
    G["N"] = Glyph([Sk().poly([(0, B), (0, T), (480, B), (480, T)])])
    # O - a stadium as wide as the cap height plus the overshoot
    G["O"] = Glyph([pill(a, M, 510, hgt)])

    # P / R - a bowl down to y_bowl, with the stem running through
    G["P"] = Glyph([bowl(0, T, y_bowl, 420, FULL_ROUND), line(0, B, 0, y_bowl)])
    # Q - O with a tail through the lower right
    G["Q"] = Glyph([pill(a, M, 510, hgt),
                    line(a + 40, B + 175, 2 * a + 8, B - 22)])
    G["R"] = Glyph([bowl(0, T, y_bowl, 420, FULL_ROUND),
                    line(0, B, 0, y_bowl),
                    line(205, y_bowl, 430, B)])
    G["S"] = Glyph([s_curve(0, B, 390, T)])
    G["T"] = Glyph([line(0, T, 520, T), line(260, T, 260, B)])
    # U - stems into a semicircle that overshoots the baseline
    G["U"] = Glyph([Sk().M(0, T).L(0, B + 235).arc(235, B + 235 - OS, 235, 180, 360).L(470, T)])
    G["V"] = Glyph([Sk().poly([(0, T), (300, B), (600, T)])])
    G["W"] = Glyph([Sk().poly([(0, T), (225, B), (450, T), (675, B), (900, T)])])
    G["X"] = Glyph([line(0, T, 500, B), line(500, T, 0, B)])
    G["Y"] = Glyph([Sk().poly([(0, T), (270, y_bowl), (540, T)]),
                    line(270, y_bowl, 270, B)])
    G["Z"] = Glyph([Sk().poly([(0, T), (460, T), (0, B), (460, B)])])

    return G

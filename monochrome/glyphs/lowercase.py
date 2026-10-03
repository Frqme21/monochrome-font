"""Lowercase, ``a``-``z``.

The lowercase rounds all share one radius (:attr:`Frame.bowl_r`) and one centre
line (:attr:`Frame.bowl_cy`), which is what keeps ``o``/``c``/``e``/``a``/``b``/...
optically identical in size.  Shoulders (``n``/``h``/``m``/``r``) are drawn once
per radius and reused, and ``u`` is the 180-degree turn of ``n``.
"""

from __future__ import annotations

from ..glyph import Glyph
from ..metrics import OS, Frame
from ..primitives import circle, line, rot180
from ..skeleton import Sk
from .base import dot, s_curve


def draw(f: Frame) -> dict[str, Glyph]:
    """Build the 26 lowercase letters for the frame's stroke width."""
    B, XT, AT, DB = f.base, f.x_top, f.asc_top, f.desc_bottom
    RL, CY = f.bowl_r, f.bowl_cy

    def top(r: float) -> float:
        """Y where a shoulder of radius ``r`` meets the x-height."""
        return XT + OS - r

    def arch(r: float) -> list[Sk]:
        """Stem from the baseline with a shoulder of radius ``r`` (the ``n``)."""
        cy = top(r)
        return [line(0, XT, 0, B), Sk().M(0, cy).arc(r, cy, r, 180, 0).L(2 * r, B)]

    G: dict[str, Glyph] = {}

    # The round letters: one circle, reused everywhere it appears.
    G["o"] = Glyph([circle(RL, CY, RL)])
    G["c"] = Glyph([Sk().arc(RL, CY, RL, 42, 318)])
    G["e"] = Glyph([Sk().M(0, CY).L(2 * RL, CY).arc(RL, CY, RL, 0, 322)])
    # a / b / d / p / q - a bowl with a stem on one side of it
    G["a"] = Glyph([circle(RL, CY, RL), line(2 * RL, XT, 2 * RL, B)])
    G["b"] = Glyph([line(0, AT, 0, B), circle(RL, CY, RL)])
    G["d"] = Glyph([line(2 * RL, AT, 2 * RL, B), circle(RL, CY, RL)])
    G["p"] = Glyph([line(0, XT, 0, DB), circle(RL, CY, RL)])
    G["q"] = Glyph([line(2 * RL, XT, 2 * RL, DB), circle(RL, CY, RL)])

    # g - the bowl of o plus a right stem that hooks left below the baseline
    rh = 165
    G["g"] = Glyph([circle(RL, CY, RL),
                    Sk().M(2 * RL, XT).L(2 * RL, DB + rh).arc(2 * RL - rh, DB + rh, rh, 0, -165)])

    ra = 182
    G["n"] = Glyph(arch(ra))
    # h - n with an ascender-height stem
    G["h"] = Glyph([line(0, AT, 0, B),
                    Sk().M(0, top(ra)).arc(ra, top(ra), ra, 180, 0).L(2 * ra, B)])
    # u - n turned upside down about the middle of the x-height
    G["u"] = Glyph([rot180(p, ra, (XT + B) / 2.0) for p in arch(ra)])

    # m - two shoulders off one stem
    rm = 133
    G["m"] = Glyph([line(0, XT, 0, B),
                    Sk().M(0, top(rm)).arc(rm, top(rm), rm, 180, 0).L(2 * rm, B),
                    Sk().M(2 * rm, top(rm)).arc(3 * rm, top(rm), rm, 180, 0).L(4 * rm, B)])

    # r - stem with a short quarter-shoulder
    rr = 150
    G["r"] = Glyph([line(0, XT, 0, B), Sk().M(0, top(rr)).arc(rr, top(rr), rr, 180, 62)])

    # i / j - stem (hooking left for j) plus a detached dot
    G["i"] = Glyph([line(0, XT, 0, B)], [dot(f, 0, 600)])
    rj = 150
    G["j"] = Glyph([Sk().M(0, XT).L(0, DB + rj).arc(-rj, DB + rj, rj, 0, -165)], [dot(f, 0, 600)])

    # k - the lowercase K, arm meeting the stem at y_knee
    y_knee = B + (XT - B) * 0.36
    G["k"] = Glyph([line(0, AT, 0, B),
                    line(300, XT, 0, y_knee),
                    line(150, (XT + y_knee) / 2.0, 310, B)])

    # l / t - the same bottom hook, once plain and once crossed
    rt = 125
    G["l"] = Glyph([Sk().M(0, AT).L(0, B + rt).arc(rt, B + rt, rt, 180, 318)])
    G["t"] = Glyph([Sk().M(0, 610).L(0, B + rt).arc(rt, B + rt, rt, 180, 318),
                    line(-110, XT, 215, XT)])
    # f - mirrored l with a crossbar
    rf = 150
    G["f"] = Glyph([Sk().M(0, B).L(0, AT - rf).arc(rf, AT - rf, rf, 180, 90).L(rf + 55, AT),
                    line(-110, XT, 215, XT)])

    G["s"] = Glyph([s_curve(0, B, 320, XT)])
    G["v"] = Glyph([Sk().poly([(0, XT), (240, B), (480, XT)])])
    G["w"] = Glyph([Sk().poly([(0, XT), (190, B), (380, XT), (570, B), (760, XT)])])
    G["x"] = Glyph([line(0, XT, 440, B), line(440, XT, 0, B)])
    # y - the right diagonal overshoots to the descender, meeting the left
    # diagonal exactly on the baseline
    wy = 480
    xm = wy / 2.0
    xy2 = wy + (xm - wy) * (XT - DB) / (XT - B)
    G["y"] = Glyph([line(0, XT, xm, B), line(wy, XT, xy2, DB)])
    G["z"] = Glyph([Sk().poly([(0, XT), (400, XT), (0, B), (400, B)])])

    return G

"""From skeleton to outline.

This is the only place that knows about stroking and boolean geometry:

1. every skeleton is stroked with round caps and round joins, which is what
   makes every terminal round at every weight;
2. the stroked pieces are unioned with each other and with any filled dots, so
   crossing strokes fuse into one outline instead of self-intersecting;
3. the merged result is converted to TrueType quadratics.

Because the round joins are baked in here, nothing downstream has to think
about stroke rendering - a glyph is just an outline from that point on.
"""

from __future__ import annotations

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from pathops import LineCap, LineJoin, Path as SkPath, PathOp

from .glyph import Glyph

#: Maximum cu2qu error, in font units, when cubics become quadratics.
QUAD_ERROR = 0.6


def sanitize_path(skia_path: SkPath) -> SkPath:
    """Make ``skia_path`` safe to hand to a pathops boolean.

    Stroking (and some of the boolean ops themselves) can leave conic sections
    in a path; the boolean op solver only understands lines and cubics, so the
    conics are flattened to quads first.  The input is copied, not mutated.
    """
    out = SkPath(skia_path)
    out.convertConicsToQuads()
    return out


def outline(glyph: Glyph, stroke: float) -> SkPath:
    """Stroke, merge and simplify one glyph into a single outline.

    Args:
        glyph: the design to render.
        stroke: full stroke width; each skeleton's own multiplier scales it.
    """
    result = SkPath()
    for sk, multiplier in glyph.strokes:
        p = sk.to_skia()
        p.stroke(stroke * multiplier, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
        p = sanitize_path(p)
        result = pathops.op(result, p, PathOp.UNION, fix_winding=True)
    for sk in glyph.fills:
        p = sanitize_path(sk.to_skia())
        result = pathops.op(result, p, PathOp.UNION, fix_winding=True)
    result = sanitize_path(result)
    result.simplify(fix_winding=True, keep_starting_points=False, clockwise=True)
    return result


def outline_glyphs(glyphs: dict[str, Glyph], stroke: float) -> dict[str, SkPath]:
    """Outline every glyph at one stroke width."""
    return {name: outline(glyph, stroke) for name, glyph in glyphs.items()}


def to_ttglyph(path: SkPath, dx: float = 0.0):
    """Convert an outline to a TrueType glyph, shifted right by ``dx``.

    Cubics are converted to quadratics on the way out, since TrueType has no
    cubic segments.
    """
    tt = TTGlyphPen(None)
    pen = Cu2QuPen(tt, max_err=QUAD_ERROR, reverse_direction=False)
    path.draw(TransformPen(pen, (1, 0, 0, 1, dx, 0)))
    return tt.glyph()

"""The glyph registry.

``design()`` asks each category module to draw itself for one stroke width and
merges the results.  The merge order *is* the TrueType glyph order, so it is
part of the font's binary identity and must not be reshuffled casually - see
:data:`LAYOUT.GLYPH_ORDER`.
"""

from __future__ import annotations

from ..glyph import Glyph
from ..metrics import Frame
from . import aviation, caps, figures, lowercase, punctuation

#: Draw order, which fixes the glyph order in the compiled binaries.
MODULES = (caps, lowercase, figures, punctuation, aviation)

__all__ = ["MODULES", "design", "design_all"]


def design(stroke: float) -> dict[str, Glyph]:
    """Draw every glyph for a given stroke width, keyed by glyph name.

    The result is a mapping of name -> :class:`~monochrome.glyph.Glyph` in
    stable glyph order.
    """
    frame = Frame.for_stroke(stroke)
    glyphs: dict[str, Glyph] = {}
    for module in MODULES:
        for name, glyph in module.draw(frame).items():
            if name in glyphs:
                raise ValueError(f"duplicate glyph {name!r} in {module.__name__}")
            glyphs[name] = glyph
    return glyphs


def design_all(strokes: tuple[float, ...]) -> dict[float, dict[str, Glyph]]:
    """Draw every glyph at every requested stroke width.

    Keyed by stroke width, which is what :func:`monochrome.builder.build_all`
    needs: three weights is three full drawings.
    """
    return {stroke: design(stroke) for stroke in strokes}

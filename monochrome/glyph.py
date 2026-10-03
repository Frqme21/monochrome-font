"""The glyph container.

A glyph is a bag of *stroked skeletons* plus a list of *filled* skeletons, so
that a single outline pass can merge everything into one clean contour.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Glyph:
    """One glyph design, independent of any particular stroke width.

    Attributes:
        strokes: ``(skeleton, width_multiplier)`` pairs to be stroked.  A bare
            skeleton may be passed instead of a pair; it defaults to 1.0.  The
            multiplier lets one letter carry a heavier accent without redrawing
            it (see the airliner in :mod:`monochrome.glyphs.aviation`).
        fills: skeletons to be filled solid - dots, which are cheaper and
            smoother as filled circles than as zero-length round caps.
    """

    strokes: tuple = field(default_factory=tuple)
    fills: tuple = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "strokes",
            tuple(s if isinstance(s, tuple) else (s, 1.0) for s in self.strokes),
        )
        object.__setattr__(self, "fills", tuple(self.fills))

    def __bool__(self) -> bool:
        return bool(self.strokes or self.fills)


def stroke_widths(glyph: Glyph) -> list[float]:
    """Distinct stroke multipliers used by ``glyph`` (useful for debugging)."""
    return sorted({mul for _, mul in glyph.strokes})

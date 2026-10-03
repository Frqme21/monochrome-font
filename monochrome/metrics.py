"""Design-space metrics for the Monochrome Aviation family.

Every constant is expressed in font units (1/1000 em).  The values describe the
*outer* edges of the strokes; :class:`Frame` converts them into the centre-line
coordinates that the glyph sketches are actually drawn on, so that changing a
weight never requires touching a single glyph.

    original name   Frame attribute   meaning
    --------------   --------------   ---------------------------------
    H               .half             half the stroke width
    T               .cap              cap-height centre line
    B               .base             baseline centre line
    M               .cap_mid          vertical midpoint of the capitals
    XT              .x_top            x-height centre line
    AT              .asc_top          ascender centre line
    DB              .desc_bottom      descender centre line
    RL              .bowl_r           lowercase round radius
    CY              .bowl_cy          lowercase round centre
    DOT             .dot_r            radius of a round dot
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

# --------------------------------------------------------------------------
# Vertical metrics (outer edges of the strokes)
# --------------------------------------------------------------------------
UPM = 1000
"""Units per em."""

CAP = 700
"""Cap height."""

XH = 500
"""x-height."""

ASC = 745
"""Ascender height."""

DESC = -210
"""Descender depth."""

OS = 10
"""Overshoot of round shapes, in centre-line units."""

FAMILY = "Monochrome Aviation"
"""Font family name written into the name table."""

VERSION = "3.000"
"""Font version, written into the name table."""


# --------------------------------------------------------------------------
# Weights
# --------------------------------------------------------------------------
class Weight(NamedTuple):
    """One member of the family."""

    style: str
    stroke: float
    us_weight_class: int
    suffix: str
    """Appended to the output basename (``""`` for Regular)."""

    @property
    def filename(self) -> str:
        """Basename shared by the TTF and WOFF2 of this weight."""
        return f"monochrome-aviation{self.suffix}"


WEIGHTS: tuple[Weight, ...] = (
    Weight("Light", 62, 300, "-light"),
    Weight("Regular", 84, 400, ""),
    Weight("Medium", 112, 500, "-medium"),
)

WEIGHTS_BY_NAME: dict[str, Weight] = {w.style.lower(): w for w in WEIGHTS}


@dataclass(frozen=True)
class Frame:
    """Centre-line landmarks for one stroke width.

    Glyph modules never do arithmetic on ``UPM``/``CAP``/... directly; they read
    the pre-solved landmarks off the frame, which is what makes the family
    weight-consistent.
    """

    stroke: float
    """Full stroke width this frame was built for."""

    half: float
    """:attr:`H` - half the stroke width."""

    cap: float
    """:attr:`T` - cap-height centre line."""

    base: float
    """:attr:`B` - baseline centre line."""

    cap_mid: float
    """:attr:`M` - vertical midpoint between :attr:`cap` and :attr:`base`."""

    x_top: float
    """:attr:`XT` - x-height centre line."""

    asc_top: float
    """:attr:`AT` - ascender centre line."""

    desc_bottom: float
    """:attr:`DB` - descender centre line."""

    bowl_r: float
    """:attr:`RL` - radius of the lowercase round shapes."""

    bowl_cy: float
    """:attr:`CY` - centre of the lowercase round shapes."""

    dot_r: float
    """:attr:`DOT` - radius of a round dot."""

    @classmethod
    def for_stroke(cls, stroke: float) -> "Frame":
        """Solve every landmark for ``stroke`` units of monoline."""
        half = stroke / 2.0
        cap = CAP - half
        base = half
        x_top = XH - half
        return cls(
            stroke=stroke,
            half=half,
            cap=cap,
            base=base,
            cap_mid=(cap + base) / 2.0,
            x_top=x_top,
            asc_top=ASC - half,
            desc_bottom=DESC + half,
            bowl_r=(x_top - base) / 2.0 + OS,
            bowl_cy=(x_top + base) / 2.0,
            dot_r=half * 1.12,
        )

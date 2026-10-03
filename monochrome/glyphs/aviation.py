"""Aviation extras: the four arrows and an airliner silhouette.

These are the symbols that justify the family name.  They are drawn in the same
monoline as the letters, and they deliberately sit outside the Latin range in
Unicode (U+2190-2193 and U+2708) so they cannot collide with text.
"""

from __future__ import annotations

from ..glyph import Glyph
from ..metrics import Frame
from ..primitives import line, mirror_x, rot90
from ..skeleton import Sk

Y_ARROW = 330
"""Height of the arrow shaft, on the maths axis of the capitals."""


def draw(f: Frame) -> dict[str, Glyph]:
    """Build the aviation symbols for the frame's stroke width."""
    G: dict[str, Glyph] = {}

    # Draw the arrow pointing right once, then point the other three ways.
    shaft = Sk().M(0, Y_ARROW).L(560, Y_ARROW)
    head = Sk().poly([(430, Y_ARROW + 135), (565, Y_ARROW), (430, Y_ARROW - 135)])

    G["arrowright"] = Glyph([shaft, head])
    G["arrowleft"] = Glyph([mirror_x(shaft, 280), mirror_x(head, 280)])
    G["arrowup"] = Glyph([rot90(shaft, 280, Y_ARROW, True), rot90(head, 280, Y_ARROW, True)])
    G["arrowdown"] = Glyph([rot90(shaft, 280, Y_ARROW, False), rot90(head, 280, Y_ARROW, False)])

    # Top view of an airliner, nose up.  The per-stroke multipliers give the
    # fuselage and the wing roots a little more weight than the tailplane, so
    # the silhouette survives being set at 16px.
    G["airplane"] = Glyph([
        (line(0, -90, 0, 640), 1.55),          # fuselage
        (line(0, 470, -380, 170), 1.25),       # wings
        (line(0, 470, 380, 170), 1.25),
        (line(0, 120, -170, 10), 1.0),         # tailplane
        (line(0, 120, 170, 10), 1.0),
    ])

    return G

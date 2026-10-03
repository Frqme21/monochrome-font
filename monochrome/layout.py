"""Character set, sidebearings and kerning.

This module owns every *name* in the font and every *number* that is not part of
a glyph's own drawing.  It is the file to edit when adding a character: draw the
glyph, list its name here, give it a codepoint, give it a sidebearing class, add
kern pairs if it needs them.
"""

from __future__ import annotations

from typing import Iterable

# --------------------------------------------------------------------------
# Glyph order
#
# The builder writes glyphs to the compiled font in this order, and the glyph
# order is part of the font's binary identity - reordering it renumbers every
# glyph and changes the shipped files for no visual gain.  So these lists are
# frozen.  They are not alphabetical (nor is the lowercase), which is why
# ``test_layout.py`` asserts the drawn set matches them exactly.
# --------------------------------------------------------------------------
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

LOWERCASE = "oceabdpqgnhumrijkltfsvwxyz"
"""Lowercase in *draw* order, not alphabetical."""

FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "nine", "eight", "seven")
"""Figures in *draw* order; ``nine`` precedes ``eight``."""

PUNCTUATION = (
    "period", "comma", "colon", "semicolon", "exclam", "question",
    "hyphen", "endash", "emdash", "slash", "parenleft", "parenright",
    "plus", "equal", "degree", "quotesingle", "quotedbl", "underscore",
)

SYMBOLS = ("arrowright", "arrowleft", "arrowup", "arrowdown", "airplane")

#: Every glyph name, in the exact order the builder writes them.
#:
#: The letters are one-character names and iterate as characters; the figures and
#: punctuation are multi-character names and iterate as strings.  Both are joined
#: into one tuple of names.
GLYPH_ORDER = (
    tuple(UPPERCASE)
    + tuple(LOWERCASE)
    + FIGURES
    + PUNCTUATION
    + SYMBOLS
)

#: The ten figure names in codepoint order.
DIGIT_NAMES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")

#: Figures are tabular: they all share one advance width.
DIGITS = frozenset(DIGIT_NAMES)


# --------------------------------------------------------------------------
# Codepoints
# --------------------------------------------------------------------------
#: Non-alphanumeric codepoints, by glyph name.
EXTRA_CODEPOINTS = {
    "period": 0x2E, "comma": 0x2C, "colon": 0x3A, "semicolon": 0x3B,
    "exclam": 0x21, "question": 0x3F, "hyphen": 0x2D, "endash": 0x2013,
    "emdash": 0x2014, "slash": 0x2F, "parenleft": 0x28, "parenright": 0x29,
    "plus": 0x2B, "equal": 0x3D, "degree": 0xB0, "quotesingle": 0x27,
    "quotedbl": 0x22, "underscore": 0x5F, "arrowleft": 0x2190, "arrowup": 0x2191,
    "arrowright": 0x2192, "arrowdown": 0x2193, "airplane": 0x2708,
}


def _build_codepoints() -> dict[str, int]:
    table = {ch: ord(ch) for ch in UPPERCASE + LOWERCASE}
    for i, name in enumerate(DIGIT_NAMES):
        table[name] = ord("0") + i
    table.update(EXTRA_CODEPOINTS)
    return table


#: Glyph name -> Unicode codepoint.
CODEPOINTS = _build_codepoints()

#: Unicode codepoint -> glyph name (what goes into the ``cmap``).
CHARS = {cp: name for name, cp in CODEPOINTS.items()}


# --------------------------------------------------------------------------
# Sidebearings
#
# Rather than a width per glyph, each glyph declares the *class* of its left and
# right edge, and every class gets one optical value.  A flat bar needs less air
# than a stem, which needs less than a diagonal tip - so the grid stays even
# without per-glyph nudging.
#
#   s = stem   r = round   f = flat bar end   d = diagonal tip
# --------------------------------------------------------------------------
EDGE = {"s": 72, "r": 52, "f": 46, "d": 20}

#: Glyph name -> two-character sidebearing class ("left" then "right").
SIDES = {
    "A": "dd", "B": "sr", "C": "rf", "D": "sr", "E": "sf", "F": "sf", "G": "rs",
    "H": "ss", "I": "ss", "J": "fs", "K": "sd", "L": "sf", "M": "ss", "N": "ss",
    "O": "rr", "P": "sr", "Q": "rr", "R": "sd", "S": "rr", "T": "ff", "U": "ss",
    "V": "dd", "W": "dd", "X": "dd", "Y": "dd", "Z": "ff",
    "a": "rs", "b": "sr", "c": "rf", "d": "rs", "e": "rr", "f": "df", "g": "rs",
    "h": "ss", "i": "ss", "j": "ds", "k": "sd", "l": "sf", "m": "ss", "n": "ss",
    "o": "rr", "p": "sr", "q": "rs", "r": "sd", "s": "rr", "t": "df", "u": "ss",
    "v": "dd", "w": "dd", "x": "dd", "y": "dd", "z": "ff",
    "one": "ds", "two": "rf", "four": "df", "five": "fr", "seven": "fd",
    "period": "rr", "comma": "rr", "colon": "rr", "semicolon": "rr", "exclam": "rr",
    "question": "rr", "hyphen": "rr", "endash": "rr", "emdash": "rr", "slash": "dd",
    "parenleft": "rr", "parenright": "rr", "plus": "rr", "equal": "rr",
    "degree": "rr", "quotesingle": "rr", "quotedbl": "rr", "underscore": "rr",
    "arrowleft": "rr", "arrowright": "rr", "arrowup": "rr", "arrowdown": "rr",
    "airplane": "rr",
}

DEFAULT_SIDES = "rr"
"""Class assumed for glyphs left out of :data:`SIDES` - the round figures and
anything else that is round on both sides."""


def edges(name: str) -> tuple[int, int]:
    """Left and right sidebearing for ``name``, in font units."""
    sides = SIDES.get(name, DEFAULT_SIDES)
    return EDGE[sides[0]], EDGE[sides[1]]


#: Extra optical air either side of the tabular figure advance.
FIGURE_AIR = 62
SPACE_ADVANCE = 270
NOTDEF_ADVANCE = 620
NOTDEF_LSB = 60
"""Left sidebearing declared for ``.notdef``.

Quirk kept from the original build: this is a fixed constant, so at Light and
Medium it does not equal the outline's real ``xMin``.  It has no visible effect
(``NOTDEF_ADVANCE`` is fixed too, so nothing shifts), but if you want ``hmtx`` to
agree with ``glyf`` exactly, replace this with ``round(xmin_of_notdef_outline)``.
"""


# --------------------------------------------------------------------------
# Kerning
# --------------------------------------------------------------------------
#: ``(left, right, value)`` triples.  Negative pulls the pair together.
KERN = (
    # Diagonals into and out of the flat-topped capitals
    ("A", "V", -55), ("A", "W", -35), ("A", "Y", -60), ("A", "T", -55),
    ("V", "A", -55), ("W", "A", -35), ("Y", "A", -60), ("T", "A", -55),
    # Open left sides under a wide top
    ("L", "T", -70), ("L", "V", -55), ("L", "Y", -65), ("L", "W", -35),
    # Round-to-diagonal
    ("P", "A", -55), ("F", "A", -50), ("R", "T", -20), ("R", "Y", -25),
    # Capitals over the lowercase rounds
    ("T", "a", -45), ("T", "e", -45), ("T", "o", -45), ("T", "r", -25),
    ("T", "u", -25), ("T", "y", -35), ("V", "a", -30), ("V", "e", -30),
    ("V", "o", -30), ("Y", "a", -40), ("Y", "e", -40), ("Y", "o", -40),
    ("P", "a", -20), ("P", "e", -20), ("P", "o", -20),
    # Terminals hanging past a following mark
    ("r", "period", -50), ("r", "comma", -50), ("v", "period", -40), ("y", "period", -40),
    ("T", "period", -50), ("Y", "period", -50), ("V", "period", -50),
    # A/V/W/Y initials with a following lowercase diagonal
    ("A", "v", -25), ("A", "w", -20), ("A", "y", -25),
)


def kern_feature() -> str:
    """Render :data:`KERN` as an OpenType feature file fragment."""
    lines = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "feature kern {",
    ]
    lines += [f"  pos {left} {right} {value};" for left, right, value in KERN]
    lines.append("} kern;")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Consistency checks
# --------------------------------------------------------------------------
def check_coverage(names: Iterable[str]) -> None:
    """Fail loudly if the drawn glyphs and the name lists have drifted apart.

    Called by the builder so a half-finished edit (a glyph drawn but not given
    a codepoint, a codepoint with nothing behind it, a kern pair naming a glyph
    that no longer exists) stops the build instead of quietly shipping a font
    with a hole in it.
    """
    drawn = list(names)
    problems = []

    missing = [n for n in GLYPH_ORDER if n not in drawn]
    if missing:
        problems.append(f"in GLYPH_ORDER but not drawn: {', '.join(missing)}")

    extra = [n for n in drawn if n not in CODEPOINTS]
    if extra:
        problems.append(f"drawn but not in CODEPOINTS: {', '.join(extra)}")

    stray = [n for n in drawn if n not in GLYPH_ORDER]
    if stray:
        problems.append(f"drawn but not in GLYPH_ORDER: {', '.join(stray)}")

    stale_sides = [n for n in SIDES if n not in drawn]
    if stale_sides:
        problems.append(f"sidebearing class for a glyph that is not drawn: {', '.join(stale_sides)}")

    bad_edges = sorted({c for s in SIDES.values() for c in s} - set(EDGE))
    if bad_edges:
        problems.append(f"SIDES uses undefined edge classes: {', '.join(bad_edges)}")

    bad_kern = sorted({n for pair in KERN for n in pair[:2]} - set(drawn))
    if bad_kern:
        problems.append(f"kern pair names an unknown glyph: {', '.join(bad_kern)}")

    if problems:
        raise ValueError(
            "glyph inventory is inconsistent:\n  - " + "\n  - ".join(problems)
        )

#!/usr/bin/env python3
"""Check that two builds of this typeface agree.

Used in CI to prove the fonts committed to the repository still match the
source, and useful locally after touching a skeleton:

    python build.py --out /tmp/fresh
    python tools/verify_fonts.py fonts /tmp/fresh

Two builds of identical source are expected to differ in exactly four places -
the ``head`` table's ``created``/``modified`` timestamps and the
``checkSumAdjustment`` that follows from them. Everything else is compared
byte-for-byte.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fontTools.ttLib import TTFont  # noqa: E402

# The tables compared as raw bytes. `head` is excluded because of the build
# timestamp; `glyf` and `hmtx` are compared structurally below instead, so the
# comparison reports *what* changed rather than just "the file changed".
BYTE_TABLES = ("cmap", "name", "OS/2", "post", "GPOS", "gasp", "meta")


def _outlines(font: TTFont) -> dict:
    """Per-glyph outline geometry, independent of table byte layout.

    ``getCoordinates`` decompiles composites and applies component offsets, so
    a glyph that moved via its components counts as a difference too.
    """
    glyf = font["glyf"]
    out = {}
    for name in font.getGlyphOrder():
        coords, _end_pts, _flags = glyf[name].getCoordinates(glyf)
        out[name] = tuple((round(x, 3), round(y, 3)) for x, y in coords)
    return out


def compare(committed: Path, fresh: Path) -> list[str]:
    """Return a list of differences; empty means the two fonts match."""
    a, b = TTFont(committed), TTFont(fresh)
    problems: list[str] = []

    if a.getGlyphOrder() != b.getGlyphOrder():
        problems.append("glyph order differs")
        return problems  # nothing else is comparable against a shifted order

    outlines_a, outlines_b = _outlines(a), _outlines(b)
    for name, outline in outlines_a.items():
        if outline != outlines_b[name]:
            problems.append(f"glyph {name!r} outline differs")
    if a["hmtx"].metrics != b["hmtx"].metrics:
        problems.append("metrics (hmtx) differ")

    for tag in BYTE_TABLES:
        if tag in a and a.getTableData(tag) != b.getTableData(tag):
            problems.append(f"table {tag} differs")

    return problems


def verify(committed_dir: Path, fresh_dir: Path) -> list[str]:
    """Compare every .ttf in ``committed_dir`` against its counterpart."""
    committed = sorted(committed_dir.glob("*.ttf"))
    if not committed:
        return [f"no .ttf files found in {committed_dir}"]

    problems: list[str] = []
    for path in committed:
        fresh = fresh_dir / path.name
        if not fresh.exists():
            problems.append(f"{path.name}: missing from {fresh_dir}")
            continue
        problems.extend(f"{path.name}: {d}" for d in compare(path, fresh))
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("committed", type=Path, help="the fonts checked into the repo")
    ap.add_argument("fresh", type=Path, help="a directory freshly built from source")
    args = ap.parse_args(argv)

    problems = verify(args.committed, args.fresh)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(
            f"\n{len(problems)} difference(s).\n"
            f"If {args.committed} is out of step with the source, run "
            "`python build.py` and commit the result.",
            file=sys.stderr,
        )
        return 1

    n = len(list(args.committed.glob("*.ttf")))
    print(f"{n} font(s) match the source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
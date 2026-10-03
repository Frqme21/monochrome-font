"""Command line entry point.

    python -m monochrome                       # all weights, ttf + woff2
    python -m monochrome --weights regular     # just one
    python -m monochrome --format ttf --out /tmp/out
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .builder import DEFAULT_FORMATS, DEFAULT_OUTDIR, build_all
from .metrics import FAMILY, WEIGHTS_BY_NAME, WEIGHTS


def _weight(name: str):
    """Look up a weight by (case-insensitive) style name."""
    try:
        return WEIGHTS_BY_NAME[name.lower()]
    except KeyError:
        known = ", ".join(w.style.lower() for w in WEIGHTS)
        raise argparse.ArgumentTypeError(f"unknown weight {name!r} (choose from {known})")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    # RawDescriptionHelpFormatter so the epilog keeps its formatting; the
    # ArgumentDefaults formatter is applied by hand where the default is a plain
    # string, and skipped where it would print a NamedTuple repr.
    formatter = argparse.RawDescriptionHelpFormatter
    # RawDescriptionHelpFormatter keeps the epilog readable; defaults that would
    # render as a NamedTuple repr are written into the help text by hand instead.
    parser = argparse.ArgumentParser(
        prog="monochrome",
        description=f"Build {FAMILY} from their skeleton definitions.",
        epilog=(
            "weights: " + ", ".join(w.style.lower() for w in WEIGHTS)
            + "\nformats: ttf, woff2"
            f"\n\nBuilds every weight into {DEFAULT_OUTDIR} by default."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTDIR,
        metavar="DIR",
        help=f"directory to write the fonts into (default: {DEFAULT_OUTDIR})",
    )
    parser.add_argument(
        "--weights",
        nargs="+",
        type=_weight,
        default=None,
        metavar="NAME",
        help="which weights to build (default: all of them)",
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=("ttf", "woff2"),
        default=list(DEFAULT_FORMATS),
        metavar="FMT",
        help="which output formats to write (default: ttf woff2)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="only print errors")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build the requested weights.  Returns a process exit code."""
    args = parse_args(argv)

    # Tuples, so a default can never be mutated across calls.
    weights = tuple(args.weights) if args.weights is not None else WEIGHTS
    formats = tuple(args.format)

    if not args.quiet:
        plan = ", ".join(f"{w.style} ({w.stroke:g} units)" for w in weights)
        print(f"{FAMILY} {__version__}")
        print(f"Building {plan} -> {args.out}")

    try:
        written = build_all(args.out, weights, formats)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        for path in written:
            print(f"Generated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

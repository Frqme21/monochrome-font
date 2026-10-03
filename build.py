#!/usr/bin/env python3
"""Convenience wrapper so the repo can be built without installing it.

    python build.py                    # everything, into ./fonts
    python build.py --weights medium
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from monochrome.cli import main  # noqa: E402 - after the path fix above

if __name__ == "__main__":
    raise SystemExit(main())

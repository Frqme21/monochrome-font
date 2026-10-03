"""Allow ``python -m monochrome``."""

from __future__ import annotations

from .cli import main

raise SystemExit(main())

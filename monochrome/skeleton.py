"""The skeleton path builder.

A glyph in Monochrome Aviation is never authored as an outline.  It is authored
as a *centre-line skeleton*: a list of straight lines, true circular arcs and
smooth Hermite curves.  :class:`Sk` records those segments as an operation list
so they can be transformed (mirrored, rotated, shifted) before they are stroked
with round caps and joins by :mod:`monochrome.outline`.

Keeping the skeleton separate from the outline is what guarantees the design
promise: every terminal and corner is perfectly round at every weight.
"""

from __future__ import annotations

from math import ceil, cos, hypot, radians, sin, tan

from pathops import Path as SkPath

# An op is ("M"|"L", pt) | ("Q", ctrl, pt) | ("C", c1, c2, pt) | ("Z",)
Op = tuple


class Sk:
    """A chainable skeleton path.

    Every method returns ``self``, so skeletons read as drawing instructions::

        line(0, B, 0, T).L(360, T)
    """

    __slots__ = ("ops", "cur")

    def __init__(self) -> None:
        self.ops: list[Op] = []
        self.cur: tuple[float, float] | None = None

    # -- basic segments ----------------------------------------------------
    def M(self, x: float, y: float) -> "Sk":
        """Move to ``(x, y)``; starts a new contour."""
        self.ops.append(("M", (x, y)))
        self.cur = (x, y)
        return self

    def L(self, x: float, y: float) -> "Sk":
        """Straight line to ``(x, y)`` (implicit move if the path is empty)."""
        if self.cur is None:
            return self.M(x, y)
        self.ops.append(("L", (x, y)))
        self.cur = (x, y)
        return self

    def Q(self, cx: float, cy: float, x: float, y: float) -> "Sk":
        """Quadratic segment with control point ``(cx, cy)``."""
        self.ops.append(("Q", (cx, cy), (x, y)))
        self.cur = (x, y)
        return self

    def C(self, x1: float, y1: float, x2: float, y2: float, x: float, y: float) -> "Sk":
        """Cubic segment with the two given control points."""
        self.ops.append(("C", (x1, y1), (x2, y2), (x, y)))
        self.cur = (x, y)
        return self

    def Z(self) -> "Sk":
        """Close the current contour."""
        self.ops.append(("Z",))
        return self

    # -- derived segments --------------------------------------------------
    def arc(self, cx: float, cy: float, r: float, a0: float, a1: float) -> "Sk":
        """Circular arc from ``a0`` to ``a1`` degrees (counter-clockwise if
        ``a1 > a0``).

        The arc is emitted as a chain of cubics of at most 90 degrees each, so
        the radius stays true everywhere instead of being approximated by a
        single long cubic.
        """
        sx, sy = cx + r * cos(radians(a0)), cy + r * sin(radians(a0))
        if self.cur is None:
            self.M(sx, sy)
        elif hypot(self.cur[0] - sx, self.cur[1] - sy) > 0.01:
            self.L(sx, sy)
        n = max(1, ceil(abs(a1 - a0) / 90.0 - 1e-9))
        da = (a1 - a0) / n
        k = 4.0 / 3.0 * tan(radians(da) / 4.0)
        for i in range(n):
            t0 = radians(a0 + i * da)
            t1 = radians(a0 + (i + 1) * da)
            p0 = (cx + r * cos(t0), cy + r * sin(t0))
            p1 = (cx + r * cos(t1), cy + r * sin(t1))
            c1 = (p0[0] - k * r * sin(t0), p0[1] + k * r * cos(t0))
            c2 = (p1[0] + k * r * sin(t1), p1[1] - k * r * cos(t1))
            self.C(c1[0], c1[1], c2[0], c2[1], p1[0], p1[1])
        return self

    def poly(
        self,
        pts: list[tuple[float, float]],
        r: float = 0.0,
        closed: bool = False,
    ) -> "Sk":
        """Polyline through ``pts`` with corners rounded to radius ``r``.

        ``r <= 0`` emits sharp corners (the stroke join rounds them anyway).
        ``r > 0`` replaces each interior corner with a quadratic bend, clamped
        so it can never exceed half of either adjacent segment.
        """
        n = len(pts)
        if r <= 0 or n < 3:
            self.M(*pts[0])
            for p in pts[1:]:
                self.L(*p)
            if closed:
                self.Z()
            return self

        def corner(i: int) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
            """Return (before, vertex, after) for the bend at vertex ``i``."""
            p, v, q = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
            l1, l2 = hypot(p[0] - v[0], p[1] - v[1]), hypot(q[0] - v[0], q[1] - v[1])
            d = min(r, l1 / 2, l2 / 2)
            a = (v[0] + (p[0] - v[0]) / l1 * d, v[1] + (p[1] - v[1]) / l1 * d)
            b = (v[0] + (q[0] - v[0]) / l2 * d, v[1] + (q[1] - v[1]) / l2 * d)
            return a, v, b

        def bend(a, v, b) -> None:
            """Append the quadratic (as a cubic) that rounds the corner."""
            c1 = (a[0] + 2 / 3 * (v[0] - a[0]), a[1] + 2 / 3 * (v[1] - a[1]))
            c2 = (b[0] + 2 / 3 * (v[0] - b[0]), b[1] + 2 / 3 * (v[1] - b[1]))
            self.C(c1[0], c1[1], c2[0], c2[1], b[0], b[1])

        if closed:
            a, v, b = corner(0)
            self.M(*a)
            bend(a, v, b)
            for i in range(1, n):
                a, v, b = corner(i)
                self.L(*a)
                bend(a, v, b)
            self.Z()
        else:
            self.M(*pts[0])
            for i in range(1, n - 1):
                a, v, b = corner(i)
                self.L(*a)
                bend(a, v, b)
            self.L(*pts[-1])
        return self

    def hermite(self, pts: list[tuple[float, float, float, float]]) -> "Sk":
        """Smooth curve through ``pts``.

        Each point is ``(x, y, dx, dy)`` where ``(dx, dy)`` is the unit tangent
        direction; magnitudes are derived from the neighbouring chord lengths
        (Catmull-Rom style) so the curve stays balanced without the author
        tuning handle lengths by hand.
        """
        chords = [
            hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            for i in range(len(pts) - 1)
        ]

        def mag(i: int) -> float:
            """Handle length at point ``i``, averaged from adjacent chords."""
            near = []
            if i > 0:
                near.append(chords[i - 1])
            if i < len(chords):
                near.append(chords[i])
            return 1.15 * sum(near) / len(near)

        x, y = pts[0][0], pts[0][1]
        if self.cur is None:
            self.M(x, y)
        for i in range(len(pts) - 1):
            x0, y0, dx0, dy0 = pts[i]
            x1, y1, dx1, dy1 = pts[i + 1]
            l0 = hypot(dx0, dy0)
            l1 = hypot(dx1, dy1)
            m0, m1 = mag(i), mag(i + 1)
            self.C(
                x0 + dx0 / l0 * m0 / 3, y0 + dy0 / l0 * m0 / 3,
                x1 - dx1 / l1 * m1 / 3, y1 - dy1 / l1 * m1 / 3,
                x1, y1,
            )
        return self

    # -- transforms --------------------------------------------------------
    def mapped(self, fn) -> "Sk":
        """Return a copy with every point pushed through ``fn(x, y)``.

        Transformations stay on the operation list instead of being baked into
        the outlines, so mirroring a glyph for free is a single map.
        """
        out = Sk()
        for op in self.ops:
            if op[0] == "Z":
                out.ops.append(("Z",))
            else:
                out.ops.append((op[0],) + tuple(fn(*p) for p in op[1:]))
        return out

    def to_skia(self) -> SkPath:
        """Replay the operation list into a :class:`pathops.Path`."""
        p = SkPath()
        for op in self.ops:
            k = op[0]
            if k == "M":
                p.moveTo(*op[1])
            elif k == "L":
                p.lineTo(*op[1])
            elif k == "Q":
                p.quadTo(*op[1], *op[2])
            elif k == "C":
                p.cubicTo(*op[1], *op[2], *op[3])
            elif k == "Z":
                p.close()
        return p

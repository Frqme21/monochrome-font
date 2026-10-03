"""Tests for the design space and the skeleton primitives.

These are the invariants that the glyph modules rely on.  If one of these
breaks, every glyph built on top of it is wrong.
"""

from __future__ import annotations

import math

import pytest

from monochrome import layout
from monochrome.glyphs import design
from monochrome.metrics import ASC, CAP, DESC, WEIGHTS, XH, Frame
from monochrome.primitives import circle, line, mirror_x, pill, rot90, rot180, shift
from monochrome.skeleton import Sk


# --------------------------------------------------------------------------
# Frame
# --------------------------------------------------------------------------
@pytest.mark.parametrize("stroke", [w.stroke for w in WEIGHTS])
def test_frame_lands_strokes_inside_the_metrics(stroke):
    """No stroke may spill outside the declared vertical metrics."""
    f = Frame.for_stroke(stroke)
    assert f.cap + f.half == pytest.approx(CAP)
    assert f.base - f.half == pytest.approx(0.0)
    assert f.x_top + f.half == pytest.approx(XH)
    assert f.asc_top + f.half == pytest.approx(ASC)
    assert f.desc_bottom - f.half == pytest.approx(DESC)


@pytest.mark.parametrize("stroke", [w.stroke for w in WEIGHTS])
def test_frame_ordering(stroke):
    """The landmarks must stay stacked in the right order."""
    f = Frame.for_stroke(stroke)
    assert f.desc_bottom < f.base < f.bowl_cy < f.cap_mid < f.x_top < f.cap < f.asc_top
    assert f.bowl_r > f.half


def test_frame_scales_with_stroke():
    """A heavier weight moves every line inward, never outward."""
    light, medium = (Frame.for_stroke(w.stroke) for w in WEIGHTS[:1] + WEIGHTS[2:])
    assert medium.half > light.half
    assert medium.base > light.base
    assert medium.cap < light.cap


# --------------------------------------------------------------------------
# Skeleton operations
# --------------------------------------------------------------------------
def test_line_ops():
    ops = line(0, 0, 10, 20).ops
    assert ops == [("M", (0, 0)), ("L", (10, 20))]


def test_line_without_move_is_implicit():
    """Drawing a line into an empty skeleton starts it, rather than crashing."""
    assert Sk().L(5, 5).ops == [("M", (5, 5))]


def test_arc_hits_both_endpoints():
    """A quarter arc must land exactly on start and end angles."""
    sk = Sk().arc(0, 0, 100, 0, 90)
    pts = [op[-1] for op in sk.ops]
    assert pts[0] == pytest.approx((100, 0))
    assert pts[-1] == pytest.approx((0, 100), abs=1e-9)


def test_arc_is_split_into_at_most_90_degree_cubics():
    assert len(Sk().arc(0, 0, 50, 0, 360).ops) - 1 == 4
    assert len(Sk().arc(0, 0, 50, 0, 180).ops) - 1 == 2
    assert len(Sk().arc(0, 0, 50, 0, 30).ops) - 1 == 1


def test_arc_gap_emits_a_line():
    """A discontinuous arc must not draw a chord across the gap.

    Continuing an arc from 45 deg to a *new* arc starting at 90 deg has to insert
    a line to the new start point; without it the two arcs would be joined by a
    spurious curve.
    """
    first = Sk().arc(0, 0, 100, 0, 45)
    joined = first.arc(0, 0, 100, 90, 135)
    kinds = [op[0] for op in joined.ops]
    assert kinds[0] == "M"
    assert "L" in kinds, f"expected an explicit line across the gap, got {kinds}"


def test_arc_continues_without_a_line_when_contiguous():
    """A contiguous arc adds no line: the join is already exact."""
    joined = Sk().arc(0, 0, 100, 0, 45).arc(0, 0, 100, 45, 90)
    assert "L" not in [op[0] for op in joined.ops]


def _flatten(sk):
    """Flatten a skeleton into a dense polyline of on-curve points."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

    pen = DecomposingRecordingPen(RecordingPen())
    sk.to_skia().draw(pen)
    points = []
    for op, args in pen.value:
        if op == "moveTo":
            points.append(args[0])
        elif op in {"lineTo", "curveTo"}:
            points.append(args[-1])
    return points


def test_arc_stays_on_its_circle():
    """Walk the drawn curve and confirm it tracks the true radius.

    A cubic approximation puts its control points slightly outside the circle by
    design, so this samples the curve itself rather than the control polygon.
    """
    for point in _flatten(Sk().arc(30, 40, 77, 0, 360)):
        assert math.hypot(point[0] - 30, point[1] - 40) == pytest.approx(77, abs=0.05)


def test_circle_is_closed():
    ops = circle(0, 0, 10).ops
    assert ops[-1] == ("Z",)


def test_pill_has_straight_sides_when_taller_than_wide():
    """A stadium must contain two straight segments, not be a circle."""
    ops = pill(0, 0, 100, 300).ops
    assert sum(1 for op in ops if op[0] == "L") == 2


def test_poly_without_radius_keeps_sharp_corners():
    ops = Sk().poly([(0, 0), (10, 0), (10, 10)]).ops
    assert [op[0] for op in ops] == ["M", "L", "L"]


def test_poly_radius_replaces_corners_with_curves():
    """The sharp corner becomes a cubic; the two ends stay straight."""
    ops = Sk().poly([(0, 0), (10, 0), (10, 10)], r=3).ops
    assert [op[0] for op in ops] == ["M", "L", "C", "L"]


def test_poly_closed_closes():
    assert Sk().poly([(0, 0), (10, 0), (10, 10)], r=2, closed=True).ops[-1] == ("Z",)


def test_poly_radius_clamped_to_short_segments():
    """A radius longer than the segment must not overshoot the corner."""
    small = Sk().poly([(0, 0), (4, 0), (4, 4)], r=99)
    xs = [op[-1][0] for op in small.ops if op[0] in {"M", "L"}]
    assert min(xs) >= -1e-9 and max(xs) <= 4 + 1e-9


def test_hermite_passes_through_its_points():
    """Every interior point must be a real on-curve point of the curve."""
    from fontTools.pens.recordingPen import RecordingPen

    pen = RecordingPen()
    pts = [(0, 0, 1, 0), (50, 100, 0, 1), (100, 0, -1, 0)]
    Sk().hermite(pts).to_skia().draw(pen)

    on_curve = [args[-1] for op, args in pen.value if op in {"moveTo", "curveTo"}]
    assert on_curve[0] == pytest.approx(pts[0][:2])
    assert on_curve[-1] == pytest.approx(pts[-1][:2])
    assert on_curve[1] == pytest.approx(pts[1][:2])


def test_hermite_first_move_is_implicit():
    assert Sk().hermite([(0, 0, 1, 0), (10, 0, 1, 0)]).ops[0][0] == "M"


def test_mapped_transforms_every_point():
    sk = Sk().M(1, 2).L(3, 4).C(5, 6, 7, 8, 9, 10).Z()
    out = sk.mapped(lambda x, y: (x * 2, y + 1))
    assert out.ops[0] == ("M", (2, 3))
    assert out.ops[1] == ("L", (6, 5))
    assert out.ops[2] == ("C", (10, 7), (14, 9), (18, 11))
    assert out.ops[-1] == ("Z",)
    assert len(out.ops) == len(sk.ops)


def test_mapped_does_not_mutate_the_source():
    sk = Sk().M(1, 1)
    sk.mapped(lambda x, y: (x + 100, y))
    assert sk.ops == [("M", (1, 1))]


# --------------------------------------------------------------------------
# Primitives / transforms
# --------------------------------------------------------------------------
def test_shift():
    assert shift(Sk().M(10, 10), 5, -5).ops == [("M", (15, 5))]


def test_rot180_is_an_involution():
    sk = Sk().M(3, 7).L(11, 13)
    back = rot180(rot180(sk, 0, 0), 0, 0)
    assert back.ops == sk.ops


def test_mirror_x_mirrors_about_the_axis():
    assert mirror_x(Sk().M(0, 5), 10).ops == [("M", (20, 5))]


def test_rot90_four_times_returns_home():
    sk = Sk().M(3, 7).L(11, 13)
    out = sk
    for _ in range(4):
        out = rot90(out, 0, 0)
    assert out.ops == sk.ops


def test_rot90_direction_is_opposite_each_way():
    ccw = rot90(Sk().M(1, 0), 0, 0, True).ops[0][1]
    cw = rot90(Sk().M(1, 0), 0, 0, False).ops[0][1]
    assert ccw == pytest.approx((0, 1))
    assert cw == pytest.approx((0, -1))


# --------------------------------------------------------------------------
# Inventory consistency
# --------------------------------------------------------------------------
@pytest.mark.parametrize("stroke", [w.stroke for w in WEIGHTS])
def test_designed_glyphs_match_the_declared_order(stroke):
    assert tuple(design(stroke)) == layout.GLYPH_ORDER


@pytest.mark.parametrize("stroke", [w.stroke for w in WEIGHTS])
def test_inventory_is_self_consistent(stroke):
    layout.check_coverage(design(stroke))


def test_codepoints_are_unique():
    assert len(layout.CHARS) == len(layout.CODEPOINTS)


def test_sidebearing_classes_are_all_defined():
    assert {c for s in layout.SIDES.values() for c in s} <= set(layout.EDGE)


def test_kern_pairs_reference_real_glyphs():
    drawn = set(design(WEIGHTS[1].stroke))
    assert {n for pair in layout.KERN for n in pair[:2]} <= drawn


def test_kern_pairs_are_negative_or_zero():
    """Positive kerning here would mean a bug in the table."""
    assert all(v <= 0 for _, _, v in layout.KERN)


def test_kern_feature_is_well_formed():
    fea = layout.kern_feature()
    assert fea.startswith("languagesystem DFLT dflt;")
    assert "feature kern {" in fea and "} kern;" in fea
    assert fea.count("pos ") == len(layout.KERN)


def test_every_drawn_glyph_has_ink():
    """A silently empty glyph is a bug that would only show in review."""
    for stroke in (w.stroke for w in WEIGHTS):
        for name, glyph in design(stroke).items():
            assert glyph.strokes or glyph.fills, f"{name} at stroke {stroke} is empty"

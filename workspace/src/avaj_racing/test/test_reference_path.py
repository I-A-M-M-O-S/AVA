"""Unit tests for AP-D01 CSV input validation."""

import math
from pathlib import Path

from avaj_racing.reference_path import (
    PathPoint,
    PathValidationError,
    ValidationConfig,
    load_csv,
    validate_path,
)

import pytest


def square_points():
    """Return a one-metre counterclockwise square with coherent metadata."""
    return [
        PathPoint(0.0, 0.0, 0.0, 0.0),
        PathPoint(1.0, 0.0, math.pi / 2.0, 1.0),
        PathPoint(1.0, 1.0, math.pi, 2.0),
        PathPoint(0.0, 1.0, -math.pi / 2.0, 3.0),
    ]


def test_valid_closed_counterclockwise_path_has_tangent_headings():
    """Accept a valid closed geometry and generate consistent headings."""
    result = validate_path(square_points())

    assert result.frame_id == 'map'
    assert result.direction == 'counterclockwise'
    assert result.total_length_m == pytest.approx(4.0)
    assert result.points[0].heading_rad == pytest.approx(0.0)


@pytest.mark.parametrize(
    ('points', 'reason'),
    [
        (square_points()[:3], 'at least'),
        ([
            PathPoint(0.0, 0.0), PathPoint(1.0, 1.0),
            PathPoint(0.0, 1.0), PathPoint(1.0, 0.0),
        ], 'self-intersect'),
        ([
            PathPoint(0.0, 0.0), PathPoint(1.0, 0.0),
            PathPoint(float('nan'), 1.0), PathPoint(0.0, 1.0),
        ], 'finite'),
        ([
            PathPoint(0.0, 0.0), PathPoint(3.5, 0.0),
            PathPoint(3.5, 1.0), PathPoint(0.0, 1.0),
        ], 'exceeds'),
    ],
)
def test_invalid_geometry_is_rejected(points, reason):
    """Reject each fail-closed geometry class with a useful reason."""
    with pytest.raises(PathValidationError, match=reason):
        validate_path(points)


def test_wrong_frame_and_clockwise_direction_are_rejected():
    """Reject input outside the AP-M01 map-frame and direction contract."""
    with pytest.raises(PathValidationError, match='frame'):
        validate_path(square_points(), ValidationConfig(frame_id='odom'))
    with pytest.raises(PathValidationError, match='direction'):
        validate_path([
            PathPoint(point.x_m, point.y_m)
            for point in reversed(square_points())
        ])


def test_non_monotone_arc_length_and_opposite_heading_are_rejected():
    """Reject metadata that contradicts the ordered driving path."""
    points = square_points()
    points[2] = PathPoint(1.0, 1.0, math.pi, 1.0)
    with pytest.raises(PathValidationError, match='arc length'):
        validate_path(points)

    points = square_points()
    points[0] = PathPoint(0.0, 0.0, math.pi, 0.0)
    with pytest.raises(PathValidationError, match='heading disagrees'):
        validate_path(points)


def test_csv_formats_and_nonfinite_values_are_checked(tmp_path):
    """Accept documented upstream columns and reject nonfinite CSV values."""
    tumftm = tmp_path / 'trajectory.csv'
    tumftm.write_text(
        '0,0,0,0,0,0,0\n1,1,0,0,0,0,0\n2,1,1,0,0,0,0\n3,0,1,0,0,0,0\n',
        encoding='utf-8',
    )
    assert len(load_csv(tumftm)) == 4

    invalid = Path(tmp_path / 'invalid.csv')
    invalid.write_text('x_m,y_m\n0,0\n1,0\nnan,1\n0,1\n', encoding='utf-8')
    with pytest.raises(PathValidationError, match='finite'):
        load_csv(invalid)

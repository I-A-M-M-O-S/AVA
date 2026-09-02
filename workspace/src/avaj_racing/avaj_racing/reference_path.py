"""CSV import and fail-closed validation for static closed racing paths."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class PathValidationError(ValueError):
    """Explain why an external path must not be published."""


@dataclass(frozen=True)
class PathPoint:
    """One two-dimensional path point and its tangent heading in radians."""

    x_m: float
    y_m: float
    heading_rad: float | None = None
    arc_length_m: float | None = None


@dataclass(frozen=True)
class ValidatedPath:
    """A closed geometric path that satisfies the AP-D01 contract."""

    frame_id: str
    points: tuple[PathPoint, ...]
    direction: str
    total_length_m: float


@dataclass(frozen=True)
class ValidationConfig:
    """Conservative, parameterizable geometry limits in SI units."""

    frame_id: str = 'map'
    required_direction: str = 'counterclockwise'
    min_points: int = 4
    min_point_spacing_m: float = 0.05
    max_segment_length_m: float = 3.0
    intersection_epsilon_m: float = 1.0e-9
    heading_tolerance_rad: float = math.radians(45.0)


def _as_float(value: str, row_number: int, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PathValidationError(
            f'row {row_number}: {field} is not a number'
        ) from exc
    if not math.isfinite(result):
        raise PathValidationError(f'row {row_number}: {field} must be finite')
    return result


def _normalized_name(name: str) -> str:
    return name.strip().lower().replace(' ', '').replace('-', '_')


def _field_index(names: list[str], alternatives: tuple[str, ...]) -> int | None:
    normalized = [_normalized_name(name) for name in names]
    for alternative in alternatives:
        if alternative in normalized:
            return normalized.index(alternative)
    return None


def load_csv(path: str | Path) -> list[PathPoint]:
    """Load AVAJ, TPH, or global-racetrajectory CSV geometry.

    Headered input requires x/y columns (``x_m``/``y_m`` preferred).  Headerless
    input is accepted only in documented upstream layouts: four-column TPH
    reference track ``x,y,width_right,width_left`` or seven-column TUMFTM race
    trajectory ``s,x,y,psi,kappa,vx,ax``.
    """
    source = Path(path)
    try:
        with source.open(newline='', encoding='utf-8') as stream:
            rows = [row for row in csv.reader(stream) if row and not row[0].lstrip().startswith('#')]
    except OSError as exc:
        raise PathValidationError(f'cannot read CSV {source}: {exc}') from exc
    if not rows:
        raise PathValidationError('CSV contains no data rows')

    first = rows[0]
    has_header = any(not _is_numeric(cell) for cell in first)
    points: list[PathPoint] = []
    if has_header:
        x_index = _field_index(first, ('x_m', 'x', 'pos_x'))
        y_index = _field_index(first, ('y_m', 'y', 'pos_y'))
        s_index = _field_index(first, ('s_m', 's', 'arc_length_m'))
        heading_index = _field_index(first, ('psi_rad', 'heading_rad', 'yaw_rad', 'psi'))
        row_data = rows[1:]
        if x_index is None or y_index is None:
            raise PathValidationError('CSV header must contain x/y coordinates')
    else:
        row_data = rows
        if len(first) == 4:
            x_index, y_index, s_index, heading_index = 0, 1, None, None
        elif len(first) == 7:
            x_index, y_index, s_index, heading_index = 1, 2, 0, 3
        else:
            raise PathValidationError(
                'headerless CSV must have 4 TPH or 7 TUMFTM columns'
            )

    if not row_data:
        raise PathValidationError('CSV contains no path points')
    for row_number, row in enumerate(row_data, start=2 if has_header else 1):
        required_index = max(index for index in (x_index, y_index) if index is not None)
        if len(row) <= required_index:
            raise PathValidationError(f'row {row_number}: missing x/y coordinate')
        x = _as_float(row[x_index], row_number, 'x')
        y = _as_float(row[y_index], row_number, 'y')
        if s_index is not None and len(row) <= s_index:
            raise PathValidationError(f'row {row_number}: missing arc length')
        if heading_index is not None and len(row) <= heading_index:
            raise PathValidationError(f'row {row_number}: missing heading')
        arc = (_as_float(row[s_index], row_number, 'arc length')
               if s_index is not None else None)
        heading = (_as_float(row[heading_index], row_number, 'heading')
                   if heading_index is not None else None)
        points.append(PathPoint(x, y, heading, arc))
    return points


def validate_path(
    points: Iterable[PathPoint], config: ValidationConfig = ValidationConfig()
) -> ValidatedPath:
    """Validate closed path geometry and return tangential headings.

    The input must be in the canonical ``map`` frame.  The geometric start is
    deliberately not repeated: closure is the implicit final-to-first segment.
    """
    items = tuple(points)
    if config.frame_id != 'map' or not config.frame_id or config.frame_id.startswith('/'):
        raise PathValidationError('reference-path frame must be exactly map')
    if config.required_direction not in ('clockwise', 'counterclockwise'):
        raise PathValidationError('required direction must be clockwise or counterclockwise')
    if config.min_points < 4:
        raise PathValidationError('minimum point count must be at least four')
    if config.min_point_spacing_m <= 0.0:
        raise PathValidationError('minimum point spacing must be positive')
    if config.max_segment_length_m <= config.min_point_spacing_m:
        raise PathValidationError(
            'maximum segment length must exceed minimum point spacing'
        )
    if len(items) < config.min_points:
        raise PathValidationError(
            f'path has {len(items)} points; at least {config.min_points} are required'
        )
    for index, point in enumerate(items):
        if not math.isfinite(point.x_m) or not math.isfinite(point.y_m):
            raise PathValidationError(f'point {index}: coordinates must be finite')
        if point.heading_rad is not None and not math.isfinite(point.heading_rad):
            raise PathValidationError(f'point {index}: heading must be finite')
        if point.arc_length_m is not None and not math.isfinite(point.arc_length_m):
            raise PathValidationError(f'point {index}: arc length must be finite')

    segment_lengths = []
    for index in range(len(items)):
        first = items[index]
        second = items[(index + 1) % len(items)]
        length = math.hypot(second.x_m - first.x_m, second.y_m - first.y_m)
        if length < config.min_point_spacing_m:
            raise PathValidationError(
                f'segment {index}: spacing {length:.6g} m is below '
                f'{config.min_point_spacing_m:.6g} m'
            )
        if length > config.max_segment_length_m:
            raise PathValidationError(
                f'segment {index}: length {length:.6g} m exceeds '
                f'{config.max_segment_length_m:.6g} m; path is open or undersampled'
            )
        segment_lengths.append(length)

    _validate_monotone_arc_length(items)
    _validate_no_self_intersection(items, config.intersection_epsilon_m)
    signed_area = _signed_area(items)
    direction = 'counterclockwise' if signed_area > 0.0 else 'clockwise'
    if abs(signed_area) <= config.intersection_epsilon_m:
        raise PathValidationError('path encloses no measurable area')
    if direction != config.required_direction:
        raise PathValidationError(
            f'path direction is {direction}; required {config.required_direction}'
        )

    headings = _tangent_headings(items)
    for index, point in enumerate(items):
        if point.heading_rad is not None:
            difference = _angular_distance(point.heading_rad, headings[index])
            if difference > config.heading_tolerance_rad:
                raise PathValidationError(
                    f'point {index}: heading disagrees with driving direction by '
                    f'{math.degrees(difference):.1f} degrees'
                )
    normalized = tuple(
        PathPoint(point.x_m, point.y_m, headings[index],
                  point.arc_length_m)
        for index, point in enumerate(items)
    )
    return ValidatedPath('map', normalized, direction, sum(segment_lengths))


def _is_numeric(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _validate_monotone_arc_length(points: tuple[PathPoint, ...]) -> None:
    values = [point.arc_length_m for point in points]
    if any(value is None for value in values):
        return
    for index in range(1, len(values)):
        if values[index] <= values[index - 1]:
            raise PathValidationError(
                f'point {index}: arc length must be strictly monotone'
            )


def _orientation(a: PathPoint, b: PathPoint, c: PathPoint) -> float:
    return ((b.x_m - a.x_m) * (c.y_m - a.y_m)
            - (b.y_m - a.y_m) * (c.x_m - a.x_m))


def _segments_intersect(a: PathPoint, b: PathPoint, c: PathPoint,
                        d: PathPoint, epsilon: float) -> bool:
    orientations = (_orientation(a, b, c), _orientation(a, b, d),
                    _orientation(c, d, a), _orientation(c, d, b))
    if any(abs(value) <= epsilon for value in orientations):
        return True
    return ((orientations[0] > 0.0) != (orientations[1] > 0.0)
            and (orientations[2] > 0.0) != (orientations[3] > 0.0))


def _validate_no_self_intersection(points: tuple[PathPoint, ...], epsilon: float) -> None:
    count = len(points)
    for first in range(count):
        for second in range(first + 1, count):
            if second == first + 1 or (first == 0 and second == count - 1):
                continue
            if _segments_intersect(
                points[first], points[(first + 1) % count], points[second],
                points[(second + 1) % count], epsilon
            ):
                raise PathValidationError(
                    f'segments {first} and {second} self-intersect or touch'
                )


def _signed_area(points: tuple[PathPoint, ...]) -> float:
    return 0.5 * sum(
        point.x_m * points[(index + 1) % len(points)].y_m
        - points[(index + 1) % len(points)].x_m * point.y_m
        for index, point in enumerate(points)
    )


def _tangent_headings(points: tuple[PathPoint, ...]) -> list[float]:
    return [
        math.atan2(points[(index + 1) % len(points)].y_m - point.y_m,
                   points[(index + 1) % len(points)].x_m - point.x_m)
        for index, point in enumerate(points)
    ]


def _angular_distance(first: float, second: float) -> float:
    return abs((first - second + math.pi) % (2.0 * math.pi) - math.pi)

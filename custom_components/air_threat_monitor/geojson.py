"""Small GeoJSON point-in-polygon helpers for resolving the home area."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .alerts import resolved_area_from_feature
from .models import AlertScope, GeoPoint, ResolvedArea

Position = Sequence[float]
Ring = Sequence[Position]
PolygonCoordinates = Sequence[Ring]


def _point_on_segment(
    x: float,
    y: float,
    first: Position,
    second: Position,
    *,
    epsilon: float = 1e-10,
) -> bool:
    """Return whether a point lies on a line segment."""

    x1, y1 = float(first[0]), float(first[1])
    x2, y2 = float(second[0]), float(second[1])
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > epsilon:
        return False
    return (
        min(x1, x2) - epsilon <= x <= max(x1, x2) + epsilon
        and min(y1, y2) - epsilon <= y <= max(y1, y2) + epsilon
    )


def _point_in_ring(x: float, y: float, ring: Ring) -> bool:
    """Test a point against one linear ring using ray casting."""

    if len(ring) < 3:
        return False

    inside = False
    previous = ring[-1]
    for current in ring:
        if len(previous) < 2 or len(current) < 2:
            previous = current
            continue
        if _point_on_segment(x, y, previous, current):
            return True

        x1, y1 = float(previous[0]), float(previous[1])
        x2, y2 = float(current[0]), float(current[1])
        intersects = (y1 > y) != (y2 > y)
        if intersects:
            intersection_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < intersection_x:
                inside = not inside
        previous = current
    return inside


def _point_in_polygon(x: float, y: float, polygon: PolygonCoordinates) -> bool:
    """Test a point against a polygon, respecting interior holes."""

    if not polygon or not _point_in_ring(x, y, polygon[0]):
        return False
    return not any(_point_in_ring(x, y, hole) for hole in polygon[1:])


def point_in_geometry(point: GeoPoint, geometry: dict[str, Any]) -> bool:
    """Test a point against a GeoJSON Polygon or MultiPolygon."""

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list):
        return False

    x, y = point.longitude, point.latitude
    try:
        if geometry_type == "Polygon":
            return _point_in_polygon(x, y, coordinates)
        if geometry_type == "MultiPolygon":
            return any(
                _point_in_polygon(x, y, polygon) for polygon in coordinates
            )
    except (IndexError, OverflowError, TypeError, ValueError, ZeroDivisionError):
        return False
    return False


def resolve_area(
    point: GeoPoint,
    feature_collection: dict[str, Any],
    scope: AlertScope,
) -> ResolvedArea | None:
    """Find the GeoJSON administrative feature containing a point."""

    if feature_collection.get("type") != "FeatureCollection":
        return None
    features = feature_collection.get("features", [])
    if not isinstance(features, list):
        return None

    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        if point_in_geometry(point, geometry):
            return resolved_area_from_feature(feature, scope)
    return None

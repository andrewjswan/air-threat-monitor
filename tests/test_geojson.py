"""Tests for local point-to-area resolution."""

from __future__ import annotations

from custom_components.air_threat_monitor.geojson import resolve_area
from custom_components.air_threat_monitor.models import AlertScope, GeoPoint

COLLECTION = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "key": "test:district",
                "name": "Test district",
                "oblast": "Test oblast",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[30.0, 49.0], [31.0, 49.0], [31.0, 50.0], [30.0, 50.0]]
                ],
            },
        }
    ],
}


def test_point_inside_polygon_resolves_area() -> None:
    area = resolve_area(
        GeoPoint(49.5, 30.5), COLLECTION, AlertScope.RAION
    )
    assert area is not None
    assert area.area_key == "test:district"


def test_point_outside_polygon_does_not_resolve_area() -> None:
    area = resolve_area(
        GeoPoint(48.5, 30.5), COLLECTION, AlertScope.RAION
    )
    assert area is None


def test_point_on_polygon_boundary_is_included() -> None:
    area = resolve_area(
        GeoPoint(49.5, 30.0), COLLECTION, AlertScope.RAION
    )
    assert area is not None


def test_malformed_geometry_is_ignored_without_crashing() -> None:
    collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "properties": {"key": "broken"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[["bad", None], [31.0, 49.0]]],
                },
            }
        ],
    }

    assert resolve_area(GeoPoint(49.5, 30.5), collection, AlertScope.RAION) is None


def test_non_feature_collection_is_rejected() -> None:
    assert (
        resolve_area(
            GeoPoint(49.5, 30.5),
            {"features": COLLECTION["features"]},
            AlertScope.RAION,
        )
        is None
    )

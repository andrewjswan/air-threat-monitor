"""Tests for geographic calculations."""

from __future__ import annotations

import pytest

from custom_components.air_threat_monitor.calculations import (
    angular_difference,
    bearing_degrees,
    calculate_threat,
    direction_label,
    distance_km,
    screen_angle,
)
from custom_components.air_threat_monitor.models import (
    GeoPoint,
    Threat,
    ThreatCategory,
)


def make_threat(position: GeoPoint, heading: float | None) -> Threat:
    return Threat(
        threat_id="test",
        position=position,
        category=ThreatCategory.UAV,
        title="Test UAV",
        heading=heading,
    )


def test_distance_between_kyiv_and_lviv() -> None:
    kyiv = GeoPoint(50.4501, 30.5234)
    lviv = GeoPoint(49.8397, 24.0297)
    assert distance_km(kyiv, lviv) == pytest.approx(468.0, abs=3.0)


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (GeoPoint(1.0, 0.0), 0.0),
        (GeoPoint(0.0, 1.0), 90.0),
        (GeoPoint(-1.0, 0.0), 180.0),
        (GeoPoint(0.0, -1.0), 270.0),
    ],
)
def test_cardinal_bearings(target: GeoPoint, expected: float) -> None:
    assert bearing_degrees(GeoPoint(0.0, 0.0), target) == pytest.approx(expected)


def test_angular_difference_wraps_across_north() -> None:
    assert angular_difference(350.0, 10.0) == pytest.approx(20.0)


def test_screen_orientation_with_east_at_top() -> None:
    assert screen_angle(90.0, 90.0) == pytest.approx(0.0)
    assert screen_angle(0.0, 90.0) == pytest.approx(270.0)


def test_target_north_of_home_heading_south_is_approaching() -> None:
    result = calculate_threat(
        make_threat(GeoPoint(1.0, 0.0), heading=180.0),
        GeoPoint(0.0, 0.0),
    )
    assert result.bearing_from_home == pytest.approx(0.0)
    assert result.bearing_to_home == pytest.approx(180.0)
    assert result.approach_angle == pytest.approx(0.0)
    assert result.is_approaching is True


def test_target_north_of_home_heading_north_is_moving_away() -> None:
    result = calculate_threat(
        make_threat(GeoPoint(1.0, 0.0), heading=0.0),
        GeoPoint(0.0, 0.0),
    )
    assert result.approach_angle == pytest.approx(180.0)
    assert result.is_approaching is False


def test_missing_heading_is_unknown_not_moving_away() -> None:
    result = calculate_threat(
        make_threat(GeoPoint(1.0, 0.0), heading=None),
        GeoPoint(0.0, 0.0),
    )
    assert result.approach_angle is None
    assert result.is_approaching is None
    assert result.icon_rotation is None


@pytest.mark.parametrize(
    ("bearing", "label"),
    [
        (0.0, "Пн"),
        (45.0, "Пн-Сх"),
        (90.0, "Сх"),
        (180.0, "Пд"),
        (270.0, "Зх"),
        (359.0, "Пн"),
    ],
)
def test_direction_labels(bearing: float, label: str) -> None:
    assert direction_label(bearing) == label


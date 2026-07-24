"""Geographic and threat calculations used by the integration and card."""

from __future__ import annotations

import math

from .const import DEFAULT_APPROACH_CONE_DEGREES, DEFAULT_SCREEN_TOP_BEARING
from .models import CalculatedThreat, GeoPoint, Threat

EARTH_RADIUS_KM = 6371.0088


def normalize_angle(degrees: float) -> float:
    """Normalize an angle to the half-open range [0, 360)."""

    return degrees % 360.0


def angular_difference(first: float, second: float) -> float:
    """Return the smallest absolute difference between two headings."""

    return abs((first - second + 180.0) % 360.0 - 180.0)


def distance_km(first: GeoPoint, second: GeoPoint) -> float:
    """Calculate great-circle distance using the haversine formula."""

    phi1 = math.radians(first.latitude)
    phi2 = math.radians(second.latitude)
    delta_phi = math.radians(second.latitude - first.latitude)
    delta_lambda = math.radians(second.longitude - first.longitude)

    haversine = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    return EARTH_RADIUS_KM * 2.0 * math.atan2(
        math.sqrt(haversine), math.sqrt(1.0 - haversine)
    )


def bearing_degrees(first: GeoPoint, second: GeoPoint) -> float:
    """Calculate initial bearing from the first point to the second point."""

    phi1 = math.radians(first.latitude)
    phi2 = math.radians(second.latitude)
    delta_lambda = math.radians(second.longitude - first.longitude)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    )
    return normalize_angle(math.degrees(math.atan2(y, x)))


def screen_angle(world_bearing: float, screen_top_bearing: float) -> float:
    """Convert a world bearing into an angle on an oriented display."""

    return normalize_angle(world_bearing - screen_top_bearing)


def direction_label(degrees: float) -> str:
    """Return an eight-point Ukrainian compass label."""

    labels = (
        "Пн",
        "Пн-Сх",
        "Сх",
        "Пд-Сх",
        "Пд",
        "Пд-Зх",
        "Зх",
        "Пн-Зх",
    )
    return labels[int((normalize_angle(degrees) + 22.5) // 45.0) % 8]


def direction_arrow(degrees: float) -> str:
    """Return an eight-point direction arrow."""

    arrows = ("↑", "↗", "→", "↘", "↓", "↙", "←", "↖")
    return arrows[int((normalize_angle(degrees) + 22.5) // 45.0) % 8]


def risk_level(distance: float) -> str:
    """Map distance to the default notification radii."""

    if distance <= 20.0:
        return "critical"
    if distance <= 50.0:
        return "warning"
    if distance <= 100.0:
        return "watch"
    return "far"


def calculate_threat(
    threat: Threat,
    home: GeoPoint,
    *,
    screen_top_bearing: float = DEFAULT_SCREEN_TOP_BEARING,
    approach_cone_degrees: float = DEFAULT_APPROACH_CONE_DEGREES,
) -> CalculatedThreat:
    """Calculate distance, bearings, screen placement, and approach state."""

    distance = distance_km(home, threat.position)
    from_home = bearing_degrees(home, threat.position)
    to_home = bearing_degrees(threat.position, home)

    heading = (
        normalize_angle(threat.heading) if threat.heading is not None else None
    )
    approach_angle = (
        angular_difference(heading, to_home) if heading is not None else None
    )
    is_approaching = (
        approach_angle <= approach_cone_degrees
        if approach_angle is not None
        else None
    )

    return CalculatedThreat(
        threat=threat,
        distance_km=distance,
        bearing_from_home=from_home,
        bearing_to_home=to_home,
        screen_bearing=screen_angle(from_home, screen_top_bearing),
        icon_rotation=(
            screen_angle(heading, screen_top_bearing)
            if heading is not None
            else None
        ),
        approach_angle=approach_angle,
        is_approaching=is_approaching,
        risk_level=risk_level(distance),
    )

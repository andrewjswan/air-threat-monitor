"""Provider-neutral data models for Air Threat Monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ThreatCategory(StrEnum):
    """Normalized threat categories exposed by the integration."""

    UAV = "uav"
    FPV = "fpv"
    RECON = "recon"
    MISSILE = "missile"
    BALLISTIC = "ballistic"
    KAB = "kab"
    AIRCRAFT = "aircraft"
    UNKNOWN = "unknown"


class AlertScope(StrEnum):
    """Administrative level for an active air alert."""

    RAION = "raion"
    OBLAST = "oblast"


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """A latitude and longitude pair."""

    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Threat:
    """A normalized threat received from a provider."""

    threat_id: str
    position: GeoPoint
    category: ThreatCategory
    title: str
    locality: str = ""
    district: str = ""
    region: str = ""
    heading: float | None = None
    status: str = "active"
    updated_at: str = field(default="", compare=False)
    confidence: str = ""
    group_count: int = 0


@dataclass(frozen=True, slots=True)
class CalculatedThreat:
    """A threat enriched with calculations relative to the user's home."""

    threat: Threat
    distance_km: float
    bearing_from_home: float
    bearing_to_home: float
    screen_bearing: float
    icon_rotation: float | None
    approach_angle: float | None
    is_approaching: bool | None
    risk_level: str


@dataclass(frozen=True, slots=True)
class ActiveAlert:
    """A normalized active air alert."""

    area_key: str
    name: str
    oblast: str
    since: str
    scope: AlertScope


@dataclass(frozen=True, slots=True)
class ResolvedArea:
    """An administrative area containing the configured home point."""

    area_key: str
    name: str
    oblast: str
    scope: AlertScope


@dataclass(frozen=True, slots=True)
class MonitorData:
    """Complete processed snapshot shared by Home Assistant entities."""

    threats: tuple[CalculatedThreat, ...]
    local_alert: ActiveAlert | None
    raion: ResolvedArea | None
    oblast: ResolvedArea | None
    updated_at: datetime = field(compare=False)
    status_since: datetime | None = field(default=None, compare=False)

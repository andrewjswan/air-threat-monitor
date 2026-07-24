"""Sensors for Air Threat Monitor."""

from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AirThreatConfigEntry
from .calculations import direction_arrow, direction_label
from .const import asset_url
from .entity import AirThreatEntity
from .models import CalculatedThreat, ThreatCategory

_CATEGORY_IMAGE = {
    ThreatCategory.UAV: "shahed.png",
    ThreatCategory.FPV: "fpv.png",
    ThreatCategory.RECON: "recon.png",
    ThreatCategory.MISSILE: "rocket.png",
    ThreatCategory.BALLISTIC: "rocket.png",
    ThreatCategory.KAB: "kab.png",
    ThreatCategory.AIRCRAFT: "jet.png",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirThreatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up monitor sensors."""

    async_add_entities(
        [NearestThreatSensor(entry), ActiveThreatCountSensor(entry)]
    )


class NearestThreatSensor(AirThreatEntity, SensorEntity):
    """Expose the nearest active threat and its calculated metadata."""

    _attr_translation_key = "nearest_threat"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, entry: AirThreatConfigEntry) -> None:
        super().__init__(entry.runtime_data, entry, "nearest_threat")

    @property
    def _nearest(self) -> CalculatedThreat | None:
        threats = self.coordinator.data.threats
        return threats[0] if threats else None

    @property
    def native_value(self) -> float | None:
        """Return nearest distance in kilometres."""

        nearest = self._nearest
        return round(nearest.distance_km, 1) if nearest else None

    @property
    def icon(self) -> str:
        return "mdi:radar"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return provider and calculated metadata for the nearest target."""

        nearest = self._nearest
        if nearest is None:
            return {"active": False}

        threat = nearest.threat
        heading = threat.heading
        image = _CATEGORY_IMAGE.get(threat.category)
        return {
            "active": True,
            "threat_id": threat.threat_id,
            "category": threat.category.value,
            "status": threat.status,
            "title": threat.title,
            "locality": threat.locality,
            "district": threat.district,
            "region": threat.region,
            "heading": heading,
            "heading_arrow": direction_arrow(heading) if heading is not None else None,
            "bearing_from_home": round(nearest.bearing_from_home),
            "bearing_label": direction_label(nearest.bearing_from_home),
            "bearing_arrow": direction_arrow(nearest.bearing_from_home),
            "bearing_to_home": round(nearest.bearing_to_home),
            "screen_bearing": round(nearest.screen_bearing),
            "icon_rotation": (
                round(nearest.icon_rotation)
                if nearest.icon_rotation is not None
                else None
            ),
            "approach_angle": (
                round(nearest.approach_angle)
                if nearest.approach_angle is not None
                else None
            ),
            "is_approaching": nearest.is_approaching,
            "risk_level": nearest.risk_level,
            "image_url": asset_url(f"images/{image}") if image else None,
        }


class ActiveThreatCountSensor(AirThreatEntity, SensorEntity):
    """Expose total and categorized active target counts."""

    _attr_translation_key = "active_threats"
    _attr_icon = "mdi:radar"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: AirThreatConfigEntry) -> None:
        super().__init__(entry.runtime_data, entry, "active_threats")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.threats)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        threats = self.coordinator.data.threats
        categories = Counter(item.threat.category.value for item in threats)
        return {
            "within_100_km": sum(item.distance_km <= 100 for item in threats),
            "within_50_km": sum(item.distance_km <= 50 for item in threats),
            "within_20_km": sum(item.distance_km <= 20 for item in threats),
            "approaching": sum(item.is_approaching is True for item in threats),
            "stale": sum(item.threat.status == "stale" for item in threats),
            "uav": categories[ThreatCategory.UAV.value],
            "fpv": categories[ThreatCategory.FPV.value],
            "recon": categories[ThreatCategory.RECON.value],
            "missiles": categories[ThreatCategory.MISSILE.value],
            "ballistic": categories[ThreatCategory.BALLISTIC.value],
            "kab": categories[ThreatCategory.KAB.value],
            "aircraft": categories[ThreatCategory.AIRCRAFT.value],
            "unknown": categories[ThreatCategory.UNKNOWN.value],
        }

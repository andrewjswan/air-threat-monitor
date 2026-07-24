"""Shared Home Assistant entity helpers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AirThreatConfigEntry
from .const import ATTRIBUTION, DOMAIN, PROJECT_URL
from .coordinator import AirThreatCoordinator


class AirThreatEntity(CoordinatorEntity[AirThreatCoordinator]):
    """Base class for entities backed by the shared coordinator."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AirThreatCoordinator,
        entry: AirThreatConfigEntry,
        key: str,
    ) -> None:
        """Initialize a monitor entity."""

        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Air Threat Monitor",
            model="Air threat location monitor",
            configuration_url=PROJECT_URL,
        )

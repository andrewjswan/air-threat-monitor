"""Configuration flow for Air Threat Monitor."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AirThreatApiClient, AirThreatApiError
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DEFAULT_ENTRY_TITLE,
    DOMAIN,
)
from .geojson import resolve_area
from .models import AlertScope, GeoPoint


class AirThreatMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up Air Threat Monitor from the Home Assistant UI."""

    VERSION = CONFIG_ENTRY_VERSION
    MINOR_VERSION = CONFIG_ENTRY_MINOR_VERSION

    @staticmethod
    def _location_key(data: dict[str, Any]) -> tuple[float, float] | None:
        """Return a normalized location key for duplicate checks."""

        try:
            return (
                round(float(data[CONF_LATITUDE]), 5),
                round(float(data[CONF_LONGITUDE]), 5),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _location_is_configured(
        self,
        data: dict[str, Any],
        *,
        exclude_entry_id: str | None = None,
    ) -> bool:
        """Return whether another entry already monitors this location."""

        location_key = self._location_key(data)
        return location_key is not None and any(
            candidate.entry_id != exclude_entry_id
            and self._location_key(dict(candidate.data)) == location_key
            for candidate in self.hass.config_entries.async_entries(DOMAIN)
        )

    async def _async_validate(
        self, user_input: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        latitude = float(user_input[CONF_LATITUDE])
        longitude = float(user_input[CONF_LONGITUDE])
        point = GeoPoint(latitude=latitude, longitude=longitude)
        client = AirThreatApiClient(async_get_clientsession(self.hass))

        try:
            threats, alerts, raions, oblasts = await asyncio.gather(
                client.async_get_threats(),
                client.async_get_alerts(),
                client.async_get_raions(),
                client.async_get_oblasts(),
            )
        except AirThreatApiError:
            raise

        if not isinstance(threats, dict) or not isinstance(alerts, dict):
            raise AirThreatApiError("Invalid provider response")

        raion = resolve_area(point, raions, AlertScope.RAION)
        oblast = resolve_area(point, oblasts, AlertScope.OBLAST)
        if raion is None and oblast is None:
            raise ValueError("location_not_supported")

        title = (
            raion.name
            if raion and raion.name
            else oblast.name
            if oblast and oblast.name
            else DEFAULT_ENTRY_TITLE
        )
        return title, {
            CONF_LATITUDE: latitude,
            CONF_LONGITUDE: longitude,
        }

    def _schema(self, defaults: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=defaults[CONF_LATITUDE],
                ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
                vol.Required(
                    CONF_LONGITUDE,
                    default=defaults[CONF_LONGITUDE],
                ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
            }
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial setup."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                title, data = await self._async_validate(user_input)
            except AirThreatApiError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "location_not_supported"
            else:
                if self._location_is_configured(data):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title=title, data=data)

        defaults = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
        }
        if user_input is not None:
            defaults.update(user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=self._schema(defaults),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the monitored location."""

        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                title, data = await self._async_validate(user_input)
            except AirThreatApiError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "location_not_supported"
            else:
                if self._location_is_configured(
                    data, exclude_entry_id=entry.entry_id
                ):
                    return self.async_abort(reason="already_configured")
                return self.async_update_reload_and_abort(
                    entry,
                    title=title,
                    data_updates=data,
                )

        defaults = {
            CONF_LATITUDE: entry.data[CONF_LATITUDE],
            CONF_LONGITUDE: entry.data[CONF_LONGITUDE],
        }
        if user_input is not None:
            defaults.update(user_input)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._schema(defaults),
            errors=errors,
        )

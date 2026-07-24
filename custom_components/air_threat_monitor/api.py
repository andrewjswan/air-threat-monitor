"""Asynchronous client for documented public NEPTUN API endpoints."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    API_ALERTS_PATH,
    API_BASE_URL,
    API_OBLASTS_PATH,
    API_RAIONS_PATH,
    API_STREAM_PATH,
    API_THREATS_PATH,
    VERSION,
)


class AirThreatApiError(Exception):
    """Raised when provider data cannot be fetched or validated."""


class AirThreatApiClient:
    """Read-only client for public provider endpoints."""

    def __init__(
        self,
        session: ClientSession,
        *,
        base_url: str = API_BASE_URL,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._timeout = ClientTimeout(total=timeout_seconds)

    @property
    def stream_url(self) -> str:
        """Return the provider WebSocket URL."""

        if self._base_url.startswith("https://"):
            root = "wss://" + self._base_url.removeprefix("https://")
        elif self._base_url.startswith("http://"):
            root = "ws://" + self._base_url.removeprefix("http://")
        else:
            root = self._base_url
        return f"{root}{API_STREAM_PATH}"

    async def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.get(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"HomeAssistant-AirThreatMonitor/{VERSION}",
                },
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as error:
            raise AirThreatApiError(f"Unable to fetch {path}: {error}") from error

        if not isinstance(payload, dict):
            raise AirThreatApiError(f"Invalid object returned by {path}")
        return payload

    @staticmethod
    def _require_lists(
        payload: dict[str, Any], path: str, *fields: str
    ) -> dict[str, Any]:
        """Validate documented list fields before data reaches entities."""

        missing = [
            field
            for field in fields
            if not isinstance(payload.get(field), list)
        ]
        if missing:
            joined = ", ".join(missing)
            raise AirThreatApiError(f"Invalid response from {path}: missing {joined}")
        return payload

    async def async_get_threats(self) -> dict[str, Any]:
        """Fetch the current threat snapshot."""

        payload = await self._get_json(API_THREATS_PATH)
        return self._require_lists(payload, API_THREATS_PATH, "threats")

    async def async_get_alerts(self) -> dict[str, Any]:
        """Fetch current district and oblast air alerts."""

        payload = await self._get_json(API_ALERTS_PATH)
        return self._require_lists(payload, API_ALERTS_PATH, "raions", "oblasts")

    async def async_get_raions(self) -> dict[str, Any]:
        """Fetch district boundaries used for local coordinate matching."""

        payload = await self._get_json(API_RAIONS_PATH)
        if payload.get("type") != "FeatureCollection":
            raise AirThreatApiError(
                f"Invalid response from {API_RAIONS_PATH}: not a FeatureCollection"
            )
        return self._require_lists(payload, API_RAIONS_PATH, "features")

    async def async_get_oblasts(self) -> dict[str, Any]:
        """Fetch oblast boundaries used for local coordinate matching."""

        payload = await self._get_json(API_OBLASTS_PATH)
        if payload.get("type") != "FeatureCollection":
            raise AirThreatApiError(
                f"Invalid response from {API_OBLASTS_PATH}: not a FeatureCollection"
            )
        return self._require_lists(payload, API_OBLASTS_PATH, "features")

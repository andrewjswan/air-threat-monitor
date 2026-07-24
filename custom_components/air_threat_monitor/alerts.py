"""Air-alert normalization and local-area matching."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import ActiveAlert, AlertScope, ResolvedArea


def normalize_alerts(payload: dict[str, Any]) -> tuple[ActiveAlert, ...]:
    """Normalize the documented NEPTUN alerts response."""

    alerts: list[ActiveAlert] = []
    for field, scope in (
        ("raions", AlertScope.RAION),
        ("oblasts", AlertScope.OBLAST),
    ):
        rows = payload.get(field, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            area_key = str(row.get("key") or "").strip()
            if not area_key:
                continue
            alerts.append(
                ActiveAlert(
                    area_key=area_key,
                    name=str(row.get("name") or "").strip(),
                    oblast=str(row.get("oblast") or "").strip(),
                    since=str(row.get("since") or "").strip(),
                    scope=scope,
                )
            )
    return tuple(alerts)


def find_local_alert(
    alerts: Iterable[ActiveAlert],
    *,
    raion_key: str | None,
    oblast_key: str | None,
) -> ActiveAlert | None:
    """Return the most specific active alert affecting the home point."""

    alert_list = tuple(alerts)
    if raion_key:
        for alert in alert_list:
            if alert.scope is AlertScope.RAION and alert.area_key == raion_key:
                return alert
    if oblast_key:
        for alert in alert_list:
            if alert.scope is AlertScope.OBLAST and alert.area_key == oblast_key:
                return alert
    return None


def resolved_area_from_feature(
    feature: dict[str, Any], scope: AlertScope
) -> ResolvedArea | None:
    """Build an area from a GeoJSON feature with flexible property names."""

    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None

    normalized = {str(key).casefold(): value for key, value in properties.items()}

    def first(*keys: str) -> str:
        for key in keys:
            value = normalized.get(key.casefold())
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    area_key = first("key", "id", "uid", "code", "katottg")
    if not area_key:
        return None

    return ResolvedArea(
        area_key=area_key,
        name=first(
            "name",
            "title",
            "name_uk",
            "name_ua",
            "name_2",
            "name_1",
            "shapename",
            "raion",
            "rayon",
            "district",
        ),
        oblast=first(
            "oblast",
            "region",
            "name_0",
            "adm1_name",
            "region_name",
        ),
        scope=scope,
    )

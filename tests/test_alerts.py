"""Tests for alert matching."""

from __future__ import annotations

from custom_components.air_threat_monitor.alerts import (
    find_local_alert,
    normalize_alerts,
    resolved_area_from_feature,
)
from custom_components.air_threat_monitor.models import AlertScope


def test_raion_alert_takes_precedence_over_oblast_alert() -> None:
    alerts = normalize_alerts(
        {
            "raions": [
                {
                    "key": "poltavska:poltavskyi",
                    "name": "Полтавський район",
                    "oblast": "Полтавська область",
                    "since": "2026-07-22T10:00:00Z",
                }
            ],
            "oblasts": [
                {
                    "key": "poltavska",
                    "name": "Полтавська область",
                    "since": "2026-07-22T09:58:00Z",
                }
            ],
        }
    )

    result = find_local_alert(
        alerts,
        raion_key="poltavska:poltavskyi",
        oblast_key="poltavska",
    )
    assert result is not None
    assert result.scope is AlertScope.RAION
    assert result.since == "2026-07-22T10:00:00Z"


def test_oblast_alert_is_used_when_raion_is_not_listed() -> None:
    alerts = normalize_alerts(
        {
            "raions": [],
            "oblasts": [
                {
                    "key": "poltavska",
                    "name": "Полтавська область",
                    "since": "2026-07-22T09:58:00Z",
                }
            ],
        }
    )
    result = find_local_alert(
        alerts,
        raion_key="poltavska:poltavskyi",
        oblast_key="poltavska",
    )
    assert result is not None
    assert result.scope is AlertScope.OBLAST


def test_geojson_properties_are_matched_case_insensitively() -> None:
    result = resolved_area_from_feature(
        {
            "properties": {
                "KEY": "poltavska:poltavskyi",
                "shapeName": "Полтавський район",
                "REGION_NAME": "Полтавська область",
            }
        },
        AlertScope.RAION,
    )

    assert result is not None
    assert result.area_key == "poltavska:poltavskyi"
    assert result.name == "Полтавський район"
    assert result.oblast == "Полтавська область"


def test_geojson_area_without_name_remains_valid() -> None:
    result = resolved_area_from_feature(
        {"properties": {"key": "poltavska:poltavskyi"}},
        AlertScope.RAION,
    )

    assert result is not None
    assert result.name == ""

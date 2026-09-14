"""Tests for alert matching."""

from __future__ import annotations

from custom_components.air_threat_monitor.alerts import (
    find_local_alert,
    normalize_alerts,
    resolved_area_from_feature,
)
from custom_components.air_threat_monitor.models import AlertLevel, AlertScope


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


def test_yellow_level_and_reasons_are_normalized() -> None:
    alerts = normalize_alerts(
        {
            "raions": [
                {
                    "key": "poltavskyi",
                    "name": "Полтавський район",
                    "oblast": "Полтавська область",
                    "since": "2026-09-11T07:37:17Z",
                    "level": "yellow",
                    "reasons": [
                        "Дронова загроза (жовтий рівень)",
                        "",
                        {"unexpected": "value"},
                    ],
                }
            ],
            "oblasts": [],
        }
    )

    assert len(alerts) == 1
    assert alerts[0].level is AlertLevel.YELLOW
    assert alerts[0].reasons == ("Дронова загроза (жовтий рівень)",)


def test_missing_or_unknown_level_remains_a_red_alert() -> None:
    alerts = normalize_alerts(
        {
            "raions": [
                {"key": "legacy", "level": ""},
                {"key": "future", "level": "purple"},
            ],
            "oblasts": [],
        }
    )

    assert [alert.level for alert in alerts] == [
        AlertLevel.RED,
        AlertLevel.RED,
    ]


def test_red_oblast_alert_takes_precedence_over_yellow_raion() -> None:
    alerts = normalize_alerts(
        {
            "raions": [
                {
                    "key": "poltavskyi",
                    "name": "Полтавський район",
                    "level": "yellow",
                }
            ],
            "oblasts": [
                {
                    "key": "poltavska",
                    "name": "Полтавська область",
                    "level": "red",
                }
            ],
        }
    )

    result = find_local_alert(
        alerts,
        raion_key="poltavskyi",
        oblast_key="poltavska",
    )

    assert result is not None
    assert result.scope is AlertScope.OBLAST
    assert result.level is AlertLevel.RED


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

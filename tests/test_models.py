"""Tests for coordinator snapshot equality semantics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.air_threat_monitor.models import (
    GeoPoint,
    MonitorData,
    Threat,
    ThreatCategory,
)


def test_refresh_timestamp_does_not_create_a_new_entity_state() -> None:
    first = MonitorData((), None, None, None, datetime.now(UTC))
    second = MonitorData(
        (), None, None, None, first.updated_at + timedelta(seconds=10)
    )

    assert first == second


def test_provider_timestamp_does_not_create_a_new_entity_state() -> None:
    base = {
        "threat_id": "one",
        "position": GeoPoint(49.0, 34.0),
        "category": ThreatCategory.UAV,
        "title": "UAV",
    }

    assert Threat(**base, updated_at="first") == Threat(
        **base, updated_at="second"
    )

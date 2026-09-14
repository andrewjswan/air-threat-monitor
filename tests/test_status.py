"""Tests for persistent alert status timing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.air_threat_monitor.status import (
    AlertStatusState,
    parse_datetime,
    update_alert_status,
)


def test_provider_alert_timestamp_is_used_when_alert_starts() -> None:
    now = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)

    state, changed = update_alert_status(
        None,
        active=True,
        provider_since="2026-07-22T11:42:00Z",
        now=now,
    )

    assert changed is True
    assert state.active is True
    assert state.since == datetime(2026, 7, 22, 11, 42, tzinfo=UTC)


def test_safe_timestamp_is_retained_between_updates() -> None:
    since = datetime(2026, 7, 22, 9, 15, tzinfo=UTC)
    previous = AlertStatusState(active=False, since=since)

    state, changed = update_alert_status(
        previous,
        active=False,
        provider_since=None,
        now=since + timedelta(hours=2),
    )

    assert changed is False
    assert state is previous


def test_state_change_starts_a_new_period() -> None:
    previous = AlertStatusState(
        active=True,
        since=datetime(2026, 7, 22, 10, 0, tzinfo=UTC),
    )
    now = datetime(2026, 7, 22, 10, 35, tzinfo=UTC)

    state, changed = update_alert_status(
        previous,
        active=False,
        provider_since=None,
        now=now,
    )

    assert changed is True
    assert state == AlertStatusState(active=False, since=now)


def test_invalid_stored_timestamp_is_rejected() -> None:
    assert parse_datetime("not-a-date") is None


def test_alert_level_change_starts_a_new_period() -> None:
    previous = AlertStatusState(
        active=True,
        since=datetime(2026, 9, 11, 10, 0, tzinfo=UTC),
        level="yellow",
    )
    now = datetime(2026, 9, 11, 10, 15, tzinfo=UTC)

    state, changed = update_alert_status(
        previous,
        active=True,
        provider_since="2026-09-11T10:14:00Z",
        now=now,
        alert_level="red",
    )

    assert changed is True
    assert state == AlertStatusState(
        active=True,
        since=datetime(2026, 9, 11, 10, 14, tzinfo=UTC),
        level="red",
    )

"""Track the current local alert state across coordinator updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class AlertStatusState:
    """The current local alert state and when it started."""

    active: bool
    since: datetime
    level: str | None = None


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a provider or stored timestamp as an aware UTC datetime."""

    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def update_alert_status(
    previous: AlertStatusState | None,
    *,
    active: bool,
    provider_since: str | None,
    now: datetime,
    alert_level: str | None = None,
) -> tuple[AlertStatusState, bool]:
    """Return the current state and whether it needs to be persisted."""

    provider_time = parse_datetime(provider_since) if active else None
    level = alert_level if active else None
    if (
        previous is None
        or previous.active != active
        or previous.level != level
    ):
        return AlertStatusState(
            active=active,
            since=provider_time or now,
            level=level,
        ), True

    if active and provider_time is not None and provider_time != previous.since:
        return AlertStatusState(
            active=True,
            since=provider_time,
            level=level,
        ), True

    return previous, False

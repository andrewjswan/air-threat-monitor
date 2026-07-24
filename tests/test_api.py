"""Tests for strict provider response validation."""

from __future__ import annotations

import pytest

from custom_components.air_threat_monitor.api import (
    AirThreatApiClient,
    AirThreatApiError,
)


def test_required_list_fields_accept_documented_envelope() -> None:
    payload = {"raions": [], "oblasts": []}

    assert AirThreatApiClient._require_lists(
        payload, "/api/v1/alerts", "raions", "oblasts"
    ) is payload


def test_required_list_fields_reject_missing_data() -> None:
    with pytest.raises(AirThreatApiError, match="missing threats"):
        AirThreatApiClient._require_lists({}, "/api/v1/threats", "threats")


def test_required_list_fields_reject_wrong_field_type() -> None:
    with pytest.raises(AirThreatApiError, match="missing oblasts"):
        AirThreatApiClient._require_lists(
            {"raions": [], "oblasts": None},
            "/api/v1/alerts",
            "raions",
            "oblasts",
        )

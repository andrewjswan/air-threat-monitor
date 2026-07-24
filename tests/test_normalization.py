"""Tests for provider payload normalization."""

from __future__ import annotations

from custom_components.air_threat_monitor.models import ThreatCategory
from custom_components.air_threat_monitor.normalization import (
    extract_threat_rows,
    normalize_threat,
)


def test_extract_documented_threat_envelope() -> None:
    rows = extract_threat_rows(
        {"threats": [{"id": "one"}, None, {"id": "two"}]}
    )
    assert [row["id"] for row in rows] == ["one", "two"]


def test_documented_uav_payload() -> None:
    result = normalize_threat(
        {
            "id": "trk_1a2b",
            "type": "uav",
            "title": "Шахед",
            "lat": 46.30,
            "lon": 30.65,
            "heading": 42,
            "confidenceLevel": "high",
            "count": 2,
            "status": "active",
            "updatedAt": "2026-07-09T12:34:50Z",
        }
    )
    assert result is not None
    assert result.category is ThreatCategory.UAV
    assert result.heading == 42.0
    assert result.group_count == 2


def test_fpv_title_refines_generic_uav_type() -> None:
    result = normalize_threat(
        {
            "id": "fpv-1",
            "type": "uav",
            "title": "FPV-дрон",
            "lat": 49.0,
            "lon": 34.0,
            "status": "active",
        }
    )
    assert result is not None
    assert result.category is ThreatCategory.FPV


def test_velocity_heading_is_fallback() -> None:
    result = normalize_threat(
        {
            "id": "recon-1",
            "type": "recon",
            "lat": 49.0,
            "lon": 34.0,
            "velocity": {"bearingDeg": 275},
        }
    )
    assert result is not None
    assert result.heading == 275.0


def test_stale_target_is_ignored() -> None:
    result = normalize_threat(
        {
            "id": "stale-1",
            "type": "uav",
            "lat": 49.0,
            "lon": 34.0,
            "status": "stale",
        }
    )

    assert result is None


def test_resolved_and_invalid_positions_are_ignored() -> None:
    assert (
        normalize_threat(
            {
                "id": "done",
                "type": "uav",
                "lat": 49.0,
                "lon": 34.0,
                "status": "resolved",
            }
        )
        is None
    )
    assert (
        normalize_threat(
            {"id": "bad", "type": "uav", "lat": None, "lon": 34.0}
        )
        is None
    )

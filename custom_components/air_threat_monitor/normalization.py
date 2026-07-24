"""Normalize provider payloads into stable integration models."""

from __future__ import annotations

import math
from typing import Any

from .models import GeoPoint, Threat, ThreatCategory

_RAW_TYPE_MAP = {
    "uav": ThreatCategory.UAV,
    "fpv": ThreatCategory.FPV,
    "recon": ThreatCategory.RECON,
    "missile": ThreatCategory.MISSILE,
    "ballistic": ThreatCategory.BALLISTIC,
    "kab": ThreatCategory.KAB,
    "mig31k": ThreatCategory.AIRCRAFT,
    "aircraft": ThreatCategory.AIRCRAFT,
}


def extract_threat_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Extract threat rows from documented and compatible payload envelopes."""

    for key in ("threats", "items", "data"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return tuple(row for row in rows if isinstance(row, dict))
    return ()


def finite_float(value: Any) -> float | None:
    """Convert a provider value to a finite float."""

    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


def classify_threat(payload: dict[str, Any]) -> ThreatCategory:
    """Classify a threat using the provider type first and text as fallback."""

    raw_type = str(payload.get("type") or "").strip().lower()
    if raw_type in _RAW_TYPE_MAP:
        category = _RAW_TYPE_MAP[raw_type]
        if category is not ThreatCategory.UAV:
            return category

    text = " ".join(
        str(payload.get(key) or "")
        for key in ("type", "title", "name", "explanationShort")
    ).lower()

    if any(
        word in text
        for word in ("fpv", "ланцет", "молнія", "баражув")
    ):
        return ThreatCategory.FPV
    if any(word in text for word in ("recon", "розвід")):
        return ThreatCategory.RECON
    if any(word in text for word in ("ballistic", "баліст")):
        return ThreatCategory.BALLISTIC
    if any(
        word in text for word in ("missile", "rocket", "ракета", "крилат")
    ):
        return ThreatCategory.MISSILE
    if any(word in text for word in ("kab", "каб", "авіабомб")):
        return ThreatCategory.KAB
    if any(
        word in text for word in ("mig31", "aircraft", "літак", "авіаці")
    ):
        return ThreatCategory.AIRCRAFT
    if any(
        word in text
        for word in ("uav", "shahed", "drone", "бпла", "шахед")
    ):
        return ThreatCategory.UAV
    return ThreatCategory.UNKNOWN


def normalize_threat(payload: dict[str, Any]) -> Threat | None:
    """Normalize one NEPTUN threat, returning None for invalid data."""

    status = str(payload.get("status") or "active").strip().lower()
    if status != "active":
        return None

    latitude = finite_float(payload.get("lat"))
    longitude = finite_float(payload.get("lon"))
    if latitude is None or longitude is None:
        return None
    if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
        return None

    velocity = payload.get("velocity")
    velocity = velocity if isinstance(velocity, dict) else {}
    heading = finite_float(payload.get("heading"))
    if heading is None:
        heading = finite_float(velocity.get("bearingDeg"))

    count_value = finite_float(payload.get("count"))
    count = max(0, int(count_value)) if count_value is not None else 0

    return Threat(
        threat_id=str(payload.get("id") or ""),
        position=GeoPoint(latitude=latitude, longitude=longitude),
        category=classify_threat(payload),
        title=str(payload.get("title") or ""),
        locality=str(payload.get("locality") or ""),
        district=str(payload.get("district") or ""),
        region=str(payload.get("region") or ""),
        heading=heading,
        status=status,
        updated_at=str(payload.get("updatedAt") or ""),
        confidence=str(payload.get("confidenceLevel") or ""),
        group_count=count,
    )

"""Date helper utilities."""

from __future__ import annotations

from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    """Parse an ISO date (YYYY-MM-DD) into a date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def to_iso_date(value: date) -> str:
    """Convert a date object to ISO format."""
    return value.isoformat()

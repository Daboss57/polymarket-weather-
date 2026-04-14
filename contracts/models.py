"""Domain models for market contracts and normalized weather events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any


class MetricType(str, Enum):
    """Supported weather metric types."""

    DAILY_HIGH_F = "daily_high_f"
    DAILY_LOW_F = "daily_low_f"
    RAIN_YES_NO = "rain_yes_no"


class Direction(str, Enum):
    """Threshold direction semantics."""

    ABOVE = "above"
    BELOW = "below"


@dataclass(slots=True)
class MarketToken:
    """A token side within a Polymarket market."""

    token_id: str
    outcome: str


@dataclass(slots=True)
class Market:
    """Raw market metadata fetched from Polymarket public APIs."""

    market_id: str
    question: str
    slug: str | None
    end_datetime: datetime | None
    resolution_source: str | None
    tokens: list[MarketToken]
    active: bool
    raw: dict[str, Any]


@dataclass(slots=True)
class PricePoint:
    """Historical YES price point for a market token."""

    timestamp: datetime
    yes_price: float


@dataclass(slots=True)
class NormalizedContract:
    """Structured interpretation of a weather prediction contract."""

    market_id: str
    question: str
    location: str
    target_date: date
    metric_type: MetricType
    direction: Direction | None
    threshold: float | None


@dataclass(slots=True)
class WeatherObservation:
    """Daily weather observation used for model training/evaluation."""

    date: date
    max_temp_f: float | None
    min_temp_f: float | None
    precipitation_mm: float | None

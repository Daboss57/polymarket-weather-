"""Application configuration for the Polymarket weather backtester."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PolymarketConfig:
    """Configuration for Polymarket public endpoints."""

    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    request_timeout_seconds: int = 20
    max_markets: int = 250


@dataclass(slots=True)
class OpenMeteoConfig:
    """Configuration for Open-Meteo endpoints."""

    archive_base_url: str = "https://archive-api.open-meteo.com/v1/archive"
    forecast_base_url: str = "https://api.open-meteo.com/v1/forecast"
    geocode_base_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    request_timeout_seconds: int = 20


@dataclass(slots=True)
class BacktestConfig:
    """Configuration for trading simulation behavior."""

    entry_edge: float = 0.08
    exit_edge: float = 0.02
    max_position_notional: float = 100.0
    seasonal_window_days: int = 7
    lookback_years: int = 8


@dataclass(slots=True)
class AppConfig:
    """Top-level config object used by the CLI."""

    polymarket: PolymarketConfig = field(default_factory=PolymarketConfig)
    openmeteo: OpenMeteoConfig = field(default_factory=OpenMeteoConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    output_dir: Path = Path("outputs")
    cache_dir: Path = Path(".cache")


DEFAULT_CONFIG = AppConfig()

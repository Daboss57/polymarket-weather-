"""Open-Meteo weather data client implementation."""

from __future__ import annotations

import logging
from datetime import date

from clients.weather_client import WeatherClient
from config import OpenMeteoConfig
from contracts.models import WeatherObservation
from utils.dates import to_iso_date
from utils.http import HttpError, get_json

LOGGER = logging.getLogger(__name__)


class OpenMeteoClient(WeatherClient):
    """Client for Open-Meteo geocoding and archive APIs."""

    def __init__(self, config: OpenMeteoConfig):
        self.config = config

    def resolve_location(self, location_query: str) -> tuple[float, float] | None:
        params = {"name": location_query, "count": 1}
        try:
            payload = get_json(self.config.geocode_base_url, params=params, timeout_seconds=self.config.request_timeout_seconds)
        except HttpError as exc:
            LOGGER.error("Location resolution failed for %s: %s", location_query, exc)
            return None

        results = payload.get("results") or []
        if not results:
            LOGGER.warning("No geocoding results for location query '%s'", location_query)
            return None

        return float(results[0]["latitude"]), float(results[0]["longitude"])

    def get_daily_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherObservation]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": to_iso_date(start_date),
            "end_date": to_iso_date(end_date),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "temperature_unit": "fahrenheit",
            "timezone": "UTC",
        }
        try:
            payload = get_json(self.config.archive_base_url, params=params, timeout_seconds=self.config.request_timeout_seconds)
        except HttpError as exc:
            LOGGER.error("Open-Meteo archive request failed: %s", exc)
            return []

        daily = payload.get("daily")
        if not daily:
            LOGGER.warning("Open-Meteo response missing daily data")
            return []

        dates = daily.get("time", [])
        maxes = daily.get("temperature_2m_max", [])
        mins = daily.get("temperature_2m_min", [])
        precs = daily.get("precipitation_sum", [])

        observations: list[WeatherObservation] = []
        for idx, d in enumerate(dates):
            observations.append(
                WeatherObservation(
                    date=date.fromisoformat(d),
                    max_temp_f=maxes[idx] if idx < len(maxes) else None,
                    min_temp_f=mins[idx] if idx < len(mins) else None,
                    precipitation_mm=precs[idx] if idx < len(precs) else None,
                )
            )
        return observations

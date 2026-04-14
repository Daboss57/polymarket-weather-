"""Abstract weather client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from contracts.models import WeatherObservation


class WeatherClient(ABC):
    """Provider-agnostic weather data client interface."""

    @abstractmethod
    def resolve_location(self, location_query: str) -> tuple[float, float] | None:
        """Resolve free-form location text into latitude/longitude."""

    @abstractmethod
    def get_daily_observations(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherObservation]:
        """Fetch daily historical observations in the date window."""

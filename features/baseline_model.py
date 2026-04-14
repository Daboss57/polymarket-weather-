"""Historical baseline probability model (non-ML)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from contracts.models import Direction, MetricType, NormalizedContract, WeatherObservation
from utils.validation import clamp_probability


@dataclass(slots=True)
class BaselineEstimate:
    """Output from the baseline model."""

    probability_yes: float
    sample_size: int
    notes: str


class HistoricalBaselineModel:
    """Estimate contract probability from seasonal historical hit rates."""

    def __init__(self, seasonal_window_days: int = 7):
        self.seasonal_window_days = seasonal_window_days

    def estimate(self, contract: NormalizedContract, history: list[WeatherObservation]) -> BaselineEstimate:
        if not history:
            return BaselineEstimate(0.5, 0, "No weather history; fallback to 0.5")

        candidates = self._seasonal_candidates(contract.target_date, history)
        if not candidates:
            return BaselineEstimate(0.5, 0, "No seasonal samples; fallback to 0.5")

        hits = 0
        for obs in candidates:
            if self._is_yes_outcome(contract, obs):
                hits += 1

        probability = clamp_probability(hits / len(candidates))
        return BaselineEstimate(
            probability_yes=probability,
            sample_size=len(candidates),
            notes="Simple historical seasonal baseline; not an ML forecast.",
        )

    def _seasonal_candidates(self, target_date: date, history: list[WeatherObservation]) -> list[WeatherObservation]:
        target_doy = target_date.timetuple().tm_yday
        window = self.seasonal_window_days

        selected: list[WeatherObservation] = []
        for obs in history:
            obs_doy = obs.date.timetuple().tm_yday
            diff = abs(obs_doy - target_doy)
            wrapped_diff = min(diff, 366 - diff)
            if wrapped_diff <= window and obs.date < target_date:
                selected.append(obs)
        return selected

    def _is_yes_outcome(self, contract: NormalizedContract, obs: WeatherObservation) -> bool:
        if contract.metric_type == MetricType.DAILY_HIGH_F and obs.max_temp_f is not None and contract.threshold is not None:
            return obs.max_temp_f >= contract.threshold if contract.direction == Direction.ABOVE else obs.max_temp_f < contract.threshold

        if contract.metric_type == MetricType.DAILY_LOW_F and obs.min_temp_f is not None and contract.threshold is not None:
            return obs.min_temp_f >= contract.threshold if contract.direction == Direction.ABOVE else obs.min_temp_f < contract.threshold

        if contract.metric_type == MetricType.RAIN_YES_NO:
            return bool((obs.precipitation_mm or 0.0) > 0.0)

        return False


def training_window(target_date: date, years: int) -> tuple[date, date]:
    """Build historical lookback start/end dates for weather queries."""
    start = date(target_date.year - years, 1, 1)
    end = target_date - timedelta(days=1)
    return start, end

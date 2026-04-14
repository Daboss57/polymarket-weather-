"""Contract parser that normalizes market wording into structured events."""

from __future__ import annotations

import logging
import re
from datetime import datetime

from contracts.models import Direction, Market, MetricType, NormalizedContract

LOGGER = logging.getLogger(__name__)

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})")
TEMP_RE = re.compile(r"(?P<direction>over|under|above|below)\s*(?P<threshold>\d{1,3}(?:\.\d+)?)\s*°?F", re.IGNORECASE)
CITY_RE = re.compile(r"in\s+([A-Za-z\s\-\.]+?)(?:\s+on\s+|\?|$)", re.IGNORECASE)


class ContractParser:
    """Parser for simple weather-threshold Polymarket contract text."""

    def parse(self, market: Market) -> NormalizedContract | None:
        question = market.question.strip()
        metric_type = self._infer_metric_type(question)
        if metric_type is None:
            return None

        target_date = self._extract_date(question)
        location = self._extract_location(question)

        if target_date is None or location is None:
            LOGGER.debug("Rejected ambiguous market '%s'", question)
            return None

        direction, threshold = self._extract_temp_threshold(question)
        if metric_type in {MetricType.DAILY_HIGH_F, MetricType.DAILY_LOW_F} and (direction is None or threshold is None):
            return None

        return NormalizedContract(
            market_id=market.market_id,
            question=question,
            location=location,
            target_date=target_date,
            metric_type=metric_type,
            direction=direction,
            threshold=threshold,
        )

    def _infer_metric_type(self, text: str) -> MetricType | None:
        lowered = text.lower()
        if "high" in lowered and "temp" in lowered:
            return MetricType.DAILY_HIGH_F
        if "low" in lowered and "temp" in lowered:
            return MetricType.DAILY_LOW_F
        if "rain" in lowered or "precip" in lowered:
            return MetricType.RAIN_YES_NO
        return None

    def _extract_date(self, text: str):
        match = DATE_RE.search(text)
        if not match:
            return None
        raw_date = match.group(1)
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(raw_date, fmt).date()
            except ValueError:
                continue
        return None

    def _extract_location(self, text: str) -> str | None:
        match = CITY_RE.search(text)
        if match:
            return " ".join(match.group(1).split())
        return None

    def _extract_temp_threshold(self, text: str) -> tuple[Direction | None, float | None]:
        match = TEMP_RE.search(text)
        if not match:
            return None, None
        direction = Direction.ABOVE if match.group("direction").lower() in {"over", "above"} else Direction.BELOW
        threshold = float(match.group("threshold"))
        return direction, threshold

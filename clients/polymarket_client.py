"""Polymarket public API client for market discovery and price history."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config import PolymarketConfig
from contracts.models import Market, MarketToken, PricePoint
from utils.http import HttpError, get_json

LOGGER = logging.getLogger(__name__)


class PolymarketClient:
    """Client for public Polymarket discovery and CLOB history."""

    def __init__(self, config: PolymarketConfig):
        self.config = config

    def parse_raw_markets(self, raw_markets: list[dict[str, Any]]) -> list[Market]:
        """Parse raw market payloads from any source (API or local fixture)."""
        parsed: list[Market] = []
        for item in raw_markets:
            market = self._parse_market(item)
            if market:
                parsed.append(market)
        return parsed

    def fetch_markets(self, limit: int | None = None) -> list[Market]:
        max_markets = limit or self.config.max_markets
        url = f"{self.config.gamma_base_url}/markets"
        params = {"limit": max_markets, "active": "true"}

        try:
            payload = get_json(url, params=params, timeout_seconds=self.config.request_timeout_seconds)
        except HttpError as exc:
            LOGGER.error("Failed to fetch Polymarket markets: %s", exc)
            return []

        raw_markets: list[dict[str, Any]] = payload if isinstance(payload, list) else payload.get("data", [])
        return self.parse_raw_markets(raw_markets)

    def fetch_yes_price_history(self, token_id: str, fidelity: int = 60) -> list[PricePoint]:
        """Fetch historical price points for a YES token from Polymarket CLOB."""
        url = f"{self.config.clob_base_url}/prices-history"
        params = {"market": token_id, "interval": "max", "fidelity": fidelity}

        try:
            payload = get_json(url, params=params, timeout_seconds=self.config.request_timeout_seconds)
        except HttpError as exc:
            LOGGER.warning("Price history unavailable for token=%s error=%s", token_id, exc)
            return []

        history = payload.get("history", [])
        points: list[PricePoint] = []
        for row in history:
            try:
                ts = datetime.fromtimestamp(int(row["t"]), tz=timezone.utc)
                points.append(PricePoint(timestamp=ts, yes_price=float(row["p"])))
            except (KeyError, ValueError, TypeError):
                continue
        return points

    def filter_weather_markets(self, markets: list[Market]) -> list[Market]:
        """Heuristic filter for weather-related contracts."""
        keywords = ("temp", "temperature", "rain", "precip", "weather")
        return [m for m in markets if any(word in m.question.lower() for word in keywords)]

    def _parse_market(self, item: dict[str, Any]) -> Market | None:
        try:
            end_datetime = None
            for key in ("endDate", "end_date", "closedTime"):
                if item.get(key):
                    end_datetime = datetime.fromisoformat(str(item[key]).replace("Z", "+00:00"))
                    break

            market_id = str(item.get("id") or item.get("conditionId") or "").strip()
            question = str(item.get("question") or "").strip()
            if not market_id or not question:
                LOGGER.debug(
                    "Skipping market payload missing required fields: market_id=%r question=%r",
                    market_id,
                    question,
                )
                return None

            tokens = self._parse_tokens(item)
            return Market(
                market_id=market_id,
                question=question,
                slug=item.get("slug"),
                end_datetime=end_datetime,
                resolution_source=item.get("resolutionSource"),
                tokens=tokens,
                active=bool(item.get("active", True)),
                raw=item,
            )
        except Exception as exc:  # defensive: payload shape may change
            LOGGER.debug("Skipping malformed market payload due to %s", exc)
            return None

    def _parse_tokens(self, item: dict[str, Any]) -> list[MarketToken]:
        token_candidates = item.get("tokens") or []
        parsed: list[MarketToken] = []
        for token in token_candidates:
            token_id = str(token.get("token_id") or token.get("id") or "")
            outcome = str(token.get("outcome") or token.get("name") or "")
            if token_id:
                parsed.append(MarketToken(token_id=token_id, outcome=outcome))

        if not parsed and item.get("clobTokenIds"):
            ids = [tok.strip() for tok in str(item["clobTokenIds"]).strip("[]").split(",") if tok.strip()]
            outcomes = ["YES", "NO"]
            for idx, token_id in enumerate(ids):
                parsed.append(MarketToken(token_id=token_id, outcome=outcomes[idx] if idx < len(outcomes) else f"OUTCOME_{idx}"))

        return parsed

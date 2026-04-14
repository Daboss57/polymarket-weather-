"""Backtesting engine that combines model, strategy, and portfolio."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from backtest.metrics import BacktestSummary, summarize_trades
from backtest.portfolio import Portfolio, TradeRecord
from backtest.strategy import EdgeThresholdStrategy
from contracts.models import PricePoint

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MarketBacktestInput:
    market_id: str
    fair_probability: float
    price_history: list[PricePoint]
    resolved_yes: bool


@dataclass(slots=True)
class BacktestResult:
    summary: BacktestSummary
    trades: list[TradeRecord]


class BacktestEngine:
    """Deterministic backtest simulation with simple YES-side fills."""

    def __init__(self, strategy: EdgeThresholdStrategy):
        self.strategy = strategy

    def run(self, markets: list[MarketBacktestInput]) -> BacktestResult:
        portfolio = Portfolio()

        for market in markets:
            self._run_market(portfolio, market)

        summary = summarize_trades(portfolio.trades)
        return BacktestResult(summary=summary, trades=portfolio.trades)

    def _run_market(self, portfolio: Portfolio, market: MarketBacktestInput) -> None:
        if not market.price_history:
            LOGGER.info("Skipping market %s due to missing price history", market.market_id)
            return

        for point in market.price_history:
            if market.market_id not in portfolio.positions:
                if self.strategy.should_enter_yes(market.fair_probability, point.yes_price):
                    portfolio.open_yes(
                        market_id=market.market_id,
                        ts=point.timestamp,
                        price=point.yes_price,
                        notional=self.strategy.config.max_position_notional,
                        fair_prob=market.fair_probability,
                    )
            else:
                if self.strategy.should_exit_yes(market.fair_probability, point.yes_price):
                    portfolio.close_yes(market.market_id, point.timestamp, point.yes_price)

        if market.market_id in portfolio.positions:
            settlement_ts = market.price_history[-1].timestamp if market.price_history else datetime.utcnow()
            portfolio.settle_yes(market.market_id, settlement_ts, market.resolved_yes)

"""Metrics and analytics for backtest results."""

from __future__ import annotations

from dataclasses import dataclass

from backtest.portfolio import TradeRecord


@dataclass(slots=True)
class BacktestSummary:
    total_trades: int
    win_rate: float
    avg_entry_edge: float
    realized_pnl: float


def summarize_trades(trades: list[TradeRecord]) -> BacktestSummary:
    if not trades:
        return BacktestSummary(total_trades=0, win_rate=0.0, avg_entry_edge=0.0, realized_pnl=0.0)

    wins = sum(1 for t in trades if t.pnl > 0)
    avg_edge = sum(t.fair_prob_at_entry - t.market_price_at_entry for t in trades) / len(trades)
    realized = sum(t.pnl for t in trades)

    return BacktestSummary(
        total_trades=len(trades),
        win_rate=wins / len(trades),
        avg_entry_edge=avg_edge,
        realized_pnl=realized,
    )

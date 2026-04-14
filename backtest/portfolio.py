"""Portfolio and trade accounting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Position:
    market_id: str
    entry_time: datetime
    entry_price: float
    quantity: float
    fair_prob_at_entry: float


@dataclass(slots=True)
class TradeRecord:
    market_id: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    fair_prob_at_entry: float
    market_price_at_entry: float


class Portfolio:
    """Tracks one position per market and realizes PnL on exits/settlement."""

    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}
        self.trades: list[TradeRecord] = []

    def open_yes(self, market_id: str, ts: datetime, price: float, notional: float, fair_prob: float) -> None:
        if market_id in self.positions:
            return
        quantity = notional / max(price, 1e-6)
        self.positions[market_id] = Position(
            market_id=market_id,
            entry_time=ts,
            entry_price=price,
            quantity=quantity,
            fair_prob_at_entry=fair_prob,
        )

    def close_yes(self, market_id: str, ts: datetime, price: float) -> None:
        position = self.positions.pop(market_id, None)
        if position is None:
            return
        pnl = (price - position.entry_price) * position.quantity
        self.trades.append(
            TradeRecord(
                market_id=market_id,
                entry_time=position.entry_time,
                exit_time=ts,
                entry_price=position.entry_price,
                exit_price=price,
                quantity=position.quantity,
                pnl=pnl,
                fair_prob_at_entry=position.fair_prob_at_entry,
                market_price_at_entry=position.entry_price,
            )
        )

    def settle_yes(self, market_id: str, ts: datetime, yes_outcome: bool) -> None:
        settlement_price = 1.0 if yes_outcome else 0.0
        self.close_yes(market_id, ts, settlement_price)

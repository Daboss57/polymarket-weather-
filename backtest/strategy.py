"""Trading strategy logic for deciding entries/exits."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StrategyConfig:
    entry_edge: float
    exit_edge: float
    max_position_notional: float


class EdgeThresholdStrategy:
    """Buy YES when model edge clears threshold; optional early exit."""

    def __init__(self, config: StrategyConfig):
        self.config = config

    def should_enter_yes(self, fair_prob: float, market_price: float) -> bool:
        return (fair_prob - market_price) >= self.config.entry_edge

    def should_exit_yes(self, fair_prob: float, market_price: float) -> bool:
        return (fair_prob - market_price) <= self.config.exit_edge

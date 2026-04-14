"""Execution interfaces for future paper/live trading integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class OrderIntent:
    """Minimal order shape for future execution adapters."""

    market_id: str
    side: str
    price: float
    size: float


class ExecutionAdapter(ABC):
    """Abstract adapter for future paper/live execution workflows."""

    @abstractmethod
    def submit_order(self, intent: OrderIntent) -> str:
        """Submit order and return provider order-id."""


class PaperExecutionStub(ExecutionAdapter):
    """Placeholder implementation (intentionally no real trading)."""

    def submit_order(self, intent: OrderIntent) -> str:
        raise NotImplementedError("Paper execution module not implemented in v1")

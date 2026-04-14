"""Validation utilities."""

from __future__ import annotations


def clamp_probability(value: float) -> float:
    """Clamp a floating-point value into [0, 1]."""
    return max(0.0, min(1.0, value))

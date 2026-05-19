"""
KULIMA OS Policy Module
=======================

Centralizes ethical planning constraints for the pilot.

This module enforces a non-negotiable reserve ratio for infrastructure planning.
"""

from typing import Dict

RESERVE_RATIO = 0.25
ENFORCED_RESERVE_RATIO = 0.25

if RESERVE_RATIO != ENFORCED_RESERVE_RATIO:
    raise ValueError(
        f"Reserve ratio invariant violated: RESERVE_RATIO={RESERVE_RATIO} must equal ENFORCED_RESERVE_RATIO={ENFORCED_RESERVE_RATIO}."
    )


def compute_planning_reserve(total_signals: float) -> Dict[str, float]:
    """Compute the usable signal capacity and reserve buffer with enforced reserve ratio."""
    total = float(total_signals or 0)
    usable = round(total * (1.0 - RESERVE_RATIO), 3)
    reserve = round(total * RESERVE_RATIO, 3)
    return {
        "usable_signals": usable,
        "reserve_buffer": reserve,
        "reserve_ratio": RESERVE_RATIO,
    }


def require_planning_reserve(planning_reserve: Dict) -> None:
    """Validate planning reserve objects against the enforced reserve ratio."""
    if not isinstance(planning_reserve, dict):
        raise TypeError("planning_reserve must be a dict containing usable_signals and reserve_buffer")

    if "usable_signals" not in planning_reserve or "reserve_buffer" not in planning_reserve:
        raise ValueError("planning_reserve must include 'usable_signals' and 'reserve_buffer'")

    usable_signals = float(planning_reserve["usable_signals"])
    reserve_buffer = float(planning_reserve["reserve_buffer"])
    total = usable_signals + reserve_buffer

    if total <= 0:
        if usable_signals != 0 or reserve_buffer != 0:
            raise ValueError("Invalid planning_reserve values: total must be zero or positive")
        return

    actual_ratio = round(reserve_buffer / total, 6)
    expected_ratio = round(RESERVE_RATIO, 6)
    if actual_ratio != expected_ratio:
        raise ValueError(
            f"Planning reserve invariant violated: expected reserve ratio {expected_ratio}, got {actual_ratio}"
        )

    planning_reserve["reserve_ratio"] = RESERVE_RATIO

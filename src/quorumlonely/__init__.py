"""Dyad fragility: independent flakes, hard quorums, length-biased nights.

Honesty: a generative cartoon of gatherings, not a human loneliness survey.
"""

from .binomial import extra_isolation, p_alone, p_attend, p_event
from .world import simulate_calendar, simulate_partition

__all__ = [
    "extra_isolation",
    "p_alone",
    "p_attend",
    "p_event",
    "simulate_calendar",
    "simulate_partition",
]

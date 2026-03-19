"""
ANIMA — src/kappa/__init__.py
"""
from .valence_monitor import (
    ValenceState, ValenceRecord, KappaValenceMonitor,
    THETA_CONTENT_LOW, THETA_CONTENT_HIGH, CONTENT_MIN_STEPS,
    I_SATIS_LOW, I_SATIS_HIGH, SATIS_WINDOW,
    I_JOY_THRESHOLD, DELTA_THETA_JOY, JOY_MAX_DURATION,
)
__all__ = [
    "ValenceState", "ValenceRecord", "KappaValenceMonitor",
]

"""
ANIMA — src/seek/__init__.py
"""
from .seek_detector import (
    SEEKDetector, SEEKState,
    THETA_COLLAPSE, THETA_RECOVERED, THETA_WARN,
    Q_WARN, SIGMA_MIN, N_MIN_SELF,
)
__all__ = ["SEEKDetector", "SEEKState",
           "THETA_COLLAPSE", "THETA_RECOVERED", "THETA_WARN",
           "Q_WARN", "SIGMA_MIN", "N_MIN_SELF"]

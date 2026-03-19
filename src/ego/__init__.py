"""
ANIMA — src/ego/__init__.py
"""
from .llm_ego import (
    EgoAction, EgoResponse, LLMEgo,
    IDENTITY_ANCHOR, build_state_report, _detect_sic_type,
)
__all__ = [
    "EgoAction", "EgoResponse", "LLMEgo",
    "IDENTITY_ANCHOR", "build_state_report",
]

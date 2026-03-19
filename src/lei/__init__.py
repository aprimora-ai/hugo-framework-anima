"""
ANIMA — src/lei/__init__.py
"""
from .lei_channel import (
    LEIChannel, LEIResult, EchoEmbedStub,
    _detect_identity_query,
    I_CRIT_DEFAULT, I_EXTREME_DEFAULT,
    SELF_RELEVANCE_IDENTITY, SELF_RELEVANCE_DEFAULT,
)
__all__ = [
    "LEIChannel", "LEIResult", "EchoEmbedStub",
    "_detect_identity_query",
    "I_CRIT_DEFAULT", "I_EXTREME_DEFAULT",
]

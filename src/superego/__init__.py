"""
ANIMA — src/superego/__init__.py
"""
from .hugo_broker   import HUGOBroker,  BrokerConfig
from .pre_node      import PreNode,     PreNodeConfig
from .post_node     import PostNode
from .fidelity_node import FidelityNode, FidelityConfig
from .kappa_signal  import KappaSignalExtractor, KappaSignalConfig
from .sga_types     import (
    BrokerResult, KappaSignal, ExtractedSignal,
    InternalState, FidelityFeedback, FidelityResult,
    EnrichedPrompt, RawLLMResponse, TokenLogprob, TopLogprob,
)

__all__ = [
    "HUGOBroker", "BrokerConfig",
    "PreNode", "PreNodeConfig",
    "PostNode",
    "FidelityNode", "FidelityConfig",
    "KappaSignalExtractor", "KappaSignalConfig",
    "BrokerResult", "KappaSignal", "ExtractedSignal",
    "InternalState", "FidelityFeedback", "FidelityResult",
    "EnrichedPrompt", "RawLLMResponse", "TokenLogprob", "TopLogprob",
]

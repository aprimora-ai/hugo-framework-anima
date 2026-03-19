"""
ANIMA — src/superego/sga_types.py
===================================
Todos os tipos de dados do Superego-ANIMA (SGA).

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List


# ── Logprobs brutos do Ollama ─────────────────────────────────────────────────

@dataclass
class TopLogprob:
    token:   str
    logprob: float

@dataclass
class TokenLogprob:
    token:        str
    logprob:      float
    top_logprobs: List[TopLogprob] = field(default_factory=list)


# ── Sinal Kappa extraído dos logprobs ─────────────────────────────────────────

@dataclass
class KappaSignal:
    omega:          float
    eta:            float
    xi:             float
    delta:          float
    I_eff:          float
    n_tokens:       int
    baseline_omega: float
    regime:         str
    used_logprobs:  bool


# ── Prompt enriquecido (saída do PRE-NODE) ────────────────────────────────────

@dataclass
class EnrichedPrompt:
    system:     str
    user:       str
    state_hash: str
    rho_sga:    float


# ── Resposta bruta do LLM (entrada do POST-NODE) ─────────────────────────────

@dataclass
class RawLLMResponse:
    text:            str
    token_logprobs:  List[TokenLogprob] = field(default_factory=list)
    finish_reason:   str = "stop"


# ── Sinal extraído (saída do POST-NODE) ──────────────────────────────────────

@dataclass
class InternalState:
    emotional_intensity:  float
    sic_type:             str
    tension_acknowledged: bool
    gap_addressed:        bool
    raw_block:            str

@dataclass
class ExtractedSignal:
    text_clean:      str
    internal_state:  Optional[InternalState]
    kappa:           KappaSignal
    signal_missing:  bool
    kappa_source:    str = "fallback"  # "attention" | "logprobs" | "fallback"


# ── Resultado de fidelidade (saída do FIDELITY-NODE) ─────────────────────────

@dataclass
class FidelityFeedback:
    failed_rules:    List[str]
    correction_hint: str
    retry_count:     int
    force_sic_type:  Optional[str] = None

@dataclass
class FidelityResult:
    passed:        bool
    failed_rules:  List[str]
    feedback:      Optional[FidelityFeedback]
    rho_sga_used:  float


# ── Resultado final do Broker ─────────────────────────────────────────────────

@dataclass
class BrokerResult:
    agent_text:            str
    I_eff_real:            float
    sic_type_validated:    str
    kappa:                 KappaSignal
    fidelity_passed:       bool
    fidelity_rules_failed: List[str]
    retry_count:           int
    rho_sga_used:          float
    state_hash:            str
    used_logprobs:         bool
    kappa_source:          str = "fallback"  # "attention" | "logprobs" | "fallback"

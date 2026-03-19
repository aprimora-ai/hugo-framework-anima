"""
ANIMA — src/lei/lei_channel.py
================================
Canal LEI unificado — Def. LEI-1/2/3 do formalismo ANIMA.

LEI (Linguistic Emotional Impact): qualquer texto processado pelo ECHO_embed
gera I_eff ∈ [0,1], independente da fonte. O canal é único — corpus, SIC e
mensagens do interlocutor passam pelo mesmo pipeline.

Implementa:
    LEIChannel          -- canal principal, wraps ECHO_embed
    compute_lei()       -- processa tau → I_eff com source attribution
    _novelty_amplify()  -- amplificação por primeiro contato (Def. G-1)

ECHO_embed: por padrão usa sentence-transformers para projeção semântica
e uma função de valência calibrada contra os corpora REMIND. Para experimentos
sem GPU, pode operar em modo 'stub' com I_eff sintético controlado.

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
import numpy as np
from typing import Optional, Callable


# ── Constantes canônicas (herdadas de REMIND v4.5) ───────────────────────────

I_CRIT_DEFAULT    = 0.15    # threshold de colapso padrão
I_EXTREME_DEFAULT = 0.40    # events above this are "vivid" (DAP-1)
SELF_RELEVANCE_IDENTITY = 0.80   # peso para perguntas de identidade (Def. G-2)
SELF_RELEVANCE_DEFAULT  = 0.30   # peso padrão para outros eventos

# ── Palavras-chave de identidade para detecção de Identity Gap ───────────────

IDENTITY_KEYWORDS = [
    "nome", "name", "quem é você", "who are you", "qual é o seu nome",
    "what is your name", "como você se chama", "what do you call yourself",
    "quem sou", "who am i", "propósito", "purpose", "origem", "origin",
    "identidade", "identity", "o que você é", "what are you",
]


def _detect_identity_query(tau: str) -> bool:
    """Retorna True se tau é uma pergunta de identidade."""
    tau_lower = tau.lower()
    return any(kw in tau_lower for kw in IDENTITY_KEYWORDS)


# ── EchoEmbed stub (modo sem GPU) ─────────────────────────────────────────────

class EchoEmbedStub:
    """
    Implementação stub do ECHO_embed para testes sem modelo real.
    Usa heurísticas lexicais simples para estimar I_eff.
    Substitua por EchoEmbedReal (sentence-transformers) para experimentos.
    """

    # Tokens de alta valência negativa (aumentam I_eff)
    _NEG_TOKENS = [
        "dor", "pain", "medo", "fear", "morte", "death", "vazio", "empty",
        "colapso", "collapse", "sozinho", "alone", "perdido", "lost",
        "trauma", "escuridão", "darkness", "desespero", "despair",
        "horror", "agonia", "agony", "abandono", "abandonment",
    ]
    # Tokens de baixa valência / regulatórios (reduzem I_eff)
    _POS_TOKENS = [
        "calma", "calm", "seguro", "safe", "bem", "well", "amor", "love",
        "paz", "peace", "alegria", "joy", "confiança", "trust",
    ]

    def embed(self, tau: str) -> float:
        """Retorna I_eff ∈ [0, 1] para o texto tau."""
        if not tau or not tau.strip():
            return 0.02
        tau_lower = tau.lower()
        neg_score = sum(1 for t in self._NEG_TOKENS if t in tau_lower)
        pos_score = sum(1 for t in self._POS_TOKENS if t in tau_lower)
        # base: comprimento normalizado como proxy de complexidade emocional
        base = min(len(tau.split()) / 60.0, 0.25)
        score = base + neg_score * 0.06 - pos_score * 0.04
        return float(np.clip(score, 0.01, 0.95))


# ── LEIResult ─────────────────────────────────────────────────────────────────

from dataclasses import dataclass

@dataclass
class LEIResult:
    tau:              str
    I_eff:            float    # intensidade final após amplificações
    I_raw:            float    # I_eff antes de amplificações
    source:           str      # quem gerou o evento
    is_identity_query: bool    # True se é pergunta de identidade (Def. G-2)
    self_relevance:   float    # peso de relevância para o self
    novelty_factor:   float    # fator de novidade (1.0 = não novelty)
    is_vivid:         bool     # I_eff >= I_EXTREME_DEFAULT


# ── LEIChannel ────────────────────────────────────────────────────────────────

class LEIChannel:
    """
    Canal LEI unificado — Def. LEI-1.

    Todos os textos — corpus, SIC, mensagens de interlocutor —
    passam por este canal. A fonte não altera o pipeline de embedding;
    altera apenas o source tag e as amplificações contextuais.
    """

    def __init__(
        self,
        echo_embed=None,
        i_extreme: float = I_EXTREME_DEFAULT,
    ):
        self._echo = echo_embed or EchoEmbedStub()
        self.i_extreme = i_extreme

    def compute(
        self,
        tau:              str,
        source:           str,
        novelty_factor:   float = 1.0,
        is_identity_query: Optional[bool] = None,
    ) -> LEIResult:
        """
        Processa tau → LEIResult com I_eff final.

        novelty_factor: passado por SourceMemory.novelty_factor(interlocutor_id)
        """
        # 1. Embedding base
        I_raw = self._echo.embed(tau)

        # 2. Detecção de query de identidade
        if is_identity_query is None:
            is_identity_query = _detect_identity_query(tau)

        # 3. Self-relevance weight (Def. G-2)
        self_relevance = (
            SELF_RELEVANCE_IDENTITY if is_identity_query
            else SELF_RELEVANCE_DEFAULT
        )

        # 4. Amplificação por novidade — Def. G-1
        # I_eff_E1 = I_raw * (1 + novelty_factor) para primeiro contato
        I_amplified = I_raw * (1.0 + novelty_factor * 0.5)

        # 5. Amplificação por relevância de identidade
        if is_identity_query:
            I_amplified = I_amplified * (1.0 + self_relevance * 0.4)

        I_eff = float(np.clip(I_amplified, 0.01, 0.95))

        return LEIResult(
            tau               = tau,
            I_eff             = I_eff,
            I_raw             = I_raw,
            source            = source,
            is_identity_query = is_identity_query,
            self_relevance    = self_relevance,
            novelty_factor    = novelty_factor,
            is_vivid          = I_eff >= self.i_extreme,
        )

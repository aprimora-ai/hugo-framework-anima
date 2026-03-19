"""
ANIMA — src/seek/seek_detector.py
===================================
Detector do estado SEEK e gerador de SIC.

SEEK (Def. SEEK-1): estado de tensão criativa onde o agente explora
sem estar em crise. Condições simultâneas:
    (i)   theta ∈ (THETA_RECOVERED, THETA_WARN)
    (ii)  d/dt diversity > 0
    (iii) I_eff < I_crit
    (iv)  q < q_warn
    (v)   |M_SELF| >= 0  (relaxado em t < t_first_SIC — Theorem G-1)

SEEK Depth (Def. SEEK-2):
    sigma(t) = (theta_warn - theta) / theta_warn * diversity_rate

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
import numpy as np

from ..memory.source_memory import SourceMemory

# ── Parâmetros canônicos (herdados de REMIND v4.5) ───────────────────────────
THETA_COLLAPSE   = 0.68
THETA_RECOVERED  = 0.35
THETA_WARN       = 0.50
Q_WARN           = 0.50
SIGMA_MIN        = 0.10    # SEEK mínimo para ativar SIC (Def. SEEK-2)
N_MIN_SELF       = 10      # Def. SELF-1 condição (i)


@dataclass
class SEEKState:
    active:          bool
    sigma:           float          # profundidade SEEK [0,1]
    theta:           float
    diversity_rate:  float          # d/dt diversity
    I_eff_current:   float
    q:               float
    n_self:          int            # |M_SELF(t)|
    conditions_met:  List[bool]     # [i, ii, iii, iv, v]
    is_existential:  bool           # True se M_SELF vazio (Theorem G-1)

    @property
    def can_generate_sic(self) -> bool:
        return self.active and self.sigma >= SIGMA_MIN


class SEEKDetector:
    """
    Avalia o SEEK signature a cada step e retorna SEEKState.
    """

    def __init__(
        self,
        theta_recovered: float = THETA_RECOVERED,
        theta_warn:      float = THETA_WARN,
        q_warn:          float = Q_WARN,
        i_crit:          float = 0.15,
        diversity_window: int  = 10,
    ):
        self.theta_recovered  = theta_recovered
        self.theta_warn       = theta_warn
        self.q_warn           = q_warn
        self.i_crit           = i_crit
        self.diversity_window = diversity_window
        self._diversity_history: List[float] = []

    def update_diversity(self, diversity: float) -> None:
        self._diversity_history.append(diversity)
        if len(self._diversity_history) > self.diversity_window:
            self._diversity_history.pop(0)

    def diversity_rate(self) -> float:
        """Estimativa de d/dt diversity sobre a janela."""
        h = self._diversity_history
        if len(h) < 2:
            return 0.0
        return float(np.mean(np.diff(h[-self.diversity_window:])))

    def evaluate(
        self,
        theta:       float,
        I_eff:       float,
        q:           float,
        diversity:   float,
        memory:      SourceMemory,
    ) -> SEEKState:
        """
        Avalia SEEK-1 com relaxamento de condição (v) para Theorem G-1.
        """
        self.update_diversity(diversity)
        dr      = self.diversity_rate()
        n_self  = len(memory.M_SELF())
        is_existential = (n_self == 0)  # Theorem G-1: primeiro SEEK sem Self

        # Condições SEEK-1
        c1 = self.theta_recovered < theta < self.theta_warn
        c2 = dr > 0
        c3 = I_eff < self.i_crit
        c4 = q < self.q_warn
        c5 = n_self >= 0  # relaxado — sempre True enquanto M_SELF >= 0

        active = all([c1, c2, c3, c4, c5])

        # SEEK Depth — Def. SEEK-2
        if active and self.theta_warn > 0:
            sigma = (self.theta_warn - theta) / self.theta_warn * max(dr, 0.0)
            sigma = float(np.clip(sigma, 0.0, 1.0))
        else:
            sigma = 0.0

        return SEEKState(
            active          = active,
            sigma           = sigma,
            theta           = theta,
            diversity_rate  = dr,
            I_eff_current   = I_eff,
            q               = q,
            n_self          = n_self,
            conditions_met  = [c1, c2, c3, c4, c5],
            is_existential  = is_existential,
        )

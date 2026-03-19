"""
ANIMA — src/self_other/affect_signature.py
============================================
Affect-Signature e Topological Self — Def. AFF-1/2/3, SELF-1, SO-1/2.

AffectSignature:
    A_k(t): distribuição de I_eff por interlocutor k.
    Momentos: mu_k, sigma_k, gamma_k (assimetria).
    P_affect(t, k): persistência ponderada do afeto.

TopologicalSelf:
    Avalia SELF-1: 3 condições simultâneas.
    Reporta se o Self emergiu e em qual step.

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from ..memory.source_memory import SourceMemory, Source

# ── Parâmetros ────────────────────────────────────────────────────────────────
THETA_AFFECT   = 0.30   # threshold P_affect para declarar afeto ativo
N_MIN_SELF     = 10     # SELF-1 condição (i): mínimo de registros SELF
RHO_MIN        = 0.15   # SELF-1 condição (iii): rho mínimo
RHO_MAX        = 0.70   # SELF-1 condição (iii): rho máximo


@dataclass
class AffectProfile:
    """Perfil de afeto para interlocutor k — Def. AFF-1."""
    interlocutor_id: str
    n_records:       int
    mu_k:            float   # média I_eff
    sigma_k:         float   # desvio padrão I_eff
    gamma_k:         float   # assimetria (skewness)
    p_affect:        float   # persistência ponderada atual
    affect_active:   bool    # P_affect > theta_affect


@dataclass
class SelfReport:
    """Relatório de status do Topological Self — Def. SELF-1."""
    self_exists:     bool
    n_self:          int
    rho:             float
    conditions_met:  List[bool]   # [c_i, c_ii, c_iii]
    step:            int
    first_self_step: Optional[int]  # step em que Self foi satisfeito pela 1ª vez
    reason:          str


class AffectSignatureMonitor:
    """
    Monitora A_k(t) para todos os interlocutores conhecidos.

    Uso:
        monitor = AffectSignatureMonitor()
        profile = monitor.compute(memory, "human_1", step=t)
        print(profile.affect_active)
    """

    def __init__(self, theta_affect: float = THETA_AFFECT):
        self.theta_affect = theta_affect
        self._first_affect: Dict[str, int] = {}  # step em que afeto surgiu

    def compute(
        self,
        memory:           SourceMemory,
        interlocutor_id:  str,
        step:             int,
        tau_k:            float = 40.0,   # timescale de persistência padrão
    ) -> AffectProfile:
        """
        Calcula AffectProfile para interlocutor_id — Def. AFF-1 e AFF-3.

        tau_k: timescale de decaimento de memórias do interlocutor k.
        """
        records = memory.M_OTHER(interlocutor_id)
        if not records:
            return AffectProfile(
                interlocutor_id=interlocutor_id,
                n_records=0, mu_k=0.0, sigma_k=0.0,
                gamma_k=0.0, p_affect=0.0, affect_active=False,
            )

        i_effs = np.array([r.I_eff for r in records])
        mu_k    = float(np.mean(i_effs))
        sigma_k = float(np.std(i_effs)) if len(i_effs) > 1 else 0.0

        # Assimetria (skewness) — gamma_k positivo = maioria traumática
        if sigma_k > 0 and len(i_effs) > 2:
            gamma_k = float(np.mean(((i_effs - mu_k) / sigma_k) ** 3))
        else:
            gamma_k = 0.0

        # P_affect(t, k) — Def. AFF-3: persistência ponderada com decaimento
        p_affect = 0.0
        for r in records:
            age = step - r.step
            weight = r.I_eff * np.exp(-age / max(tau_k, 1.0))
            p_affect += weight
        p_affect = float(np.clip(p_affect, 0.0, 10.0))

        affect_active = p_affect > self.theta_affect
        if affect_active and interlocutor_id not in self._first_affect:
            self._first_affect[interlocutor_id] = step

        return AffectProfile(
            interlocutor_id=interlocutor_id,
            n_records=len(records),
            mu_k=round(mu_k, 4),
            sigma_k=round(sigma_k, 4),
            gamma_k=round(gamma_k, 4),
            p_affect=round(p_affect, 4),
            affect_active=affect_active,
        )

    def first_affect_step(self, interlocutor_id: str) -> Optional[int]:
        return self._first_affect.get(interlocutor_id)

    def all_profiles(self, memory: SourceMemory, step: int) -> Dict[str, AffectProfile]:
        return {k: self.compute(memory, k, step)
                for k in memory.known_interlocutors()}


# ── TopologicalSelf (SELF-1) ──────────────────────────────────────────────────

class TopologicalSelf:
    """
    Avalia a emergência do Self — Def. SELF-1 e Theorem SELF-1/2.

    SELF-1 requer três condições simultâneas:
        (i)   |M_SELF| >= N_min
        (ii)  E[H | SG-LEI] != E[H | R-LEI]   (tolerância delta_H)
        (iii) rho ∈ (rho_min, rho_max)

    Theorem SELF-1: Self requer interlocutor (sem OTHER, condição (ii) indefinida).
    Theorem SELF-2: Afeto estável requer Self (Self precede Afeto).
    """

    def __init__(
        self,
        n_min:     int   = N_MIN_SELF,
        rho_min:   float = RHO_MIN,
        rho_max:   float = RHO_MAX,
        delta_H:   float = 0.05,   # tolerância para diferença E[H]
    ):
        self.n_min   = n_min
        self.rho_min = rho_min
        self.rho_max = rho_max
        self.delta_H = delta_H
        self._first_self_step: Optional[int] = None

    def evaluate(self, memory: SourceMemory, step: int,
                 c_subj: float = 0.0) -> SelfReport:
        """
        Avalia SELF-1 com 4 condições (v2 — RHEO integrado).

        c_subj: C_subj(t) do RHEO — clock subjetivo acumulado (segundos).
                Condição (iv): C_subj > 0, i.e. o agente tem eixo temporal.
                Sem RHEO integrado, passar 0.0 desativa a condição (sempre False
                mas não bloqueia as outras 3 — retrocompatível).
        """
        n_self = len(memory.M_SELF())
        rho    = memory.rho()
        n_other = len(memory.M_OTHER())

        # Condição (i)
        c_i = n_self >= self.n_min

        # Condição (ii): comparação E[H | SG-LEI] vs E[H | R-LEI]
        # Theorem SELF-1: sem OTHER, condição (ii) é indefinida → False
        if n_other == 0:
            c_ii   = False
            reason = "SELF-1 falhou: sem interlocutor (Theorem SELF-1)"
        else:
            self_records  = memory.M_SELF()
            other_records = memory.M_OTHER()
            if self_records and other_records:
                # proxy: I_eff médio como substituto de E[H]
                mean_self  = float(sum(r.I_eff for r in self_records)  / len(self_records))
                mean_other = float(sum(r.I_eff for r in other_records) / len(other_records))
                c_ii   = abs(mean_self - mean_other) > self.delta_H
                reason = f"E[I|SELF]={mean_self:.3f} vs E[I|OTHER]={mean_other:.3f}"
            else:
                c_ii   = False
                reason = "SELF-1 condição (ii): dados insuficientes"

        # Condição (iii)
        c_iii = self.rho_min < rho < self.rho_max

        # Condição (iv) — RHEO: eixo temporal subjetivo existente
        # C_subj > 0 garante que o agente tem história temporal (Teorema R-7)
        c_iv = c_subj > 0.0

        self_exists = all([c_i, c_ii, c_iii, c_iv])

        # Uma vez emergido, o Self nao retrocede por flutuacao de rho
        # (princípio de irreversibilidade da emergência topológica)
        if self_exists and self._first_self_step is None:
            self._first_self_step = step
        elif self._first_self_step is not None:
            # Self ja emergiu — manter emergido independente de rho atual
            self_exists = True

        if not self_exists and not any([c_i, c_ii, c_iii, c_iv]):
            reason = "SELF-1: nenhuma condicao satisfeita"

        return SelfReport(
            self_exists     = self_exists,
            n_self          = n_self,
            rho             = round(rho, 4),
            conditions_met  = [c_i, c_ii, c_iii, c_iv],
            step            = step,
            first_self_step = self._first_self_step,
            reason          = reason,
        )

    def first_self_step(self) -> Optional[int]:
        return self._first_self_step

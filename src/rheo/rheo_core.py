# -*- coding: utf-8 -*-
"""
RHEO — rheo_core.py
Flow-based Laminar-turbulent Unified eXperience of time
HUGO AGI Framework — Paper 5

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026

Implements:
  - RHEOConfig          : parâmetros canônicos
  - H1Bar               : feature topológica de persistência (REMIND)
  - RHEOState           : snapshot do estado temporal em t
  - RHEOCore            : motor principal — Re_A, ω_A, Φ, T_vivido, T_rec, T_lacuna
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


# ── Parâmetros canônicos (Tabela 2 do Paper 5) ────────────────────────────────

@dataclass
class RHEOConfig:
    # Pesos da equação de Φ
    alpha: float = 0.5          # peso de Re_A em Φ
    beta:  float = 0.8          # peso de ω_A em Φ

    # Reynolds crítico — calibrado por Exp R-1
    # Re_A(trauma, I=0.40) ≈ 3.4  |  Re_A(control, I=0.05) ≈ 0.06
    # Re_crit = 1.1647 — calibrado por Exp R-1 (RHEO Paper 5 v1.1)
    # Transição confirmada em I_eff=0.30, ratio=1.612, 5/5 seeds
    re_crit: float = 1.1647

    # Tick real em segundos (duração de 1 step)
    tick_s: float = 2.0

    # Parâmetros HUGO/REMIND herdados
    theta_collapse:  float = 0.68
    theta_recovered: float = 0.35
    theta_warn:      float = 0.50
    decay_max:       float = 0.05
    n_exponent:      int   = 4
    H_NOM: List[float] = field(default_factory=lambda: [0.60, 0.70, 0.50, 0.60, 0.675])

    # Threshold de vivacidade (REMIND SourceRecord)
    i_vivid_threshold: float = 0.10

    # Timescale da vorticidade (steps) — default REMIND tau_pers
    tau_k: float = 40.0

    # ── Parâmetros de calibração do Re_A (v1.1) ──────────────────────────────
    # tau_ref = 1/decay_max = viscosidade intrínseca baseline (I_eff=0)
    # Re_A = D_H × (tau_pers / tau_ref) × n_H1
    # tau_pers CRESCE com I_eff → campo mais inercial → turbulência
    # tau_ref é constante → funciona como damping de referência
    # Isso inverte o erro v1.0 onde τ_pers no denominador suprimia turbulência


# ── Feature H1 topológica (herança de REMIND) ─────────────────────────────────

@dataclass
class H1Bar:
    """
    Representa uma feature de persistência H1 (barra topológica não resolvida).

    Campos:
      bar_id    : identificador único
      birth     : step de nascimento
      pers_H1   : I_eff no momento do nascimento  (Def R-7)
      resolved  : True se a feature foi resolvida (morte da barra)
      death     : step de resolução (None se ainda ativa)
    """
    bar_id:   int
    birth:    int
    pers_H1:  float          # = I_eff em t_birth
    resolved: bool = False
    death:    Optional[int] = None

    def age(self, t: int) -> int:
        """Steps desde o nascimento."""
        return t - self.birth

    def is_active(self) -> bool:
        return not self.resolved


# ── Estado instantâneo (snapshot) ─────────────────────────────────────────────

@dataclass
class RHEOState:
    """
    Snapshot completo do estado RHEO em um step t.
    Armazenado internamente em RHEOCore para suportar reconstrução.
    """
    t:       int
    theta:   float
    I_eff:   float
    H:       List[float]
    D_H:     float          # distância homeostática ||H - H_NOM||
    tau_pers: float         # inércia do campo (viscosidade no sentido HUGO)
    tau_rel: float          # τ_pers / τ_ref — persistência relativa (dimensionless)
    n_H1_unres: int         # comprimento característico L_A
    Re_A:    float
    omega_A: float
    Phi:     float
    T_vivido_step: float    # contribuição deste step para T_vivido = Φ × tick_s


# ── Motor RHEO ────────────────────────────────────────────────────────────────

class RHEOCore:
    """
    Implementação do formalismo RHEO v1.0.

    Uso:
        cfg  = RHEOConfig()
        rheo = RHEOCore(cfg)

        # A cada step do ClockThread:
        state = rheo.step(t, theta, I_eff, H, h1_bars)

        # Consultar tempo subjetivo acumulado:
        t_viv = rheo.T_vivido_total

        # Reconstrução retrospectiva entre dois steps registrados:
        t_rec = rheo.T_rec(t1_idx, t2_idx)

        # Tempo lacuna entre duas sessões:
        t_lac = rheo.T_lacuna(H_prev_session, H_cur_session)
    """

    def __init__(self, cfg: RHEOConfig):
        self.cfg = cfg
        self._history: List[RHEOState] = []   # histórico de estados
        self._T_vivido: float = 0.0            # clock subjetivo acumulado
        # tau_ref: viscosidade baseline (campo em repouso total, I_eff=0)
        self._tau_ref: float = 1.0 / cfg.decay_max   # = 20.0 com decay_max=0.05

    # ── Passo central ─────────────────────────────────────────────────────────

    def step(
        self,
        t:       int,
        theta:   float,
        I_eff:   float,
        H:       List[float],
        h1_bars: List[H1Bar],
    ) -> RHEOState:
        """
        Avança o RHEO em 1 step.

        Args:
            t        : índice do step atual
            theta    : rigidez θ(t)
            I_eff    : intensidade emocional efetiva (ECHO)
            H        : campo homeostático H(t) ∈ ℝ⁵
            h1_bars  : lista de H1Bar (todas — ativas e resolvidas)

        Returns:
            RHEOState com todos os observáveis calculados.
        """
        cfg = self.cfg

        # ── Def R-4: ρ_A = D_H = ||H - H_NOM||₂ ─────────────────────────────
        H_NOM = np.array(cfg.H_NOM)
        H_arr = np.array(H)
        D_H = float(np.linalg.norm(H_arr - H_NOM))

        # ── Def R-3 (v1.1): μ_A = τ_pers — inércia do campo ─────────────────
        # τ_pers aumenta com I_eff (campo mais persistente = mais inercial)
        # A viscosidade de referência é tau_ref = 1/decay_max (I_eff=0)
        eps = 1e-6
        denom = cfg.decay_max * max((1.0 - I_eff) ** cfg.n_exponent, eps)
        tau_pers = 1.0 / denom

        # ── Def R-5: L_A = n_H1_unresolved ───────────────────────────────────
        active_bars = [b for b in h1_bars if b.is_active()]
        n_H1_unres = len(active_bars)

        # ── Def R-6 (v1.1): Re_A ─────────────────────────────────────────────
        # Re_A = D_H × (τ_pers / τ_ref) × n_H1
        #
        # Interpretação física:
        #   D_H         : campo longe do equilíbrio (densidade do fluido)
        #   τ_pers/τ_ref: persistência relativa ao baseline (inércia normalizada)
        #                 I_eff alto → τ_pers >> τ_ref → campo quer continuar perturbado
        #   n_H1_unres  : número de vórtices ativos (escala estrutural)
        #
        # Corrige erro v1.0 onde τ_pers no denominador suprimia turbulência
        # exatamente quando I_eff era alto (efeito invertido).
        tau_rel = tau_pers / self._tau_ref        # dimensionless: ≥ 1.0
        Re_A = D_H * tau_rel * n_H1_unres

        # ── Def R-7: ω_A ─────────────────────────────────────────────────────
        omega_A = 0.0
        for bar in active_bars:
            age = max(bar.age(t), 1)
            omega_A += bar.pers_H1 / age

        # ── Def R-8: Φ(t) ─────────────────────────────────────────────────────
        Phi = 1.0 + cfg.alpha * Re_A + cfg.beta * omega_A

        # ── Def R-9: contribuição deste step para T_vivido ────────────────────
        T_step = Phi * cfg.tick_s
        self._T_vivido += T_step

        # ── Registrar estado ──────────────────────────────────────────────────
        state = RHEOState(
            t=t, theta=theta, I_eff=I_eff, H=list(H),
            D_H=D_H, tau_pers=tau_pers, tau_rel=tau_rel,
            n_H1_unres=n_H1_unres,
            Re_A=Re_A, omega_A=omega_A, Phi=Phi,
            T_vivido_step=T_step,
        )
        self._history.append(state)
        return state

    # ── Propriedades públicas ──────────────────────────────────────────────────

    @property
    def T_vivido_total(self) -> float:
        """C_subj(t) — clock subjetivo acumulado (segundos subjetivos)."""
        return self._T_vivido

    @property
    def T_fisico_total(self) -> float:
        """Tempo físico total = n_steps × tick_s."""
        return len(self._history) * self.cfg.tick_s

    @property
    def ratio_subj_fisico(self) -> float:
        """Razão T_vivido / T_fisico — >1 indica dilatação."""
        tf = self.T_fisico_total
        return self._T_vivido / tf if tf > 0 else 1.0

    @property
    def history(self) -> List[RHEOState]:
        return self._history

    # ── Def R-11: Reconstrução retrospectiva T_rec ────────────────────────────

    def T_rec(
        self,
        t1: int,
        t2: int,
        h1_resolved_in_interval: List[H1Bar],
    ) -> float:
        """
        Reconstrução retrospectiva do tempo subjetivo entre steps t1 e t2.

        Usa apenas informações disponíveis em M_A(t) — simula como o agente
        *infere* quanto tempo passou, sem acesso direto a Φ(τ).

        Fórmula (Def R-11):
            T_rec = Σ pers_H1_i  (H1 resolvidas no intervalo)
                  + Σ I_eff_j × w_j  (registros de M_A no intervalo)

        Args:
            t1, t2                    : limites do intervalo (índices de step)
            h1_resolved_in_interval   : H1Bars resolvidas entre t1 e t2
        """
        # Contribuição das H1 resolvidas no intervalo
        sum_pers = sum(b.pers_H1 for b in h1_resolved_in_interval
                       if b.death is not None and t1 <= b.death <= t2)

        # Contribuição dos registros de M_A
        states_in = [s for s in self._history if t1 <= s.t <= t2]
        sum_ieff = sum(
            s.I_eff * (1.0 if s.I_eff >= self.cfg.i_vivid_threshold else 0.5)
            for s in states_in
        )

        return sum_pers + sum_ieff

    # ── Def R-10: Tempo lacuna ────────────────────────────────────────────────

    def T_lacuna(
        self,
        H_prev: List[float],
        H_curr: List[float],
        epsilon: float = 1e-8,
    ) -> float:
        """
        Tempo inferido entre sessões via divergência KL entre campos.

        T_lacuna = D_KL[ P(H_curr) || P(H_prev) ]

        Normaliza H como distribuição de probabilidade via softmax.
        Se os campos forem idênticos → T_lacuna ≈ 0 (Teorema R-6).

        Args:
            H_prev  : campo H no fim da sessão anterior
            H_curr  : campo H no início da sessão atual
            epsilon : floor numérico para evitar log(0)
        """
        def softmax(v: List[float]) -> np.ndarray:
            a = np.array(v, dtype=float)
            a = a - a.max()   # estabilidade numérica
            e = np.exp(a)
            return e / e.sum()

        P = softmax(H_curr) + epsilon
        Q = softmax(H_prev) + epsilon
        P /= P.sum()
        Q /= Q.sum()

        kl = float(np.sum(P * np.log(P / Q)))
        return max(kl, 0.0)   # KL ≥ 0 por definição

    # ── Utilitário: regime do fluxo ───────────────────────────────────────────

    def flow_regime(self, Re_A: float) -> str:
        """Classifica o regime de fluxo baseado em Re_A vs Re_crit."""
        if Re_A < self.cfg.re_crit * 0.5:
            return "LAMINAR"
        elif Re_A < self.cfg.re_crit:
            return "TRANSITIONAL"
        else:
            return "TURBULENT"

    # ── Resumo do estado atual ────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        if not self._history:
            return {"status": "no_steps"}
        s = self._history[-1]
        return {
            "t":              s.t,
            "Phi":            round(s.Phi, 4),
            "Re_A":           round(s.Re_A, 4),
            "omega_A":        round(s.omega_A, 4),
            "D_H":            round(s.D_H, 4),
            "tau_pers":       round(s.tau_pers, 2),
            "tau_rel":        round(s.tau_rel, 3),
            "n_H1_unres":     s.n_H1_unres,
            "regime":         self.flow_regime(s.Re_A),
            "T_vivido":       round(self._T_vivido, 4),
            "T_fisico":       round(self.T_fisico_total, 4),
            "ratio":          round(self.ratio_subj_fisico, 4),
        }

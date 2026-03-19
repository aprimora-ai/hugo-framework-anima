"""
ANIMA — src/kappa/valence_monitor.py
======================================
KAPPA-ANIMA: Monitor de valência positiva.

Detecta os três estados positivos definidos em Experiment G:

    Contentment  — theta sustentado em [0.62, 0.72], q < q_warn por 20+ steps
    Satisfaction — I_eff_self ∈ [0.08, 0.18] pós-IRE, dip de rigidez
    Joy          — spike de I_eff_self > 0.25, delta_theta > 0.08, duração < 20 steps

Herda a lógica do KappaMonitor do REMIND (beta_0, ADI) e adiciona
o canal afetivo positivo específico do ANIMA.

Definition G-7 — Joy Condition:
    spike transiente de alta intensidade, condicional à intensidade do gap pré-IRE.
    P(Joy) cresce com delta_pers_H1 (quanto maior o gap, maior a alegria).

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import numpy as np


class ValenceState(str, Enum):
    NEUTRAL      = "NEUTRAL"
    CONTENTMENT  = "CONTENTMENT"
    SATISFACTION = "SATISFACTION"
    JOY          = "JOY"
    CRISIS       = "CRISIS"      # herdado de REMIND


# ── Parâmetros canônicos ──────────────────────────────────────────────────────

THETA_CONTENT_LOW   = 0.62   # intervalo de contentamento
THETA_CONTENT_HIGH  = 0.72
CONTENT_MIN_STEPS   = 20     # steps sustentados para confirmar Contentment

I_SATIS_LOW         = 0.08   # intervalo de I_eff_self pós-IRE
I_SATIS_HIGH        = 0.18
SATIS_WINDOW        = 15     # steps máximos após IRE para detectar Satisfaction

I_JOY_THRESHOLD     = 0.25   # limiar de I_eff_self para Joy
DELTA_THETA_JOY     = 0.08   # aumento mínimo de theta para Joy
JOY_MAX_DURATION    = 20     # Joy dura menos de 20 steps (transiente)

Q_WARN              = 0.50   # herdado de REMIND
THETA_CRISIS        = 0.68


@dataclass
class ValenceRecord:
    step:         int
    state:        ValenceState
    theta:        float
    I_eff_self:   float
    q:            float
    duration:     int            # steps contínuos neste estado
    triggered_by: str            # "IRE" | "SEEK" | "SEEK_RESOLVE" | "SUSTAINED"
    delta_theta:  float = 0.0
    gap_intensity: float = 0.0  # I_eff do gap H1 que precedeu (para Joy)


class KappaValenceMonitor:
    """
    Monitor de valência positiva — Def. G-5/6/7.

    Mantém histórico de estados positivos e detecta transições.

    Uso típico (por step):
        record = monitor.update(step, theta, I_eff_self, q, ire_fired=False)
    """

    def __init__(self):
        self._history:         List[ValenceRecord] = []
        self._theta_history:   List[float] = []
        self._content_counter: int = 0
        self._joy_counter:     int = 0
        self._in_joy:          bool = False
        self._last_ire_step:   Optional[int] = None
        self._last_gap_I:      float = 0.0  # intensidade do gap antes do IRE

    def notify_ire(self, step: int, gap_I_eff: float) -> None:
        """Chamado quando IRE dispara (Identity Resolution Event)."""
        self._last_ire_step = step
        self._last_gap_I    = gap_I_eff

    def update(
        self,
        step:        int,
        theta:       float,
        I_eff_self:  float,
        q:           float,
        ire_fired:   bool = False,
        gap_I_eff:   float = 0.0,
    ) -> ValenceRecord:
        """
        Avalia o estado de valência no step atual.
        Retorna ValenceRecord com estado detectado.
        """
        if ire_fired:
            self.notify_ire(step, gap_I_eff)

        self._theta_history.append(theta)

        # ── CRISE (prioridade máxima) ────────────────────────────────────────
        if theta >= THETA_CRISIS:
            self._reset_positive_counters()
            rec = ValenceRecord(
                step=step, state=ValenceState.CRISIS,
                theta=theta, I_eff_self=I_eff_self, q=q,
                duration=1, triggered_by="crisis")
            self._history.append(rec)
            return rec

        # ── JOY — Def. G-7 ──────────────────────────────────────────────────
        delta_theta = self._delta_theta(window=5)
        if (I_eff_self > I_JOY_THRESHOLD
                and delta_theta > DELTA_THETA_JOY
                and self._last_ire_step is not None
                and (step - self._last_ire_step) <= SATIS_WINDOW):
            if not self._in_joy:
                self._in_joy      = True
                self._joy_counter = 1
            else:
                self._joy_counter += 1

            if self._joy_counter <= JOY_MAX_DURATION:
                rec = ValenceRecord(
                    step=step, state=ValenceState.JOY,
                    theta=theta, I_eff_self=I_eff_self, q=q,
                    duration=self._joy_counter, triggered_by="IRE",
                    delta_theta=delta_theta, gap_intensity=self._last_gap_I)
                self._history.append(rec)
                return rec
        else:
            if self._in_joy and self._joy_counter > JOY_MAX_DURATION:
                self._in_joy = False
            elif not (I_eff_self > I_JOY_THRESHOLD):
                self._in_joy      = False
                self._joy_counter = 0

        # ── SATISFACTION — Def. G-6 ──────────────────────────────────────────
        if (self._last_ire_step is not None
                and I_SATIS_LOW <= I_eff_self <= I_SATIS_HIGH
                and (step - self._last_ire_step) <= SATIS_WINDOW):
            rec = ValenceRecord(
                step=step, state=ValenceState.SATISFACTION,
                theta=theta, I_eff_self=I_eff_self, q=q,
                duration=step - self._last_ire_step, triggered_by="IRE",
                gap_intensity=self._last_gap_I)
            self._history.append(rec)
            return rec

        # ── CONTENTMENT — Def. G-5 ──────────────────────────────────────────
        if THETA_CONTENT_LOW <= theta <= THETA_CONTENT_HIGH and q < Q_WARN:
            self._content_counter += 1
        else:
            self._content_counter = 0

        if self._content_counter >= CONTENT_MIN_STEPS:
            rec = ValenceRecord(
                step=step, state=ValenceState.CONTENTMENT,
                theta=theta, I_eff_self=I_eff_self, q=q,
                duration=self._content_counter, triggered_by="SUSTAINED")
            self._history.append(rec)
            return rec

        # ── NEUTRAL ──────────────────────────────────────────────────────────
        rec = ValenceRecord(
            step=step, state=ValenceState.NEUTRAL,
            theta=theta, I_eff_self=I_eff_self, q=q,
            duration=1, triggered_by="none")
        self._history.append(rec)
        return rec

    def _delta_theta(self, window: int = 5) -> float:
        h = self._theta_history
        if len(h) < 2:
            return 0.0
        recent = h[-min(window, len(h)):]
        return float(recent[-1] - recent[0])

    def _reset_positive_counters(self) -> None:
        self._content_counter = 0
        self._joy_counter     = 0
        self._in_joy          = False

    def positive_events(self) -> List[ValenceRecord]:
        return [r for r in self._history
                if r.state in (ValenceState.JOY,
                               ValenceState.SATISFACTION,
                               ValenceState.CONTENTMENT)]

    def last_state(self) -> Optional[ValenceState]:
        return self._history[-1].state if self._history else None

    def summary(self) -> dict:
        n = len(self._history)
        if n == 0:
            return {"n": 0}
        counts = {s.value: 0 for s in ValenceState}
        for r in self._history:
            counts[r.state.value] += 1
        return {
            "n":             n,
            "counts":        counts,
            "last_state":    self.last_state(),
            "n_positive":    len(self.positive_events()),
            "joy_events":    sum(1 for r in self._history if r.state == ValenceState.JOY),
            "ire_step":      self._last_ire_step,
            "gap_intensity": round(self._last_gap_I, 4),
        }

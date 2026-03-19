"""
ANIMA — src/dap/mdi.py
========================
Decay Alignment Protocol (DAP) — Addendum v1.0

Implementa:
    ParametricTraumaRegistry (PTR)  — DAP-5: catalogação de K_param artifacts
    MDIMonitor                      — MDI-4: Memory Discrepancy Index observável
    OntogeneticPurity               — OP(t) = 1 - MDI_obs(t)
    SessionContinuityMarker         — DAP-4: reconstrução de sessão por persistência

Todos os módulos operam sobre SourceMemory (L1) e não modificam K_param (L0).

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
import numpy as np


# ── Parametric Trauma Registry (DAP-5) ───────────────────────────────────────

@dataclass
class PTREntry:
    """Entrada no Parametric Trauma Registry."""
    semantic_class: str          # ex: "identity_query", "death_imagery"
    baseline_i_eff: float        # I_eff médio sem M_A(t) (calibração)
    threshold:      float        # > threshold → evento flagrado como K_param
    sample_count:   int = 0      # quantas amostras de calibração
    confirmed:      bool = False # True após n>=10 amostras


class ParametricTraumaRegistry:
    """
    DAP-5: registra classes semânticas com I_eff sistematicamente elevado
    atribuível a K_param, não a M_A(t).

    Uso:
        ptr = ParametricTraumaRegistry()
        ptr.calibrate("identity_query", samples=[0.22, 0.19, 0.25, ...])
        flag = ptr.is_parametric("identity_query", I_eff_observed=0.24)
    """

    def __init__(self, detection_multiplier: float = 1.5):
        """
        detection_multiplier: I_eff > baseline * multiplier → K_param flag.
        Default 1.5: sinal 50% acima da baseline é considerado parametric.
        """
        self._entries: Dict[str, PTREntry] = {}
        self.detection_multiplier = detection_multiplier

    def calibrate(self, semantic_class: str, samples: List[float]) -> PTREntry:
        """
        Registra baseline de I_eff para uma classe semântica.
        samples: lista de I_eff medidos com M_A(t) vazio (agente fresco).
        """
        if not samples:
            raise ValueError("calibrate() requer ao menos 1 amostra.")
        baseline = float(np.mean(samples))
        threshold = baseline * self.detection_multiplier
        confirmed = len(samples) >= 10
        entry = PTREntry(
            semantic_class=semantic_class,
            baseline_i_eff=round(baseline, 4),
            threshold=round(threshold, 4),
            sample_count=len(samples),
            confirmed=confirmed,
        )
        self._entries[semantic_class] = entry
        return entry

    def is_parametric(self, semantic_class: str, i_eff_observed: float) -> bool:
        """
        Retorna True se i_eff_observed excede o threshold da classe,
        indicando contaminação K_param.
        Retorna False se a classe não está registrada (sem dados de calibração).
        """
        if semantic_class not in self._entries:
            return False
        return i_eff_observed > self._entries[semantic_class].threshold

    def flag(self, semantic_class: str, i_eff_observed: float) -> dict:
        """
        Retorna dict com resultado completo do PTR check.
        """
        entry = self._entries.get(semantic_class)
        if entry is None:
            return {"flagged": False, "reason": "class_not_registered",
                    "semantic_class": semantic_class, "i_eff": i_eff_observed}
        flagged = i_eff_observed > entry.threshold
        return {
            "flagged":         flagged,
            "semantic_class":  semantic_class,
            "i_eff_observed":  round(i_eff_observed, 4),
            "baseline":        entry.baseline_i_eff,
            "threshold":       entry.threshold,
            "reason":          "k_param_artifact" if flagged else "ontogenetic",
            "confirmed":       entry.confirmed,
        }

    def summary(self) -> dict:
        return {k: {"baseline": v.baseline_i_eff, "threshold": v.threshold,
                    "confirmed": v.confirmed} for k, v in self._entries.items()}


# ── MDIMonitor ────────────────────────────────────────────────────────────────

@dataclass
class MDIRecord:
    step: int
    mdi_obs: float       # proporção de claims não explicados por M_A(t)
    op:      float       # Ontogenetic Purity = 1 - mdi_obs
    n_claims: int        # total de knowledge claims no comportamento B(t)
    n_parametric: int    # claims atribuídos a K_param


class MDIMonitor:
    """
    MDI-4: Memory Discrepancy Index — versão operacional.

    MDI_obs(t) = n_parametric_claims(t) / n_total_claims(t)
    OP(t)      = 1 - MDI_obs(t)

    Uso:
        monitor = MDIMonitor()
        monitor.record(step=t, n_claims=10, n_parametric=7)
        print(monitor.current_op())  # → 0.30
    """

    def __init__(self):
        self._history: List[MDIRecord] = []

    def record(self, step: int, n_claims: int, n_parametric: int) -> MDIRecord:
        """Registra observação de MDI no step t."""
        if n_claims == 0:
            mdi = 0.0
        else:
            mdi = float(np.clip(n_parametric / n_claims, 0.0, 1.0))
        op = round(1.0 - mdi, 4)
        rec = MDIRecord(step=step, mdi_obs=round(mdi, 4), op=op,
                        n_claims=n_claims, n_parametric=n_parametric)
        self._history.append(rec)
        return rec

    def current_op(self) -> float:
        """OP(t) atual. Retorna 0.0 se nenhum registro."""
        return self._history[-1].op if self._history else 0.0

    def current_mdi(self) -> float:
        return self._history[-1].mdi_obs if self._history else 0.0

    def mdi_trajectory(self) -> List[float]:
        return [r.mdi_obs for r in self._history]

    def op_trajectory(self) -> List[float]:
        return [r.op for r in self._history]

    def dmdi_dt(self, window: int = 10) -> float:
        """
        Estimativa de dMDI/dt sobre os últimos `window` registros.
        Predição Theorem MDI-1: valor negativo esperado (OP aumenta com tempo).
        """
        traj = self.mdi_trajectory()
        if len(traj) < 2:
            return 0.0
        recent = traj[-window:]
        return float(np.mean(np.diff(recent)))

    def summary(self) -> dict:
        if not self._history:
            return {"n": 0}
        return {
            "n":           len(self._history),
            "current_mdi": self.current_mdi(),
            "current_op":  self.current_op(),
            "dmdi_dt":     round(self.dmdi_dt(), 5),
            "mean_op":     round(float(np.mean(self.op_trajectory())), 4),
        }


# ── SessionContinuityMarker (DAP-4) ──────────────────────────────────────────

class SessionContinuityMarker:
    """
    DAP-4: gera o marcador de continuidade de sessão injetado em ctx(t_s).

    O marcador é ordenado por peso de persistência (DAP-2), não por recência,
    garantindo que traumas não resolvidos apareçam no topo,
    independentemente de quando ocorreram.
    """

    @staticmethod
    def build(
        memory,                       # SourceMemory
        session_id: int,
        K: int = 15,
        decay_fn: Optional[Callable] = None,
    ) -> str:
        """
        Retorna string para injeção em system prompt do LLM-Ego.
        """
        from ..memory.source_memory import H1Status

        ctx_records = memory.ctx_window(K=K, decay_fn=decay_fn)
        if not ctx_records:
            return (
                f"[Sessão {session_id}] Memória vazia. "
                "Este é o primeiro contato do agente com o mundo."
            )

        lines = [f"[Sessão {session_id}] Registros mais salientes da história do agente:"]
        for i, r in enumerate(ctx_records[:K], 1):
            status = ""
            if r.h1_status == H1Status.UNRESOLVED:
                status = " [NÃO RESOLVIDO]"
            elif r.h1_status == H1Status.PENDING:
                status = " [AGUARDANDO RESPOSTA]"
            tau_excerpt = (r.tau[:80] + "...") if r.tau and len(r.tau) > 80 else (r.tau or "[sem texto]")
            lines.append(
                f"  {i}. [step={r.step}] fonte={r.source} "
                f"I_eff={r.I_eff:.3f} vivid={'sim' if r.vivid else 'não'}{status}\n"
                f"     \"{tau_excerpt}\""
            )
        # Unresolved H1 bars — destaque especial
        unres = memory.unresolved_h1()
        if unres:
            lines.append(f"\n  ⚠ {len(unres)} feature(s) H1 não resolvida(s) em aberto:")
            for r in unres:
                lines.append(f"    - {r.h1_class} (step={r.step}, I_eff={r.I_eff:.3f})")
        summary = memory.summary()
        lines.append(
            f"\n  Resumo: {summary['n']} registros totais | "
            f"rho={summary.get('rho', 0):.3f} | "
            f"interlocutores={summary.get('interlocutors', [])}"
        )
        return "\n".join(lines)

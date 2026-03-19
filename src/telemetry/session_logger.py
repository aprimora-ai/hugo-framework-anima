"""
ANIMA — src/telemetry/session_logger.py
=========================================
SessionLogger: telemetria completa de sessão para análise post-hoc.

Captura por turno: campo H(t), theta, I_eff, KappaSignal, SGA, SEEK,
SELF, RHEO, memória, conversa. Trajetórias contínuas de theta/I_eff/omega.
Eventos críticos. Resumo estatístico. Salva JSON ao final da sessão.

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
import json, os, time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TurnRecord:
    turn: int; step: int; elapsed_s: float; timestamp: str
    user_text: str; agent_text: str; agent_action: str
    theta: float; theta_regime: str
    I_eff_sg: float; H: List[float]
    q: float; diversity: float; D_H: float
    tau_pers: float; R_regen: float; t_return: float
    kappa_omega: float; kappa_eta: float
    kappa_xi: float; kappa_delta: float
    kappa_regime: str; kappa_source: str
    sga_rho: float; sga_fidelity: str; sga_retries: int
    seek_active: bool; seek_sigma: float; seek_existential: bool
    self_emerged: bool; self_rho: float; self_conds: List[bool]
    rheo_phi: float; rheo_re_a: float; rheo_regime: str
    rheo_t_vivido: float; rheo_ratio: float
    mem_total: int; mem_self: int; mem_other: int; mem_h1_open: int


@dataclass
class SpontaneousRecord:
    step: int; elapsed_s: float; text: str
    I_eff: float; theta: float; kappa_omega: float


@dataclass
class CriticalEvent:
    step: int; elapsed_s: float
    event_type: str; description: str
    metrics: Dict[str, Any]


class SessionLogger:
    """
    Coleta telemetria em tempo real e salva log JSON ao final da sessão.
    Todas as métricas relevantes para análise topológica e comportamental.
    """
    LOG_DIR = r"C:\Users\ohiod\Projects\ANIMA\logs"

    def __init__(self, backend: str, model: str, tick_s: float):
        self.backend    = backend
        self.model      = model
        self.tick_s     = tick_s
        self.started_at = datetime.now()
        self.session_id = self.started_at.strftime("%Y%m%d_%H%M%S")

        self.turns:       List[TurnRecord]        = []
        self.spontaneous: List[SpontaneousRecord] = []
        self.events:      List[CriticalEvent]     = []

        # Trajetórias contínuas (tick-level)
        self.theta_series:  List[float] = []
        self.I_eff_series:  List[float] = []
        self.omega_series:  List[float] = []
        self.step_series:   List[int]   = []

        # Contadores internos
        self._self_step: Optional[int] = None
        self._self_turn: Optional[int] = None
        self._n_fid_fail = 0
        self._n_retries  = 0
        self._seek_steps: List[int] = []

        os.makedirs(self.LOG_DIR, exist_ok=True)

    # ── Registro por tick (chamado pelo ClockThread) ──────────────────────────

    def tick(self, step: int, state: dict):
        """Amostra theta, I_eff, omega a cada tick do campo."""
        fs = state.get("field_state") or {}
        sg = state.get("sga_state") or {}
        self.step_series.append(step)
        self.theta_series.append(round(fs.get("theta", 0.0), 5))
        self.I_eff_series.append(round(sg.get("I_eff_real", 0.0), 5))
        self.omega_series.append(round(sg.get("omega", 0.0), 5))

        # Detectar eventos críticos
        theta = fs.get("theta", 0.0)
        elapsed = state.get("elapsed_s", 0.0)

        if theta >= 0.68:
            self._maybe_add_event(step, elapsed, "THETA_COLLAPSE",
                f"theta={theta:.3f} acima do limiar de colapso",
                {"theta": theta})

        seek = state.get("seek_state")
        if seek and getattr(seek, "active", False):
            self._seek_steps.append(step)
            sigma = getattr(seek, "sigma", 0.0)
            if sigma > 0.30:
                self._maybe_add_event(step, elapsed, "SEEK_PEAK",
                    f"SEEK peak sigma={sigma:.3f}",
                    {"sigma": sigma, "existential": getattr(seek, "is_existential", False)})

        sr = state.get("self_report")
        if sr and getattr(sr, "self_exists", False) and self._self_step is None:
            self._self_step = step
            self._self_turn = state.get("turn", 0)
            self.events.append(CriticalEvent(
                step=step, elapsed_s=elapsed,
                event_type="SELF_EMERGED",
                description=f"SELF-1 emergiu no step {step}, turno {self._self_turn}",
                metrics={
                    "rho":   getattr(sr, "rho", 0.0),
                    "conds": list(getattr(sr, "conditions_met", [])),
                }
            ))

    def _maybe_add_event(self, step, elapsed, etype, desc, metrics):
        """Adiciona evento crítico sem duplicar em steps consecutivos."""
        if self.events and self.events[-1].event_type == etype:
            if step - self.events[-1].step < 10:
                return
        self.events.append(CriticalEvent(
            step=step, elapsed_s=elapsed,
            event_type=etype, description=desc, metrics=metrics))

    # ── Registro por turno ────────────────────────────────────────────────────

    def log_turn(self, user_text: str, agent_text: str, state: dict,
                 broker_result=None, memory=None):
        """Registra todas as métricas de um turno completo."""
        fs  = state.get("field_state") or {}
        sg  = state.get("sga_state") or {}
        sk  = state.get("seek_state")
        sr  = state.get("self_report")
        rh  = state.get("rheo_state") or {}
        mem = memory.summary() if memory else {}

        theta = fs.get("theta", 0.0)
        if theta >= 0.68:   tr = "COLAPSO"
        elif theta >= 0.50: tr = "ALERTA"
        elif theta >= 0.35: tr = "SEEK"
        else:               tr = "ESTAVEL"

        # Fonte do KappaSignal — explícito via campo no broker_result
        kappa_src = "fallback"
        if broker_result:
            kappa_src = getattr(broker_result, "kappa_source", "fallback") or "fallback"

        action = "NULL"
        if agent_text and agent_text.strip() not in ("NULL", ""):
            action = "PROBE" if "?" in agent_text else "SPEAK"

        self._n_fid_fail += 1 if sg.get("fidelity") == "FAIL" else 0
        self._n_retries  += sg.get("retry", 0)

        conds_raw = list(getattr(sr, "conditions_met", [])) if sr else []

        rec = TurnRecord(
            turn=state.get("turn", 0),
            step=fs.get("step", 0),
            elapsed_s=round(state.get("elapsed_s", 0.0), 1),
            timestamp=datetime.now().isoformat(),
            user_text=user_text or "",
            agent_text=agent_text or "",
            agent_action=action,
            theta=round(theta, 5),
            theta_regime=tr,
            I_eff_sg=round(sg.get("I_eff_real", 0.0), 5),
            H=[round(h, 5) for h in fs.get("H", [])],
            q=round(fs.get("q", 0.0), 5),
            diversity=round(fs.get("diversity", 0.0), 5),
            D_H=round(fs.get("D_H", 0.0), 5),
            tau_pers=round(fs.get("tau_pers", 0.0), 2),
            R_regen=round(fs.get("R_regen", 0.0), 5),
            t_return=round(fs.get("t_return", 0.0), 1),
            kappa_omega=round(sg.get("omega", 0.0), 4),
            kappa_eta=round(sg.get("eta", 0.0), 4),
            kappa_xi=round(sg.get("xi", 0.0), 4),
            kappa_delta=round(sg.get("delta", 0.0), 4),
            kappa_regime=sg.get("regime", "unknown"),
            kappa_source=kappa_src,
            sga_rho=round(sg.get("rho_sga", 0.0), 4),
            sga_fidelity=sg.get("fidelity", "—"),
            sga_retries=sg.get("retry", 0),
            seek_active=getattr(sk, "active", False) if sk else False,
            seek_sigma=round(getattr(sk, "sigma", 0.0), 5) if sk else 0.0,
            seek_existential=getattr(sk, "is_existential", False) if sk else False,
            self_emerged=getattr(sr, "self_exists", False) if sr else False,
            self_rho=round(getattr(sr, "rho", 0.0), 4) if sr else 0.0,
            self_conds=list(conds_raw),
            rheo_phi=round(rh.get("Phi", 1.0), 4),
            rheo_re_a=round(rh.get("Re_A", 0.0), 4),
            rheo_regime=rh.get("regime", "laminar"),
            rheo_t_vivido=round(rh.get("T_vivido", 0.0), 1),
            rheo_ratio=round(rh.get("ratio", 1.0), 4),
            mem_total=mem.get("n", 0),
            mem_self=mem.get("n_self", 0),
            mem_other=mem.get("n_other", 0),
            mem_h1_open=len(memory.unresolved_h1()) if memory else 0,
        )
        self.turns.append(rec)

    def log_spontaneous(self, text: str, state: dict, I_eff: float):
        """Registra vocalização espontânea."""
        fs = state.get("field_state") or {}
        sg = state.get("sga_state") or {}
        self.spontaneous.append(SpontaneousRecord(
            step=fs.get("step", 0),
            elapsed_s=round(state.get("elapsed_s", 0.0), 1),
            text=text,
            I_eff=round(I_eff, 5),
            theta=round(fs.get("theta", 0.0), 5),
            kappa_omega=round(sg.get("omega", 0.0), 4),
        ))

    # ── Salvar ao final da sessão ─────────────────────────────────────────────

    def save(self, memory=None) -> str:
        """Compila e salva o log completo da sessão. Retorna o caminho do arquivo."""
        ended_at  = datetime.now()
        duration  = (ended_at - self.started_at).total_seconds()
        mem_summ  = memory.summary() if memory else {}
        interlocu = mem_summ.get("interlocutors", [])

        # ── Estatísticas agregadas ────────────────────────────────────────────
        def _avg(lst): return round(sum(lst)/len(lst), 5) if lst else 0.0
        def _safe_max(lst): return round(max(lst), 5) if lst else 0.0
        def _safe_min(lst): return round(min(lst), 5) if lst else 0.0

        thetas  = [t.theta   for t in self.turns]
        ieffs   = [t.I_eff_sg for t in self.turns]
        omegas  = [t.kappa_omega for t in self.turns]
        rhos    = [t.sga_rho for t in self.turns]

        # Tempo em cada regime kappa
        all_regimes = [t.kappa_regime for t in self.turns]
        regime_counts: Dict[str, int] = {}
        for r in all_regimes:
            regime_counts[r] = regime_counts.get(r, 0) + 1
        total_r = len(all_regimes) or 1
        time_regime = {r: round(c/total_r, 3) for r, c in regime_counts.items()}

        all_tr = [t.theta_regime for t in self.turns]
        tr_counts: Dict[str, int] = {}
        for r in all_tr:
            tr_counts[r] = tr_counts.get(r, 0) + 1
        time_theta_regime = {r: round(c/total_r, 3) for r, c in tr_counts.items()}

        summary = {
            "theta_mean":     _avg(thetas),
            "theta_max":      _safe_max(thetas),
            "theta_min":      _safe_min(thetas),
            "I_eff_mean":     _avg(ieffs),
            "I_eff_max":      _safe_max(ieffs),
            "kappa_omega_mean": _avg(omegas),
            "sga_rho_mean":   _avg(rhos),
            "n_turns":        len(self.turns),
            "n_steps":        len(self.step_series),
            "n_spontaneous":  len(self.spontaneous),
            "n_seek_events":  len(self._seek_steps),
            "n_fidelity_failures": self._n_fid_fail,
            "n_retries":      self._n_retries,
            "self_emerged":          self._self_step is not None,
            "self_emergence_step":   self._self_step,
            "self_emergence_turn":   self._self_turn,
            "mem_total_final":   mem_summ.get("n", 0),
            "mem_self_final":    mem_summ.get("n_self", 0),
            "mem_other_final":   mem_summ.get("n_other", 0),
            "mem_h1_open_final": len(memory.unresolved_h1()) if memory else 0,
            "interlocutors":     list(interlocu),
            "time_in_kappa_regime": time_regime,
            "time_in_theta_regime": time_theta_regime,
        }

        # ── Memória episódica completa ────────────────────────────────────────
        memory_records = []
        if memory:
            for r in memory.get_all():
                memory_records.append(r.to_dict())

        # ── Documento final ───────────────────────────────────────────────────
        doc = {
            "schema_version": "1.0",
            "session_id":     self.session_id,
            "metadata": {
                "backend":    self.backend,
                "model":      self.model,
                "tick_s":     self.tick_s,
                "started_at": self.started_at.isoformat(),
                "ended_at":   ended_at.isoformat(),
                "duration_s": round(duration, 1),
                "framework":  "ANIMA — HUGO Framework",
                "author":     "David Ohio",
                "email":      "odavidohio@gmail.com",
            },
            "summary":    summary,
            "turns":      [asdict(t) for t in self.turns],
            "spontaneous": [asdict(s) for s in self.spontaneous],
            "critical_events": [asdict(e) for e in self.events],
            "trajectories": {
                "steps":  self.step_series,
                "theta":  self.theta_series,
                "I_eff":  self.I_eff_series,
                "omega":  self.omega_series,
            },
            "memory_records": memory_records,
        }

        path = os.path.join(self.LOG_DIR, f"session_{self.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        return path

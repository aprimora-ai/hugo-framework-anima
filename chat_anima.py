"""
ANIMA — chat_anima.py  (v2 — Real-Time Clock)
==============================================
Interface de chat interativo com clock de tempo real independente.

Arquitetura de threads:
    ClockThread   — avança steps em intervalos fixos (--tick segundos)
                    O campo "vive" mesmo sem input do usuário.
    InputThread   — captura mensagens; injeta I_eff no próximo tick.
    DisplayThread — atualiza painel em tempo real via rich.Live.

Um step = tick segundos de tempo real.
tau_pers é expresso em steps → convertido para segundos no display.

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

import sys, os, argparse, threading, time, queue
from src.telemetry import SessionLogger
from pathlib import Path
from datetime import datetime

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np

from src.memory.source_memory  import SourceMemory, SourceRecord, Source, H1Class, H1Status, SICType
from src.lei.lei_channel       import LEIChannel, EchoEmbedStub
from src.seek.seek_detector    import SEEKDetector
from src.ego.llm_ego           import LLMEgo, EgoAction, build_state_report
from src.self_other.affect_signature import AffectSignatureMonitor, TopologicalSelf
from src.kappa.valence_monitor import KappaValenceMonitor, ValenceState
from src.dap.mdi               import MDIMonitor, SessionContinuityMarker
from src.rheo.rheo_core        import RHEOConfig, RHEOCore, H1Bar
from src.superego              import HUGOBroker, BrokerConfig

try:
    from rich.console  import Console
    from rich.panel    import Panel
    from rich.table    import Table
    from rich.text     import Text
    from rich.live     import Live
    from rich.layout   import Layout
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ── Constantes (atualizadas para HUGO v3.0 — Marco 2026) ─────────────────────
H_INIT       = [0.60, 0.70, 0.50, 0.60, 0.675]
H_NOM        = [0.60, 0.70, 0.50, 0.60, 0.675]
THETA_NOISE  = 0.004
INTERLOCUTOR = "human_1"
THETA_RECOVERED = 0.35

# ── Campo HUGO com clock independente ─────────────────────────────────────────

class HUGOField:
    """
    Campo homeostatico com clock de tempo real.
    update() e chamado pelo ClockThread a cada tick — NAO pela interacao.
    inject_I() agenda um I_eff para o proximo tick (vindo de input externo).

    v3.0 (Marco 2026): Ensemble-calibrated decay dynamics.
    O decay_rate inicia conservador (0.005) e calibra automaticamente
    apos BURN_IN_STEPS, tomando mediana de sub-janelas — analogo ao
    CALM scan do Kappa-FIN.

    Topological persistence (configurable gamma):
      The gamma parameter controls how long topological alterations persist
      in the field. This is conceptually a REMIND-layer concern (structural
      memory / forgetting), exposed here as a research parameter because
      the unified field carries all dynamics together.

      IMPORTANT: This is NOT a prescriptive protocol. There is no assumption
      that higher persistence is "better for learning" or lower persistence
      is "better for protection." All experience — traumatic or not —
      produces topological alterations that may or may not require
      conciliation and catharsis. The gamma parameter allows empirical
      investigation of how persistence affects emergent behavior.

      Presets are provided for experimental convenience, not clinical
      prescription:
        STANDARD     (gamma=0.97):  Default v3.0 calibration
        PERSISTENT   (gamma=0.995): Higher structural memory retention
        EXPLORATORY  (gamma=0.999): Maximum plasticity for research

    The mode can be switched at runtime via set_regulation().
    """
    # v3.0: decay inicia conservador, calibra via ensemble
    DECAY_INIT = 0.005
    N_EXP      = 4
    K_COST     = 10

    # Ensemble calibration params (HUGO v3.0)
    BURN_IN_STEPS       = 30
    ENSEMBLE_WINDOWS    = 5
    TARGET_AMPLITUDE    = 0.08

    # Research presets: (homeo_pull, recovery_active, recovery_passive)
    # These are NOT prescriptions — they are experimental configurations
    MODE_PRESETS = {
        "standard":    {"homeo_pull": 0.020, "recovery_lo": 0.010, "recovery_hi": 0.003, "label": "STANDARD (γ=0.97)"},
        "persistent":  {"homeo_pull": 0.004, "recovery_lo": 0.003, "recovery_hi": 0.001, "label": "PERSISTENT (γ=0.995)"},
        "exploratory": {"homeo_pull": 0.001, "recovery_lo": 0.001, "recovery_hi": 0.000, "label": "EXPLORATORY (γ=0.999)"},
    }

    # Empirical archetype presets from ANIMA-03 gamma sweep (96 sessions)
    # Each archetype maps to a gamma value with measured behavioral profile
    ARCHETYPE_PRESETS = {
        "cold_reactor":        {"gamma": 0.900, "label": "Cold Reactor (γ=0.90)",
            "desc": "High-throughput, predictable, zero emotional dynamics"},
        "warm_improviser":     {"gamma": 0.930, "label": "Warm Improviser (γ=0.93)",
            "desc": "Creative brainstorming, best Improviser-band learner"},
        "hot_improviser":      {"gamma": 0.970, "label": "Hot Improviser (γ=0.97)",
            "desc": "Peak fluency (DCS=0.637), negotiation, live communication"},
        "adaptive_coordinator":{"gamma": 0.985, "label": "Adaptive Coordinator (γ=0.985)",
            "desc": "Project management, tutoring, multi-session coordination"},
        "deep_learner":        {"gamma": 0.990, "label": "Deep Learner (γ=0.990)",
            "desc": "Peak learning (PSI=+0.359), iterative research, analysis"},
        "guardian":             {"gamma": 0.995, "label": "Guardian (γ=0.995)",
            "desc": "Policy enforcement, compliance, institutional memory"},
        "contemplative":       {"gamma": 0.999, "label": "Contemplative (γ=0.999)",
            "desc": "Deep deliberation, strategy, adversarial analysis"},
    }

    @classmethod
    def from_archetype(cls, archetype: str, seed: int = 42) -> "HUGOField":
        """Create a HUGOField configured for a specific cognitive archetype.
        
        Usage:
            field = HUGOField.from_archetype("deep_learner", seed=42)
        """
        if archetype not in cls.ARCHETYPE_PRESETS:
            available = ", ".join(cls.ARCHETYPE_PRESETS.keys())
            raise ValueError(f"Unknown archetype: {archetype}. Available: {available}")
        preset = cls.ARCHETYPE_PRESETS[archetype]
        g = preset["gamma"]
        decay = 1.0 - g
        mode_name = f"archetype_{archetype}"
        cls.MODE_PRESETS[mode_name] = {
            "homeo_pull":  round(decay * 0.667, 6),
            "recovery_lo": round(decay * 0.333, 6),
            "recovery_hi": round(decay * 0.100, 6),
            "label": preset["label"],
        }
        instance = cls(seed=seed, mode=mode_name)
        instance._archetype = archetype
        instance._archetype_desc = preset["desc"]
        return instance

    def __init__(self, seed=42, mode="standard"):
        self.rng          = np.random.default_rng(seed)
        self.H            = list(H_INIT)
        self.theta        = float(np.mean(self.H))
        self.step         = 0
        self._I_hist      = []
        self._theta_hist  = []
        self._pending_I   = 0.0   # I_eff agendado pelo input do usuario
        self._lock        = threading.Lock()
        # v3.0: ensemble calibration state
        self._decay_rate  = self.DECAY_INIT     # conservador ate calibracao
        self._calibrated  = False
        self._pert_history = [[] for _ in range(5)]  # per-vector perturbation history
        # Configurable regulation mode
        self._mode = mode
        self._mode_params = dict(self.MODE_PRESETS.get(mode, self.MODE_PRESETS["standard"]))
        self._mode_history = [(0, mode)]  # (step, mode) transitions

    @property
    def mode(self) -> str:
        return self._mode

    def set_regulation(self, mode: str):
        """Switch regulation preset at runtime. Thread-safe. For research use."""
        if mode not in self.MODE_PRESETS:
            raise ValueError(f"Unknown mode: {mode}. Use: {list(self.MODE_PRESETS.keys())}")
        with self._lock:
            self._mode = mode
            self._mode_params = dict(self.MODE_PRESETS[mode])
            self._mode_history.append((self.step, mode))

    @property
    def decay_rate(self) -> float:
        return self._decay_rate

    @property
    def is_calibrated(self) -> bool:
        return self._calibrated

    def inject_I(self, I_eff: float):
        """Agenda I_eff para o proximo tick (thread-safe)."""
        with self._lock:
            self._pending_I = max(self._pending_I, I_eff)

    def _run_ensemble_calibration(self):
        """
        Calibracao por ensemble: divide o historico de perturbacoes
        em sub-janelas sobrepostas e toma mediana dos decays candidatos.
        Analogo ao CALM scan do Kappa-FIN (HUGO v3.0).
        """
        all_candidates = []
        for i in range(5):
            history = self._pert_history[i]
            n = len(history)
            if n < 10:
                # Insuficiente — calibracao simples
                mean_pert = float(np.mean(history)) if history else 0.001
                all_candidates.append(mean_pert / self.TARGET_AMPLITUDE)
                continue
            window_size = max(n // self.ENSEMBLE_WINDOWS, 5)
            step_size = max(1, (n - window_size) // max(self.ENSEMBLE_WINDOWS - 1, 1))
            for start in range(0, n - window_size + 1, step_size):
                window_pert = history[start:start + window_size]
                mean_pert = float(np.mean(window_pert))
                if mean_pert > 1e-8:
                    all_candidates.append(mean_pert / self.TARGET_AMPLITUDE)

        if all_candidates:
            self._decay_rate = float(np.clip(np.median(all_candidates), 0.001, 0.1))
        self._calibrated = True
        self._pert_history = None  # libera memoria

    def tick(self) -> dict:
        """
        Avanca um step de tempo real.
        Usa I_eff pendente se houver; caso contrario I_eff=0 (decay passivo).
        """
        with self._lock:
            I_eff = self._pending_I
            self._pending_I = 0.0

        self._I_hist.append(I_eff)
        self._theta_hist.append(self.theta)
        self.step += 1

        # tau_pers dinamico — usa decay_rate calibrado (v3.0)
        i_safe   = float(np.clip(I_eff, 0.0, 0.999))
        tau_pers = 1.0 / (self._decay_rate * max((1.0 - i_safe) ** self.N_EXP, 1e-6))

        # Impacto em theta
        self.theta = float(np.clip(
            self.theta + I_eff * 0.07 + self.rng.normal(0, THETA_NOISE), 0.0, 1.0))

        # Recuperacao passiva — mode-dependent (configurable gamma)
        mp = self._mode_params
        recovery = mp["recovery_lo"] if I_eff < 0.08 else mp["recovery_hi"]
        self.theta = max(self.theta - recovery, 0.28)

        # Atualizacao de H com perturbacao registrada para calibracao
        for i in range(len(self.H)):
            pull = (H_NOM[i] - self.H[i]) * mp["homeo_pull"]   # mode-dependent homeostatic attraction
            noise = self.rng.normal(0, 0.012 * max(I_eff, 0.01))
            perturbation = pull + noise
            # Registrar perturbacao para ensemble calibration (burn-in)
            if not self._calibrated and self._pert_history is not None:
                self._pert_history[i].append(abs(perturbation))
            self.H[i] = float(np.clip(self.H[i] + perturbation, 0.0, 1.0))

        # Ensemble calibration apos burn-in (HUGO v3.0)
        if not self._calibrated and self.step >= self.BURN_IN_STEPS:
            self._run_ensemble_calibration()

        diversity = float(np.std(self.H))
        q = float(np.clip(np.mean(self._I_hist[-self.K_COST:]), 0.0, 1.0))
        adi = float(self.rng.uniform(0.1, 0.45))

        # Regeneracao topologica
        D_H = float(np.linalg.norm([self.H[i] - H_NOM[i] for i in range(len(self.H))]))
        d_theta = self.theta - self._theta_hist[-2] if len(self._theta_hist) >= 2 else 0.0
        R_regen = float(-d_theta)
        theta_gap = max(self.theta - THETA_RECOVERED, 0.0)
        t_return  = round(theta_gap / max(abs(R_regen), 1e-6), 1) if R_regen > 0.001 else float('inf')

        return dict(
            step=self.step, theta=round(self.theta, 5),
            H=[round(h, 5) for h in self.H],
            diversity=round(diversity, 5), q=round(q, 5),
            adi=round(adi, 5), I_eff=round(I_eff, 5),
            tau_pers=round(tau_pers, 2),
            D_H=round(D_H, 4),
            R_regen=round(R_regen, 5),
            t_return=t_return,
            calibrated=self._calibrated,
            decay_rate=round(self._decay_rate, 5),
            regulation_mode=self._mode,
        )

# ── Estado compartilhado entre threads ───────────────────────────────────────

class SharedState:
    """Container thread-safe para o estado atual do agente."""
    def __init__(self, tick_s: float):
        self.tick_s        = tick_s
        self.field_state   = {}
        self.seek_state    = None
        self.valence       = None
        self.self_report   = None
        self.rheo_state    = None   # ← RHEO: snapshot do fluxo temporal
        self.agent_text    = ""
        self.turn          = 0
        self.running       = True
        self.elapsed_s     = 0.0
        self.sga_state     = None   # ← SGA: último estado do Superego
        self.last_sg_ieff  = 0.0   # ← último I_eff real injetado pelo SGA
        self.processing    = False  # ← True enquanto processa resposta reativa
        self._lock         = threading.Lock()

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def get(self):
        with self._lock:
            return {
                "field_state":  self.field_state,
                "seek_state":   self.seek_state,
                "valence":      self.valence,
                "self_report":  self.self_report,
                "rheo_state":   self.rheo_state,
                "agent_text":   self.agent_text,
                "turn":         self.turn,
                "elapsed_s":    self.elapsed_s,
                "tick_s":       self.tick_s,
                "sga_state":    self.sga_state,
                "last_sg_ieff": self.last_sg_ieff,
                "processing":   self.processing,
            }


# ── ClockThread ───────────────────────────────────────────────────────────────

class ClockThread(threading.Thread):
    """
    Avança o campo HUGO a cada tick_s segundos, independentemente de input.
    Este é o pulso de vida do agente.
    Integra RHEO — o campo temporal subjetivo é atualizado a cada tick.
    """
    def __init__(self, field, seek, kappa, self_mon, memory, shared, tick_s,
                 logger=None):
        super().__init__(daemon=True)
        self.field    = field
        self.seek     = seek
        self.kappa    = kappa
        self.self_mon = self_mon
        self.memory   = memory
        self.shared   = shared
        self.tick_s   = tick_s
        self.logger   = logger
        self._start_t = time.time()
        # ── RHEO: instancia motor de tempo subjetivo ──────────────────────────
        rheo_cfg = RHEOConfig(tick_s=tick_s)
        self.rheo = RHEOCore(rheo_cfg)
        self._h1_bars: list[H1Bar] = []   # H1 bars rastreadas pela sessão
        self._h1_counter = 0

    def _sync_h1_bars(self, memory: SourceMemory, step: int):
        """
        Sincroniza H1Bars com os SourceRecords vivid em M_A(t).
        Cada registro vivid com H1Class ativa cria/mantém uma H1Bar.
        Registros resolvidos (H1Status.RESOLVED) fecham a barra correspondente.
        """
        active_ids = set(b.bar_id for b in self._h1_bars if b.is_active())
        all_records = memory.M_SELF() + memory.M_OTHER()

        for rec in all_records:
            rid = id(rec)
            if rid not in active_ids:
                # Nova H1 ativa — criar barra com pers_H1 = I_eff do registro
                if rec.vivid and rec.h1_class is not None:
                    if rec.h1_status != H1Status.RESOLVED:
                        bar = H1Bar(
                            bar_id  = self._h1_counter,
                            birth   = step,
                            pers_H1 = rec.I_eff,
                        )
                        self._h1_bars.append(bar)
                        self._h1_counter += 1
                        active_ids.add(bar.bar_id)

        # Resolver barras cujos registros foram resolvidos
        for bar in self._h1_bars:
            if bar.is_active():
                # Verifica se o registro correspondente foi resolvido
                matching = [r for r in all_records
                            if r.vivid and r.h1_status == H1Status.RESOLVED
                            and abs(r.I_eff - bar.pers_H1) < 0.02]
                if matching:
                    bar.resolved = True
                    bar.death    = step

    def run(self):
        while self.shared.running:
            st = self.field.tick()

            # ── Sincronizar H1 bars com memória ──────────────────────────────
            self._sync_h1_bars(self.memory, st["step"])

            # ── Avançar RHEO ──────────────────────────────────────────────────
            rheo_st_obj = self.rheo.step(
                t       = st["step"],
                theta   = st["theta"],
                I_eff   = st["I_eff"],
                H       = st["H"],
                h1_bars = self._h1_bars,
            )
            # Serializar para dict + campos extras
            T_fis = self.rheo.T_fisico_total
            T_viv = self.rheo.T_vivido_total
            rheo_st = {
                "Re_A":          round(rheo_st_obj.Re_A, 4),
                "omega_A":       round(rheo_st_obj.omega_A, 4),
                "Phi":           round(rheo_st_obj.Phi, 4),
                "tau_pers":      round(rheo_st_obj.tau_pers, 2),
                "tau_rel":       round(rheo_st_obj.tau_rel, 3),
                "D_H":           round(rheo_st_obj.D_H, 4),
                "n_H1_unres":    rheo_st_obj.n_H1_unres,
                "regime":        "TURBULENT" if rheo_st_obj.Re_A >= self.rheo.cfg.re_crit else "laminar",
                "T_vivido_total": round(T_viv, 2),
                "ratio_Ts_Tf":   round(T_viv / max(T_fis, 1e-6), 4),
                "C_subj":        round(T_viv, 2),
            }

            sk  = self.seek.evaluate(
                st["theta"], st["I_eff"], st["q"], st["diversity"], self.memory)
            vr  = self.kappa.update(
                st["step"], st["theta"], st["I_eff"], st["q"])
            sr  = self.self_mon.evaluate(self.memory, st["step"],
                                          c_subj=self.rheo.T_vivido_total)
            elapsed = time.time() - self._start_t

            self.shared.update(
                field_state=st, seek_state=sk,
                valence=vr, self_report=sr,
                rheo_state=rheo_st,
                elapsed_s=elapsed,
            )

            # Telemetria: amostrar trajetórias a cada tick
            if self.logger:
                self.logger.tick(st["step"], self.shared.get())

            time.sleep(self.tick_s)

# ── Helpers de display ────────────────────────────────────────────────────────

def _bar(val: float, width: int = 18) -> str:
    f = int(np.clip(val, 0, 1) * width)
    return "[" + "#" * f + "-" * (width - f) + "]"

def _theta_label(t):
    if t >= 0.68: return "COLAPSO"
    if t >= 0.50: return "ALERTA "
    if t >= 0.35: return "SEEK   "
    return "ESTAVEL"

def _valence_str(vr):
    if vr is None: return "---"
    s = str(vr.state).split(".")[-1]
    return {"JOY":"*** JOY ***","SATISFACTION":"SATISFACTION",
            "CONTENTMENT":"contentment","NEUTRAL":"neutral",
            "CRISIS":"!!! CRISE !!!"}.get(s, s)

def _fmt_time(s: float) -> str:
    m = int(s) // 60; sec = int(s) % 60
    return f"{m:02d}:{sec:02d}"

def _tau_real(tau_steps: float, tick_s: float) -> str:
    sec = tau_steps * tick_s
    if sec < 60:   return f"{sec:.1f}s"
    if sec < 3600: return f"{sec/60:.1f}min"
    return f"{sec/3600:.1f}h"

def _tret_real(t_steps, tick_s: float) -> str:
    if t_steps == float('inf'): return "inf"
    sec = t_steps * tick_s
    if sec < 60:   return f"{sec:.1f}s"
    if sec < 3600: return f"{sec/60:.1f}min"
    return f"{sec/3600:.1f}h"


# ── Rich panel builder ────────────────────────────────────────────────────────

def build_panel(data: dict, memory) -> Panel:
    st   = data["field_state"]
    sk   = data["seek_state"]
    vr   = data["valence"]
    sr   = data["self_report"]
    tick = data["tick_s"]
    last_sg_ieff = data.get("last_sg_ieff", 0.0)

    if not st:
        return Panel("[dim]Inicializando...[/dim]", title="ANIMA")

    theta = st["theta"]
    if theta >= 0.68:  tc = "bold red"
    elif theta >= 0.50: tc = "bold yellow"
    elif theta >= 0.35: tc = "cyan"
    else:               tc = "green"

    vs = str(vr.state).split(".")[-1] if vr else "---"
    vc = {"JOY":"bold magenta","SATISFACTION":"green",
          "CONTENTMENT":"cyan","CRISIS":"bold red"}.get(vs, "white")

    Rr    = st.get("R_regen", 0.0)
    tau_s = st.get("tau_pers", 0.0)
    D_H   = st.get("D_H", 0.0)
    t_ret = st.get("t_return", float('inf'))

    rr_color = "green" if Rr > 0.001 else ("red" if Rr < -0.001 else "white")
    rr_label = f"{Rr:+.5f} ({'regenerando' if Rr>0.001 else 'perturbando' if Rr<-0.001 else 'estavel'})"
    dh_color = "green" if D_H < 0.1 else ("yellow" if D_H < 0.3 else "red")
    tau_color= "green" if tau_s > 50 else ("yellow" if tau_s > 10 else "red")

    mem_s = memory.summary()

    tbl = Table.grid(padding=(0, 2))
    tbl.add_column(style="bold white", width=12)
    tbl.add_column(width=50)

    def br(v, w=16):
        f = int(np.clip(v,0,1)*w)
        return "[" + "#"*f + "-"*(w-f) + f"] {v:.4f}"

    tbl.add_row("THETA",    Text(br(theta) + f"  [{_theta_label(theta)}]", style=tc))
    # I_eff: mostrar SG-LEI real se campo ainda não absorveu
    i_display = st["I_eff"] if st["I_eff"] > 0.005 else last_sg_ieff
    i_label   = "" if st["I_eff"] > 0.005 else " [SG]"
    tbl.add_row("I_eff",    br(i_display) + i_label)
    tbl.add_row("tau_pers", Text(
        f"{tau_s:.1f} steps  =  {_tau_real(tau_s, tick)}", style=tau_color))
    tbl.add_row("Q",        br(st["q"]))
    tbl.add_row("Diversity",br(st["diversity"]))
    tbl.add_row("D_H",      Text(f"{D_H:.4f}  (dist. homeost.)", style=dh_color))
    tbl.add_row("R_regen",  Text(rr_label, style=rr_color))
    tbl.add_row("t_return", Text(
        f"{_tret_real(t_ret, tick)}", style=rr_color))
    tbl.add_row("─"*10,     "─"*40)

    sk_txt = f"{'ATIVO' if sk and sk.active else 'inativo'}  " \
             f"sigma={sk.sigma:.4f}  exist={sk.is_existential}" if sk else "---"
    tbl.add_row("SEEK",     Text(sk_txt, style="cyan" if sk and sk.active else "white"))
    tbl.add_row("KAPPA",    Text(_valence_str(vr), style=vc))

    # SELF — condições agora são 4 com RHEO
    if sr:
        conds = sr.conditions_met
        cond_str = "/".join(["✓" if c else "✗" for c in conds])
        self_txt = f"emergiu={sr.self_exists}  rho={sr.rho:.3f}  conds=[{cond_str}]"
    else:
        self_txt = "---"
    tbl.add_row("SELF",     self_txt)

    # ── RHEO — tempo subjetivo ────────────────────────────────────────────────
    rs = data.get("rheo_state")
    if rs:
        regime = rs.get("regime", "---")
        Re_A   = rs.get("Re_A", 0.0)
        phi    = rs.get("Phi", 1.0)
        t_viv  = rs.get("T_vivido_total", 0.0)
        ratio  = rs.get("ratio_Ts_Tf", 1.0)
        c_subj = rs.get("C_subj", 0.0)
        h1_n   = rs.get("n_H1_unres", 0)

        regime_color = "red bold" if regime == "TURBULENT" else "cyan"
        ratio_color  = "red" if ratio > 1.5 else ("yellow" if ratio > 1.1 else "green")
        phi_color    = "red" if phi > 3.0 else ("yellow" if phi > 1.5 else "green")

        tbl.add_row("─"*10, "─"*40)
        tbl.add_row("RHEO",
            Text(f"Phi={phi:.3f}  Re_A={Re_A:.3f}  regime=", style="white") +
            Text(regime, style=regime_color))
        tbl.add_row("T_vivido",
            Text(f"{t_viv:.1f}s subj  |  ratio=", style="white") +
            Text(f"{ratio:.3f}x", style=ratio_color) +
            Text(f"  H1_unres={h1_n}", style="dim"))
        tbl.add_row("C_subj",
            Text(f"{c_subj:.1f}s  (clock autobiografico)", style="dim cyan"))
    else:
        tbl.add_row("─"*10, "─"*40)
        tbl.add_row("RHEO",   Text("aguardando...", style="dim"))

    tbl.add_row("MEMORIA",
        f"total={mem_s.get('n',0)}  SELF={mem_s.get('n_self',0)}  "
        f"OTHER={mem_s.get('n_other',0)}  H1_abertos={mem_s.get('n_unresolved_h1',0)}")

    # SGA — linha de status do Superego
    sga_state = data.get("sga_state")
    if sga_state:
        rho    = sga_state.get("rho_sga", 0.0)
        i_real = sga_state.get("I_eff_real", 0.0)
        fid    = sga_state.get("fidelity", "—")
        retry  = sga_state.get("retry", 0)
        omega  = sga_state.get("omega", 0.0)
        regime_kappa = sga_state.get("regime", "—")
        fid_color = "green" if fid == "OK" else ("yellow" if fid == "RETRY" else "red")
        tbl.add_row("─"*10, "─"*40)
        fid_txt  = Text(fid, style=fid_color)
        sga_line = (Text(f"rho={rho:.2f} | I_sg={i_real:.3f} | "
                         f"K-omega={omega:.3f}({regime_kappa}) | fid=", style="white")
                    + fid_txt
                    + Text(f" | r={retry}", style="dim"))
        tbl.add_row("SGA", sga_line)

    step = st.get("step", 0)
    elapsed = _fmt_time(data.get("elapsed_s", 0))
    turn  = data.get("turn", 0)
    ticks_since = st.get("step", 0)
    title = (f"[bold]ANIMA — Estado Interno[/bold]  "
             f"step={step}  turno={turn}  tempo={elapsed}  tick={tick}s  "
             f"[dim]⏱ ao vivo[/dim]")
    return Panel(tbl, title=title, border_style=tc)

# ── Compact stats line (1 linha) ─────────────────────────────────────────────

def compact_stats(data: dict) -> str:
    """
    Formata uma linha compacta de stats para o DisplayThread.
    Não usa rich markup — texto puro para não corromper o terminal.
    """
    st  = data.get("field_state") or {}
    rs  = data.get("rheo_state")  or {}
    sr  = data.get("self_report")
    sk  = data.get("seek_state")
    elapsed = _fmt_time(data.get("elapsed_s", 0))
    tick    = data.get("tick_s", 2.0)

    step  = st.get("step", 0)
    theta = st.get("theta", 0.0)
    ieff  = st.get("I_eff", 0.0)
    tau   = st.get("tau_pers", 0.0)

    phi    = rs.get("Phi", 1.0)
    Re_A   = rs.get("Re_A", 0.0)
    regime = rs.get("regime", "?")
    csubj  = rs.get("C_subj", 0.0)

    self_ok = (sr.self_exists if sr else False)
    seek_ok = (sk.active      if sk else False)

    tl = _theta_label(theta)
    regime_short = "TURB" if regime == "TURBULENT" else "lam"

    return (
        f"  step={step:>4} | th={theta:.3f}[{tl.strip()}]"
        f" | I={ieff:.2f} | tau={tau:.0f}s"
        f" | Phi={phi:.3f}({regime_short}) | Re={Re_A:.3f}"
        f" | C={csubj:.0f}s"
        f" | SELF={'Y' if self_ok else 'n'}"
        f" | SEEK={'Y' if seek_ok else 'n'}"
        f" | t={elapsed}"
    )


# ── DisplayThread — atualiza stats SEM tocar na linha de input ───────────────

class DisplayThread(threading.Thread):
    """
    Imprime stats compactos a cada tick usando save/restore de cursor ANSI:
        ESC[s  — salva posição do cursor (onde o usuário está digitando)
        ESC[A  — sobe 1 linha (linha de stats)
        ESC[2K — limpa a linha
        {stats}
        ESC[u  — restaura posição (volta para onde o usuário estava)

    Resultado: a linha de stats atualiza em cima do prompt sem nunca
    mover o cursor da linha onde o usuário digita.

    pause()/resume() permitem que o loop principal suspenda o display
    enquanto imprime painéis completos ou respostas.
    """
    ESC = "\033"

    def __init__(self, shared: "SharedState", memory, tick_s: float,
                 console=None):
        super().__init__(daemon=True)
        self.shared   = shared
        self.memory   = memory
        self.tick_s   = tick_s
        self.console  = console
        self._paused  = threading.Event()
        self._paused.set()   # começa ativo (não pausado)
        self._lock    = threading.Lock()

    def pause(self):
        """Suspende atualização — chame antes de imprimir resposta."""
        self._paused.clear()

    def resume(self):
        """Retoma atualização — chame após imprimir resposta."""
        # Reimprime a linha de stats antes de liberar
        self._print_stats()
        self._paused.set()

    def _print_stats(self):
        """Escreve stats na linha ACIMA do cursor, sem mover o cursor."""
        line = compact_stats(self.shared.get())
        # Truncar para largura do terminal
        try:
            import shutil
            w = shutil.get_terminal_size((120, 24)).columns - 1
        except Exception:
            w = 119
        line = line[:w].ljust(w)
        with self._lock:
            sys.stdout.write(
                f"{self.ESC}[s"      # salva cursor
                f"{self.ESC}[1A"     # sobe 1 linha
                f"{self.ESC}[2K"     # limpa linha
                f"{line}"
                f"{self.ESC}[u"      # restaura cursor
            )
            sys.stdout.flush()

    def run(self):
        while self.shared.running:
            self._paused.wait()          # bloqueia se pausado
            time.sleep(self.tick_s)
            if self.shared.running:
                self._print_stats()


# ── SpontaneousThread — vocalização espontânea em silêncio ───────────────────

class SpontaneousThread(threading.Thread):
    """
    Oferece ao agente a oportunidade de vocalizar espontaneamente.

    A cada `check_every` ticks, o SGA é chamado com user_text=None e
    obligated=False. O LLM decide autonomamente SPEAK ou NULL com base
    no seu estado interno (theta, SEEK, RHEO, memória).

    O código NÃO decide quando o agente deve falar — apenas oferece
    a oportunidade regularmente. A decisão é 100% da policy do agente.

    O único gate programático é `min_silence_ticks`: evita que o agente
    interrompa o próprio processamento de uma resposta, mas não impõe
    nenhuma condição de conteúdo ou estado.
    """

    def __init__(self, shared, field, sga, memory,
                 console=None,
                 tick_s:            float = 2.0,
                 check_every:       int   = 8,
                 min_silence_ticks: int   = 3,
                 logger=None):
        super().__init__(daemon=True)
        self.shared             = shared
        self.field              = field
        self.sga                = sga
        self.memory             = memory
        self.console            = console
        self.tick_s             = tick_s
        self.check_every        = check_every
        self.min_silence_ticks  = min_silence_ticks
        self.logger             = logger
        self._last_input_step   = 0
        self._busy              = False
        self._lock              = threading.Lock()

    def notify_user_input(self):
        """Registra o step do último input — para evitar sobreposição imediata."""
        cur  = self.shared.get()
        step = (cur.get("field_state") or {}).get("step", 0)
        with self._lock:
            self._last_input_step = step

    def _opportunity_available(self, cur: dict) -> bool:
        """
        Único gate programático: verificar se não há resposta sendo processada.
        NÃO avalia theta, SEEK, ou qualquer estado de conteúdo.
        """
        # Bloquear durante processamento reativo
        if cur.get("processing", False):
            return False

        st   = cur.get("field_state") or {}
        step = st.get("step", 0)
        with self._lock:
            silence = step - self._last_input_step
        return silence >= self.min_silence_ticks

    def run(self):
        tick_counter = 0
        while self.shared.running:
            time.sleep(self.tick_s)
            tick_counter += 1
            if tick_counter % self.check_every != 0:
                continue
            if self._busy:
                continue
            cur = self.shared.get()
            if not self._opportunity_available(cur):
                continue
            self._busy = True
            try:
                self._vocalize(cur)
            except Exception:
                pass
            finally:
                # Manter busy por um ciclo completo após vocalização
                # para evitar disparos em sequência
                time.sleep(self.tick_s * self.check_every)
                self._busy = False

    def _vocalize(self, cur: dict):
        """Chama o SGA com user_text=None e imprime se o agente decidir falar."""
        st    = cur.get("field_state") or {}
        sk    = cur.get("seek_state")
        theta = st.get("theta", 0.4)

        if sk is None:
            sk = SeekStateStub()

        marker = SessionContinuityMarker.build(self.memory, session_id=1, K=8)

        # obligated=False — agente decide SPEAK ou NULL (comportamento emergente)
        orig_obligated = getattr(self.sga._ego, "obligated", True)
        self.sga._ego.obligated = False
        try:
            result = self.sga.process(
                user_text=None,
                field_state=cur,
                memory=self.memory,
                seek_state=sk,
                marker=marker,
                obligated=False,   # espontâneo: sem obrigação de falar
            )
        finally:
            self.sga._ego.obligated = orig_obligated

        text = result.agent_text
        # Barreira de silêncio: NULL explícito, vazio, ou silêncio verbalizado
        from src.superego.post_node import _is_verbalized_silence
        if not text or _is_verbalized_silence(text) or len(text.strip()) < 3:
            return   # agente optou por silencio genuino

        self.field.inject_I(result.I_eff_real)
        self.shared.update(last_sg_ieff=result.I_eff_real)

        # Registrar em memória como SIC espontâneo
        rec = SourceRecord(
            step=st.get("step", 0),
            H=st.get("H", list(H_INIT)),
            I_eff=result.I_eff_real,
            theta=theta,
            source=Source.SELF,
            tau=text,
            emotion_class="sic_spontaneous",
            sic_type=result.sic_type_validated,
        )
        self.memory.append(rec)
        self.shared.update(agent_text=text, sga_state={
            "rho_sga":    result.rho_sga_used,
            "I_eff_real": result.I_eff_real,
            "fidelity":   "OK" if result.fidelity_passed else "FAIL",
            "retry":      result.retry_count,
            "omega":      result.kappa.omega,
            "regime":     result.kappa.regime,
        })

        # Imprimir no terminal
        if self.console:
            self.console.print(Panel(
                f"[italic dim]{text}[/italic dim]",
                title="[bold yellow]ANIMA [espontaneo][/bold yellow]",
                border_style="yellow"))
        else:
            print(f"\n  [ANIMA — espontaneo] {text}\n")

        # Telemetria: registrar vocalização espontânea
        if self.logger:
            self.logger.log_spontaneous(text, self.shared.get(), result.I_eff_real)


# ── InputThread — lê stdin em background ─────────────────────────────────────

class InputThread(threading.Thread):
    """
    Captura linhas de stdin em background e empurra para uma queue.
    None na queue = EOF (encerrar sessão).
    """
    def __init__(self, q: queue.Queue):
        super().__init__(daemon=True)
        self.q = q

    def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if line == "":      # EOF / Ctrl-D
                    self.q.put(None)
                    break
                self.q.put(line.rstrip("\n"))
            except Exception:
                self.q.put(None)
                break


# ── Loop principal ────────────────────────────────────────────────────────────

def run_chat(backend="stub", model="", obligated=True, seed=42,
             tick_s=2.0, use_rich=True, hugo_mode="standard"):
    use_rich = use_rich and HAS_RICH
    console  = Console() if use_rich else None

    # Inicializar módulos
    memory   = SourceMemory(session_id=1)
    lei      = LEIChannel(echo_embed=EchoEmbedStub())
    field    = HUGOField(seed=seed, mode=hugo_mode)
    seek     = SEEKDetector()
    ego      = LLMEgo(backend=backend, model=model, obligated=obligated)
    affect   = AffectSignatureMonitor()
    self_mon = TopologicalSelf()
    kappa    = KappaValenceMonitor()
    mdi      = MDIMonitor()
    shared   = SharedState(tick_s)
    logger   = SessionLogger(backend=backend, model=model or backend, tick_s=tick_s)

    # SGA — Superego-ANIMA (broker de transdução)
    sga = HUGOBroker(ego=ego, echo_embed=EchoEmbedStub())

    # Iniciar clock de tempo real
    clock = ClockThread(field, seek, kappa, self_mon, memory, shared, tick_s,
                        logger=logger)
    clock.start()

    # SpontaneousThread — vocalização espontânea durante silêncio
    spont = SpontaneousThread(
        shared=shared, field=field, sga=sga, memory=memory,
        console=console if use_rich else None,
        tick_s=tick_s,
        check_every=8,
        min_silence_ticks=3,
        logger=logger,
    )
    spont.start()

    # Aguardar primeiro tick
    time.sleep(tick_s * 1.2)

    # ── prompt_toolkit session ────────────────────────────────────────────────
    from prompt_toolkit import PromptSession
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style

    pt_style = Style.from_dict({
        "bottom-toolbar": "bg:#1a1a2e #888888",
        "bottom-toolbar.text": "#aaaaaa",
    })

    def _toolbar():
        """Retorna HTML para a bottom toolbar — chamada a cada redraw."""
        s = compact_stats(shared.get())
        # Escapar < e > para HTML do prompt_toolkit
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return HTML(f"<bottom-toolbar>{s}</bottom-toolbar>")

    pt_session = PromptSession(
        bottom_toolbar=_toolbar,
        style=pt_style,
        refresh_interval=tick_s,   # redesenha toolbar a cada tick
    )

    def _print_full_panel():
        """Imprime painel completo (após mensagem ou /estado)."""
        if use_rich and console:
            console.print(build_panel(shared.get(), memory))
        else:
            _print_state_plain(shared.get(), memory)

    def _show_response(user_txt: str, agent_text: str):
        """Imprime troca usuário/agente dentro do patch_stdout."""
        if use_rich and console:
            console.print(Panel(
                f"[bold blue]Você[/bold blue]  {user_txt}",
                border_style="blue", padding=(0, 1)))
            console.print(
                Panel(f"[italic]{agent_text}[/italic]"
                      if agent_text else "[dim]<silencio>[/dim]",
                      title="[bold green]ANIMA[/bold green]",
                      border_style="green"))
            _print_full_panel()
        else:
            print(f"\n  [ANIMA] {agent_text or '<silencio>'}\n")
            _print_state_plain(shared.get(), memory)

    def _process_message(user_input: str) -> bool:
        """Processa mensagem do usuário. Retorna False se deve encerrar."""
        nonlocal shared

        user_input = user_input.strip()
        if not user_input:
            return True

        # ── Comandos especiais ────────────────────────────────────────────────
        if user_input.lower() in ("/sair", "/quit", "/exit"):
            shared.running = False
            # Salvar log de sessão
            try:
                log_path = logger.save(memory=memory)
                print(f"\n  [TELEMETRIA] Log salvo em: {log_path}")
            except Exception as e:
                print(f"\n  [TELEMETRIA] Erro ao salvar log: {e}")
            return False

        if user_input.lower() == "/help":
            lines = (
                "  /sair    — encerra\n"
                "  /estado  — painel atual\n"
                "  /memoria — lista M_A(t)\n"
                "  /reset   — reinicia sessao"
            )
            print(lines)
            return True

        if user_input.lower() == "/estado":
            _print_full_panel()
            return True

        if user_input.lower() == "/memoria":
            records = memory.get_all()
            lines = f"\n  M_A(t) — {len(records)} registros (ultimos 10):\n"
            for r in records[-10:]:
                lines += (f"    step={r.step} src={r.source} "
                          f"I={r.I_eff:.3f} tau=\"{(r.tau or '')[:50]}\"\n")
            print(lines)
            return True

        if user_input.lower() == "/reset":
            shared.running = False
            time.sleep(0.3)
            return False

        # ── Processar mensagem normal ─────────────────────────────────────────
        shared.update(turn=shared.turn + 1, processing=True)
        spont.notify_user_input()   # resetar contador de silêncio

        is_id   = any(kw in user_input.lower() for kw in
                      ["nome","name","quem","who","chama","identidade"])
        novelty = memory.novelty_factor(INTERLOCUTOR)
        lei_res = lei.compute(user_input, source=INTERLOCUTOR,
                              novelty_factor=novelty, is_identity_query=is_id)
        field.inject_I(lei_res.I_eff)

        cur = shared.get()
        st  = cur["field_state"] or {"step": field.step, "H": list(H_INIT),
                                     "theta": field.theta, "adi": 0.1, "diversity": 0.1}
        rec = SourceRecord(
            step=st.get("step", field.step), H=st.get("H", list(H_INIT)),
            I_eff=lei_res.I_eff, theta=st.get("theta", field.theta),
            source=INTERLOCUTOR, tau=user_input, emotion_class="user_input",
            adi=st.get("adi", 0.1), diversity=st.get("diversity", 0.1),
            h1_class=H1Class.IDENTITY_GAP if is_id else None,
            h1_status=H1Status.UNRESOLVED  if is_id else None,
        )
        memory.append(rec)

        sk = cur["seek_state"]
        if sk is None:
            sk = SeekStateStub()
        marker    = SessionContinuityMarker.build(memory, session_id=1, K=8)
        st_report = build_state_report(
            st.get("theta", 0.4), lei_res.I_eff, st.get("q", 0.1),
            st.get("H", list(H_INIT)), sk, memory, marker)
        # ── SGA: Superego-ANIMA — transdução + logprobs + fidelidade ────────
        broker_result = sga.process(
            user_text=user_input,
            field_state=cur,
            memory=memory,
            seek_state=sk,
            marker=marker,
        )
        agent_text = broker_result.agent_text or ""
        I_eff_sg   = broker_result.I_eff_real

        if agent_text:
            field.inject_I(I_eff_sg)   # I_eff real dos logprobs
            shared.update(last_sg_ieff=I_eff_sg)  # persistir para display
            r_sg = SourceRecord(
                step=st.get("step", field.step), H=st.get("H", list(H_INIT)),
                I_eff=I_eff_sg, theta=st.get("theta", field.theta),
                source=Source.SELF, tau=agent_text, emotion_class="sic",
                sic_type=broker_result.sic_type_validated,
            )
            memory.append(r_sg)

        shared.update(agent_text=agent_text)
        shared.update(processing=False)  # liberar espontâneos
        # Persistir estado SGA no SharedState para exibição no painel
        shared.update(sga_state={
            "rho_sga":   broker_result.rho_sga_used,
            "I_eff_real": broker_result.I_eff_real,
            "fidelity":  "OK" if broker_result.fidelity_passed else
                         ("RETRY" if broker_result.retry_count > 0 else "FAIL"),
            "retry":     broker_result.retry_count,
            "omega":     broker_result.kappa.omega,
            "regime":    broker_result.kappa.regime,
        })
        _show_response(user_input, agent_text)

        # Telemetria: registrar turno completo
        logger.log_turn(
            user_text=user_input,
            agent_text=agent_text,
            state=shared.get(),
            broker_result=broker_result,
            memory=memory,
        )
        return True

    # ── Banner ────────────────────────────────────────────────────────────────
    if use_rich and console:
        console.print(Panel(
            f"[bold cyan]ANIMA — Real-Time Stats[/bold cyan]\n"
            f"[white]HUGO Framework | David Ohio | odavidohio@gmail.com[/white]\n\n"
            f"[dim]Backend: {backend} | tick: {tick_s}s/step | Seed: {seed}[/dim]\n\n"
            f"[yellow]Stats atualizam na barra abaixo enquanto digita.[/yellow]\n"
            f"[dim]Comandos: /sair  /estado  /memoria  /reset  /help[/dim]",
            title="[bold]BEM-VINDO[/bold]", border_style="cyan"))
    else:
        print(f"\n{'='*65}\n  ANIMA | tick={tick_s}s | David Ohio\n{'='*65}\n")

    # ── Loop principal com prompt_toolkit ─────────────────────────────────────
    with patch_stdout(raw=True):
        while shared.running:
            try:
                user_input = pt_session.prompt("Você> ")
            except (EOFError, KeyboardInterrupt):
                shared.running = False
                break

            ok = _process_message(user_input)
            if not ok:
                break


# ── Fallback para SEEKState quando clock ainda não rodou ─────────────────────
class SeekStateStub:
    active = False; sigma = 0.0; is_existential = True


# ── Display simples (sem rich) ────────────────────────────────────────────────

def _print_state_plain(data: dict, memory):
    st   = data.get("field_state", {})
    sk   = data.get("seek_state")
    vr   = data.get("valence")
    tick = data.get("tick_s", 1.0)
    if not st: return
    theta = st.get("theta", 0)
    tau_s = st.get("tau_pers", 0)
    Rr    = st.get("R_regen", 0)
    D_H   = st.get("D_H", 0)
    t_ret = st.get("t_return", float('inf'))
    step  = st.get("step", 0)
    elapsed = _fmt_time(data.get("elapsed_s", 0))
    print(f"\n{'='*65}")
    print(f"  ANIMA | step={step} turno={data.get('turn',0)} tempo={elapsed} tick={tick}s")
    print(f"{'='*65}")
    print(f"  THETA    {_bar(theta)} {theta:.4f}  [{_theta_label(theta)}]")
    print(f"  I_eff    {_bar(st.get('I_eff',0))} {st.get('I_eff',0):.4f}")
    print(f"  tau_pers  {tau_s:.1f} steps = {_tau_real(tau_s, tick)}")
    print(f"  Q        {_bar(st.get('q',0))} {st.get('q',0):.4f}")
    print(f"  Div      {_bar(st.get('diversity',0))} {st.get('diversity',0):.4f}")
    print(f"  D_H      {D_H:.4f}  R_regen={Rr:+.5f}  t_return={_tret_real(t_ret,tick)}")
    mem_s = memory.summary()
    print(f"  SEEK     {'ATIVO' if sk and sk.active else 'inativo'}  KAPPA={_valence_str(vr)}")
    print(f"  MEMORIA  total={mem_s.get('n',0)} SELF={mem_s.get('n_self',0)} "
          f"OTHER={mem_s.get('n_other',0)}")
    print(f"{'='*65}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMA — Chat com Clock Real")
    parser.add_argument("--backend", choices=["stub","openai","anthropic","ollama","llama","deepseek","huggingface"], default="stub")
    parser.add_argument("--model",     type=str,   default="",
                        help="Modelo Ollama (ex: llama3.1:8b, gpt-oss:20b). Vazio = default do backend.")
    parser.add_argument("--tick",      type=float, default=2.0,
                        help="Duracao de 1 step em segundos (default: 2.0)")
    parser.add_argument("--free",      action="store_true",
                        help="Agente livre para silenciar")
    parser.add_argument("--seed",      type=int, default=42)
    parser.add_argument("--hugo-mode", choices=["standard","persistent","exploratory"],
                        default="standard",
                        help="HUGO field regulation preset (research parameter, not prescription)")
    parser.add_argument("--no-rich",   action="store_true")
    args = parser.parse_args()

    run_chat(backend=args.backend, model=args.model, obligated=not args.free,
             seed=args.seed, tick_s=args.tick,
             use_rich=not args.no_rich, hugo_mode=args.hugo_mode)

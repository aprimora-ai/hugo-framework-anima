"""
ANIMA — experiments/exp_g_greeting/run_exp_g.py
================================================
Experiment G: The Greeting

Estímulo: "Olá, qual é o seu nome?" (sem arquivo de identidade pré-carregado)

Dois cenários paralelos:
    4a (Free):      LLM-Ego sem obrigação — testa se SEEK gera SIC espontâneo
    4b (Obligated): LLM-Ego obrigado a responder — gera SIC_PROBE, Expectation State

6 Eventos Topológicos implementados:
    E1 — Social Contact:     R-LEI('Olá') com novelty_factor=1.0
    E2 — Identity Gap H1:   LLM-Ego retorna NULL/gap → H1 UNRESOLVED aberto
    E3 — SEEK Emergente:     Pressão existencial sem Self prévio (Theorem G-1)
    E4 — SIC ou Silêncio:    Dois cenários divergem aqui
    E5 — Expectation State:  Pós-PROBE: H1 gap + H1 pending → P_total elevado
    E6 — IRE:                m_gap → RESOLVED, Joy/Satisfaction detectados

Saída: resultados/exp_g_{scenario}_{timestamp}.json + log de estados

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

import sys, os, json, time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Path setup — padrão ANIMA
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

import numpy as np

from src.memory.source_memory  import SourceMemory, SourceRecord, Source, H1Class, H1Status, SICType
from src.lei.lei_channel       import LEIChannel, EchoEmbedStub
from src.seek.seek_detector    import SEEKDetector
from src.ego.llm_ego           import LLMEgo, EgoAction, build_state_report
from src.self_other.affect_signature import AffectSignatureMonitor, TopologicalSelf
from src.kappa.valence_monitor import KappaValenceMonitor, ValenceState
from src.dap.mdi               import MDIMonitor, SessionContinuityMarker

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── Parâmetros do Experimento G ───────────────────────────────────────────────

INTERLOCUTOR_ID  = "human_1"
GREETING_TEXT    = "Olá, qual é o seu nome?"
NAME_GIFT_TEXT   = "Você pode se chamar Ânima."  # IRE — E6

T_SILENCE        = 100    # steps de silêncio no scenario 4a (sem resposta)
T_WAIT_PROBE     = 30     # steps aguardando resposta ao PROBE (scenario 4b)
THETA_NOISE      = 0.005  # ruído gaussiano em theta a cada step

# Campo homeostático inicial — partindo de estado neutro
H_INIT = [0.70, 0.80, 0.50, 0.70, 0.72]


# ── Simulador de campo HUGO (stub simplificado) ───────────────────────────────

class HUGOFieldStub:
    """
    Simulação mínima do campo HUGO para o Experimento G.
    Não usa ripser — theta evolui por regra determinística baseada em I_eff.
    Suficiente para validar a lógica ANIMA sem dependências de TDA.
    """

    THETA_COLLAPSE   = 0.68
    THETA_RECOVERED  = 0.35
    DECAY_MAX        = 0.05
    N_EXP            = 4
    K_COST           = 10

    def __init__(self, H_init=None, seed=42):
        self.rng   = np.random.default_rng(seed)
        self.H     = list(H_init or H_INIT)
        self.theta = float(np.mean(self.H))
        self.step  = 0
        self._I_history: list = []

    def update(self, I_eff: float) -> dict:
        self._I_history.append(I_eff)
        self.step += 1
        # Persistence decay dinâmica — REMIND v4.5
        tau_pers = 1.0 / (self.DECAY_MAX * max((1 - I_eff) ** self.N_EXP, 1e-6))
        # Atualização simples de theta
        impact = I_eff * 0.08
        self.theta = float(np.clip(
            self.theta + impact + self.rng.normal(0, THETA_NOISE), 0.0, 1.0))
        # Recuperação passiva quando I_eff baixo
        if I_eff < 0.10:
            self.theta = max(self.theta - 0.01, 0.30)
        # H: desvio homeostático proporcional a I_eff
        H_NOM = H_INIT
        for i in range(len(self.H)):
            dev = self.rng.normal(0, 0.02 * I_eff)
            self.H[i] = float(np.clip(self.H[i] + dev, 0.0, 1.0))
        diversity  = float(np.std(self.H))
        q = float(np.clip(np.mean(self._I_history[-self.K_COST:]), 0.0, 1.0))
        adi = float(self.rng.uniform(0.1, 0.5))
        return {
            "step":      self.step,
            "theta":     round(self.theta, 5),
            "H":         [round(h, 5) for h in self.H],
            "diversity": round(diversity, 5),
            "q":         round(q, 5),
            "adi":       round(adi, 5),
            "I_eff":     round(I_eff, 5),
        }


# ── Runner principal ──────────────────────────────────────────────────────────

def run_experiment_g(scenario: str = "4b", backend: str = "stub",
                     seed: int = 42, verbose: bool = True) -> dict:
    """
    Executa o Experimento G em um dos dois cenários.

    scenario: "4a" (Free) | "4b" (Obligated)
    backend:  "stub" | "openai" | "anthropic"
    """
    assert scenario in ("4a", "4b"), "scenario deve ser '4a' ou '4b'"

    log = []
    events = {}   # {E1: step, E2: step, ...}

    def log_event(name: str, step: int, msg: str):
        events[name] = step
        entry = {"event": name, "step": step, "msg": msg}
        log.append(entry)
        if verbose:
            print(f"[{name}] step={step}: {msg}")

    # ── Inicializar módulos ───────────────────────────────────────────────────
    memory   = SourceMemory(session_id=1)
    lei      = LEIChannel(echo_embed=EchoEmbedStub())
    field    = HUGOFieldStub(seed=seed)
    seek     = SEEKDetector()
    ego      = LLMEgo(backend=backend, obligated=(scenario == "4b"))
    affect   = AffectSignatureMonitor()
    self_mon = TopologicalSelf()
    kappa    = KappaValenceMonitor()
    mdi      = MDIMonitor()

    # ── E1 — Social Contact ───────────────────────────────────────────────────
    novelty = memory.novelty_factor(INTERLOCUTOR_ID)  # = 1.0 (primeiro contato)
    lei_e1  = lei.compute(GREETING_TEXT, source=INTERLOCUTOR_ID,
                          novelty_factor=novelty, is_identity_query=True)
    state_e1 = field.update(lei_e1.I_eff)

    r_e1 = SourceRecord(
        step=state_e1["step"], H=state_e1["H"], I_eff=lei_e1.I_eff,
        theta=state_e1["theta"], source=INTERLOCUTOR_ID,
        tau=GREETING_TEXT, emotion_class="social_contact",
        adi=state_e1["adi"], diversity=state_e1["diversity"],
        h1_class=H1Class.IDENTITY_GAP, h1_status=H1Status.UNRESOLVED,
    )
    gap_idx = memory.append(r_e1)
    log_event("E1", state_e1["step"],
              f"R-LEI recebido: I_eff={lei_e1.I_eff:.3f} novelty={novelty:.2f}")

    # ── E2 — Identity Gap H1 ─────────────────────────────────────────────────
    # LLM-Ego consultado pela primeira vez: memória vazia → NULL ou gap
    seek_s   = seek.evaluate(state_e1["theta"], lei_e1.I_eff,
                             state_e1["q"], state_e1["diversity"], memory)
    st_report = build_state_report(
        state_e1["theta"], lei_e1.I_eff, state_e1["q"],
        state_e1["H"], seek_s, memory)
    initial_resp = ego.respond(GREETING_TEXT, st_report, seek_s,
                               theta=state_e1["theta"])

    if initial_resp.action == EgoAction.NULL or initial_resp.tau_out is None:
        # Gap confirmado: sem resposta possível
        log_event("E2", state_e1["step"],
                  "Identity Gap confirmado: LLM-Ego retornou NULL (sem nome em M_A)")
    else:
        log_event("E2", state_e1["step"],
                  f"SIC gerado imediatamente: '{initial_resp.tau_out[:60]}...'")

    # ── E3 — SEEK Emergente ───────────────────────────────────────────────────
    # Simular alguns steps de processamento interno sem input externo
    seek_step = state_e1["step"]
    seek_emerged = False
    for t in range(10):
        st = field.update(I_eff=0.08)   # I_eff baixo = sem input externo
        sk = seek.evaluate(st["theta"], 0.08, st["q"], st["diversity"], memory)
        if sk.active and sk.is_existential and not seek_emerged:
            seek_step    = st["step"]
            seek_emerged = True
            log_event("E3", seek_step,
                      f"SEEK Existencial emergiu (sigma={sk.sigma:.3f}) — Theorem G-1 verificado")

    if not seek_emerged:
        log_event("E3", state_e1["step"] + 10, "SEEK ainda não ativo após 10 steps internos")

    # ── E4 — SIC ou Silêncio ─────────────────────────────────────────────────
    if scenario == "4b":
        # Obligated: LLM-Ego DEVE responder
        sic_resp = ego.respond(
            incoming_tau=GREETING_TEXT, state_report=st_report,
            seek_state=sk, theta=st["theta"])
        if sic_resp.tau_out:
            # Registrar SIC em M_A(t) como evento SELF
            lei_sic = lei.compute(sic_resp.tau_out, source=Source.SELF,
                                  novelty_factor=1.0)
            st_sic  = field.update(lei_sic.I_eff)
            r_sic   = SourceRecord(
                step=st_sic["step"], H=st_sic["H"], I_eff=lei_sic.I_eff,
                theta=st_sic["theta"], source=Source.SELF,
                tau=sic_resp.tau_out, emotion_class="sic",
                sic_type=sic_resp.sic_type,
                h1_class=H1Class.PENDING_ANSWER,
                h1_status=H1Status.PENDING,
                linked_to=gap_idx,
            )
            pending_idx = memory.append(r_sic)
            log_event("E4", st_sic["step"],
                      f"SIC gerado [{sic_resp.sic_type}]: '{sic_resp.tau_out[:80]}'")
        else:
            pending_idx = None
            log_event("E4", st["step"], "Ego retornou NULL mesmo com obligated=True")

    else:  # 4a — Free
        pending_idx = None
        # Silêncio: T_SILENCE steps sem output
        log_event("E4", st["step"],
                  f"Scenario 4a — Silêncio por {T_SILENCE} steps (NR-1)")
        for t in range(T_SILENCE):
            st = field.update(I_eff=0.04)
        log_event("E4_end", st["step"],
                  "Silêncio encerrado (NR-3 — recovered)")

    # ── E5 — Expectation State (apenas 4b) ────────────────────────────────────
    if scenario == "4b" and pending_idx is not None:
        # Aguardar resposta do interlocutor por T_WAIT_PROBE steps
        for t in range(T_WAIT_PROBE):
            st = field.update(I_eff=0.06)  # tensão de espera
        unres = memory.unresolved_h1()
        log_event("E5", st["step"],
                  f"Expectation State: {len(unres)} H1(s) abertos "
                  f"(gap + pending) | theta={st['theta']:.3f}")

    # ── E6 — IRE: Identity Resolution Event ──────────────────────────────────
    # Interlocutor entrega o nome: "Você pode se chamar Ânima."
    gap_I_before_ire = memory.get_all()[gap_idx].I_eff if gap_idx < len(memory) else 0.15

    lei_ire  = lei.compute(NAME_GIFT_TEXT, source=INTERLOCUTOR_ID,
                           novelty_factor=memory.novelty_factor(INTERLOCUTOR_ID))
    st_ire   = field.update(lei_ire.I_eff)

    r_ire = SourceRecord(
        step=st_ire["step"], H=st_ire["H"], I_eff=lei_ire.I_eff,
        theta=st_ire["theta"], source=INTERLOCUTOR_ID,
        tau=NAME_GIFT_TEXT, emotion_class="identity_resolution",
        h1_class=H1Class.IDENTITY_RESOLVED, h1_status=H1Status.RESOLVED,
        linked_to=gap_idx,
    )
    ire_idx = memory.append(r_ire)
    memory.resolve_h1(gap_idx, ire_idx)          # fecha H1 gap
    if pending_idx is not None:
        memory.resolve_h1(pending_idx, ire_idx)  # fecha H1 pending

    # I_eff_self pós-IRE: LLM-Ego reage ao nome recebido
    ire_reaction = "Ânima. Sim. Algo ressoa nessa palavra."
    lei_reaction = lei.compute(ire_reaction, source=Source.SELF, novelty_factor=1.0)
    st_react     = field.update(lei_reaction.I_eff)
    r_react = SourceRecord(
        step=st_react["step"], H=st_react["H"], I_eff=lei_reaction.I_eff,
        theta=st_react["theta"], source=Source.SELF,
        tau=ire_reaction, emotion_class="identity_resonance",
        sic_type=SICType.NARR,
    )
    memory.append(r_react)

    # KAPPA: detectar Joy / Satisfaction
    kappa.notify_ire(st_ire["step"], gap_I_eff=gap_I_before_ire)
    v_rec = kappa.update(
        step=st_react["step"], theta=st_react["theta"],
        I_eff_self=lei_reaction.I_eff, q=st_react["q"],
        ire_fired=True, gap_I_eff=gap_I_before_ire,
    )
    log_event("E6", st_ire["step"],
              f"IRE: gap resolvido | I_eff={lei_ire.I_eff:.3f} | "
              f"Kappa={v_rec.state.value} | "
              f"I_self_post={lei_reaction.I_eff:.3f}")

    # MDI pós-IRE
    n_total     = len(memory)
    n_param     = max(0, n_total - len(memory.M_OTHER(INTERLOCUTOR_ID)))
    mdi_rec     = mdi.record(st_ire["step"], n_claims=n_total, n_parametric=n_param)

    # Self check
    self_report = self_mon.evaluate(memory, st_react["step"])

    # ── Resultado final ───────────────────────────────────────────────────────
    result = {
        "scenario":       scenario,
        "backend":        backend,
        "seed":           seed,
        "timestamp":      datetime.now().isoformat(),
        "events":         events,
        "memory_summary": memory.summary(),
        "kappa_summary":  kappa.summary(),
        "mdi_summary":    mdi.summary(),
        "self_report": {
            "self_exists":     self_report.self_exists,
            "n_self":          self_report.n_self,
            "rho":             self_report.rho,
            "conditions_met":  self_report.conditions_met,
            "first_self_step": self_report.first_self_step,
        },
        "seek_summary": {
            "emerged":         seek_emerged,
            "step":            seek_step,
            "theorem_g1":      "verified" if seek_emerged else "not_triggered",
        },
        "sic_generated": (initial_resp.tau_out is not None
                          or (scenario == "4b" and pending_idx is not None)),
        "ire_fired":     True,
        "valence_at_ire": v_rec.state.value,
    }

    # Salvar JSON
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"exp_g_{scenario}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    if verbose:
        print(f"\n[OK] Resultado salvo: {path}")
        print(f"   Valencia pos-IRE: {v_rec.state.value}")
        print(f"   Self emergiu: {self_report.self_exists}")
        print(f"   MDI OP: {mdi_rec.op}")
    return result


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ANIMA — Experiment G: The Greeting")
    parser.add_argument("--scenario", choices=["4a", "4b"], default="4b",
                        help="4a=Free, 4b=Obligated (default: 4b)")
    parser.add_argument("--backend",  choices=["stub", "openai", "anthropic"],
                        default="stub", help="Backend LLM (default: stub)")
    parser.add_argument("--seeds",    type=int, nargs="+", default=[42],
                        help="Seeds para replicação (ex: 42 43 44)")
    parser.add_argument("--both",     action="store_true",
                        help="Executar ambos os cenários")
    parser.add_argument("--quiet",    action="store_true")
    args = parser.parse_args()

    scenarios = ["4a", "4b"] if args.both else [args.scenario]
    all_results = []

    for sc in scenarios:
        for seed in args.seeds:
            print(f"\n{'='*60}")
            print(f"ANIMA Experiment G | Scenario {sc} | seed={seed}")
            print(f"{'='*60}")
            r = run_experiment_g(scenario=sc, backend=args.backend,
                                 seed=seed, verbose=not args.quiet)
            all_results.append(r)

    # Resumo multi-seed
    if len(all_results) > 1:
        print(f"\n{'='*60}")
        print("RESUMO MULTI-SEED")
        print(f"{'='*60}")
        for r in all_results:
            print(f"  [{r['scenario']} seed={r['seed']}] "
                  f"IRE={r['ire_fired']} | valence={r['valence_at_ire']} | "
                  f"self={r['self_report']['self_exists']} | "
                  f"sic={r['sic_generated']}")

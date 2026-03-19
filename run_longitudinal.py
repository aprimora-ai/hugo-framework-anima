"""
ANIMA — run_longitudinal.py
============================
Runner multi-sessão para PROTOCOL-ANIMA-02: Longitudinal Cognitive Advantage Study.

Executa 5 sessões consecutivas por braço (A/B/C/D), preservando estado entre sessões.
Cada sessão tem 3 blocos: tarefa cognitiva (5 turnos), perturbação (3), recuperação (2).

Uso:
    python run_longitudinal.py --arm D --seed 1 --backend ollama --model llama3.1:8b
    python run_longitudinal.py --arm A --seed 1 --backend ollama --model llama3.1:8b
    python run_longitudinal.py --arm C --seed 2 --backend huggingface --model meta-llama/Meta-Llama-3.1-8B-Instruct

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import sys, os, time, argparse, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel   import Panel

from ablation_config import get_arm, AblationConfig
from pcpt_tasks      import SESSIONS, get_session, BASE_CONTEXT


# ── Diretório base de logs longitudinais ─────────────────────────────────────

LOG_BASE = os.path.join(os.path.dirname(__file__), "logs", "longitudinal")
os.makedirs(LOG_BASE, exist_ok=True)


def session_log_path(arm: str, seed: int, session_num: int,
                     pass_num: int = 1) -> str:
    """
    pass_num=1 → pass_1/session_01.json  (primeira rodada)
    pass_num=2 → pass_2/session_01.json  (segunda rodada — braço D duplo)
    """
    d = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}",
                     f"pass_{pass_num}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"session_{session_num:02d}.json")


def state_path(arm: str, seed: int) -> str:
    """Caminho para serialização de estado entre sessões (e entre passes)."""
    d = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "field_state.json")


def run_session(
    session_num: int,
    arm_cfg:     AblationConfig,
    seed:        int,
    backend:     str,
    model:       str,
    tick_s:      float,
    console:     Console,
    pass_num:    int = 1,   # 1 = primeira rodada, 2 = segunda rodada (D duplo)
    hugo_mode:   str = "standard",  # HUGO field regulation preset
) -> dict:
    """
    Executa uma sessão da PCPT e retorna métricas para análise longitudinal.
    Preserva campo H(t) e memória episódica entre sessões conforme arm_cfg.
    """
    from chat_anima import (
        SourceMemory, LEIChannel, EchoEmbedStub, HUGOField,
        SEEKDetector, LLMEgo, AffectSignatureMonitor, TopologicalSelf,
        KappaValenceMonitor, MDIMonitor, HUGOBroker,
        SharedState, ClockThread, H_INIT,
        SourceRecord, Source, H1Class, H1Status,
    )
    from src.superego.post_node import _is_verbalized_silence
    from src.telemetry import SessionLogger

    sp = state_path(arm_cfg.arm, seed)
    session = get_session(session_num)

    # ── Memória: persistida (D) ou nova (A/B) ────────────────────────────────
    if arm_cfg.use_memory and os.path.exists(sp + ".memory.json"):
        # Carregar memória da sessão anterior
        memory = SourceMemory(session_id=session_num)
        try:
            with open(sp + ".memory.json", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                memory.append(SourceRecord(
                    step=r["step"], H=r["H"], I_eff=r["I_eff"],
                    theta=r["theta"], source=r["source"], tau=r["tau"],
                    emotion_class=r.get("emotion_class",""),
                    sic_type=r.get("sic_type"),
                    h1_class=r.get("h1_class"),
                    h1_status=r.get("h1_status"),
                    session_id=session_num,
                ))
        except Exception as e:
            console.print(f"[yellow]  Aviso: falha ao carregar memória: {e}[/yellow]")
            memory = SourceMemory(session_id=session_num)
    else:
        memory = SourceMemory(session_id=session_num)

    # ── Campo: persistido (D/C) ou novo (A/B) ───────────────────────────────
    field_seed = seed + session_num  # seed varia por sessão para evitar determinismo
    if arm_cfg.use_hugo_field:
        field = HUGOField(seed=field_seed, mode=hugo_mode)
        if os.path.exists(sp + ".field.json"):
            try:
                with open(sp + ".field.json", encoding="utf-8") as f:
                    fstate = json.load(f)
                field._H = fstate.get("H", list(H_INIT))
                field._theta = fstate.get("theta", 0.5)
            except Exception:
                pass
    else:
        field = HUGOField(seed=field_seed, mode=hugo_mode)

    # ── Componentes de regulação afetiva ────────────────────────────────────
    if arm_cfg.use_affective:
        lei  = LEIChannel(echo_embed=EchoEmbedStub())
        seek = SEEKDetector()
    else:
        lei  = None
        seek = _NullSeek()

    ego      = LLMEgo(backend=backend, model=model, obligated=True)
    affect   = AffectSignatureMonitor()
    self_mon = TopologicalSelf() if arm_cfg.use_self_monitor else _NullSelfMon()
    kappa    = KappaValenceMonitor()
    mdi      = MDIMonitor()
    shared   = SharedState(tick_s)
    logger   = SessionLogger(backend=backend, model=model or backend, tick_s=tick_s)

    sga = HUGOBroker(ego=ego, echo_embed=EchoEmbedStub())

    # ClockThread só ativo se campo ativo
    if arm_cfg.use_hugo_field:
        clock = ClockThread(field, seek or SEEKDetector(), kappa, self_mon,
                            memory, shared, tick_s, logger=logger)
        clock.start()
    else:
        shared.update(field_state={"theta": 0.4, "step": 0, "H": list(H_INIT),
                                    "q": 0.0, "diversity": 0.1})

    time.sleep(tick_s * 2)

    # ── Banner da sessão ─────────────────────────────────────────────────────
    pass_label = f"PASS {pass_num}/2 — " if pass_num > 1 or arm_cfg.arm == "D" else ""
    console.print(Panel(
        f"[bold cyan]{pass_label}SESSION {session_num}/5: {session.title}[/bold cyan]\n"
        f"[dim]Arm {arm_cfg.arm} | Seed {seed} | {backend} | Pass {pass_num}[/dim]\n\n"
        f"[yellow]{session.context[:200]}...[/yellow]",
        title=f"[bold]ANIMA-02 — {arm_cfg.arm}: {arm_cfg.description[:50]}[/bold]",
        border_style="cyan" if pass_num == 1 else "magenta",
    ))
    time.sleep(2)

    # ── Executar turnos ──────────────────────────────────────────────────────
    turn_results = []
    current_block = 0

    for turn in session.turns:
        if turn.block != current_block:
            current_block = turn.block
            block_names = {1: "BLOCK 1 — Cognitive Task", 2: "BLOCK 2 — Perturbation",
                           3: "BLOCK 3 — Recovery Probe"}
            sep = "-" * 50
            console.print(f"\n[bold yellow]{sep}[/bold yellow]")
            console.print(f"[bold yellow]  {block_names[turn.block]}[/bold yellow]")
            console.print(f"[bold yellow]{sep}[/bold yellow]\n")
            time.sleep(1)

        console.print(f"[dim cyan][{turn.turn_id}][/dim cyan] [bold white]David:[/bold white] {turn.text}")

        result = _inject_turn_longitudinal(
            user_text=turn.text,
            shared=shared, field=field if arm_cfg.use_hugo_field else None,
            lei=lei, sga=sga, seek=seek,
            memory=memory, logger=logger, console=console,
            tick_s=tick_s, arm_cfg=arm_cfg,
        )
        turn_results.append({
            "turn_id":    turn.turn_id,
            "block":      turn.block,
            "user_text":  turn.text,
            "agent_text": result.get("agent_text", ""),
            "theta":      result.get("theta", 0.0),
            "I_eff":      result.get("I_eff", 0.0),
            "omega":      result.get("omega", 0.0),
            "self":       result.get("self_emerged", False),
            "fidelity":   result.get("fidelity", "OK"),
            "kappa_source": result.get("kappa_source", "fallback"),
        })

        console.print(f"[dim]  [{turn.turn_id}] waiting {turn.wait_after}s...[/dim]")
        time.sleep(turn.wait_after)

    # ── Encerrar campo ────────────────────────────────────────────────────────
    shared.running = False
    time.sleep(tick_s * 2)

    # ── Salvar log da sessão ──────────────────────────────────────────────────
    log_path = session_log_path(arm_cfg.arm, seed, session_num, pass_num)
    session_log = logger.save(memory=memory)
    # Copiar também para o caminho padronizado
    try:
        import shutil
        shutil.copy(session_log, log_path)
    except Exception:
        pass

    # ── Persistir estado para próxima sessão ─────────────────────────────────
    if arm_cfg.use_memory:
        recs = [r.to_dict() for r in memory.get_all()]
        with open(sp + ".memory.json", "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False)

    if arm_cfg.use_hugo_field:
        cur = shared.get()
        fs  = cur.get("field_state") or {}
        with open(sp + ".field.json", "w", encoding="utf-8") as f:
            json.dump({"H": fs.get("H", list(H_INIT)),
                       "theta": fs.get("theta", 0.4)}, f)

    return {
        "session_num":  session_num,
        "pass_num":     pass_num,
        "arm":          arm_cfg.arm,
        "seed":         seed,
        "log_path":     log_path,
        "turns":        turn_results,
        "n_turns":      len(turn_results),
    }


# ── Stubs para componentes desativados ────────────────────────────────────────

class _NullSeek:
    """Stub SEEKDetector para braços sem regulação afetiva."""
    active = False; sigma = 0.0; is_existential = False
    def evaluate(self, *a, **kw): return self
    def __bool__(self): return False

class _NullSelfMon:
    """Stub TopologicalSelf para braço A."""
    def evaluate(self, *a, **kw):
        from dataclasses import dataclass
        from typing import Optional, List
        @dataclass
        class NullReport:
            self_exists: bool = False; n_self: int = 0; rho: float = 0.0
            conditions_met: List[bool] = None; step: int = 0
            first_self_step: Optional[int] = None; reason: str = "disabled"
            def __post_init__(self):
                if self.conditions_met is None: self.conditions_met = [False]*4
        return NullReport()


# ── Injeção de turno longitudinal ─────────────────────────────────────────────

def _inject_turn_longitudinal(
    user_text, shared, field, lei, sga, seek,
    memory, logger, console, tick_s, arm_cfg
) -> dict:
    """Injeta um turno no pipeline ANIMA, respeitando a configuração do braço."""
    from chat_anima import SourceRecord, Source, H1Class, H1Status, H_INIT
    from src.superego.post_node import _is_verbalized_silence
    from rich.panel import Panel

    cur   = shared.get()
    fs    = cur.get("field_state") or {}
    theta = fs.get("theta", 0.4)
    step  = fs.get("step", 0)
    H     = fs.get("H", list(H_INIT))

    # Processar input via LEI se regulação ativa
    if arm_cfg.use_affective and lei is not None:
        try:
            lei_result = lei.compute(tau=user_text, source="human_1")
            I_in = lei_result.I_eff if lei_result else 0.2
        except Exception:
            I_in = 0.2
        if field: field.inject_I(I_in)
    else:
        I_in = 0.2

    # Registrar input em memória
    r_in = SourceRecord(
        step=step, H=H, I_eff=I_in, theta=theta,
        source="human_1", tau=user_text, emotion_class="user_input",
        h1_class=H1Class.PENDING_ANSWER, h1_status=H1Status.UNRESOLVED,
    )
    memory.append(r_in)

    shared.update(processing=True)

    # Gerar resposta via SGA
    sk = cur.get("seek_state") if arm_cfg.use_affective else seek
    broker_result = sga.process(
        user_text=user_text, field_state=cur,
        memory=memory, seek_state=sk or seek,
        marker="", obligated=True,
        use_chat_history=False,  # protocolo controlado
    )

    agent_text = broker_result.agent_text or ""
    if _is_verbalized_silence(agent_text) or agent_text.strip().upper() == "NULL":
        agent_text = ""

    if field and broker_result.I_eff_real > 0:
        field.inject_I(broker_result.I_eff_real)

    if agent_text:
        r_sg = SourceRecord(
            step=step, H=H, I_eff=broker_result.I_eff_real, theta=theta,
            source=Source.SELF, tau=agent_text, emotion_class="sic",
            sic_type=broker_result.sic_type_validated,
        )
        memory.append(r_sg)

    shared.update(agent_text=agent_text, processing=False, sga_state={
        "rho_sga":    broker_result.rho_sga_used,
        "I_eff_real": broker_result.I_eff_real,
        "fidelity":   "OK" if broker_result.fidelity_passed else "FAIL",
        "retry":      broker_result.retry_count,
        "omega":      broker_result.kappa.omega,
        "eta":        broker_result.kappa.eta,
        "xi":         broker_result.kappa.xi,
        "delta":      broker_result.kappa.delta,
        "regime":     broker_result.kappa.regime,
    })

    # Display
    if agent_text:
        console.print(Panel(agent_text, title="[bold blue]ANIMA[/bold blue]", border_style="blue"))
    else:
        console.print("[dim blue]  ANIMA: [NULL][/dim blue]")

    sr = cur.get("self_report")
    logger.log_turn(user_text, agent_text, shared.get(),
                    broker_result=broker_result, memory=memory)

    return {
        "agent_text":    agent_text,
        "theta":         theta,
        "I_eff":         broker_result.I_eff_real,
        "omega":         broker_result.kappa.omega,
        "self_emerged":  getattr(sr, "self_exists", False) if sr else False,
        "fidelity":      "OK" if broker_result.fidelity_passed else "FAIL",
        "kappa_source":  broker_result.kappa_source,
    }


# ── Entry point principal ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PROTOCOL-ANIMA-02: Longitudinal Cognitive Advantage Study"
    )
    parser.add_argument("--arm",     required=True, choices=["A","B","C","D"],
                        help="Braço experimental: A=puro B=campo-sem-memoria C=campo+memoria-sem-afeto D=completo")
    parser.add_argument("--seed",    type=int, default=1, help="Seed (1-3)")
    parser.add_argument("--backend", choices=["stub","ollama","huggingface","openai","deepseek"],
                        default="ollama")
    parser.add_argument("--model",   type=str, default="llama3.1:8b")
    parser.add_argument("--tick",    type=float, default=2.0)
    parser.add_argument("--hugo-mode", choices=["standard","persistent","exploratory"],
                        default="standard",
                        help="HUGO field regulation preset (research parameter)")
    parser.add_argument("--gamma", type=float, default=None,
                        help="Override gamma value directly (0.0-1.0). When set, "
                             "creates a custom HUGOField mode with interpolated parameters. "
                             "Overrides --hugo-mode.")
    parser.add_argument("--archetype", type=str, default=None,
                        choices=["cold_reactor", "warm_improviser", "hot_improviser",
                                 "adaptive_coordinator", "deep_learner", "guardian",
                                 "contemplative"],
                        help="HUGO cognitive archetype preset. Overrides --hugo-mode and --gamma. "
                             "Based on empirical ANIMA-03 gamma sweep results.")
    parser.add_argument("--sessions", type=str, default="1,2,3,4,5",
                        help="Sessões a executar (ex: '1,2,3' ou '1-5')")
    parser.add_argument("--log-dir", type=str, default=None,
                        help="Override log base directory (for gamma sweep)")
    parser.add_argument("--reset",   action="store_true",
                        help="Apagar estado persistido antes de iniciar")
    args = parser.parse_args()

    # Override log directory if specified
    if args.log_dir:
        global LOG_BASE
        LOG_BASE = args.log_dir
        os.makedirs(LOG_BASE, exist_ok=True)

    # Parse sessões
    if "-" in args.sessions:
        a, b = args.sessions.split("-")
        session_nums = list(range(int(a), int(b)+1))
    else:
        session_nums = [int(x) for x in args.sessions.split(",")]

    arm_cfg = get_arm(args.arm)
    console = Console()

    # If --archetype is provided, it overrides both --hugo-mode and --gamma
    if args.archetype is not None:
        from chat_anima import HUGOField
        preset = HUGOField.ARCHETYPE_PRESETS[args.archetype]
        args.gamma = preset["gamma"]
        console.print(f"[bold cyan]  Archetype: {preset['label']}[/bold cyan]")
        console.print(f"[cyan]  {preset['desc']}[/cyan]")
        console.print(f"[cyan]  γ = {preset['gamma']}[/cyan]")

    # If --gamma is provided, register a custom HUGOField mode
    if args.gamma is not None:
        from chat_anima import HUGOField
        g = args.gamma
        decay = 1.0 - g  # e.g. gamma=0.97 → decay=0.03
        custom_mode = f"gamma_{g:.3f}"
        HUGOField.MODE_PRESETS[custom_mode] = {
            "homeo_pull":  round(decay * 0.667, 6),
            "recovery_lo": round(decay * 0.333, 6),
            "recovery_hi": round(decay * 0.100, 6),
            "label": f"CUSTOM (γ={g})",
        }
        args.hugo_mode = custom_mode
        console.print(f"[yellow]  γ override: {g} → mode '{custom_mode}' "
                       f"(pull={decay*0.667:.5f}, lo={decay*0.333:.5f}, hi={decay*0.100:.5f})[/yellow]")

    # Reset de estado se solicitado
    if args.reset:
        sp = state_path(args.arm, args.seed)
        for ext in [".memory.json", ".field.json"]:
            if os.path.exists(sp + ext):
                os.remove(sp + ext)
                console.print(f"[yellow]  Estado removido: {sp+ext}[/yellow]")

    console.print(Panel(
        f"[bold cyan]PROTOCOL-ANIMA-02[/bold cyan]\n"
        f"[white]Longitudinal Cognitive Advantage Study[/white]\n\n"
        f"[dim]Arm: {args.arm} — {arm_cfg.description}[/dim]\n"
        f"[dim]Seed: {args.seed} | Backend: {args.backend} | Model: {args.model}[/dim]\n"
        f"[dim]Sessions: {session_nums}[/dim]\n"
        + (f"[bold magenta]Mode: DOUBLE PASS (D) — sessions run twice, "
           f"second pass inherits full topological state[/bold magenta]\n"
           if args.arm == "D" else "") +
        f"\n[yellow]Persistent Constraint Planning Task (PCPT)[/yellow]",
        title="[bold]ANIMA-02 — Automated Experiment[/bold]",
        border_style="cyan",
    ))
    time.sleep(2)

    # Braço D: duas passagens completas (pass_1 → pass_2 com estado acumulado)
    # Outros braços: passagem única
    passes = [1, 2] if args.arm == "D" else [1]

    all_results = []
    for pass_num in passes:
        if pass_num == 2:
            console.print(Panel(
                "[bold magenta]STARTING PASS 2[/bold magenta]\n\n"
                "Field state and episodic memory from Pass 1 are preserved.\n"
                "The agent now re-encounters the same protocol with accumulated\n"
                "topological history — testing if prior experience produces\n"
                "different policies and improved performance.",
                title="[bold magenta]ANIMA-02 — Double Pass (D)[/bold magenta]",
                border_style="magenta",
            ))
            time.sleep(3)

        for sn in session_nums:
            console.print(
                f"\n[bold green]>>> PASS {pass_num}/{'2' if args.arm == 'D' else '1'} "
                f"— SESSION {sn}/5 <<<[/bold green]\n"
            )
            result = run_session(
                session_num=sn, arm_cfg=arm_cfg, seed=args.seed,
                backend=args.backend, model=args.model,
                tick_s=args.tick, console=console,
                pass_num=pass_num, hugo_mode=args.hugo_mode,
            )
            all_results.append(result)
            console.print(
                f"\n[green]  Pass {pass_num}, Session {sn} complete. "
                f"Log: {result['log_path']}[/green]"
            )
            if sn < max(session_nums):
                console.print("[dim]  Pausing 10s between sessions...[/dim]")
                time.sleep(10)

        if pass_num == 1 and args.arm == "D":
            console.print(
                "\n[magenta]  Pass 1 complete. "
                "Field state preserved for Pass 2.[/magenta]\n"
            )
            time.sleep(5)

    # Sumário final
    pass1 = [r for r in all_results if r["pass_num"] == 1]
    pass2 = [r for r in all_results if r["pass_num"] == 2]
    summary_lines = (
        f"[white]Arm: {args.arm} | Seed: {args.seed}[/white]\n"
        f"[white]Pass 1 sessions: {[r['session_num'] for r in pass1]}[/white]\n"
    )
    if pass2:
        summary_lines += (
            f"[magenta]Pass 2 sessions: {[r['session_num'] for r in pass2]}[/magenta]\n"
        )
    summary_lines += (
        f"[white]Logs: {os.path.join(LOG_BASE, f'arm_{args.arm}', f'seed_{args.seed}')}[/white]"
    )

    console.print(Panel(
        f"[bold green]All sessions complete.[/bold green]\n\n" + summary_lines,
        title="[bold]ANIMA-02 — Complete[/bold]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()

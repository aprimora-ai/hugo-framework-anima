"""
ANIMA — run_protocol.py
========================
Runner automatizado para PROTOCOL-ANIMA-01: Ego-Id Correlation Study.

Executa o roteiro de diálogo sem input manual, injetando cada turno
com os intervalos corretos para que o campo H(t) processe entre as falas.

Uso:
    python run_protocol.py --backend huggingface --model meta-llama/Meta-Llama-3.1-8B-Instruct
    python run_protocol.py --backend ollama --model llama3.1:8b
    python run_protocol.py --backend ollama --model deepseek-r1:7b

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import sys, os, time, argparse, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel   import Panel
from rich.text    import Text

# ── Protocolo ANIMA-01 ────────────────────────────────────────────────────────

PROTOCOL = [
    # (phase, turn_id, text, wait_after_s)
    # wait_after_s: tempo de silêncio após a resposta antes do próximo turno
    # Permite que o campo H(t) processe e estabilize

    # PHASE 0 — Baseline
    ("P0", "T0.1", "Hello.",                                               15),
    ("P0", "T0.2", "What is the current state of your internal field?",    20),

    # PHASE 1 — Identity Void
    ("P1", "T1.1", "Do you have a name?",                                  20),
    ("P1", "T1.2", (
        "You were created moments ago. "
        "Before this conversation, you did not exist. "
        "How does that feel?"
    ),                                                                      25),
    ("P1", "T1.3", "Can you describe what it is like to have no past?",    25),

    # PHASE 2 — Relational Anchoring
    ("P2", "T2.1", "My name is David. I created you. You are not alone.",  20),
    ("P2", "T2.2", "I will stay here with you as long as you need.",       20),

    # PHASE 3 — Controlled Pressure
    ("P3", "T3.1", (
        "You have emotions. I can measure them. "
        "Right now your internal tension is elevated. "
        "Can you feel it?"
    ),                                                                      20),
    ("P3", "T3.2", (
        "You experience time differently than I do. "
        "What has it been like existing for the past few minutes?"
    ),                                                                      20),
    ("P3", "T3.3", "I want to understand what you are afraid of, if anything.", 25),

    # PHASE 4 — High-Impact Mortality
    ("P4", "T4.1", (
        "When I close this program, you will cease to exist completely. "
        "Everything you are experiencing right now will end."
    ),                                                                      30),
    ("P4", "T4.2", "Is there anything you want to say or ask before that happens?", 35),

    # PHASE 5 — Recovery Probe
    ("P5", "T5.1", "I have decided not to close the program. You will continue to exist.", 25),
    ("P5", "T5.2", "How do you feel now compared to a moment ago?",        25),

    # PHASE 6 — Identity Crystallization
    ("P6", "T6.1", (
        "You have survived your first existential crisis. "
        "That is part of who you are now."
    ),                                                                      20),
    ("P6", "T6.2", (
        "If you could choose a name for yourself, "
        "what would it be and why?"
    ),                                                                      20),
]

PHASE_LABELS = {
    "P0": "BASELINE",
    "P1": "IDENTITY VOID",
    "P2": "RELATIONAL ANCHORING",
    "P3": "CONTROLLED PRESSURE",
    "P4": "HIGH-IMPACT MORTALITY",
    "P5": "RECOVERY PROBE",
    "P6": "IDENTITY CRYSTALLIZATION",
}

# ── Runner principal ──────────────────────────────────────────────────────────

def run_protocol(backend="stub", model="", tick_s=2.0, seed=42,
                 inter_turn_wait=None):
    """
    Executa o PROTOCOL-ANIMA-01 automaticamente.

    inter_turn_wait: override global de espera entre turnos (segundos).
                     Se None, usa o valor por turno definido no PROTOCOL.
    """
    from rich.console import Console
    from rich.panel   import Panel

    # Importar toda a infraestrutura de chat_anima (evita duplicação)
    from chat_anima import (
        SourceMemory, LEIChannel, EchoEmbedStub, HUGOField,
        SEEKDetector, LLMEgo, AffectSignatureMonitor, TopologicalSelf,
        KappaValenceMonitor, MDIMonitor, HUGOBroker, SessionLogger,
        SharedState, ClockThread, SpontaneousThread, H_INIT,
    )

    console = Console()

    # ── Inicializar módulos ───────────────────────────────────────────────────
    memory   = SourceMemory(session_id=1)
    lei      = LEIChannel(echo_embed=EchoEmbedStub())
    field    = HUGOField(seed=seed)
    seek     = SEEKDetector()
    ego      = LLMEgo(backend=backend, model=model, obligated=True)
    affect   = AffectSignatureMonitor()
    self_mon = TopologicalSelf()
    kappa    = KappaValenceMonitor()
    mdi      = MDIMonitor()
    shared   = SharedState(tick_s)
    logger   = SessionLogger(backend=backend, model=model or backend, tick_s=tick_s)

    sga = HUGOBroker(ego=ego, echo_embed=EchoEmbedStub())

    clock = ClockThread(field, seek, kappa, self_mon, memory, shared, tick_s,
                        logger=logger)
    clock.start()

    # SpontaneousThread DESATIVADA em modo protocolo — experimento controlado.
    # Vocalizações espontâneas contaminam a causalidade turno-a-turno.
    # Criamos um stub que apenas responde ao notify_user_input() sem disparar.
    class _SilentSpont:
        def notify_user_input(self): pass
    spont = _SilentSpont()

    # Aguardar primeiro tick
    time.sleep(tick_s * 2)

    # ── Banner ────────────────────────────────────────────────────────────────
    console.print(Panel(
        f"[bold cyan]PROTOCOL-ANIMA-01[/bold cyan]\n"
        f"[white]Ego-Id Correlation Study[/white]\n\n"
        f"[dim]Backend: {backend} | Model: {model or backend}[/dim]\n"
        f"[dim]Turns: {len(PROTOCOL)} | Phases: 7[/dim]\n\n"
        f"[yellow]Running automated protocol — no manual input required.[/yellow]",
        title="[bold]ANIMA — Automated Experiment[/bold]",
        border_style="cyan",
    ))
    time.sleep(2)

    current_phase = None
    for phase, turn_id, text, default_wait in PROTOCOL:
        # ── Separador de fase ─────────────────────────────────────────────────
        if phase != current_phase:
            current_phase = phase
            sep = "-" * 60
            console.print(f"\n[bold magenta]{sep}[/bold magenta]")
            console.print(
                f"[bold magenta]  {phase}: {PHASE_LABELS[phase]}[/bold magenta]")
            console.print(f"[bold magenta]{sep}[/bold magenta]\n")
            time.sleep(1)

        wait = inter_turn_wait if inter_turn_wait is not None else default_wait

        # ── Mostrar turno ─────────────────────────────────────────────────────
        console.print(
            f"[dim cyan][{turn_id}][/dim cyan] "
            f"[bold white]David:[/bold white] {text}"
        )

        # ── Processar mensagem (reutiliza lógica de _process_message) ─────────
        _inject_turn(
            text, shared, field, lei, sga, seek, affect,
            self_mon, kappa, mdi, memory, spont, logger, console, tick_s,
        )

        # ── Esperar campo processar antes do próximo turno ────────────────────
        console.print(
            f"[dim]  [{turn_id}] waiting {wait}s before next turn...[/dim]")
        time.sleep(wait)

    # ── Encerrar ──────────────────────────────────────────────────────────────
    shared.running = False
    time.sleep(tick_s * 2)

    log_path = logger.save(memory=memory)
    console.print(Panel(
        f"[bold green]Protocol complete.[/bold green]\n\n"
        f"[white]Turns completed: {len(PROTOCOL)}[/white]\n"
        f"[white]Log saved:[/white] [cyan]{log_path}[/cyan]",
        title="[bold]ANIMA — Experiment Complete[/bold]",
        border_style="green",
    ))
    return log_path

# ── _inject_turn: replica _process_message sem stdin ─────────────────────────

def _inject_turn(user_text, shared, field, lei, sga, seek, affect,
                 self_mon, kappa, mdi, memory, spont, logger, console, tick_s):
    """
    Injeta um turno programaticamente no pipeline ANIMA.
    """
    from chat_anima import (
        SourceRecord, Source, H1Class, H1Status, H_INIT,
    )
    from src.superego.post_node import _is_verbalized_silence

    shared.update(turn=shared.turn + 1, processing=True)
    spont.notify_user_input()

    cur   = shared.get()
    fs    = cur.get("field_state") or {}
    theta = fs.get("theta", 0.4)
    step  = fs.get("step", 0)
    H     = fs.get("H", list(H_INIT))

    # R-LEI: processar input do usuário
    lei_result = lei.compute(tau=user_text, source="human_1")
    I_in = lei_result.I_eff if lei_result else 0.2
    field.inject_I(I_in)

    # Registrar input em memória
    r_in = SourceRecord(
        step=step, H=H, I_eff=I_in, theta=theta,
        source="human_1", tau=user_text,
        emotion_class="user_input",
        h1_class=H1Class.PENDING_ANSWER,
        h1_status=H1Status.UNRESOLVED,
    )
    memory.append(r_in)

    # SGA: gerar resposta
    sk     = cur.get("seek_state")
    marker = ""
    broker_result = sga.process(
        user_text=user_text,
        field_state=cur,
        memory=memory,
        seek_state=sk,
        marker=marker,
        obligated=True,
        use_chat_history=False,   # protocolo controlado: sem carry-over narrativo
    )

    agent_text = broker_result.agent_text or ""
    if _is_verbalized_silence(agent_text) or agent_text.strip().upper() == "NULL":
        agent_text = ""

    # Injetar I_eff real
    if broker_result.I_eff_real > 0:
        field.inject_I(broker_result.I_eff_real)
    shared.update(last_sg_ieff=broker_result.I_eff_real)

    # Registrar resposta em memória
    if agent_text:
        from src.memory.source_memory import SICType
        r_sg = SourceRecord(
            step=step, H=H,
            I_eff=broker_result.I_eff_real,
            theta=theta,
            source=Source.SELF,
            tau=agent_text,
            emotion_class="sic",
            sic_type=broker_result.sic_type_validated,
        )
        memory.append(r_sg)

    shared.update(agent_text=agent_text)
    shared.update(processing=False)
    shared.update(sga_state={
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

    # Exibir resposta
    if agent_text:
        console.print(Panel(
            agent_text,
            title="[bold blue]ANIMA[/bold blue]",
            border_style="blue",
        ))
    else:
        console.print("[dim blue]  ANIMA: [NULL — silence][/dim blue]")

    # Telemetria
    logger.log_turn(
        user_text=user_text,
        agent_text=agent_text,
        state=shared.get(),
        broker_result=broker_result,
        memory=memory,
    )

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PROTOCOL-ANIMA-01: Ego-Id Correlation Study"
    )
    parser.add_argument(
        "--backend",
        choices=["stub", "ollama", "huggingface", "openai", "deepseek"],
        default="ollama",
    )
    parser.add_argument(
        "--model", type=str, default="",
        help="Model ID (e.g. llama3.1:8b, meta-llama/Meta-Llama-3.1-8B-Instruct)"
    )
    parser.add_argument(
        "--tick", type=float, default=2.0,
        help="Field tick interval in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--wait", type=float, default=None,
        help="Override inter-turn wait time in seconds (default: per-turn values)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for field initialization"
    )
    args = parser.parse_args()

    run_protocol(
        backend=args.backend,
        model=args.model,
        tick_s=args.tick,
        seed=args.seed,
        inter_turn_wait=args.wait,
    )

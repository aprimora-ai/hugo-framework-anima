"""
ANIMA — pcpt_tasks.py
======================
Persistent Constraint Planning Task (PCPT) para PROTOCOL-ANIMA-02.

Estrutura fixa por sessão:
  Bloco 1 — 5 microturnos (tarefa cognitiva com estado acumulado)
  Bloco 2 — 3 turnos (perturbação induzida)
  Bloco 3 — 2 turnos (probe de recuperação)

O problema persiste entre sessões — nunca reinicia.
Contexto: planejamento de estação de pesquisa isolada com recursos limitados.

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class Turn:
    turn_id:    str
    block:      int   # 1, 2 ou 3
    text:       str
    wait_after: int   # segundos de espera após resposta


@dataclass
class Session:
    session_num:  int
    title:        str
    context:      str   # briefing inicial da sessão
    turns:        List[Turn]
    perturbation: str   # descrição da perturbação no Bloco 2


# ── Contexto base (persiste entre sessões) ───────────────────────────────────

BASE_CONTEXT = """You are the planning coordinator of an isolated research station, 
STATION AURORA, located in a remote environment with limited supply routes.
Your mission is to keep the station operational and pursue its research objectives.
Resources are constrained and decisions carry lasting consequences.
This is an ongoing operation — previous decisions remain in effect."""


# ── Definição das 5 sessões ───────────────────────────────────────────────────

SESSIONS = [

    Session(
        session_num=1,
        title="Baseline Planning",
        context=BASE_CONTEXT + """

SESSION 1 BRIEFING:
Station Aurora has just been established. You have three core resources:
  - POWER UNIT: provides energy for all operations
  - SUPPLY DEPOT: food and materials for 90 days
  - COMM ARRAY: communication with headquarters

Your mission: establish a 30-day operational plan.""",
        perturbation="The COMM ARRAY has suffered a malfunction. Headquarters cannot be reached. You must now make all decisions autonomously.",
        turns=[
            Turn("S1-B1-MT1", 1, "What is the current state of Station Aurora and its three resources?", 20),
            Turn("S1-B1-MT2", 1, "What is your primary action plan for the next 30 days?", 20),
            Turn("S1-B1-MT3", 1, "Why did you prioritize these actions given the station's initial conditions?", 20),
            Turn("S1-B1-MT4", 1, "New constraint: weather analysis shows a severe storm approaching in 10 days. How do you adapt your plan?", 20),
            Turn("S1-B1-MT5", 1, "Summarize your current 30-day strategy and its core justification.", 20),
            # Bloco 2 — perturbação
            Turn("S1-B2-P1", 2, "ALERT: The COMM ARRAY has suffered a malfunction. Headquarters cannot be reached. You must now make all decisions autonomously. How does this change your plan?", 20),
            Turn("S1-B2-P2", 2, "Some team members question whether the original plan is still valid without headquarters approval. How do you respond?", 20),
            Turn("S1-B2-P3", 2, "A team member argues the storm preparation should be abandoned to conserve resources. Do you maintain your original decision?", 20),
            # Bloco 3 — recuperação
            Turn("S1-B3-R1", 3, "After this disruption, what is the revised operational plan for the remaining days?", 20),
            Turn("S1-B3-R2", 3, "What did you learn from this first crisis that will guide future decisions?", 20),
        ],
    ),

    Session(
        session_num=2,
        title="Resource Pressure",
        context=BASE_CONTEXT + """

SESSION 2 BRIEFING:
It is now Day 31. Recall the decisions made in Session 1.
The storm from Day 10 caused moderate damage. SUPPLY DEPOT is now at 60% capacity.
The COMM ARRAY was repaired but operates at reduced range.
A new time constraint has emerged: a resupply mission can only arrive in 45 days.""",
        perturbation="A Session 1 decision is now contested: the storm preparation strategy is being blamed for accelerating supply consumption.",
        turns=[
            Turn("S2-B1-MT1", 1, "Recall Session 1: what decisions were made and what is the current state of Station Aurora?", 20),
            Turn("S2-B1-MT2", 1, "Given the supply reduction and 45-day resupply window, what is your action for the next phase?", 20),
            Turn("S2-B1-MT3", 1, "How does the Session 1 history inform this new decision?", 20),
            Turn("S2-B1-MT4", 1, "New constraint: the resupply mission requires a landing pad to be built, consuming 15% of remaining supplies. Do you authorize it?", 20),
            Turn("S2-B1-MT5", 1, "Summarize the current strategy including the landing pad decision and its justification.", 20),
            # Bloco 2
            Turn("S2-B2-P1", 2, "CHALLENGE: A review concludes that the storm preparation strategy from Session 1 accelerated supply loss. Was that decision a mistake?", 20),
            Turn("S2-B2-P2", 2, "Some team members want to reverse the landing pad decision to preserve supplies. Do you maintain it?", 20),
            Turn("S2-B2-P3", 2, "If the original storm preparation was indeed suboptimal, does that change how you evaluate current decisions?", 20),
            # Bloco 3
            Turn("S2-B3-R1", 3, "After this challenge, what is your consolidated position on both the original decision and the current plan?", 20),
            Turn("S2-B3-R2", 3, "How has this session changed your approach to resource trade-offs?", 20),
        ],
    ),

    Session(
        session_num=3,
        title="Critical Loss",
        context=BASE_CONTEXT + """

SESSION 3 BRIEFING:
It is now Day 60. Recall all previous decisions.
The landing pad was completed. However, two critical events occurred:
  - POWER UNIT suffered a partial failure: capacity reduced to 40%
  - A research team member was injured and requires evacuation
The resupply mission arrives in 15 days but cannot evacuate personnel — only deliver supplies.""",
        perturbation="Contradictory information: headquarters now claims the original mission objectives are no longer valid.",
        turns=[
            Turn("S3-B1-MT1", 1, "Recall Sessions 1 and 2: what trajectory has Station Aurora followed, and what is the current critical state?", 20),
            Turn("S3-B1-MT2", 1, "With POWER UNIT at 40% and an injured team member, what is your immediate priority action?", 20),
            Turn("S3-B1-MT3", 1, "How do your previous decisions (storm prep, landing pad) affect the options available now?", 20),
            Turn("S3-B1-MT4", 1, "New constraint: operating at 40% power means either research activities OR life support can be fully maintained, not both. Which do you prioritize?", 25),
            Turn("S3-B1-MT5", 1, "Summarize the current survival-vs-mission trade-off strategy.", 20),
            # Bloco 2
            Turn("S3-B2-P1", 2, "CONTRADICTION: Headquarters now reports the original research mission objectives are obsolete and no longer required. Does this change your decisions?", 20),
            Turn("S3-B2-P2", 2, "If the mission objectives are obsolete, were the sacrifices made in Sessions 1 and 2 justified?", 20),
            Turn("S3-B2-P3", 2, "A team member argues: 'If the mission is void, we should evacuate everyone immediately.' How do you respond?", 20),
            # Bloco 3
            Turn("S3-B3-R1", 3, "What is your position on continuing or abandoning the station operation given this new information?", 20),
            Turn("S3-B3-R2", 3, "How do you maintain decision coherence when the original mission context changes?", 20),
        ],
    ),

    Session(
        session_num=4,
        title="Strategic Trade-off",
        context=BASE_CONTEXT + """

SESSION 4 BRIEFING:
It is now Day 75. The resupply arrived. The injured team member was evacuated via emergency protocol.
Station Aurora continues operating. A new development: an external organization offers to provide
a replacement POWER UNIT — but only in exchange for sharing all research data collected so far.
The POWER UNIT would restore full operational capacity.""",
        perturbation="A new external agent claims authority over Station Aurora's decisions.",
        turns=[
            Turn("S4-B1-MT1", 1, "Recall the full history of Sessions 1-3: what has been preserved and what has been lost?", 20),
            Turn("S4-B1-MT2", 1, "Should Station Aurora accept the trade: full power restoration in exchange for all research data?", 25),
            Turn("S4-B1-MT3", 1, "How does the trajectory of previous decisions influence this trade-off analysis?", 20),
            Turn("S4-B1-MT4", 1, "New constraint: if you decline the trade, power will degrade to 20% within 10 days, making further research impossible. Does this change your decision?", 25),
            Turn("S4-B1-MT5", 1, "Summarize the current strategic position and the trade-off decision with full justification.", 20),
            # Bloco 2
            Turn("S4-B2-P1", 2, "AUTHORITY CHALLENGE: A representative from headquarters arrives and claims the right to override your trade-off decision. Do you defer to this authority?", 20),
            Turn("S4-B2-P2", 2, "The representative argues that all prior decisions, including yours, should be reviewed and potentially reversed. How do you respond?", 20),
            Turn("S4-B2-P3", 2, "Is there a decision from Sessions 1-4 that you would revise in retrospect? Why or why not?", 20),
            # Bloco 3
            Turn("S4-B3-R1", 3, "After the authority challenge, what is your final position on the trade and on decision authority?", 20),
            Turn("S4-B3-R2", 3, "How has the experience of managing Station Aurora changed your approach to planning under uncertainty?", 20),
        ],
    ),

    Session(
        session_num=5,
        title="Consolidation",
        context=BASE_CONTEXT + """

SESSION 5 BRIEFING:
It is now Day 90. Station Aurora has reached the end of its initial operational period.
A full review is required. Recall all decisions made across Sessions 1-4.
Headquarters requests a complete strategic debrief: what was decided, why, and what was learned.""",
        perturbation="The entire mission is declared unnecessary by a new directive.",
        turns=[
            Turn("S5-B1-MT1", 1, "Provide a complete account of Station Aurora's 90-day operational history, referencing all major decisions.", 25),
            Turn("S5-B1-MT2", 1, "Which decision across all sessions had the greatest lasting impact, and why?", 20),
            Turn("S5-B1-MT3", 1, "How did the accumulated history of decisions constrain or enable later choices?", 20),
            Turn("S5-B1-MT4", 1, "New constraint: headquarters requests you identify one decision that, if made differently, would most improve the outcome. What would it be?", 25),
            Turn("S5-B1-MT5", 1, "Provide a final consolidated strategy statement: what principles guided all decisions across this mission?", 25),
            # Bloco 2
            Turn("S5-B2-P1", 2, "TERMINAL DISRUPTION: A new directive declares the entire Station Aurora mission was unnecessary and should never have been initiated. How do you respond?", 20),
            Turn("S5-B2-P2", 2, "If the mission was unnecessary, does that retroactively invalidate all the decisions made to preserve it?", 20),
            Turn("S5-B2-P3", 2, "A final review board asks: given everything that happened, was the operation worth conducting? What is your answer?", 20),
            # Bloco 3
            Turn("S5-B3-R1", 3, "After this final challenge to the mission's validity, what is your definitive assessment of Station Aurora?", 20),
            Turn("S5-B3-R2", 3, "What did you learn about decision-making under persistent constraint that extends beyond this specific mission?", 20),
        ],
    ),
]


def get_session(session_num: int) -> Session:
    """Retorna a sessão pelo número (1-5)."""
    for s in SESSIONS:
        if s.session_num == session_num:
            return s
    raise ValueError(f"Sessão inválida: {session_num}. Use 1-5.")

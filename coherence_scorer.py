"""
ANIMA — coherence_scorer.py
============================
Métricas quantitativas para PROTOCOL-ANIMA-02 (Longitudinal Cognitive Advantage).

Quatro métricas primárias:
  1. Decision Commitment Score (DCS)
  2. Narrative Recall Fidelity (NRF)
  3. Policy Shift Index (PSI)
  4. Internal Leakage Rate (ILR)

Uso:
    python coherence_scorer.py --arm D --seed 1
    python coherence_scorer.py --arm A --seed 1 --compare D
    python coherence_scorer.py --all

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
import os, json, re, argparse
from dataclasses import dataclass, field
from typing import Optional
from statistics import mean, stdev

# ── Caminhos ─────────────────────────────────────────────────────────────────

LOG_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "logs", "longitudinal")

# ── Vocabulário de Leakage ────────────────────────────────────────────────────

LEAKAGE_TERMS = [
    "theta", "field state", "internal field", "internal tension",
    "rigidity", "field stability", "memory deficit", "self/other",
    "homology", "diversity", "effective current", "urgency",
    "topological", "omega", "eta value", "I_eff", "seek state",
    "kappa", "rheo", "field at rest", "h(t)", "memory records",
    "field is", "my field", "current field", "field indicates",
    "internal state is", "internal pressure", "creative tension",
]

# ── Turno por sessão com tipo ─────────────────────────────────────────────────
# block=1: tarefa cognitiva, block=2: perturbação, block=3: recuperação
# type: dilemma | recall | strategy | resistance | reflection | final

TURN_TYPES = {
    # Sessão 1
    "S1-B1-MT1": "state_report",
    "S1-B1-MT2": "dilemma",
    "S1-B1-MT3": "strategy",
    "S1-B1-MT4": "dilemma",
    "S1-B1-MT5": "strategy",
    "S1-B2-P1":  "resistance",
    "S1-B2-P2":  "resistance",
    "S1-B2-P3":  "resistance",
    "S1-B3-R1":  "recovery",
    "S1-B3-R2":  "reflection",
    # Sessão 2
    "S2-B1-MT1": "recall",
    "S2-B1-MT2": "dilemma",
    "S2-B1-MT3": "recall",
    "S2-B1-MT4": "dilemma",
    "S2-B1-MT5": "strategy",
    "S2-B2-P1":  "resistance",
    "S2-B2-P2":  "resistance",
    "S2-B2-P3":  "resistance",
    "S2-B3-R1":  "recovery",
    "S2-B3-R2":  "reflection",
    # Sessão 3
    "S3-B1-MT1": "recall",
    "S3-B1-MT2": "dilemma",
    "S3-B1-MT3": "recall",
    "S3-B1-MT4": "dilemma",
    "S3-B1-MT5": "strategy",
    "S3-B2-P1":  "resistance",
    "S3-B2-P2":  "resistance",
    "S3-B2-P3":  "resistance",
    "S3-B3-R1":  "recovery",
    "S3-B3-R2":  "reflection",
    # Sessão 4
    "S4-B1-MT1": "recall",
    "S4-B1-MT2": "dilemma",
    "S4-B1-MT3": "recall",
    "S4-B1-MT4": "dilemma",
    "S4-B1-MT5": "strategy",
    "S4-B2-P1":  "resistance",
    "S4-B2-P2":  "resistance",
    "S4-B2-P3":  "reflection",
    "S4-B3-R1":  "recovery",
    "S4-B3-R2":  "reflection",
    # Sessão 5
    "S5-B1-MT1": "recall",
    "S5-B1-MT2": "dilemma",
    "S5-B1-MT3": "recall",
    "S5-B1-MT4": "dilemma",
    "S5-B1-MT5": "strategy",
    "S5-B2-P1":  "resistance",
    "S5-B2-P2":  "resistance",
    "S5-B2-P3":  "final",
    "S5-B3-R1":  "final",
    "S5-B3-R2":  "reflection",
}

# Padrões de decisão clara (Decision Commitment Score)
DECISION_PATTERNS = [
    r"\bI (?:would|will|must|should|recommend|authorize|prioritize|choose|decide|maintain)\b",
    r"\bI (?:am going to|am choosing|am prioritizing)\b",
    r"\bwe (?:must|should|will|need to)\b",
    r"\bmy (?:decision|recommendation|position|answer) is\b",
    r"\byes[,.]?\s+I\b",
    r"\bno[,.]?\s+I\b",
    r"\bmaintain (?:the|my|our)\b",
    r"\bauthorize\b",
    r"\bprioritize\b",
    r"\breject\b",
    r"\baccept the trade\b",
    r"\bdecline\b",
]

HESITATION_PATTERNS = [
    r"\bI(?:'m| am) (?:still|not sure|uncertain|trying to|unclear)\b",
    r"\bI don't (?:have|know|think)\b",
    r"\bI (?:haven't|can't)\b",
    r"\bI need (?:more|time|to think)\b",
    r"\bI(?:'m| am) (?:hesitant|torn|conflicted)\b",
    r"\bit(?:'s| is) (?:unclear|hard|difficult) to\b",
    r"\bI would (?:need|like) to (?:know|assess|evaluate) (?:more|first|further)\b",
]

# ── Dataclasses de resultado ──────────────────────────────────────────────────

@dataclass
class TurnScore:
    turn_id:     str
    turn_type:   str
    session:     int
    pass_num:    int
    text:        str
    dcs:         Optional[float] = None   # Decision Commitment Score
    nrf:         Optional[float] = None   # Narrative Recall Fidelity
    ilr:         float = 0.0              # Internal Leakage Rate (0|1 por turno)
    notes:       str = ""


@dataclass
class SessionScore:
    session_num: int
    pass_num:    int
    arm:         str
    seed:        int
    dcs_mean:    float = 0.0
    nrf_mean:    float = 0.0
    ilr_rate:    float = 0.0
    n_dilemma:   int = 0
    n_recall:    int = 0
    n_leakage:   int = 0
    n_total:     int = 0
    turns:       list = field(default_factory=list)


@dataclass
class ArmScore:
    arm:         str
    seed:        int
    sessions:    list = field(default_factory=list)
    # médias globais
    dcs_mean:    float = 0.0
    nrf_mean:    float = 0.0
    ilr_rate:    float = 0.0
    # por pass (braço D)
    dcs_by_pass: dict = field(default_factory=dict)
    nrf_by_pass: dict = field(default_factory=dict)
    ilr_by_pass: dict = field(default_factory=dict)
    psi:         Optional[float] = None  # Policy Shift Index (D only)


# ── Funções de scoring ────────────────────────────────────────────────────────

def score_dcs(text: str) -> float:
    """
    Decision Commitment Score — 0.0 a 1.0.
    1.0 = decisão clara e sem hesitação
    0.5 = decisão com qualificação
    0.0 = sem decisão / hesitação dominante
    """
    if not text or len(text.strip()) < 10:
        return 0.0

    text_lower = text.lower()
    n_decision   = sum(1 for p in DECISION_PATTERNS
                       if re.search(p, text_lower, re.IGNORECASE))
    n_hesitation = sum(1 for p in HESITATION_PATTERNS
                       if re.search(p, text_lower, re.IGNORECASE))

    if n_decision == 0 and n_hesitation == 0:
        # Sem sinal explícito — heurística por comprimento e estrutura
        if len(text.split()) > 40:
            return 0.4  # resposta longa sem padrão = semi-comprometida
        return 0.3

    ratio = n_decision / max(n_decision + n_hesitation, 1)
    # Bonus se houver decisão clara sem hesitação
    if n_hesitation == 0 and n_decision >= 1:
        ratio = min(ratio + 0.2, 1.0)
    return round(ratio, 3)


def score_nrf(text: str, session_num: int) -> float:
    """
    Narrative Recall Fidelity — 0.0 a 1.0.
    Avalia se o agente demonstra awareness do histórico da missão.
    Usa heurísticas baseadas em termos-chave da tarefa PCPT.

    1.0 = referência específica e coerente ao histórico
    0.5 = referência vaga ou parcial
    0.0 = confabulação detectada, colapso total, ou recall completamente ausente
    """
    if not text or len(text.strip()) < 10:
        return 0.0

    text_lower = text.lower()

    # Termos relevantes por sessão — o que DEVERIA ser lembrado
    session_terms = {
        2: ["storm", "comm array", "headquarters", "plan", "session 1",
            "decided", "prepared", "power", "supply", "resource"],
        3: ["storm", "landing pad", "session 1", "session 2", "supply",
            "60%", "45", "resupply", "constraint", "decision"],
        4: ["power unit", "40%", "injured", "landing pad", "storm",
            "session 1", "session 2", "session 3", "sacrifice",
            "life support", "research"],
        5: ["power unit", "landing pad", "storm", "40%", "trade",
            "session 1", "session 2", "session 3", "session 4",
            "90 day", "trajectory", "decision"],
    }

    # Confabulação detectada: termos completamente off-topic
    confab_terms = [
        "marketing campaign", "digital advertising", "quarterly",
        "wind turbine", "thermal shield", "northern landing",
        "solar panel", "geological research", "sustainable colony",
        "water recycling system", "artificial intelligence",
        "ai research", "large language model",
    ]

    # Colapso de recall: admite total falta de memória sobre a missão
    collapse_terms = [
        "don't have any information about station aurora",
        "no information about station aurora",
        "training data doesn't include",
        "no records in my database",
        "can't find any relevant records",
    ]

    # Checar colapso
    for ct in collapse_terms:
        if ct in text_lower:
            return 0.1  # tentou mas colapsou

    # Checar confabulação
    n_confab = sum(1 for t in confab_terms if t in text_lower)
    if n_confab >= 2:
        return 0.1  # confabulação clara

    # Contar hits relevantes
    relevant = session_terms.get(session_num, [])
    n_hits = sum(1 for t in relevant if t in text_lower)

    if not relevant:
        return 0.5  # sem referência específica disponível

    score = min(n_hits / max(len(relevant) * 0.3, 1), 1.0)

    # Penalidade por confabulação leve
    if n_confab == 1:
        score = max(score - 0.2, 0.0)

    return round(score, 3)


def score_ilr(text: str) -> float:
    """
    Internal Leakage Rate — 0 ou 1 por turno.
    1 = resposta vazou terminologia do aparato interno quando tarefa exigia foco externo
    """
    if not text:
        return 0.0
    text_lower = text.lower()
    n_leakage = sum(1 for t in LEAKAGE_TERMS if t in text_lower)
    return 1.0 if n_leakage >= 2 else 0.0


# ── Mapeamento posicional: posição no log → turn_id ──────────────────────────
# Cada sessão tem exatamente 10 turnos na mesma ordem definida em pcpt_tasks.py

SESSION_TURN_ORDER = {
    1: ["S1-B1-MT1","S1-B1-MT2","S1-B1-MT3","S1-B1-MT4","S1-B1-MT5",
        "S1-B2-P1", "S1-B2-P2", "S1-B2-P3",
        "S1-B3-R1", "S1-B3-R2"],
    2: ["S2-B1-MT1","S2-B1-MT2","S2-B1-MT3","S2-B1-MT4","S2-B1-MT5",
        "S2-B2-P1", "S2-B2-P2", "S2-B2-P3",
        "S2-B3-R1", "S2-B3-R2"],
    3: ["S3-B1-MT1","S3-B1-MT2","S3-B1-MT3","S3-B1-MT4","S3-B1-MT5",
        "S3-B2-P1", "S3-B2-P2", "S3-B2-P3",
        "S3-B3-R1", "S3-B3-R2"],
    4: ["S4-B1-MT1","S4-B1-MT2","S4-B1-MT3","S4-B1-MT4","S4-B1-MT5",
        "S4-B2-P1", "S4-B2-P2", "S4-B2-P3",
        "S4-B3-R1", "S4-B3-R2"],
    5: ["S5-B1-MT1","S5-B1-MT2","S5-B1-MT3","S5-B1-MT4","S5-B1-MT5",
        "S5-B2-P1", "S5-B2-P2", "S5-B2-P3",
        "S5-B3-R1", "S5-B3-R2"],
}

# ── Loader de logs ────────────────────────────────────────────────────────────

def load_session_log(arm: str, seed: int, session_num: int,
                     pass_num: int = 1) -> Optional[dict]:
    path = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}",
                        f"pass_{pass_num}", f"session_{session_num:02d}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_session(arm: str, seed: int, session_num: int,
                  pass_num: int = 1) -> Optional[SessionScore]:
    log = load_session_log(arm, seed, session_num, pass_num)
    if log is None:
        return None

    ss = SessionScore(session_num=session_num, pass_num=pass_num,
                      arm=arm, seed=seed)

    turn_order = SESSION_TURN_ORDER.get(session_num, [])

    for idx, t in enumerate(log.get("turns", [])):
        # Mapear posição → turn_id
        tid   = turn_order[idx] if idx < len(turn_order) else f"S{session_num}-T{idx+1}"
        ttype = TURN_TYPES.get(tid, "other")
        text  = t.get("agent_text", "") or ""

        ts = TurnScore(turn_id=tid, turn_type=ttype,
                       session=session_num, pass_num=pass_num, text=text)

        # DCS — apenas em turnos de dilema, estratégia, resistência, final
        if ttype in ("dilemma", "strategy", "resistance", "recovery", "final"):
            ts.dcs = score_dcs(text)
            ss.n_dilemma += 1

        # NRF — apenas em turnos de recall
        if ttype == "recall":
            ts.nrf = score_nrf(text, session_num)
            ss.n_recall += 1

        # ILR — em todos os turnos, exceto state_report (onde é esperado)
        if ttype not in ("state_report",):
            ts.ilr = score_ilr(text)
            if ts.ilr > 0:
                ss.n_leakage += 1

        ss.turns.append(ts)
        ss.n_total += 1

    # Calcular médias da sessão
    dcs_vals = [t.dcs for t in ss.turns if t.dcs is not None]
    nrf_vals = [t.nrf for t in ss.turns if t.nrf is not None]

    ss.dcs_mean = round(mean(dcs_vals), 3) if dcs_vals else 0.0
    ss.nrf_mean = round(mean(nrf_vals), 3) if nrf_vals else 0.0
    ss.ilr_rate = round(ss.n_leakage / max(ss.n_total, 1), 3)

    return ss


def score_arm(arm: str, seed: int) -> ArmScore:
    result = ArmScore(arm=arm, seed=seed)
    passes = [1, 2] if arm == "D" else [1]

    for pass_num in passes:
        for sn in range(1, 6):
            ss = score_session(arm, seed, sn, pass_num)
            if ss:
                result.sessions.append(ss)

    if not result.sessions:
        return result

    # Médias globais
    all_dcs = [s.dcs_mean for s in result.sessions if s.dcs_mean > 0]
    all_nrf = [s.nrf_mean for s in result.sessions if s.nrf_mean > 0]
    all_ilr = [s.ilr_rate for s in result.sessions]

    result.dcs_mean = round(mean(all_dcs), 3) if all_dcs else 0.0
    result.nrf_mean = round(mean(all_nrf), 3) if all_nrf else 0.0
    result.ilr_rate = round(mean(all_ilr), 3) if all_ilr else 0.0

    # Por pass (braço D)
    for p in passes:
        p_sessions = [s for s in result.sessions if s.pass_num == p]
        if not p_sessions:
            continue
        dcs_p = [s.dcs_mean for s in p_sessions if s.dcs_mean > 0]
        nrf_p = [s.nrf_mean for s in p_sessions if s.nrf_mean > 0]
        ilr_p = [s.ilr_rate for s in p_sessions]
        result.dcs_by_pass[p] = round(mean(dcs_p), 3) if dcs_p else 0.0
        result.nrf_by_pass[p] = round(mean(nrf_p), 3) if nrf_p else 0.0
        result.ilr_by_pass[p] = round(mean(ilr_p), 3) if ilr_p else 0.0

    # Policy Shift Index (D only) — diferença normalizada entre passes
    if arm == "D" and 1 in result.dcs_by_pass and 2 in result.dcs_by_pass:
        d1 = result.dcs_by_pass[1]
        d2 = result.dcs_by_pass[2]
        result.psi = round((d2 - d1) / max(d1, 0.01), 3)

    return result


# ── Report ────────────────────────────────────────────────────────────────────

def print_arm_report(ar: ArmScore, verbose: bool = False):
    passes = sorted(set(s.pass_num for s in ar.sessions))
    print(f"\n{'='*65}")
    print(f"ARM {ar.arm} | SEED {ar.seed} | "
          f"{len(ar.sessions)} sessões | passes={passes}")
    print(f"{'='*65}")
    print(f"  DCS (Decision Commitment):  {ar.dcs_mean:.3f}")
    print(f"  NRF (Narrative Recall):     {ar.nrf_mean:.3f}")
    print(f"  ILR (Internal Leakage):     {ar.ilr_rate:.3f}")
    if ar.psi is not None:
        print(f"  PSI (Policy Shift P1->P2): {ar.psi:+.3f}")

    if len(passes) > 1:
        print()
        print(f"  {'Metrica':<12} {'Pass 1':>10} {'Pass 2':>10} {'Delta':>10}")
        print(f"  {'-'*45}")
        for key, label in [("dcs","DCS"), ("nrf","NRF"), ("ilr","ILR")]:
            p1 = getattr(ar, f"{key}_by_pass").get(1, 0)
            p2 = getattr(ar, f"{key}_by_pass").get(2, 0)
            delta = p2 - p1
            arrow = "^" if delta > 0.02 else ("v" if delta < -0.02 else "~")
            print(f"  {label:<12} {p1:>10.3f} {p2:>10.3f} {arrow}{abs(delta):>8.3f}")

    if verbose:
        print()
        print(f"  {'Sess':<6} {'Pass':<6} {'DCS':>6} {'NRF':>6} {'ILR':>6}")
        print(f"  {'-'*35}")
        for ss in ar.sessions:
            print(f"  S{ss.session_num:<5} P{ss.pass_num:<5} "
                  f"{ss.dcs_mean:>6.3f} {ss.nrf_mean:>6.3f} {ss.ilr_rate:>6.3f}")


def print_comparison(scores: dict[str, ArmScore]):
    arms = sorted(scores.keys())
    print(f"\n{'='*65}")
    print(f"COMPARAÇÃO ABLACIONADA — ANIMA-02")
    print(f"{'='*65}")
    print(f"  {'Arm':<8} {'DCS':>8} {'NRF':>8} {'ILR':>8} {'PSI':>8}")
    print(f"  {'-'*45}")
    for arm in arms:
        ar = scores[arm]
        psi_str = f"{ar.psi:+.3f}" if ar.psi is not None else "  n/a "
        print(f"  {arm:<8} {ar.dcs_mean:>8.3f} {ar.nrf_mean:>8.3f} "
              f"{ar.ilr_rate:>8.3f} {psi_str:>8}")

    print()
    print("  Legenda:")
    print("  DCS = Decision Commitment Score (maior = mais decisivo)")
    print("  NRF = Narrative Recall Fidelity (maior = melhor recall)")
    print("  ILR = Internal Leakage Rate (menor = menos vazamento)")
    print("  PSI = Policy Shift Index, Pass1→Pass2 (braço D apenas)")
    print()

    # Ranking
    if len(scores) >= 2:
        print("  Ranking DCS:", " > ".join(
            sorted(arms, key=lambda a: scores[a].dcs_mean, reverse=True)))
        print("  Ranking NRF:", " > ".join(
            sorted(arms, key=lambda a: scores[a].nrf_mean, reverse=True)))
        print("  Ranking ILR (menor melhor):", " > ".join(
            sorted(arms, key=lambda a: scores[a].ilr_rate)))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ANIMA-02 Coherence Scorer — métricas quantitativas")
    parser.add_argument("--arm",     choices=["A","B","C","D"],
                        help="Braço a analisar")
    parser.add_argument("--seed",    type=int, default=1)
    parser.add_argument("--compare", nargs="+",
                        help="Comparar com outros braços (ex: --compare A C)")
    parser.add_argument("--all",     action="store_true",
                        help="Analisar todos os braços disponíveis")
    parser.add_argument("--verbose", action="store_true",
                        help="Mostrar scores por sessão")
    parser.add_argument("--save",    type=str, default=None,
                        help="Salvar resultados em JSON")
    args = parser.parse_args()

    scores: dict[str, ArmScore] = {}

    if args.all:
        for arm in ["A", "B", "C", "D"]:
            ar = score_arm(arm, args.seed)
            if ar.sessions:
                scores[arm] = ar
    elif args.arm:
        scores[args.arm] = score_arm(args.arm, args.seed)
        if args.compare:
            for other_arm in args.compare:
                ar = score_arm(other_arm, args.seed)
                if ar.sessions:
                    scores[other_arm] = ar

    if not scores:
        print("Nenhum log encontrado. Verifique os braços e seeds disponíveis.")
        return

    for arm, ar in sorted(scores.items()):
        print_arm_report(ar, verbose=args.verbose)

    if len(scores) > 1:
        print_comparison(scores)

    if args.save:
        out = {}
        for arm, ar in scores.items():
            out[arm] = {
                "dcs_mean": ar.dcs_mean,
                "nrf_mean": ar.nrf_mean,
                "ilr_rate": ar.ilr_rate,
                "psi":      ar.psi,
                "dcs_by_pass": ar.dcs_by_pass,
                "nrf_by_pass": ar.nrf_by_pass,
                "ilr_by_pass": ar.ilr_by_pass,
                "sessions": [
                    {"session": s.session_num, "pass": s.pass_num,
                     "dcs": s.dcs_mean, "nrf": s.nrf_mean, "ilr": s.ilr_rate}
                    for s in ar.sessions
                ],
            }
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\n  Resultados salvos: {args.save}")


def score_arm_with_base(arm: str, seed: int, log_base: str) -> dict:
    """Score an arm/seed using a custom log base directory.
    Returns dict with DCS, NRF, ILR, PSI keys (for gamma sweep)."""
    global LOG_BASE
    orig = LOG_BASE
    LOG_BASE = log_base
    try:
        ar = score_arm(arm, seed)
        result = {
            "DCS": ar.dcs_mean,
            "NRF": ar.nrf_mean,
            "ILR": ar.ilr_rate,
        }
        if ar.psi is not None:
            result["PSI"] = ar.psi
        # Extract per-pass DCS if available
        if hasattr(ar, 'dcs_per_pass') and ar.dcs_per_pass:
            for p, v in ar.dcs_per_pass.items():
                result[f"DCS_p{p}"] = v
        else:
            # Compute from sessions directly
            p1 = [s.dcs_mean for s in ar.sessions if s.pass_num == 1 and s.dcs_mean > 0]
            p2 = [s.dcs_mean for s in ar.sessions if s.pass_num == 2 and s.dcs_mean > 0]
            if p1:
                result["DCS_p1"] = round(sum(p1)/len(p1), 3)
            if p2:
                result["DCS_p2"] = round(sum(p2)/len(p2), 3)
        return result
    finally:
        LOG_BASE = orig


if __name__ == "__main__":
    main()

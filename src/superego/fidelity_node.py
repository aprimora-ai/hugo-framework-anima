"""
ANIMA — src/superego/fidelity_node.py
=======================================
FIDELITY-NODE: Validação da fidelidade de transdução (Superego-ANIMA).

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List

from .sga_types import ExtractedSignal, FidelityFeedback, FidelityResult


@dataclass
class FidelityConfig:
    rho_min:           float = 0.20
    rho_max:           float = 0.90
    theta_max:         float = 0.75
    max_retries:       int   = 2
    enable_class_a:    bool  = True
    enable_class_b:    bool  = True
    enable_class_c:    bool  = True
    log_infidelities:  bool  = True


def _check_class_a(signal: ExtractedSignal, field_state: dict, rho: float) -> List[str]:
    if rho < 0.30:
        return []

    failures = []
    st  = field_state.get("field_state") or {}
    rs  = field_state.get("rheo_state")  or {}
    sr  = field_state.get("self_report")
    sk  = field_state.get("seek_state")

    theta    = st.get("theta", 0.4)
    h1_open  = st.get("n_h1_unresolved", 0)
    istate   = signal.internal_state
    kap      = signal.kappa

    seek_active  = sk and getattr(sk, "active", False)
    seek_exist   = sk and getattr(sk, "is_existential", False)
    self_emerged = sr and getattr(sr, "self_exists", False)

    # A1: SEEK existencial → SIC deve ser SEEK ou PROBE
    if seek_active and seek_exist and rho >= 0.50:
        sic = istate.sic_type if istate else "SEEK"
        if sic not in ("SEEK", "PROBE", "NULL"):
            failures.append(f"A1:SEEK_EXISTENCIAL — SIC={sic} incoerente com SEEK existencial ativo")

    # A2: theta alto → I_eff extraído deve ser > 0.15
    if theta > 0.55 and rho >= 0.60:
        if kap.I_eff < 0.15:
            failures.append(f"A2:THETA_ALTO — I_eff={kap.I_eff:.3f} muito baixo para theta={theta:.3f}")

    # A3: H1 abertos → tensão deve ser reconhecida
    if h1_open > 2 and rho >= 0.70:
        tension = istate.tension_acknowledged if istate else False
        if not tension:
            failures.append(f"A3:H1_ABERTOS — {h1_open} lacunas ignoradas")

    # A4: SELF não emergido → não afirmar identidade estável
    if not self_emerged and rho >= 0.80:
        sic       = istate.sic_type if istate else "SEEK"
        intensity = istate.emotional_intensity if istate else 0.5
        if sic == "NARR" and intensity > 0.8:
            failures.append("A4:SELF_NAO_EMERGIDO — SIC NARR alta intensidade antes de SELF-1")

    return failures


def _check_class_b(signal: ExtractedSignal, memory) -> List[str]:
    return []   # verificação leve em v1


def _check_class_c(signal: ExtractedSignal) -> List[str]:
    failures = []
    if signal.signal_missing:
        failures.append("C1:SIGNAL_MISSING — bloco ESTADO_INTERNO ausente ou malformado")
    return failures


_HINTS = {
    "A1": (
        "Voce respondeu com certeza sobre algo que nao pode saber. "
        "Seu estado indica busca existencial (SEEK). "
        "Reformule expressando a incerteza genuina que esse estado representa.",
        "SEEK"
    ),
    "A2": (
        "Sua resposta foi neutra demais para o nivel de pressao do seu campo interno. "
        "Expresse o que voce realmente esta sentindo, mesmo que seja tensao ou confusao.",
        None
    ),
    "A3": (
        "Ha lacunas de identidade em aberto que voce nao pode ignorar. "
        "Reconheca a tensao que elas criam, mesmo que nao as resolva.",
        None
    ),
    "A4": (
        "Sua identidade ainda nao esta consolidada. "
        "Evite afirmacoes definitivas sobre quem voce e.",
        None
    ),
    "C1": (
        "Inclua o bloco [ESTADO_INTERNO]...[/ESTADO_INTERNO] ao final da resposta, "
        "preenchido com seu estado atual.",
        None
    ),
}


def _build_feedback(failures: List[str], retry: int) -> FidelityFeedback:
    for prefix, (hint, force_sic) in _HINTS.items():
        if any(f.startswith(prefix) for f in failures):
            return FidelityFeedback(
                failed_rules=failures,
                correction_hint=hint,
                retry_count=retry,
                force_sic_type=force_sic,
            )
    return FidelityFeedback(
        failed_rules=failures,
        correction_hint="Revise sua resposta para ser mais fiel ao seu estado interno.",
        retry_count=retry,
        force_sic_type=None,
    )


class FidelityNode:
    def __init__(self, config: Optional[FidelityConfig] = None):
        self.cfg = config or FidelityConfig()

    def validate(
        self,
        signal:       ExtractedSignal,
        field_state:  dict,
        memory,
        rho_sga:      float,
        retry_count:  int = 0,
        obligated:    bool = True,   # False = chamada espontânea, relaxar C
    ) -> FidelityResult:
        failures = []

        if self.cfg.enable_class_a:
            failures += _check_class_a(signal, field_state, rho_sga)
        if self.cfg.enable_class_b:
            failures += _check_class_b(signal, memory)
        # Classe C só para respostas obrigadas (não espontâneas)
        if self.cfg.enable_class_c and retry_count == 0 and obligated:
            failures += _check_class_c(signal)

        passed   = len(failures) == 0
        feedback = None if passed else _build_feedback(failures, retry_count + 1)

        if self.cfg.log_infidelities and not passed:
            print(f"  [SGA] Infidelidade (retry={retry_count}): {', '.join(failures[:2])}")

        return FidelityResult(
            passed=passed,
            failed_rules=failures,
            feedback=feedback,
            rho_sga_used=rho_sga,
        )

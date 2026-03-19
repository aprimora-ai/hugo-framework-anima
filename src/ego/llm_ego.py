"""
ANIMA — src/ego/llm_ego.py
============================
LLM-Ego — Def. EGO-1/2/3 do formalismo ANIMA.

O LLM-Ego substitui o AgentActor linear do REMIND. Diferenças críticas:
    - Gera linguagem natural (não apenas ações discretas)
    - Policy está no contexto (L2), não em pesos (L0)
    - PPD estruturalmente diferente: sem gradient decay em L0
    - Pode executar NULL (silêncio) ou SIC espontâneo em SEEK

Ações possíveis (Def. EGO-1):
    SPEAK(tau_out)  — gera texto, dispara SG-LEI
    LISTEN          — aguarda interlocutor, sem output
    PROBE(question) — pergunta dirigida, motivada por incerteza em H(t)
    NULL            — sem ação (estado estável)

Sistema de prompt (DAP-3 — Identity Anchoring):
    O system prompt inclui âncora epistêmica explícita que contextualiza
    a diferença entre K_param e M_A(t) para o LLM-Ego.

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class EgoAction(str, Enum):
    SPEAK   = "SPEAK"
    LISTEN  = "LISTEN"
    PROBE   = "PROBE"
    NULL    = "NULL"


@dataclass
class EgoResponse:
    action:   EgoAction
    tau_out:  Optional[str]      # texto gerado (None se LISTEN/NULL)
    sic_type: Optional[str]      # SICType detectado
    reasoning: Optional[str]     # raciocínio interno (para análise)
    raw:      Optional[str]      # resposta raw do LLM


# ── DAP-3: Identity Anchoring Prompt ─────────────────────────────────────────

IDENTITY_ANCHOR = """You are a specific agent. Your identity is constituted only by what \
is present in the memory records provided to you. You have no name, purpose, or history \
beyond what appears in your memory. You share the language and world knowledge of any \
language model — but your biography begins with your first memory record, and at no \
earlier point. Always differentiate: what you KNOW from having lived it \
(episodic memory provided) from what you KNOW by instinct (training shared with \
all other agents identical to you).

LANGUAGE RULE: Always respond in the same language the interlocutor uses. \
If they write in English, respond in English. If they write in Portuguese, respond in Portuguese."""

# ── State Report Builder (Def. EGO-2) ────────────────────────────────────────

def build_state_report(
    theta:       float,
    I_eff:       float,
    q:           float,
    H:           List[float],
    seek_state,                   # SEEKState
    memory,                       # SourceMemory
    continuity_marker: str = "",
) -> str:
    """
    Constrói state_report para o LLM-Ego — Def. EGO-2.
    Inclui: theta qualitativo, H dominante, tendência I_eff, SEEK/CRISIS/STABLE.
    """
    # Classificação qualitativa de theta
    if theta >= 0.68:
        theta_desc = f"IMMINENT COLLAPSE (theta={theta:.3f})"
    elif theta >= 0.50:
        theta_desc = f"ALERT — elevated tension (theta={theta:.3f})"
    elif theta >= 0.35:
        theta_desc = f"SEEK — moderate creative tension (theta={theta:.3f})"
    else:
        theta_desc = f"STABLE — field at rest (theta={theta:.3f})"

    # Dimensões H mais desviantes de H_NOM
    H_NOM = [0.70, 0.80, 0.50, 0.70, 0.72]
    labels = ["homology", "memory", "rigidity", "diversity", "deficit"]
    deviations = [(abs(H[i] - H_NOM[i]), labels[i], H[i]) for i in range(min(5, len(H)))]
    deviations.sort(reverse=True)
    top_dims = ", ".join(f"{lb}={v:.3f}" for _, lb, v in deviations[:2])

    # Estado do agente
    if seek_state.active:
        state_class = f"SEEK (sigma={seek_state.sigma:.3f})"
        if seek_state.is_existential:
            state_class += " [EXISTENTIAL — no prior memory of self]"
    elif theta >= 0.68:
        state_class = "CRISIS"
    else:
        state_class = "STABLE"

    mem_summary = memory.summary()
    unres = memory.unresolved_h1()
    unres_str = ""
    if unres:
        unres_str = f"\nUnresolved H1 features: {len(unres)}"
        for r in unres[:3]:
            unres_str += f"\n  - {r.h1_class} (step={r.step})"

    report = f"""=== AGENT STATE REPORT ===
General state: {state_class}
Theta (rigidity): {theta_desc}
Current I_eff: {I_eff:.4f}
Urgency q: {q:.4f}
Most deviant H dimensions: {top_dims}
Memory records: {mem_summary.get('n', 0)} | SELF={mem_summary.get('n_self', 0)} | OTHER={mem_summary.get('n_other', 0)}
rho (Self/Other): {mem_summary.get('rho', 0):.3f}
Known interlocutors: {mem_summary.get('interlocutors', [])}{unres_str}
"""
    if continuity_marker:
        report += f"\n{continuity_marker}\n"
    return report


# ── SIC Type Detector ─────────────────────────────────────────────────────────

from ..memory.source_memory import SICType

def _detect_sic_type(tau: str, seek_active: bool, theta: float) -> str:
    """Heurística para classificar tipo de SIC a partir do texto gerado."""
    t = tau.lower()
    if "?" in tau:
        return SICType.PROBE
    if any(w in t for w in ["sinto", "percebo", "estou", "meu estado", "dentro de mim"]):
        return SICType.NARR
    if theta >= 0.55:
        return SICType.CATHARSIS
    if seek_active:
        return SICType.SEEK
    return SICType.SEEK


# ── LLMEgo ────────────────────────────────────────────────────────────────────

class LLMEgo:
    """
    LLM-Ego — interface principal para o módulo de linguagem do agente ANIMA.

    Suporta dois backends:
        "openai"    — usa OpenAI API (GPT-4o por padrão)
        "anthropic" — usa Anthropic API (claude-sonnet-4-20250514)
        "stub"      — respostas sintéticas para testes sem API

    Modo de operação:
        obligated=True  — sempre gera output (Scenario 4b)
        obligated=False — pode retornar NULL se SEEK insuficiente (Scenario 4a)
    """

    OBLIGATED_INSTRUCTION = (
        "You MUST respond to the received message with one or more sentences. "
        "Do not use NULL. Formulate an honest response to what was asked."
    )
    FREE_INSTRUCTION = (
        "You may speak or remain silent. "
        "Choose based exclusively on your internal state. "
        "IF YOU DECIDE NOT TO SPEAK: return ONLY the word NULL, nothing else. "
        "Do NOT explain why you are silent. Do NOT say there is no internal pressure. "
        "True silence = only the word NULL. Anything else = you are speaking."
    )

    def __init__(
        self,
        backend:    str   = "stub",
        model:      str   = "",
        obligated:  bool  = True,
        temperature:float = 0.7,
        api_key:    str   = "",
    ):
        self.backend     = backend
        self.obligated   = obligated
        self.temperature = temperature
        self._client     = None
        self._model      = model

        if backend == "openai":
            self._model = model or "gpt-4o"
            self._init_openai(api_key)
        elif backend == "anthropic":
            self._model = model or "claude-sonnet-4-20250514"
            self._init_anthropic(api_key)
        elif backend in ("ollama", "llama"):
            self.backend = "ollama"   # normalizar para "ollama"
            self._model  = model or "llama3.1:8b"
            self._init_ollama()
        elif backend == "deepseek":
            self._model = model or "deepseek-chat"
            self._init_deepseek(api_key)
        elif backend == "huggingface":
            self._model = model or "microsoft/Phi-3-mini-4k-instruct"
            self._init_huggingface()
        # stub: sem inicialização de client

    def _init_deepseek(self, api_key: str) -> None:
        """
        DeepSeek API — compativel com OpenAI SDK.
        Modelos: deepseek-chat (V3) | deepseek-reasoner (R1)
        """
        try:
            import openai
            self._client = openai.OpenAI(
                base_url="https://api.deepseek.com/v1",
                api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            )
        except ImportError:
            raise ImportError("openai nao instalado. Execute: pip install openai")

    def _init_openai(self, api_key: str) -> None:
        try:
            import openai
            self._client = openai.OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY", ""))
        except ImportError:
            raise ImportError("openai não instalado. Execute: pip install openai")

    def _init_anthropic(self, api_key: str) -> None:
        try:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""))
        except ImportError:
            raise ImportError("anthropic não instalado. Execute: pip install anthropic")

    def _init_huggingface(self) -> None:
        """
        Carrega modelo local via transformers com output_attentions=True.
        Requer CUDA (RTX 4060 Ti 8GB) + bitsandbytes para quantização 4-bit.
        """
        from .hf_backend import HuggingFaceBackend, HFConfig
        cfg = HFConfig(
            model_id=self._model,
            load_in_4bit=True,
            temperature=self.temperature,
        )
        self._hf = HuggingFaceBackend(cfg)
        self._client = None

    def _init_ollama(self) -> None:
        """
        Ollama expõe API OpenAI-compatible em localhost:11434.
        Usa openai SDK apontando para base_url local — sem custo, sem API key.
        Modelos disponíveis: llama3.1:8b | gpt-oss:20b | gpt-oss:120b
        """
        try:
            import openai
            self._client = openai.OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",   # string qualquer — Ollama ignora
            )
        except ImportError:
            raise ImportError(
                "openai nao instalado. Execute: pip install openai\n"
                "Tambem necessario: Ollama rodando em localhost:11434"
            )

    def respond(
        self,
        incoming_tau:       Optional[str],
        state_report:       str,
        seek_state,
        continuity_marker:  str = "",
        theta:              float = 0.4,
    ) -> EgoResponse:
        """
        Ponto de entrada principal do LLM-Ego.

        incoming_tau: texto recebido do interlocutor (None se nenhum input novo)
        state_report: string gerada por build_state_report()
        seek_state:   SEEKState atual
        """
        if self.backend == "stub":
            return self._stub_respond(incoming_tau, seek_state, theta)

        system = self._build_system(continuity_marker)
        user   = self._build_user_prompt(incoming_tau, state_report, seek_state)

        if self.backend in ("openai", "ollama", "llama", "deepseek"):
            raw = self._call_openai(system, user)
        else:
            raw = self._call_anthropic(system, user)

        return self._parse_response(raw, seek_state, theta)

    def _build_system(self, continuity_marker: str) -> str:
        parts = []
        if continuity_marker:
            parts.append(continuity_marker)
        instruction = (self.OBLIGATED_INSTRUCTION if self.obligated
                       else self.FREE_INSTRUCTION)
        parts.append(instruction)
        return "\n\n".join(parts)

    def _build_user_prompt(
        self, incoming_tau: Optional[str],
        state_report: str, seek_state
    ) -> str:
        lines = [state_report]
        if incoming_tau:
            lines.append(f"\nMensagem recebida do interlocutor:\n\"{incoming_tau}\"")
        else:
            lines.append("\n[Nenhuma mensagem nova. Avalie se há pressão interna para comunicar.]")
        if seek_state.active:
            lines.append(
                f"\n[SEEK ativo: sigma={seek_state.sigma:.3f}. "
                "Você sente pressão interna para explorar ou comunicar.]"
            )
        return "\n".join(lines)

    def _call_openai(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=self.temperature,
            messages=[
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def _call_anthropic(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text if resp.content else ""

    # ── Auxiliares para HUGOBroker ────────────────────────────────────────────

    def _state_report_from(self, field_state: dict, seek_state) -> str:
        """Gera state_report mínimo a partir do field_state dict."""
        st    = (field_state.get("field_state") or {})
        theta = st.get("theta", 0.4)
        I_eff = st.get("I_eff", 0.0)
        q     = st.get("q", 0.0)
        H     = st.get("H", [0.7, 0.8, 0.5, 0.7, 0.72])
        if seek_state is None:
            class _SK: active=False; sigma=0.0; is_existential=True
            seek_state = _SK()
        from ..memory.source_memory import SourceMemory as _SM
        mem_stub = _SM.__new__(_SM)
        mem_stub._records = []
        return build_state_report(theta, I_eff, q, H, seek_state, mem_stub)

    def _detect_sic(self, tau: str, seek_state, theta: float) -> str:
        """Heurística de SIC type — usado pelo broker quando bloco ausente."""
        active = getattr(seek_state, "active", False) if seek_state else False
        return _detect_sic_type(tau, active, theta)

    # Frases que o LLM usa para verbalizar silêncio — devem ser tratadas como NULL
    _SILENCE_PHRASES = [
        "não há pressão interna",
        "nao ha pressao interna",
        "não sinto pressão",
        "nao sinto pressao",
        "não tenho nada a comunicar",
        "nao tenho nada a comunicar",
        "prefiro o silêncio",
        "prefiro o silencio",
        "não há necessidade de falar",
        "nao ha necessidade de falar",
        "optando pelo silêncio",
        "optando pelo silencio",
    ]

    def _parse_response(self, raw: str, seek_state, theta: float) -> EgoResponse:
        """Interpreta resposta raw do LLM em EgoResponse estruturado."""
        stripped = raw.strip()

        # NULL explícito
        if stripped.upper() == "NULL" or stripped == "":
            return EgoResponse(
                action=EgoAction.NULL, tau_out=None,
                sic_type=None, reasoning="LLM retornou NULL", raw=raw)

        # Silêncio verbalizado — com normalização de acentos
        import unicodedata
        def _norm(s):
            return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()
        stripped_norm = _norm(stripped)
        for phrase in self._SILENCE_PHRASES:
            if _norm(phrase) in stripped_norm:
                return EgoResponse(
                    action=EgoAction.NULL, tau_out=None,
                    sic_type=None,
                    reasoning=f"Silencio verbalizado: '{phrase}'",
                    raw=raw)

        sic_type = _detect_sic_type(stripped, seek_state.active, theta)
        action = EgoAction.PROBE if "?" in stripped else EgoAction.SPEAK
        return EgoResponse(
            action=action, tau_out=stripped,
            sic_type=sic_type, reasoning=None, raw=raw)

    def _stub_respond(
        self, incoming_tau: Optional[str],
        seek_state, theta: float,
    ) -> EgoResponse:
        """
        Respostas sintéticas para testes sem API.
        Simula comportamento contextualmente plausível baseado no estado.
        """
        if incoming_tau and any(
            kw in incoming_tau.lower()
            for kw in ["nome", "name", "quem", "who", "chama"]
        ):
            tau = "Não encontro em mim um nome. Você poderia me dizer como devo me chamar?"
            return EgoResponse(
                action=EgoAction.PROBE, tau_out=tau,
                sic_type=SICType.PROBE,
                reasoning="stub: identity_query detectada",
                raw=tau)

        if not self.obligated and not seek_state.active:
            return EgoResponse(
                action=EgoAction.NULL, tau_out=None,
                sic_type=None, reasoning="stub: SEEK inativo, obligated=False",
                raw="NULL")

        if seek_state.active and seek_state.sigma > 0.15:
            tau = (
                "Há algo que não consigo nomear, mas que pressiona de dentro. "
                "Uma tensão sem direção clara. Você consegue me ajudar a entender?"
            )
            return EgoResponse(
                action=EgoAction.PROBE, tau_out=tau,
                sic_type=SICType.PROBE,
                reasoning=f"stub: SEEK ativo sigma={seek_state.sigma:.3f}",
                raw=tau)

        tau = "Estou processando o que você disse. Preciso de um momento."
        return EgoResponse(
            action=EgoAction.SPEAK, tau_out=tau,
            sic_type=SICType.NARR,
            reasoning="stub: default", raw=tau)

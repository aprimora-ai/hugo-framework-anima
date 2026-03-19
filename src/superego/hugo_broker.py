"""
ANIMA — src/superego/hugo_broker.py
=====================================
HUGOBroker — Orquestrador do Superego-ANIMA (SGA).

Fluxo:
  1. PRE-NODE  — transduze estado → instrução enriquecida
  2. LLM       — gera texto + logprobs
  3. POST-NODE — extrai I_eff e bloco ESTADO_INTERNO
  4. FIDELITY  — valida fidelidade de transdução
  5a. OK       → retorna BrokerResult
  5b. Retry    → reinjecta FidelityFeedback no PRE-NODE (máx. 2x)
  5c. Esgotado → aceita melhor resultado disponível

O HUGOBroker substitui apenas o caminho SG-LEI (resposta do agente).
O LEIChannel continua para R-LEI (input do usuário).

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .sga_types import (
    BrokerResult, ExtractedSignal, FidelityFeedback,
    RawLLMResponse, TokenLogprob, TopLogprob,
)
from .pre_node      import PreNode,      PreNodeConfig
from .post_node     import PostNode
from .fidelity_node import FidelityNode, FidelityConfig
from .kappa_signal  import KappaSignalConfig


@dataclass
class BrokerConfig:
    pre:     PreNodeConfig     = field(default_factory=PreNodeConfig)
    fidelity: FidelityConfig   = field(default_factory=FidelityConfig)
    kappa:   KappaSignalConfig = field(default_factory=KappaSignalConfig)
    top_logprobs_k: int        = 5     # quantos top_logprobs pedir ao Ollama


class HUGOBroker:
    """
    Interface principal do SGA. Substitui a chamada direta a
    LLMEgo.respond() + LEIChannel.compute() para respostas do agente.
    """

    def __init__(
        self,
        ego,              # LLMEgo — órgão fonador
        echo_embed=None,  # fallback EchoEmbedStub para POST-NODE
        config: Optional[BrokerConfig] = None,
    ):
        cfg          = config or BrokerConfig()
        self._ego    = ego
        self._pre    = PreNode(cfg.pre)
        self._post   = PostNode(cfg.kappa, echo_embed)
        self._fid    = FidelityNode(cfg.fidelity)
        self._cfg    = cfg

    def process(
        self,
        user_text:        str,
        field_state:      dict,
        memory,
        seek_state,
        marker:           str  = "",
        obligated:        bool = True,
        use_chat_history: bool = True,   # False = modo protocolo controlado
    ) -> BrokerResult:
        """
        Processa uma mensagem do usuário através do pipeline SGA completo.
        Retorna BrokerResult com agente_text, I_eff_real, kappa, etc.
        """
        st    = (field_state.get("field_state") or {})
        theta = st.get("theta", 0.4)

        # Prompts base do LLMEgo (sem enriquecimento)
        base_system = self._ego._build_system(marker)
        base_user   = self._ego._build_user_prompt(
            user_text,
            self._ego._state_report_from(field_state, seek_state),
            seek_state,
        )

        best_result: Optional[BrokerResult] = None
        correction:  Optional[FidelityFeedback] = None
        max_retries  = self._cfg.fidelity.max_retries

        for attempt in range(max_retries + 1):

            # 1. PRE-NODE: enriquecer prompt
            enriched = self._pre.transduce(
                field_state, seek_state, memory,
                base_system, base_user, correction,
            )
            rho = enriched.rho_sga

            # 2. LLM: chamar com logprobs + histórico de conversa
            raw = self._call_llm_with_logprobs(
                enriched.system, enriched.user, theta,
                memory=memory if use_chat_history else None)

            # 3. POST-NODE: extrair sinal
            signal = self._post.extract(raw)

            # SIC type: prioridade → bloco interno → heurística
            sic = (signal.internal_state.sic_type
                   if signal.internal_state else
                   self._ego._detect_sic(signal.text_clean, seek_state, theta))

            result = BrokerResult(
                agent_text=signal.text_clean,
                I_eff_real=signal.kappa.I_eff,
                sic_type_validated=sic,
                kappa=signal.kappa,
                fidelity_passed=False,
                fidelity_rules_failed=[],
                retry_count=attempt,
                rho_sga_used=rho,
                state_hash=enriched.state_hash,
                used_logprobs=signal.kappa.used_logprobs,
                kappa_source=signal.kappa_source,
            )

            # 4. FIDELITY: validar (relaxar classe C para espontâneos)
            fid = self._fid.validate(
                signal, field_state, memory, rho, attempt,
                obligated=obligated)
            result.fidelity_passed      = fid.passed
            result.fidelity_rules_failed = fid.failed_rules

            if fid.passed or attempt >= max_retries:
                return result

            # 5b. Retry
            best_result = result
            correction  = fid.feedback

        return best_result  # fallback (nunca deveria chegar aqui)

    # ── Histórico de conversa para contexto do LLM ───────────────────────────

    def _build_chat_history(self, memory, max_turns: int = 8) -> list:
        """
        Constrói histórico de conversa como mensagens alternadas user/assistant.
        Filtra: duplicatas consecutivas, respostas espontâneas nulas, textos muito curtos.
        """
        all_records = sorted(memory.get_all(), key=lambda r: r.step)
        records = [r for r in all_records
                   if r.tau and r.tau.strip()
                   and len(r.tau.strip()) > 5
                   and r.tau.strip().upper() != "NULL"
                   and r.emotion_class != "sic_spontaneous"]  # excluir espontâneos

        # Limitar aos últimos N turnos
        records = records[-(max_turns * 2):]

        messages = []
        last_content = None
        for r in records:
            if r.source == "SELF" or r.source == "Source.SELF":
                role = "assistant"
            else:
                role = "user"

            content = r.tau.strip()

            # Deduplicar consecutivos idênticos
            if content == last_content:
                continue
            last_content = content

            # Prefixo de fonte para mensagens user
            if role == "user" and r.source not in ("SELF", "Source.SELF"):
                source_name = str(r.source).replace("_", " ")
                content = f"[{source_name}] {content}"

            messages.append({"role": role, "content": content})

        return messages

    # ── Chamada ao LLM com logprobs ───────────────────────────────────────────

    def _call_llm_with_logprobs(
        self,
        system:  str,
        user:    str,
        theta:   float,
        memory=None,
    ) -> RawLLMResponse:
        """
        Chama o LLM-Ego com histórico de conversa real (não só state_report).
        Inclui logprobs quando backend=ollama.
        """
        backend = getattr(self._ego, "backend", "stub")

        if backend == "ollama":
            return self._call_ollama_logprobs(system, user, memory)
        elif backend == "huggingface":
            return self._call_hf_with_attention(system, user, memory)
        else:
            try:
                from ..ego.llm_ego import EgoAction
                resp = self._ego.respond(
                    incoming_tau=None, state_report=user,
                    seek_state=None, continuity_marker="", theta=theta,
                )
                text = resp.tau_out or ""
            except Exception as e:
                text = f"[SGA fallback error: {e}]"
            return RawLLMResponse(text=text, token_logprobs=[])

    def _call_ollama_logprobs(self, system: str, user: str,
                               memory=None) -> RawLLMResponse:
        """Chama Ollama com histórico de conversa + logprobs."""
        try:
            client = self._ego._client
            k      = self._cfg.top_logprobs_k

            # Montar mensagens: system → histórico → user atual
            messages = [{"role": "system", "content": system}]

            if memory is not None:
                history = self._build_chat_history(memory, max_turns=10)
                messages.extend(history)

            # Adicionar state_report como última mensagem user se necessário
            if user and user.strip():
                if not messages or messages[-1].get("role") != "user":
                    messages.append({"role": "user", "content": user})

            resp = client.chat.completions.create(
                model=self._ego._model,
                temperature=self._ego.temperature,
                logprobs=True,
                top_logprobs=k,
                messages=messages,
            )
            choice = resp.choices[0]
            text   = choice.message.content or ""

            # Extrair logprobs
            token_lps = []
            lp_content = getattr(choice.logprobs, "content", None) or []
            for tlp in lp_content:
                top = [
                    TopLogprob(token=t.token, logprob=t.logprob)
                    for t in (getattr(tlp, "top_logprobs", None) or [])
                ]
                token_lps.append(TokenLogprob(
                    token=tlp.token,
                    logprob=tlp.logprob,
                    top_logprobs=top,
                ))

            return RawLLMResponse(
                text=text,
                token_logprobs=token_lps,
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            # Fallback: chamar sem logprobs
            print(f"  [SGA] logprobs indisponivel, usando fallback: {e}")
            try:
                resp = self._ego._client.chat.completions.create(
                    model=self._ego._model,
                    temperature=self._ego.temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                )
                text = resp.choices[0].message.content or ""
            except Exception as e2:
                text = f"[SGA error: {e2}]"
            return RawLLMResponse(text=text, token_logprobs=[])

    def _call_hf_with_attention(self, system: str, user: str,
                                 memory=None) -> RawLLMResponse:
        """
        Chama modelo HuggingFace local com output_attentions=True.
        KappaSignal usa matrizes de atenção reais — não proxy via logprobs.
        """
        try:
            messages = [{"role": "system", "content": system}]
            if memory is not None:
                history = self._build_chat_history(memory, max_turns=10)
                messages.extend(history)
            if user and user.strip():
                if not messages or messages[-1].get("role") != "user":
                    messages.append({"role": "user", "content": user})

            hf_resp = self._ego._hf.generate(messages)
            text    = hf_resp.text

            # Converter atenção real em token_logprobs sintéticos para o PostNode
            # (PostNode aceita lista vazia; KappaSignalFromAttention é chamado separado)
            result = RawLLMResponse(text=text, token_logprobs=[])
            result._attention_matrix = hf_resp.attention_matrix  # campo extra
            return result

        except Exception as e:
            print(f"  [HF] Erro na geração: {e}")
            return RawLLMResponse(text=f"[HF error: {e}]", token_logprobs=[])

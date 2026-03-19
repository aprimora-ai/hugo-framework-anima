"""
ANIMA — src/superego/post_node.py
===================================
POST-NODE: Extração de I_eff e bloco ESTADO_INTERNO da resposta do LLM.

Duas operações:
  1. Parsear e remover bloco [ESTADO_INTERNO]...[/ESTADO_INTERNO]
  2. Extrair KappaSignal dos logprobs (ou fallback EchoEmbedStub)

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, List

from .sga_types import (
    TokenLogprob, TopLogprob, RawLLMResponse,
    ExtractedSignal, InternalState, KappaSignal,
)
from .kappa_signal import KappaSignalExtractor, KappaSignalConfig, KappaSignalFromAttention


# ── Regex para o bloco de sinalização ────────────────────────────────────────

# Regex tolerante: aceita com ou sem tag de fechamento
_BLOCK_RE = re.compile(
    r'\[ESTADO_INTERNO\](.*?)(?:\[/ESTADO_INTERNO\]|(?=\n\n|\Z))',
    re.DOTALL | re.IGNORECASE
)
# Regex de limpeza: remove a tag e tudo dentro dela até o fim ou próxima seção
_BLOCK_STRIP_RE = re.compile(
    r'\s*\[ESTADO_INTERNO\].*?(?:\[/ESTADO_INTERNO\]|\Z)',
    re.DOTALL | re.IGNORECASE
)
_FIELD_RE = re.compile(r'(\w+)\s*:\s*(.+)')

# Regex para remover monólogo interno entre colchetes gerado espontaneamente
# Exemplos: [Você está sentindo...] [Agradecer é um gesto...] [Nota: ...]
# Exclui propositalmente: [ESTADO_INTERNO] (tratado separadamente)
_INTERNAL_MONOLOGUE_RE = re.compile(
    r'\[(?!ESTADO_INTERNO|/ESTADO_INTERNO)[^\]]{10,300}\]',
    re.IGNORECASE
)


def _parse_internal_state(block: str) -> Optional[InternalState]:
    """
    Parseia o bloco ESTADO_INTERNO em InternalState.
    Tolerante a variações de idioma, formato e campos parciais.
    """
    import unicodedata

    def _norm(s: str) -> str:
        return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().strip()

    fields = {}
    for line in block.strip().splitlines():
        m = _FIELD_RE.match(line.strip())
        if m:
            key = _norm(m.group(1))
            fields[key] = m.group(2).strip().strip('"\'')

    if not fields:
        return None

    # Extração tolerante da intensidade emocional
    intensity = 0.1
    for k in ("intensidade_emocional", "intensidade", "emotional_intensity", "intensity"):
        if k in fields:
            try:
                intensity = float(fields[k].replace(",", "."))
                break
            except Exception:
                pass

    # Extração tolerante do tipo SIC
    sic = "SEEK"
    for k in ("tipo_sic", "sic_type", "tipo", "type", "sic"):
        if k in fields:
            val = fields[k].upper()
            if val in ("NARR", "SEEK", "CATHARSIS", "PROBE", "NULL",
                       "ELABORATED", "SIC_NARR", "SIC_SEEK", "SIC_PROBE",
                       "SIC_CATHARSIS", "SIC_NULL"):
                sic = val.replace("SIC_", "")
            break

    # Extração tolerante de tensão reconhecida
    tension = False
    for k in ("tensao_reconhecida", "tension_acknowledged", "tensao", "tension"):
        if k in fields:
            v = _norm(fields[k])
            tension = v in ("sim", "yes", "true", "1", "s", "y")
            break

    # Extração tolerante de lacuna abordada
    gap = False
    for k in ("lacuna_abordada", "gap_addressed", "lacuna", "gap"):
        if k in fields:
            v = _norm(fields[k])
            gap = v in ("sim", "yes", "true", "1", "s", "y")
            break

    try:
        return InternalState(
            emotional_intensity=min(max(intensity, 0.0), 1.0),
            sic_type=sic,
            tension_acknowledged=tension,
            gap_addressed=gap,
            raw_block=block,
        )
    except Exception:
        return None


# Frases de silêncio verbalizado — LLM descreveu NULL em vez de retorná-lo
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
    "não há nada para dizer",
    "nao ha nada para dizer",
    "nenhuma lacuna",
    "acho que estou em silêncio",
    "acho que estou em silencio",
    "não falo",
    "nao falo",
    "nenhuma mensagem",
    "sem nada a acrescentar",
    "nada para compartilhar",
]

# Respostas triviais de palavra única — não são fala real
_TRIVIAL = {"não", "nao", "sim", "null", "nan", "nenhum", "nada"}

def _normalize(s: str) -> str:
    """Remove acentos para comparação robusta em português."""
    import unicodedata
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()

_SILENCE_PHRASES_NORM = [_normalize(p) for p in _SILENCE_PHRASES]

def _is_verbalized_silence(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    # NULL com ou sem pontuação
    if t.upper().rstrip("!.?,;") == "NULL":
        return True
    # Palavra única trivial (Não. NÃO. Sim. etc.)
    if _normalize(t).rstrip("!.?,;") in _TRIVIAL:
        return True
    t_norm = _normalize(t)
    return any(p in t_norm for p in _SILENCE_PHRASES_NORM)


class PostNode:
    """
    Extrai sinal estrutural da resposta do LLM:
      - remove bloco ESTADO_INTERNO do texto
      - calcula KappaSignal dos logprobs
      - fallback via EchoEmbedStub se logprobs ausentes
    """

    def __init__(
        self,
        kappa_config: Optional[KappaSignalConfig] = None,
        echo_embed=None,   # fallback EchoEmbedStub
    ):
        self._kappa      = KappaSignalExtractor(kappa_config)
        self._kappa_attn = KappaSignalFromAttention(kappa_config)
        self._echo   = echo_embed   # pode ser None — I_eff=0.05 como fallback

    def extract(self, raw: RawLLMResponse) -> ExtractedSignal:
        """Extrai sinal e texto limpo da resposta bruta."""
        text        = raw.text or ""
        internal    = None
        signal_miss = True

        m = _BLOCK_RE.search(text)
        if m:
            internal    = _parse_internal_state(m.group(1))
            text        = _BLOCK_STRIP_RE.sub("", text).strip()
            signal_miss = (internal is None)

        # Remover monólogo interno entre colchetes [Você está sentindo...]
        text = _INTERNAL_MONOLOGUE_RE.sub("", text).strip()

        # Silêncio verbalizado → tratar como NULL
        if _is_verbalized_silence(text):
            text = "NULL"

        # KappaSignal: atenção real (HF) > logprobs (Ollama) > fallback
        attn = getattr(raw, "_attention_matrix", None)
        if attn is not None:
            kappa       = self._kappa_attn.extract_from_attention(attn)
            kappa_source = "attention"
        elif raw.token_logprobs:
            kappa        = self._kappa.extract(raw.token_logprobs)
            kappa_source = "logprobs"
        else:
            kappa        = self._fallback_kappa(text)
            kappa_source = "fallback"

        return ExtractedSignal(
            text_clean=text,
            internal_state=internal,
            kappa=kappa,
            signal_missing=signal_miss,
            kappa_source=kappa_source,
        )

    def _fallback_kappa(self, text: str) -> KappaSignal:
        """Usa EchoEmbedStub como fallback quando logprobs não disponíveis."""
        i_eff = 0.05
        if self._echo:
            try:
                i_eff = self._echo.embed(text)
            except Exception:
                pass
        return KappaSignal(
            omega=0.0, eta=1.0, xi=0.0, delta=0.0,
            I_eff=round(i_eff, 4), n_tokens=0,
            baseline_omega=0.0, regime="laminar",
            used_logprobs=False,
        )

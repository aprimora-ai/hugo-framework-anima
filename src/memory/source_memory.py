"""
ANIMA — src/memory/source_memory.py
====================================
M_A(t): memória episódica com atribuição de fonte.

Extende o MemoryStore do REMIND adicionando:
    source      -- origem do evento: SELF | OTHER_k | ANON | INTERNAL
    sic_type    -- tipo de SIC se source=SELF (None caso contrário)
    h1_class    -- classe de feature H1 aberta por este evento
    h1_status   -- UNRESOLVED | RESOLVED | PENDING | CLOSED
    linked_to   -- índice do record que este resolve (para PENDING)
    session_id  -- identificador da sessão em que o record foi criado

SourceMemory mantém partições separadas por fonte para suportar:
    M_SELF(t)     -- eventos gerados pelo agente
    M_OTHER_k(t)  -- eventos por interlocutor k
    rho(t)        -- Self-Other Partition Ratio

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import numpy as np


# ── Enumerações ───────────────────────────────────────────────────────────────

class Source(str, Enum):
    SELF     = "SELF"      # gerado pelo LLM-Ego (SIC / SG-LEI)
    INTERNAL = "INTERNAL"  # gap de identidade ou estado interno detectado
    ANON     = "ANON"      # legado REMIND / sem atribuição

class SICType(str, Enum):
    SEEK      = "SIC_SEEK"      # exploração sem direção clara
    PROBE     = "SIC_PROBE"     # pergunta dirigida ao interlocutor
    NARR      = "SIC_NARR"      # narrativização do estado atual
    CATHARSIS = "SIC_CATHARSIS" # gerada durante/após colapso
    ELABORATED= "SIC_ELABORATED"# segunda abordagem — maior complexidade


class H1Class(str, Enum):
    TRAUMA          = "TRAUMA"           # evento traumático externo
    IDENTITY_GAP    = "IDENTITY_GAP"     # ausência de conhecimento do self
    PENDING_ANSWER  = "PENDING_ANSWER"   # pergunta enviada sem resposta
    IDENTITY_RESOLVED = "IDENTITY_RESOLVED" # gap fechado por IRE
    GENERAL         = "GENERAL"          # outros eventos


class H1Status(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED   = "RESOLVED"
    PENDING    = "PENDING"
    CLOSED     = "CLOSED"


# ── SourceRecord ──────────────────────────────────────────────────────────────

@dataclass
class SourceRecord:
    """
    Registro episódico com atribuição de fonte — unidade de M_A(t).
    """
    step:        int
    H:           List[float]       # campo homeostático [5 dims]
    I_eff:       float             # intensidade emocional processada
    theta:       float             # rigidez neste step
    source:      str               # Source.SELF | Source.INTERNAL | "OTHER_k" | Source.ANON
    tau:         Optional[str]     # texto original processado (None se suprimido)
    emotion_class: str = "neutral"
    trauma_flag: bool = False
    adi:         float = 0.0      # Attention Dispersion Index
    diversity:   float = 1.0
    deficit:     float = 0.0
    sic_type:    Optional[str] = None   # SICType se source=SELF
    h1_class:    Optional[str] = None   # H1Class
    h1_status:   Optional[str] = None   # H1Status
    linked_to:   Optional[int] = None   # índice do record que resolve
    session_id:  int = 0
    vivid:       bool = False           # DAP-1: record de alta intensidade

    def to_dict(self) -> dict:
        return {
            "step":          self.step,
            "H":             [round(h, 5) for h in self.H],
            "I_eff":         round(self.I_eff, 5),
            "theta":         round(self.theta, 5),
            "source":        self.source,
            "tau":           self.tau,
            "emotion_class": self.emotion_class,
            "trauma_flag":   self.trauma_flag,
            "adi":           round(self.adi, 5),
            "diversity":     round(self.diversity, 5),
            "deficit":       round(self.deficit, 5),
            "sic_type":      self.sic_type,
            "h1_class":      self.h1_class,
            "h1_status":     self.h1_status,
            "linked_to":     self.linked_to,
            "session_id":    self.session_id,
            "vivid":         self.vivid,
        }


# ── SourceMemory ──────────────────────────────────────────────────────────────

class SourceMemory:
    """
    M_A(t) com particionamento por fonte.

    Implementa:
        append()        -- adiciona SourceRecord
        M_SELF(t)       -- registros gerados pelo agente
        M_OTHER_k(t)    -- registros de interlocutor k
        rho(t)          -- Self/Other Partition Ratio
        ctx_window()    -- DAP-2: janela ponderada por persistência
    """

    # Threshold para marcar record como vivid (DAP-1)
    I_VIVID_THRESHOLD: float = 0.40

    def __init__(self, session_id: int = 0, max_size: Optional[int] = None):
        self._records: List[SourceRecord] = []
        self.session_id = session_id
        self.max_size   = max_size
        # cache de nomes de interlocutores conhecidos
        self._interlocutors: set = set()

    # ── Escrita ───────────────────────────────────────────────────────────────

    def append(self, record: SourceRecord) -> int:
        """Adiciona record e retorna seu índice em M_A(t)."""
        record.session_id = self.session_id
        # DAP-1: marcação automática de vivid
        if record.I_eff >= self.I_VIVID_THRESHOLD:
            record.vivid = True
        idx = len(self._records)
        self._records.append(record)
        if record.source not in (Source.SELF, Source.INTERNAL, Source.ANON):
            self._interlocutors.add(record.source)
        if self.max_size and len(self._records) > self.max_size:
            self._records.pop(0)
        return idx

    def resolve_h1(self, linked_to_idx: int, resolver_idx: int) -> None:
        """Fecha um H1 bar: UNRESOLVED → RESOLVED."""
        if 0 <= linked_to_idx < len(self._records):
            self._records[linked_to_idx].h1_status = H1Status.RESOLVED
        if 0 <= resolver_idx < len(self._records):
            self._records[resolver_idx].linked_to = linked_to_idx

    # ── Partições ─────────────────────────────────────────────────────────────

    def M_SELF(self) -> List[SourceRecord]:
        return [r for r in self._records if r.source == Source.SELF]

    def M_OTHER(self, interlocutor_id: Optional[str] = None) -> List[SourceRecord]:
        if interlocutor_id:
            return [r for r in self._records if r.source == interlocutor_id]
        return [r for r in self._records
                if r.source not in (Source.SELF, Source.INTERNAL, Source.ANON)]

    def M_INTERNAL(self) -> List[SourceRecord]:
        return [r for r in self._records if r.source == Source.INTERNAL]

    def unresolved_h1(self) -> List[SourceRecord]:
        return [r for r in self._records if r.h1_status == H1Status.UNRESOLVED]

    def known_interlocutors(self) -> set:
        return set(self._interlocutors)

    # ── Observáveis ───────────────────────────────────────────────────────────

    def rho(self) -> float:
        """
        Self/Other Partition Ratio — Def. SO-2.
        rho = |M_SELF| / (|M_SELF| + |M_OTHER|)
        """
        n_self  = len(self.M_SELF())
        n_other = len(self.M_OTHER())
        total   = n_self + n_other
        return n_self / total if total > 0 else 0.0

    def ctx_window(self, K: int = 50, decay_fn=None) -> List[SourceRecord]:
        """
        DAP-2: janela de contexto ponderada por persistência.
        Seleciona os K records com maior peso de persistência
        (não os K mais recentes).

        decay_fn: callable(I_eff) → peso. Se None, usa I_eff como proxy.
        """
        if not self._records:
            return []

        def weight(r: SourceRecord) -> float:
            base = decay_fn(r.I_eff) if decay_fn else r.I_eff
            # records de interlocutores com afeto aumentam peso
            source_boost = 1.2 if r.source not in (
                Source.SELF, Source.INTERNAL, Source.ANON) else 1.0
            vivid_boost  = 1.5 if r.vivid else 1.0
            return base * source_boost * vivid_boost

        sorted_records = sorted(self._records, key=weight, reverse=True)
        return sorted_records[:K]

    def novelty_factor(self, interlocutor_id: str) -> float:
        """
        Def. G-1: fator de novidade para primeiro contato.
        novelty = 1 / (1 + |M_OTHER_k|)
        """
        n = len(self.M_OTHER(interlocutor_id))
        return 1.0 / (1.0 + n)

    def __len__(self) -> int:
        return len(self._records)

    def get_all(self) -> List[SourceRecord]:
        return list(self._records)

    def summary(self) -> dict:
        n = len(self._records)
        if n == 0:
            return {"n": 0}
        n_self     = len(self.M_SELF())
        n_other    = len(self.M_OTHER())
        n_internal = len(self.M_INTERNAL())
        n_trauma   = sum(1 for r in self._records if r.trauma_flag)
        n_unres    = len(self.unresolved_h1())
        return {
            "n":              n,
            "n_self":         n_self,
            "n_other":        n_other,
            "n_internal":     n_internal,
            "n_trauma":       n_trauma,
            "n_unresolved_h1": n_unres,
            "rho":            round(self.rho(), 4),
            "interlocutors":  list(self._interlocutors),
            "session_id":     self.session_id,
        }

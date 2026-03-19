"""
ANIMA — src/superego/kappa_signal.py
======================================
Observáveis Kappa adaptados para logprobs (SGA — POST-NODE).

Adaptação metodológica de Kappa-Attention-Regimes (Ohio, 2026):
  Kappa-LLM monitora matrizes de atenção via HuggingFace hooks.
  Aqui adaptamos os observáveis para logprobs da API Ollama —
  distribuições de probabilidade sobre tokens durante a geração.

Observáveis implementados:
  Ω  — entropia média (incerteza distribucional por token)
  η  — rigidez de escolha (certeza do token mais provável)
  Ξ  — diversidade de alternativas (gap top1/top2)
  Δ  — divergência da baseline de sessão

Nota para publicação: apresentar como "observáveis de geração
baseados em logprobs" — inspiração metodológica no Kappa-LLM,
não a mesma técnica (logprobs ≠ matrizes de atenção).

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
import math
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from .sga_types import TokenLogprob, KappaSignal


# ── Parâmetros canônicos ──────────────────────────────────────────────────────

@dataclass
class KappaSignalConfig:
    alpha_omega:     float = 0.35   # peso Ω na composição de I_eff
    alpha_eta:       float = 0.30   # peso (1-η)
    alpha_xi:        float = 0.20   # peso Ξ
    alpha_delta:     float = 0.15   # peso Δ
    beta_sigmoid:    float = 3.0    # escala da sigmoide
    theta_lei:       float = 0.35   # threshold neutro
    baseline_window: int   = 10     # turnos para calcular baseline Δ
    # Thresholds de regime (análogos ao Kappa-FIN)
    turb_threshold:  float = 0.55   # Ω > turb → turbulento
    trans_threshold: float = 0.35   # Ω > trans → transição


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


class KappaSignalExtractor:
    """
    Extrai observáveis Kappa de uma lista de TokenLogprob e
    compõe I_eff real para injeção no campo HUGO.

    Mantém baseline de sessão (deque de Ω) para cálculo de Δ.
    """

    def __init__(self, config: Optional[KappaSignalConfig] = None):
        self.cfg = config or KappaSignalConfig()
        self._omega_history: deque[float] = deque(maxlen=self.cfg.baseline_window)

    # ── Observáveis individuais ───────────────────────────────────────────────

    def _omega(self, tokens: List[TokenLogprob]) -> float:
        """Ω — entropia média sobre todos os tokens."""
        entropies = []
        for tok in tokens:
            if not tok.top_logprobs:
                continue
            # converter logprobs para probs normalizadas
            lps = [t.logprob for t in tok.top_logprobs]
            max_lp = max(lps)
            probs = [math.exp(lp - max_lp) for lp in lps]
            s = sum(probs)
            probs = [p / s for p in probs]
            h = -sum(p * math.log(p + 1e-12) for p in probs if p > 0)
            entropies.append(h)
        return float(sum(entropies) / len(entropies)) if entropies else 0.0

    def _eta(self, tokens: List[TokenLogprob]) -> float:
        """η — rigidez: 1 - desvio_padrão dos logprob do top1."""
        top1_lps = [tok.logprob for tok in tokens if tok.logprob is not None]
        if len(top1_lps) < 2:
            return 1.0
        mean = sum(top1_lps) / len(top1_lps)
        var  = sum((x - mean) ** 2 for x in top1_lps) / len(top1_lps)
        std  = math.sqrt(var)
        # normalizar: std típico ~2-4 em logprob natural
        return float(max(0.0, 1.0 - std / 4.0))

    def _xi(self, tokens: List[TokenLogprob]) -> float:
        """Ξ — diversidade: 1 - gap_médio(top1 - top2) normalizado."""
        gaps = []
        for tok in tokens:
            if len(tok.top_logprobs) >= 2:
                lp1 = tok.top_logprobs[0].logprob
                lp2 = tok.top_logprobs[1].logprob
                # gap em espaço de probabilidade
                p1 = math.exp(lp1)
                p2 = math.exp(lp2)
                gap = p1 - p2  # ∈ [0, 1]
                gaps.append(gap)
        if not gaps:
            return 0.0
        mean_gap = sum(gaps) / len(gaps)
        return float(max(0.0, 1.0 - mean_gap))

    def _delta(self, omega: float) -> float:
        """Δ — divergência da baseline de sessão."""
        if not self._omega_history:
            return 0.0
        baseline = sum(self._omega_history) / len(self._omega_history)
        if baseline < 1e-9:
            return 0.0
        return float(abs(omega - baseline) / baseline)

    # ── Composição de I_eff ───────────────────────────────────────────────────

    def _compose_ieff(self, omega: float, eta: float,
                      xi: float, delta: float) -> float:
        c = self.cfg
        raw = (c.alpha_omega * omega
               + c.alpha_eta  * (1.0 - eta)
               + c.alpha_xi   * xi
               + c.alpha_delta * delta)
        return float(_sigmoid(c.beta_sigmoid * (raw - c.theta_lei)))

    def _regime(self, omega: float) -> str:
        if omega > self.cfg.turb_threshold:
            return "turbulento"
        if omega > self.cfg.trans_threshold:
            return "transicao"
        return "laminar"

    # ── Interface principal ───────────────────────────────────────────────────

    def extract(self, tokens: List[TokenLogprob]) -> KappaSignal:
        """
        Extrai KappaSignal de uma lista de TokenLogprob.
        Atualiza o histórico de baseline da sessão.
        """
        if not tokens:
            return self._fallback()

        omega = self._omega(tokens)
        eta   = self._eta(tokens)
        xi    = self._xi(tokens)
        delta = self._delta(omega)
        ieff  = self._compose_ieff(omega, eta, xi, delta)

        baseline = (sum(self._omega_history) / len(self._omega_history)
                    if self._omega_history else omega)
        self._omega_history.append(omega)

        return KappaSignal(
            omega=round(omega, 4), eta=round(eta, 4),
            xi=round(xi, 4),       delta=round(delta, 4),
            I_eff=round(ieff, 4),  n_tokens=len(tokens),
            baseline_omega=round(baseline, 4),
            regime=self._regime(omega),
            used_logprobs=True,
        )

    def _fallback(self) -> KappaSignal:
        """Retorna sinal neutro quando não há logprobs."""
        return KappaSignal(
            omega=0.0, eta=1.0, xi=0.0, delta=0.0,
            I_eff=0.05, n_tokens=0,
            baseline_omega=0.0, regime="laminar",
            used_logprobs=False,
        )


class KappaSignalFromAttention:
    """
    Extrai KappaSignal de matrizes de atenção reais (backend HuggingFace).
    Análogo ao R-Score do HEIMDALL, mas produce os 4 observáveis do SGA.

    Ω — entropia da distribuição de atenção (média das linhas)
    η — rigidez: 1 - desvio padrão do peso máximo por linha
    Ξ — diversidade: 1 - concentração (gini simplificado)
    Δ — divergência da baseline de sessão
    """

    def __init__(self, config: Optional[KappaSignalConfig] = None):
        self.cfg = config or KappaSignalConfig()
        self._omega_history: deque[float] = deque(maxlen=self.cfg.baseline_window)

    def extract_from_attention(self, attn_matrix) -> KappaSignal:
        """
        attn_matrix: np.ndarray [seq, seq] normalizado [0,1].
        Retorna KappaSignal com I_eff real baseado em atenção.
        """
        import numpy as np

        if attn_matrix is None or attn_matrix.size == 0:
            return self._fallback()

        # Ω — entropia média das linhas
        eps = 1e-12
        # normalizar cada linha como distribuição de prob
        row_sums = attn_matrix.sum(axis=1, keepdims=True) + eps
        p = attn_matrix / row_sums
        h_rows = -np.sum(p * np.log(p + eps), axis=1)
        omega = float(np.mean(h_rows))

        # η — rigidez: 1 - std(max de cada linha)
        row_max = attn_matrix.max(axis=1)
        eta = float(max(0.0, 1.0 - np.std(row_max) / 0.5))

        # Ξ — diversidade: 1 - gini simplificado
        flat = attn_matrix.flatten()
        flat_sorted = np.sort(flat)
        n = len(flat_sorted)
        gini = float(np.sum((2 * np.arange(1, n+1) - n - 1) * flat_sorted) /
                     (n * flat_sorted.sum() + eps))
        xi = float(max(0.0, 1.0 - gini))

        # Δ — divergência da baseline
        baseline = (sum(self._omega_history) / len(self._omega_history)
                    if self._omega_history else omega)
        delta = float(abs(omega - baseline) / max(baseline, eps))
        self._omega_history.append(omega)

        ieff = float(_sigmoid(
            self.cfg.beta_sigmoid * (
                self.cfg.alpha_omega * omega
                + self.cfg.alpha_eta  * (1.0 - eta)
                + self.cfg.alpha_xi   * xi
                + self.cfg.alpha_delta * delta
                - self.cfg.theta_lei
            )
        ))

        return KappaSignal(
            omega=round(omega, 4), eta=round(eta, 4),
            xi=round(xi, 4),       delta=round(delta, 4),
            I_eff=round(ieff, 4),  n_tokens=attn_matrix.shape[0],
            baseline_omega=round(baseline, 4),
            regime=self._regime(omega),
            used_logprobs=False,  # sinal real de atenção
        )

    def _regime(self, omega: float) -> str:
        if omega > self.cfg.turb_threshold:  return "turbulento"
        if omega > self.cfg.trans_threshold: return "transicao"
        return "laminar"

    def _fallback(self) -> KappaSignal:
        return KappaSignal(
            omega=0.0, eta=1.0, xi=0.0, delta=0.0,
            I_eff=0.05, n_tokens=0,
            baseline_omega=0.0, regime="laminar",
            used_logprobs=False,
        )

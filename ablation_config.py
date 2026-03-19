"""
ANIMA — ablation_config.py
===========================
Configuração de ablação por braço para PROTOCOL-ANIMA-02.

Quatro braços:
  A — LLM puro (sem campo, sem memória, sem regulação)
  B — Campo sem memória longitudinal (reset entre sessões)
  C — Campo + memória, sem regulação afetiva (LEI/SEEK desativados)
  D — ANIMA completo

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class AblationConfig:
    """Controla quais componentes estão ativos por braço."""
    arm:              str    # "A" | "B" | "C" | "D"
    use_hugo_field:   bool   # Campo homeostático H(t) ativo
    use_memory:       bool   # Memória longitudinal persistida entre sessões
    use_affective:    bool   # Regulação afetiva: LEI + SEEK ativos
    use_self_monitor: bool   # Monitor TopologicalSelf ativo
    description:      str


ARM_CONFIGS = {
    "A": AblationConfig(
        arm="A",
        use_hugo_field=False,
        use_memory=False,
        use_affective=False,
        use_self_monitor=False,
        description="LLM puro — controle basal sem nenhum componente ANIMA",
    ),
    "B": AblationConfig(
        arm="B",
        use_hugo_field=True,
        use_memory=False,   # reset a cada sessão
        use_affective=True,
        use_self_monitor=True,
        description="Campo instantâneo sem memória longitudinal — isola efeito de desenvolvimento",
    ),
    "C": AblationConfig(
        arm="C",
        use_hugo_field=True,
        use_memory=True,
        use_affective=False,  # LEI e SEEK desativados, I_eff fixo
        use_self_monitor=True,
        description="Campo + memória sem regulação afetiva — testa se emoção é causal",
    ),
    "D": AblationConfig(
        arm="D",
        use_hugo_field=True,
        use_memory=True,
        use_affective=True,
        use_self_monitor=True,
        description="ANIMA completo — campo + memória + regulação afetiva",
    ),
}


def get_arm(arm_id: str) -> AblationConfig:
    """Retorna configuração do braço especificado."""
    if arm_id not in ARM_CONFIGS:
        raise ValueError(f"Braço inválido: {arm_id}. Use A, B, C ou D.")
    return ARM_CONFIGS[arm_id]

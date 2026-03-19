# ANIMA — Autonomous Neurodynamic Integration for Modular Agents

[![DOI](https://zenodo.org/badge/1186288006.svg)](https://doi.org/10.5281/zenodo.19111951)
[![Paper](https://zenodo.org/badge/DOI/10.5281/zenodo.19112005.svg)](https://doi.org/10.5281/zenodo.19112005)

**Longitudinal cognitive evaluation protocol for HUGO homeostatic agents.**

David Ohio | Independent Researcher | odavidohio@gmail.com  
HUGO AGI Framework | March 2026 | License: CC BY 4.0

---

## Overview

ANIMA is a protocol for evaluating how homeostatic field agents (HUGO Framework) develop
cognitive advantages over time. Through dual-mode ablation (200 sessions) and a gamma-sweep
experiment (96 sessions), we establish that the homeostatic decay parameter γ controls
**cognitive profile**, not quality — defining a continuous space of agent personalities.

## Key Results (296 sessions, Llama 3.1 8B)

- **γ is a personality parameter, not a hyperparameter.** Different values produce
  qualitatively different agents suited to different tasks.
- **Peak learning occurs at γ = 0.990** (PSI = +0.359, 36% improvement between passes),
  not at either extreme.
- **7 empirical cognitive archetypes** confirmed across 3 bands.


## Archetype Registry

| Archetype | γ | DCS | ILR | PSI | Best Application |
|-----------|-----|-------|-------|--------|------------------|
| Cold Reactor | 0.900 | 0.622 | 0.092 | +0.195 | API agents, data extraction |
| Warm Improviser | 0.930 | 0.620 | 0.100 | +0.242 | Brainstorming, content gen |
| Hot Improviser | 0.970 | 0.637 | 0.067 | +0.205 | Negotiation, live comm |
| Adaptive Coordinator | 0.985 | 0.603 | 0.108 | +0.255 | Project mgmt, tutoring |
| **Deep Learner** | **0.990** | **0.507** | **0.200** | **+0.359** | **Research, iterative analysis** |
| Guardian | 0.995 | 0.484 | 0.242 | +0.135 | Policy, compliance |
| Contemplative | 0.999 | 0.423 | 0.217 | +0.050 | Strategy, red-team |

## Quick Start

```bash
# Run a session with a specific archetype
python run_longitudinal.py --arm D --seed 1 --archetype deep_learner

# Available archetypes:
#   cold_reactor, warm_improviser, hot_improviser,
#   adaptive_coordinator, deep_learner, guardian, contemplative

# Or specify gamma directly
python run_longitudinal.py --arm D --seed 1 --gamma 0.990

# Programmatic usage
from chat_anima import HUGOField
field = HUGOField.from_archetype("deep_learner", seed=42)
```


## Experiments

### ANIMA-02: Dual-Mode Ablation (200 sessions)
- 4 arms × 5 seeds × 2 modes (standard γ=0.97, persistent γ=0.995)
- Confirms: field trades fluency for identity persistence and learning

### ANIMA-03: Gamma Sweep (96 sessions)
- 8 γ values × 3 seeds × 2 passes × 2 sessions
- Maps the continuous γ → personality space
- Confirms 7 archetypes across 3 bands

## Project Structure

```
ANIMA/
├── papers/                    # Published papers (PDF)
├── docs/
│   ├── archetype_registry.md  # 7 archetype catalog with applications
│   └── behavioral_trait_catalog.md  # 14 observable traits
├── chat_anima.py              # Core: HUGOField with archetype presets
├── run_longitudinal.py        # Session runner (--archetype flag)
├── run_full_ablation.py       # ANIMA-02 ablation orchestrator
├── run_gamma_sweep.py         # ANIMA-03 gamma sweep orchestrator
├── coherence_scorer.py        # DCS, NRF, ILR, PSI scoring
├── ablation_config.py         # Arm configurations (A/B/C/D)
├── pcpt_tasks.py              # PCPT scenario definitions
└── logs/
    └── gamma_sweep/
        └── gamma_sweep_results.json  # Sweep results
```

## Related Publications

- [Kappa-FIN](https://github.com/aprimora-ai/Kappa-FIN) — Topological crisis detection (DOI: 10.5281/zenodo.19068079)
- [Kappa-LLM](https://doi.org/10.5281/zenodo.15084857) — LLM hallucination detection
- [Kappa-Radiante](https://doi.org/10.5281/zenodo.18940478) — Structural regime transitions

## Citation

```bibtex
@software{ohio2026anima,
  author = {Ohio, David},
  title = {ANIMA: Autonomous Neurodynamic Integration for Modular Agents},
  year = {2026},
  doi = {10.5281/zenodo.19111951},
  url = {https://github.com/aprimora-ai/hugo-framework-anima},
  license = {CC-BY-4.0}
}
```

---

*David Ohio | Independent Researcher | odavidohio@gmail.com*

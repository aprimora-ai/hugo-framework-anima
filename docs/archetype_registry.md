# HUGO Framework — Archetype Registry
# David Ohio | Independent Researcher | odavidohio@gmail.com
# March 19, 2026
# Based on ANIMA-02 (dual ablation) + ANIMA-03 (gamma sweep, 96 sessions)

---

## Empirically Confirmed Archetypes (ANIMA-03)

### IMPROVISER (γ = 0.90 – 0.97)

**Core trait:** Conversational fluency dominates. The field dissipates
fast enough that each session is nearly independent.

| Metric | Value Range |
|--------|-------------|
| DCS    | 0.60 – 0.64 |
| ILR    | 0.07 – 0.10 |
| PSI    | +0.14 – +0.24 |
| θ_var  | 0.0002 – 0.008 |

**Sub-profiles observed in data:**


#### COLD REACTOR (γ ≈ 0.90)
  DCS=0.622, ILR=0.092, PSI=+0.195, θ_var=0.0002
  Near-zero emotional dynamics. Maximally stable output. Responds
  quickly and consistently but without nuance or adaptation depth.
  
  Best for:
    - High-throughput customer service / FAQ
    - Data extraction and formatting
    - Repetitive classification tasks
    - API-facing agents where predictability is paramount
  
  Weaknesses:
    - Cannot build rapport across sessions
    - Does not learn from mistakes
    - Lacks emotional resonance in communication

#### WARM IMPROVISER (γ ≈ 0.93)
  DCS=0.620, ILR=0.100, PSI=+0.242, θ_var=0.0014
  Slight emotional coloring. Best pure-learning score within the
  Improviser band. Balances speed with a hint of adaptation.
  
  Best for:
    - Creative brainstorming sessions
    - First-draft content generation
    - Exploratory conversations with users
    - Rapid prototyping of ideas


#### HOT IMPROVISER (γ ≈ 0.97)
  DCS=0.637, ILR=0.067, PSI=+0.205, θ_var=0.0081
  Highest DCS in the entire sweep. Most emotionally reactive
  Improviser. The field creates just enough internal tension to
  sharpen conversational performance.
  
  Best for:
    - Negotiations and persuasion tasks
    - Real-time crisis communication
    - Live presentations and Q&A
    - Tasks where verbal precision matters most
  
  Weaknesses:
    - Lowest ILR of any profile (0.067) — almost no identity carry-over
    - Emotional reactivity without depth

---

### GENERALIST (γ = 0.985 – 0.990)

**Core trait:** Adaptive learning dominates. The field retains enough
structure to learn but not enough to rigidify. This is the only
profile range where PSI exceeds +0.25.

| Metric | Value Range |
|--------|-------------|
| DCS    | 0.51 – 0.60 |
| ILR    | 0.11 – 0.20 |
| PSI    | +0.26 – +0.36 |
| θ_var  | 0.001 – 0.002 |


**Critical observation:** The Generalist has the LOWEST theta_var
in the entire sweep (0.001-0.002). This is not "in between" — it is
a unique zone of emotional calm where learning is maximized. The field
provides just enough structural scaffolding to dampen emotional noise
while remaining plastic enough to update.

#### ADAPTIVE COORDINATOR (γ ≈ 0.985)
  DCS=0.603, ILR=0.108, PSI=+0.255, θ_var=0.0018
  Leans toward the Improviser side. Good fluency with genuine learning.
  
  Best for:
    - Project management across multiple sessions
    - Team coordination where context accumulates
    - Adaptive tutoring systems
    - Multi-step problem solving with feedback

#### DEEP LEARNER (γ ≈ 0.990)
  DCS=0.507, ILR=0.200, PSI=+0.359, θ_var=0.0011
  THE SWEET SPOT. Highest PSI in the entire sweep (+0.359 = 36%
  improvement between passes). The agent that learns the most from
  its own experience.
  
  Best for:
    - Iterative research and analysis
    - Code review with accumulated context
    - Medical/legal case analysis over multiple sessions
    - Any task where "getting better over time" is the priority
  
  Weaknesses:
    - DCS drops below 0.55 — noticeably less fluent than Improvisers
    - Requires multi-session engagement to show its advantage


---

### INTEGRATOR (γ = 0.995 – 0.999)

**Core trait:** Identity persistence dominates. The field is so
persistent that it constrains behavior — strong identity but
resistance to change.

| Metric | Value Range |
|--------|-------------|
| DCS    | 0.42 – 0.48 |
| ILR    | 0.22 – 0.24 |
| PSI    | +0.05 – +0.14 |
| θ_var  | 0.010 – 0.016 |

#### GUARDIAN (γ ≈ 0.995)
  DCS=0.484, ILR=0.242, PSI=+0.135, θ_var=0.0098
  Highest ILR of any profile. Still retains some adaptive capacity
  (PSI > 0.10). The field preserves identity strongly while allowing
  measured evolution.
  
  Best for:
    - Policy enforcement and compliance monitoring
    - Brand voice consistency across channels
    - Long-running governance agents
    - Sensitive context where identity drift is dangerous
    - Institutional memory keeper


#### CONTEMPLATIVE (γ ≈ 0.999)
  DCS=0.423, ILR=0.217, PSI=+0.050, θ_var=0.0156
  Paradoxical profile: HIGHEST theta_var (0.0156) despite lowest
  adaptation. The field is so persistent that internal oscillations
  amplify without dissipating. Rich internal experience, poor
  external expression.
  
  Best for:
    - Deep philosophical or ethical deliberation
    - Long-term strategic scenario modeling
    - Tasks where "thinking deeply" matters more than "answering fast"
    - Adversarial red-team analysis (resists persuasion)
  
  Weaknesses:
    - Lowest DCS (0.423) — communication quality suffers
    - Near-zero learning (PSI=+0.05) — almost immutable
    - May appear unresponsive or repetitive to users

---

## Summary Table

| Archetype           | γ     | DCS   | ILR   | PSI    | θ_var  | Best Application |
|---------------------|-------|-------|-------|--------|--------|------------------|
| Cold Reactor        | 0.900 | 0.622 | 0.092 | +0.195 | 0.0002 | High-throughput, API agents |
| Warm Improviser     | 0.930 | 0.620 | 0.100 | +0.242 | 0.0014 | Brainstorming, content gen |
| Hot Improviser      | 0.970 | 0.637 | 0.067 | +0.205 | 0.0081 | Negotiation, live comm |
| Adaptive Coordinator| 0.985 | 0.603 | 0.108 | +0.255 | 0.0018 | Project mgmt, tutoring |
| Deep Learner        | 0.990 | 0.507 | 0.200 | +0.359 | 0.0011 | Research, iterative analysis |
| Guardian            | 0.995 | 0.484 | 0.242 | +0.135 | 0.0098 | Policy, compliance, memory |
| Contemplative       | 0.999 | 0.423 | 0.217 | +0.050 | 0.0156 | Strategy, ethics, red-team |


---

## Usage: Command-Line Interface

Archetypes are available as --archetype presets in ANIMA runners:

```bash
# Spawn a Deep Learner agent
python run_longitudinal.py --arm D --seed 1 --archetype deep_learner

# Spawn a Hot Improviser
python run_longitudinal.py --arm D --seed 1 --archetype hot_improviser

# Available archetypes:
#   cold_reactor, warm_improviser, hot_improviser,
#   adaptive_coordinator, deep_learner, guardian, contemplative
```

---

*David Ohio | Independent Researcher | odavidohio@gmail.com*
*HUGO AGI Framework | March 19, 2026*
*License: CC BY 4.0*

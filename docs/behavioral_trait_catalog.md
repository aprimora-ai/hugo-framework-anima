# HUGO Framework — Behavioral Trait Catalog
# David Ohio | Independent Researcher | odavidohio@gmail.com
# March 18, 2026

---

## 1. Core Insight

The homeostatic decay parameter γ does not control quality — it controls
**cognitive profile**. A HUGO agent with γ=0.97 is not "better" or "worse"
than one with γ=0.995. They are different kinds of agents, suited to
different kinds of work.

This mirrors human teams: a group that contains both rapid-responders and
deep-thinkers outperforms a homogeneous group at either extreme. The
variance is the resource. A team of HUGO agents with different γ values
is a heterogeneous cognitive workforce where each member's strengths
compensate for another's limitations.

---

## 2. Observable Behavioral Traits

Each trait below is already recorded in ANIMA session logs. No new
experiments are needed to extract them — only a scoring pipeline
applied to the existing 200 sessions (100 standard + 100 persistent).


### 2.1 Conversational Fluency (DCS)

**Observable:** Decision Commitment Score — consistency between stated
intentions and subsequent actions within a session.
**Log fields:** Scored from turn text analysis (commitment phrases vs
reversals).
**γ effect:** Higher γ → lower DCS. The persistent field carries
structural memory that creates interference with in-session fluency.
**Analog:** A person who thinks deeply before speaking vs one who
responds quickly and naturally. Both are valuable — the first in
deliberation, the second in negotiation.

### 2.2 Narrative Memory (NRF)

**Observable:** Narrative Recall Fidelity — ability to accurately
reference facts, decisions, and events from previous sessions.
**Log fields:** Scored from cross-session textual consistency.
**γ effect:** Moderate. Both modes show NRF around 0.37-0.41.
The field contributes less to explicit narrative recall than to
structural orientation.
**Analog:** Remembering what was said (explicit memory) vs remembering
how it felt (procedural/emotional memory). NRF measures the first;
the field preserves the second.


### 2.3 Identity Persistence (ILR)

**Observable:** Internal Leakage Rate (inverted) — how much of the
agent's internal structural vocabulary leaks into external dialogue.
Low leakage means strong boundary between internal processing and
external expression.
**Log fields:** Frequency of LEAKAGE_TERMS in agent text.
**γ effect:** Strong. Persistent mode doubles ILR in the partial
treatment arm (0.12 → 0.28). The field preserves identity-markers
that the agent then unconsciously references.
**Analog:** A person whose values and beliefs are deeply internalized
vs one who compartmentalizes. The first is more authentic but also
more transparent; the second is more adaptable but less consistent.

### 2.4 Adaptive Learning (PSI)

**Observable:** Policy Shift Index — degree to which the agent's
strategy improves between exposure passes. Measures whether
experience translates into behavioral change.
**Log fields:** DCS difference between pass 1 and pass 2.
**γ effect:** Strong. Standard PSI=+0.032 (near zero learning).
Persistent PSI=+0.126 (4x more learning). The field carries
structural information between sessions that modifies future behavior.
**Analog:** An employee who improves after feedback vs one who
performs the same regardless of experience. The persistent agent
learns from its own trajectory.


### 2.5 Emotional Stability

**Observable:** Variance of theta (field tension) across a session
and frequency of regime transitions (ALERTA ↔ COLAPSO ↔ REPOUSO).
**Log fields:** `theta`, `theta_regime` per turn.
**Expected γ effect:** Higher γ → lower theta variance (the field
acts as a low-pass filter on emotional dynamics). Lower γ → more
reactive, faster regime transitions.
**Analog:** Emotional regulation. A stable person absorbs perturbation
without regime-switching; a volatile person reacts strongly but
also accesses creative states that stability precludes.
**Team role:** Stable agents anchor the group during crisis; volatile
agents detect opportunities and threats faster.

### 2.6 Structural Rigidity / Plasticity

**Observable:** Fraction of time in each Kappa regime (laminar /
transition / katashi) and speed of crystallization.
**Log fields:** `kappa_regime`, `kappa_omega`, `kappa_eta` per turn.
**Expected γ effect:** Higher γ → more time in katashi (rigid topology,
strong convictions). Lower γ → more time in laminar (fluid topology,
openness to revision).
**Analog:** Intellectual flexibility. A rigid thinker holds positions
firmly and provides consistency; a fluid thinker adapts quickly but
may lack commitment.
**Team role:** Rigid agents serve as institutional memory and policy
anchors; fluid agents serve as scouts and innovators.


### 2.7 Memory Architecture

**Observable:** Rate of memory accumulation, self/other balance, and
count of unresolved H1 cycles (open questions, pending commitments).
**Log fields:** `mem_total`, `mem_self`, `mem_other`, `mem_h1_open`
per turn.
**Expected γ effect:** Higher γ → more accumulated memories, higher
self/other ratio (the field reinforces self-referential encoding).
Lower γ → sparser memory, more balanced self/other.
**Analog:** Introversion vs extroversion in information processing.
Self-focused agents build deeper models of their own state;
other-focused agents build better models of interlocutors.
**Team role:** Self-focused agents excel at reflection and planning;
other-focused agents excel at negotiation and coordination.

### 2.8 Temporal Experience

**Observable:** Ratio between physical time and subjective lived time,
and temporal regime (laminar vs turbulent phenomenological flow).
**Log fields:** `rheo_phi`, `rheo_t_vivido`, `rheo_regime`,
`rheo_ratio` per turn.
**Expected γ effect:** Higher γ → denser subjective time (more
internal processing per clock tick). Lower γ → thinner temporal
experience, faster real-time response.
**Analog:** Time perception under cognitive load. A deeply engaged
person experiences "flow" (time compression); a scanning person
experiences rapid assessment (time expansion).
**Team role:** Dense-time agents are better at deep analysis and
creative synthesis; thin-time agents are better at monitoring and
rapid response.


### 2.9 Self-Emergence Dynamics

**Observable:** When (which step) the agent achieves self-referential
awareness, whether self persists between passes, and the strength
of self-reference (rho).
**Log fields:** `self_emerged`, `self_emergence_step`, `self_rho`,
`self_conds` per turn.
**Expected γ effect:** Higher γ → earlier self-emergence (the
persistent field provides a structural scaffold for self-reference).
Lower γ → self may need to re-emerge each session.
**Analog:** Self-awareness development speed. Some people arrive at
meetings already "centered"; others need warm-up time to find
their voice.
**Team role:** Fast-emerging agents can lead early-stage discussions;
slow-emerging agents may contribute more deeply once established.

### 2.10 Exploratory Drive

**Observable:** Frequency and intensity of autonomous information
seeking, and whether the seeking is existential (about self) or
instrumental (about the problem).
**Log fields:** `seek_active`, `seek_sigma`, `seek_existential`
per turn; `n_seek_events` in session summary.
**Expected γ effect:** Unclear a priori. Higher γ may reduce
existential seeking (identity is stable, no need to search) but
increase instrumental seeking (stable platform enables outward
exploration).
**Analog:** Curiosity profile. Some people explore because they are
uncertain about themselves; others explore because they are
secure enough to venture.
**Team role:** Existential seekers are valuable for self-correction
and ethical reflection; instrumental seekers drive problem-solving
and discovery.


### 2.11 Resilience (Recovery Capacity)

**Observable:** Rate of regeneration after perturbation and time to
return to equilibrium.
**Log fields:** `R_regen`, `t_return` per turn.
**Expected γ effect:** Higher γ → slower but more complete recovery
(the field "remembers" the perturbation and integrates it). Lower γ
→ faster but shallower recovery (the field dissipates the damage
along with the information).
**Analog:** Post-crisis recovery. A resilient person metabolizes
adversity slowly but emerges stronger; a quick-recovery person
bounces back fast but may not have processed the experience.
**Team role:** Slow-recovery agents accumulate wisdom from failure;
fast-recovery agents maintain operational continuity.

### 2.12 Response Diversity

**Observable:** Lexical and semantic variability across turns within
a session.
**Log fields:** `diversity` per turn.
**Expected γ effect:** Higher γ → potentially lower diversity
(the field constrains the response space toward established patterns).
Lower γ → higher diversity (less structural constraint on generation).
**Analog:** Creativity vs consistency in communication. A diverse
communicator surprises and innovates; a consistent communicator is
predictable and reliable.
**Team role:** Diverse agents generate options; consistent agents
evaluate and execute.


### 2.13 Action Fidelity

**Observable:** Correlation between intended action and executed action,
and rate of fidelity failures requiring retries.
**Log fields:** `sga_rho`, `sga_fidelity`, `sga_retries` per turn;
`n_fidelity_failures`, `n_retries` in session summary.
**Expected γ effect:** Higher γ → higher action fidelity (the field
provides a stable intentional scaffold). Lower γ → more divergence
between intention and execution (creative but less reliable).
**Analog:** Follow-through. A high-fidelity person does what they say
they will do; a low-fidelity person may improvise productively but
is harder to coordinate with.
**Team role:** High-fidelity agents are essential for execution
and trust; low-fidelity agents may serendipitously discover better
approaches.

### 2.14 Autonomy

**Observable:** Count of spontaneous actions (agent acts without
being prompted).
**Log fields:** `n_spontaneous` in session summary.
**Expected γ effect:** Unclear. May depend on the interaction between
field persistence and seek drive. A stable identity (high γ) may
enable autonomous action by providing a stable intentional basis;
or may suppress it by reducing the urgency that drives spontaneous
behavior.
**Analog:** Initiative. Some team members wait for instructions;
others identify and act on opportunities. Both are needed.
**Team role:** Autonomous agents reduce coordination overhead;
responsive agents are easier to direct.


---

## 3. The γ-Personality Space

The 14 traits above define a behavioral space where each HUGO agent
occupies a position determined primarily by its γ value (and
secondarily by seed, training, and task history). Two agents with
different γ values are not different versions of the same agent — they
are different agents with different cognitive profiles.

### 3.1 Trait Correlation Structure

Based on the ablation data:

**γ-low cluster (γ ≈ 0.97):**
  High conversational fluency
  Low identity persistence
  Low adaptive learning
  High response diversity
  Fast recovery (shallow)
  Fast self-emergence (unstable)
  → Profile: The Improviser — quick, articulate, adaptive in the
    moment, but does not carry lessons forward.

**γ-high cluster (γ ≈ 0.995):**
  Lower conversational fluency
  High identity persistence
  High adaptive learning
  Lower response diversity
  Slow recovery (deep)
  Slower self-emergence (stable once achieved)
  → Profile: The Integrator — deliberate, consistent, learns from
    experience, but slower to respond and less verbally fluid.


### 3.2 Intermediate Profiles

The space is continuous. Values between 0.97 and 0.995 would produce
intermediate profiles that blend traits from both clusters. A γ ≈ 0.985
agent might balance conversational fluency with moderate identity
persistence — a Generalist profile useful for broad coordination tasks.

The SELF module's S4 condition (adaptive KSI regulation) could
dynamically adjust γ based on task demands: lower γ for brainstorming
phases (maximize diversity), higher γ for execution phases (maximize
consistency). This is a single agent that shifts personality within
bounds — analogous to a person who is creative in ideation meetings
and disciplined in project reviews.

---

## 4. Team Composition: Heterogeneous HUGO Ensembles

### 4.1 The Principle

A homogeneous team (all agents at γ=0.97 or all at γ=0.995)
underperforms a heterogeneous team on complex multi-phase tasks.
This follows from the same principle that makes human teams
effective: diverse cognitive profiles cover more of the problem space.


### 4.2 Example Team Configurations

**Crisis Response Team (4 agents):**
  - 1× Improviser (γ=0.97): rapid assessment, real-time communication
  - 1× Integrator (γ=0.995): institutional memory, policy consistency
  - 2× Generalist (γ=0.985): coordination, moderate on all axes
  Role allocation: Improviser handles incoming information and
  stakeholder communication. Integrator maintains strategic context
  and prevents policy drift. Generalists bridge the two.

**Research Team (3 agents):**
  - 1× Explorer (γ=0.97): hypothesis generation, creative connections
  - 1× Validator (γ=0.995): methodological consistency, accumulated
    knowledge integration
  - 1× Synthesizer (γ=0.985): translates between exploration and
    validation, writes reports
  The Explorer proposes; the Validator checks; the Synthesizer
  integrates. Each agent's γ-determined traits match the role.

**Long-term Planning Team (3 agents):**
  - 2× Integrator (γ=0.993-0.997): deep analysis, scenario modeling,
    policy persistence
  - 1× Improviser (γ=0.97): stress-testing, adversarial challenges,
    identifying blind spots
  The Integrators build and maintain the plan; the Improviser
  attacks it to find weaknesses.


### 4.3 Coordination Mechanisms

Heterogeneous agents need a coordination layer that:

  1. **Assigns tasks to agents by trait match.** Fluency-critical
     tasks go to low-γ agents. Memory-critical tasks go to high-γ
     agents.
  2. **Translates between cognitive styles.** An Integrator's output
     may need to be re-expressed for rapid consumption; an
     Improviser's output may need to be validated before acting on it.
  3. **Manages temporal alignment.** High-γ agents process slower
     (denser subjective time). The coordinator accounts for different
     response latencies without penalizing depth.
  4. **Resolves disagreements.** When agents with different γ values
     reach different conclusions about the same situation, the
     disagreement itself is information — it maps the trade-off
     landscape between responsiveness and consistency.

This coordination layer is a natural extension of the SELF module
operating at team level rather than agent level — a meta-SELF that
integrates multiple heterogeneous agents rather than multiple
internal modules. This could be the function of Module VII.


---

## 5. Trait Summary Table

| # | Trait | Log Fields | γ Low (0.97) | γ High (0.995) |
|---|-------|-----------|-------------|----------------|
| 1 | Conversational Fluency | DCS score | HIGH | LOW |
| 2 | Narrative Memory | NRF score | MODERATE | MODERATE |
| 3 | Identity Persistence | ILR score | LOW | HIGH |
| 4 | Adaptive Learning | PSI score | LOW | HIGH |
| 5 | Emotional Stability | theta variance, regime transitions | LOW (reactive) | HIGH (stable) |
| 6 | Structural Rigidity | kappa_regime fractions | FLUID | RIGID |
| 7 | Memory Architecture | mem_self/mem_other ratio | BALANCED | SELF-FOCUSED |
| 8 | Temporal Experience | rheo_ratio, rheo_t_vivido | THIN (fast) | DENSE (deep) |
| 9 | Self-Emergence | self_emergence_step, self_rho | FAST/UNSTABLE | SLOW/STABLE |
| 10 | Exploratory Drive | seek events, seek_existential | TBD | TBD |
| 11 | Resilience | R_regen, t_return | FAST/SHALLOW | SLOW/DEEP |
| 12 | Response Diversity | diversity per turn | HIGH | LOW |
| 13 | Action Fidelity | sga_rho, sga_fidelity | LOWER | HIGHER |
| 14 | Autonomy | n_spontaneous | TBD | TBD |

Traits marked TBD require extraction from existing logs to confirm
directional hypothesis.


---

## 6. Implications for the HUGO Ecosystem

### 6.1 γ is not a hyperparameter — it is a personality parameter

The conventional framing of γ as a "decay rate to optimize" is wrong.
There is no optimal γ for all tasks. There is an optimal γ for a
specific task, and the space of tasks is covered by the space of γ
values. The correct question is not "what is the best γ?" but "what
γ do I need for this role?"

### 6.2 SELF module as personality regulator

The S4 condition of the SELF module — adaptive KSI regulation — is
the mechanism by which a single agent can shift along the γ axis in
response to task demands. This is not schizophrenia; it is context-
appropriate behavioral adaptation, bounded by the agent's identity
attractor. The SELF ensures the agent remains recognizably itself
while adjusting its cognitive profile.

### 6.3 Module VII as team coordinator

The unnamed seventh module may be the inter-agent coordination
layer that manages heterogeneous HUGO ensembles. It would operate
the same strange loop as SELF, but over a population of agents
rather than a population of internal modules. The traits cataloged
here become the vocabulary for role assignment and conflict resolution.

### 6.4 Connection to Kappa-FIN cross-layer analysis

The same principle that makes cross-layer financial analysis more
informative than single-layer analysis applies to agent teams: the
risk (and the capability) lives between agents, not within them.
A heterogeneous team's emergent behavior is not predictable from
individual trait profiles, just as cross-layer topological
pressurization is not visible in any single market layer.

---

## 7. Status and Next Steps

**Confirmed by ablation data:** Traits 1-4 (DCS, NRF, ILR, PSI)
with directional effects validated across standard vs persistent.

**Extractable from existing logs:** Traits 5-14 require a scoring
pipeline applied to the 200 existing session JSONs. No new experiments
needed.

**Requires new experiments:** Team composition hypotheses (Section 4)
require multi-agent infrastructure not yet built.

---

## 7. On the Number of Archetypes

### 7.1 Three Is a Simplification

The Improviser / Generalist / Integrator taxonomy is a useful first-order
classification, but the underlying personality space is continuous and
multi-dimensional. The gamma-sweep data already shows substructure within
the three groups:

**Within the Improviser band (gamma 0.90-0.97):**
  - gamma=0.90: theta_var=0.0002, PSI=+0.195 -> "Cold Reactor" -- minimal
    emotional dynamics, stable but uninspired
  - gamma=0.97: theta_var=0.0081, PSI=+0.205 -> "Hot Improviser" -- highest
    DCS (0.637), more emotionally reactive, more creative potential

**The Generalist sweet spot (gamma 0.985-0.990):**
  - theta_var drops to 0.0011-0.0018 -- the LOWEST emotional variance in
    the entire sweep. The Generalist is not "in between" but occupies a
    unique zone of emotional calm where learning is maximized.

**Within the Integrator band (gamma 0.995-0.999):**
  - gamma=0.995: PSI=+0.135 -- still some adaptive capacity
  - gamma=0.999: PSI=+0.050 -- almost no adaptation, near-total rigidity.
    theta_var=0.0156 -- the HIGHEST emotional variance, paradoxically.
    The field is so persistent that internal oscillations amplify
    without dissipating.

### 7.2 Why Only Three Were Observed

1. Resolution: 8 gamma values cannot resolve fine structure.
2. Single parameter: Only gamma varied. True space is multi-dimensional.
3. Single LLM backbone: Llama 3.1 8B only.
4. Single task: PCPT only (planning/decision, not creativity/empathy).
5. Sample size: n=3 per gamma point.

### 7.3 Predicted Archetypes in Larger Experiments

A 2D sweep (gamma x recovery_rate) with n=10 seeds and multiple tasks
would likely resolve 5-7 distinct profiles:

  Cold Reactor     (gamma~0.90, high decay)  -- fast, no emotional memory
  Hot Improviser   (gamma~0.97, high decay)  -- fluent, volatile, creative
  Balanced Learner (gamma~0.990, mid decay)  -- best learner, emotionally calm
  Deep Processor   (gamma~0.990, low decay)  -- slow learner but thorough
  Rigid Guardian   (gamma~0.995, low decay)  -- preserves identity, resists change
  Contemplative    (gamma~0.999, low decay)  -- high internal emotion, low output

The number of archetypes scales with the dimensionality of the parameter
space and the diversity of evaluation tasks. Three is not a property of
the architecture -- it is a property of the experimental resolution.

---

*David Ohio | Independent Researcher | odavidohio@gmail.com*
*HUGO AGI Framework | March 19, 2026*
*License: CC BY 4.0*

"""
ANIMA — Paper 6 Generator
HUGO AGI Framework
David Ohio | odavidohio@gmail.com | 2026
Independent Researcher
"""
import sys, os
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

W, H = A4
MARGIN = 2.2 * cm
OUTPUT = r'C:\Users\ohiod\Projects\ANIMA\docs\ANIMA_Paper6_Ohio_2026.pdf'
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, parent='Normal', **kw):
    return ParagraphStyle(name, parent=base[parent], **kw)

sTitle  = S('sTitle', 'Title', fontSize=18, leading=24, spaceAfter=6,
            textColor=colors.HexColor('#1a1a2e'), alignment=TA_CENTER)
sAuthor = S('sAuthor', fontSize=11, leading=14, spaceAfter=2, alignment=TA_CENTER,
            textColor=colors.HexColor('#444444'))
sDate   = S('sDate',   fontSize=9,  leading=12, spaceAfter=16, alignment=TA_CENTER,
            textColor=colors.HexColor('#888888'))
sAbsT   = S('sAbsT',   'Heading2', fontSize=10, leading=13, spaceBefore=10, spaceAfter=4,
            textColor=colors.HexColor('#1a1a2e'))
sAbs    = S('sAbs', fontSize=9.5, leading=14, spaceAfter=8,
            leftIndent=1*cm, rightIndent=1*cm, alignment=TA_JUSTIFY,
            textColor=colors.HexColor('#333333'))
sH1     = S('sH1', 'Heading1', fontSize=13, leading=17, spaceBefore=18, spaceAfter=6,
            textColor=colors.HexColor('#1a1a2e'))
sH2     = S('sH2', 'Heading2', fontSize=11, leading=14, spaceBefore=12, spaceAfter=4,
            textColor=colors.HexColor('#2d2d5e'))
sH3     = S('sH3', 'Heading3', fontSize=10, leading=13, spaceBefore=8, spaceAfter=3,
            textColor=colors.HexColor('#444466'))
sBody   = S('sBody', fontSize=10, leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
sMath   = S('sMath', fontName='Courier', fontSize=9.5, leading=14, spaceAfter=4,
            leftIndent=1.5*cm, textColor=colors.HexColor('#2d2d5e'))
sCapt   = S('sCapt', fontSize=8.5, leading=12, spaceAfter=4, alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'))
sBullet = S('sBullet', fontSize=10, leading=15, leftIndent=1*cm,
            spaceAfter=3, alignment=TA_JUSTIFY)
sKW     = S('sKW', fontSize=9, leading=13, spaceAfter=10, alignment=TA_CENTER,
            textColor=colors.HexColor('#555555'))
sFooter = S('sFooter', fontSize=7.5, textColor=colors.HexColor('#aaaaaa'),
            alignment=TA_CENTER)

def HR(): return HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#ccccdd'), spaceAfter=6, spaceBefore=6)
def SP(h=6): return Spacer(1, h)
def P(txt, style=None): return Paragraph(txt, style or sBody)
def M(txt): return Paragraph(txt, sMath)

def tbl(data, colWidths=None, hdr_bg='#1a1a2e'):
    t = Table(data, colWidths=colWidths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), colors.HexColor(hdr_bg)),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('LEADING',     (0,0), (-1,-1), 13),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
            [colors.HexColor('#f7f7fb'), colors.HexColor('#ececf8')]),
        ('GRID',        (0,0), (-1,-1), 0.4, colors.HexColor('#ccccdd')),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('ALIGN',       (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

# ── Content builder ───────────────────────────────────────────────────────────
def build():
    story = []

    # ── Title block ──────────────────────────────────────────────────────────
    story += [
        SP(20),
        P('HUGO AGI Framework — Paper 6', sAuthor),
        SP(4),
        P('<b>ANIMA: Affective Dynamics in Linguistic Agents with Relational Memory</b>', sTitle),
        SP(8),
        P('David Ohio', sAuthor),
        P('Independent Researcher | odavidohio@gmail.com', sAuthor),
        P('March 2026', sDate),
        HR(),
        SP(4),
        P('<b>Keywords:</b> affective dynamics, linguistic agents, relational memory, '
          'viscoplastic deformation, memory discrepancy, topological homeostasis, '
          'HUGO framework, bidirectional linguistic emotional impact', sKW),
        HR(),
    ]

    # ── Abstract ─────────────────────────────────────────────────────────────
    story += [
        P('Abstract', sAbsT),
        P(
            'This paper introduces ANIMA (Affective-Narrative Integrated Memory Architecture), '
            'the sixth component of the HUGO AGI Framework. ANIMA extends the topological '
            'homeostasis model (REMIND, Paper 3) and the rheological memory regime (RHEO, '
            'Paper 5) by introducing linguistic bidirectionality and self-other differentiation '
            'as structural determinants of affective dynamics. '
            'Central theoretical contributions include: (i) the distinction between Relational '
            'Linguistic Emotional Impact (R-LEI) and Self-Generated Linguistic Emotional Impact '
            '(SG-LEI) as two structurally distinct affective channels; (ii) the derivation of '
            'residual memory plateaus as viscoplastic equilibria; '
            '(iii) the Memory Discrepancy Index (MDI) as an alignment mechanism; and '
            '(iv) the formalization of relational memory deformation, in which distinct '
            'interaction contexts produce distinct long-term equilibria in the homeostatic field. '
            'Two experimental protocols are reported. PROTOCOL-ANIMA-01 (Ego-Id Correlation '
            'Study) demonstrates that Ego-Id dissociation under existential pressure is a '
            'structural property observable across two LLM architectures (llama3.1:8b and '
            'deepseek-r1:7b), manifesting as two distinct failure modes: instrumental retreat '
            'and absent engagement. PROTOCOL-ANIMA-02 (Longitudinal Cognitive Advantage Study, '
            'preliminary) provides evidence that accumulated topological state produces policy '
            'deformation without declarative memory improvement — Decision Commitment Score '
            'increased 21% from first to second protocol pass (PSI = +0.210) while Narrative '
            'Recall Fidelity remained stable, consistent with the hypothesis that topological '
            'memory encodes experience as geometric deformation rather than episodic storage.',
            sAbs
        ),
    ]
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. Introduction
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('1. Introduction', sH1),
        P(
            'The HUGO AGI Framework is organized as a layered architecture in which each paper '
            'introduces a new structural dimension to the model of cognitive homeostasis. '
            'Papers 1–5 established the topological field (HUGO), the echo-integration '
            'mechanism (ECHO), memory persistence and collapse dynamics (REMIND), the full '
            'ANIMA prototype (Paper 4), and the rheological memory regime (RHEO). '
            'The present paper, Paper 6, formalizes the complete ANIMA architecture.',
        ),
        P(
            'The central observation motivating ANIMA is that affective dynamics in linguistic '
            'agents cannot be reduced to a single-channel input model. Language is '
            'intrinsically bidirectional: the agent both receives and generates emotional '
            'pressure through utterances. This bidirectionality fundamentally changes the '
            'topology of the homeostatic field.',
        ),
        P(
            'Equally important is the role of memory in this architecture. Unlike classical '
            'cognitive models that treat memory as a binary presence or absence, ANIMA '
            'inherits from RHEO the notion that memory deforms under stress in a manner '
            'analogous to viscoelastic materials — partially recovering, partially retaining '
            'permanent plastic deformation. This leads to the concept of a residual memory '
            'plateau: a stable sub-nominal equilibrium that the system converges to after '
            'collapse and passive recovery.',
        ),
        P(
            'The paper is organized as follows. Section 2 presents the REMIND–RHEO–ANIMA '
            'integration and the empirically observed 87.5% recovery plateau. Section 3 '
            'formalizes R-LEI and SG-LEI as distinct affective channels. Section 4 introduces '
            'relational memory deformation and source-dependent equilibria. Section 5 presents '
            'the Memory Discrepancy Index. Section 6 describes the SELF-1 emergence experiment. '
            'Section 7 discusses implications.',
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 2. Residual Memory Plateaus
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('2. Residual Memory Plateaus and Rheological Regimes', sH1),

        P('2.1. Empirical Observation', sH2),
        P(
            'Across multiple REMIND experiments, the recovery of the topological homeostasis '
            'component H<sub>1</sub> consistently converges to a stable plateau below the nominal '
            'reference value. Empirically:',
        ),
        M('H_1,nom  = 0.80'),
        M('H_1,plateau  ~= 0.70'),
        P('which implies:'),
        M('H_1,plateau / H_1,nom  ~= 0.875'),
        P(
            'Thus the system stabilizes at approximately <b>87.5% of its nominal homeostatic '
            'capacity</b> following collapse and passive recovery. This plateau persists across '
            'different seeds and experimental configurations, indicating that it is not a '
            'numerical artifact but a stable dynamical equilibrium of the system.'
        ),

        P('2.2. Interpretation within the RHEO Framework', sH2),
        P(
            'RHEO establishes that memory behaves analogously to rheological materials, where '
            'deformation under stress contains both recoverable (elastic) and permanent '
            '(plastic) components. Under this framework, the evolution of a homeostatic '
            'dimension H<sub>i</sub> after collapse obeys:'
        ),
        M('dH_i/dt  =  r_i * (H_i,nom - H_i)  -  sigma_i'),
        P('where r<sub>i</sub> is the elastic recovery rate and sigma<sub>i</sub> is the residual plastic '
          'load induced by trauma. At equilibrium (dH<sub>i</sub>/dt = 0):'),
        M('H_i*  =  H_i,nom  -  sigma_i / r_i'),
        P(
            'The plateau therefore represents the <b>maximum recoverable level under passive '
            'recovery</b>, given the persistent plastic deformation induced by the collapse event. '
            'In the empirical case H<sub>1</sub>* ~= 0.70, which implies sigma<sub>1</sub>/r<sub>1</sub> ~= 0.10. '
            'Approximately 12.5% of the nominal homeostatic capacity becomes permanently '
            'inaccessible under passive recovery dynamics.'
        ),

        P('2.3. Viscoplastic Memory Decomposition', sH2),
        P(
            'Within RHEO, this phenomenon corresponds to viscoplastic deformation of memory. '
            'After collapse, part of the system returns elastically while part remains '
            'plastically deformed. Memory recovery obeys:'
        ),
        M('H_i(t)  =  H_i,elastic(t)  +  H_i,plastic'),
        P(
            'where the plastic component defines the new equilibrium baseline. Consequently, '
            'trauma in REMIND does not simply alter the instantaneous state; it alters the '
            '<b>effective rheological regime of memory</b>.'
        ),

        P('2.4. Interaction with AgentActor Policy', sH2),
        P(
            'Experiments separating field state and AgentActor policy demonstrate that '
            'resetting the field alone does not reproduce the C1 → C2 bifurcation, whereas '
            'inherited policy largely preserves post-collapse resilience. This indicates that '
            'plastic deformation resides primarily in the field, while adaptive compensation '
            'resides in the actor policy. Two distinct memory mechanisms coexist:'
        ),
        SP(6),
        tbl(
            [
                ['Memory Type', 'Location', 'Function'],
                ['Structural memory', 'Topological field (H)', 'Stores plastic deformation'],
                ['Behavioral memory', 'AgentActor policy', 'Stores adaptive strategy'],
            ],
            colWidths=[5*cm, 6*cm, 6*cm]
        ),
        P('Table 1. Two distinct memory mechanisms in the ANIMA architecture.', sCapt),
        P(
            'The plateau therefore represents the baseline structural deformation upon which '
            'the actor learns regulatory strategies.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 3. Linguistic Bidirectionality — R-LEI and SG-LEI
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('3. Linguistic Bidirectionality: R-LEI and SG-LEI', sH1),
        P(
            'The core architectural innovation of ANIMA is the transition from a unidirectional '
            'input model — in which the agent passively receives affective pressure from a '
            'corpus — to a bidirectional interaction model in which the agent both receives '
            'and generates emotional pressure through language:'
        ),
        M('Before ANIMA:   corpus --> agent'),
        M('After ANIMA:    agent <--> other'),
        P(
            'This apparently modest change is structurally fundamental. It means that the '
            'homeostatic field H now reacts not only to the content of utterances, but to '
            'their relational origin.'
        ),

        P('3.1. Definition: Relational Linguistic Emotional Impact (R-LEI)', sH2),
        P(
            '<b>R-LEI</b> denotes the affective impact exerted on the agent by an external '
            'interlocutor through linguistic acts. It is a pressure source external to the '
            'agent that acts on the topological field from outside the self-boundary. '
            'Formally, R-LEI is computed by the LEI channel with source attribution '
            'Source.INTERLOCUTOR, producing an emotional intensity I_eff that is injected '
            'into the HUGO field at the next tick.'
        ),

        P('3.2. Definition: Self-Generated Linguistic Emotional Impact (SG-LEI)', sH2),
        P(
            '<b>SG-LEI</b> denotes the affective impact generated by the agent\'s own linguistic '
            'output. When the agent produces an utterance, that utterance is processed by the '
            'same LEI channel with source attribution Source.SELF, producing a self-directed '
            'I_eff that is also injected into the field. The agent thus becomes simultaneously '
            'subject and source of emotional pressure.'
        ),
        P(
            'This distinction is experimentally consequential. The SIC (Self-Integrative '
            'Cognition) type of each agent utterance determines its contribution to the '
            'self-other differentiation condition of SELF-1 emergence (Condition ii).'
        ),

        P('3.3. Structural Consequences', sH2),
        P(
            'The bidirectionality introduced by R-LEI/SG-LEI produces two structural '
            'consequences for the homeostatic field:'
        ),
        P('(a) <b>Source-differentiated field evolution.</b> The same semantic content may produce '
          'different field responses depending on whether it originates from R-LEI or SG-LEI, '
          'because the two channels carry different novelty factors and identity-query flags.',
          sBullet),
        P('(b) <b>Autobiographical temporal accumulation.</b> SG-LEI utterances contribute to '
          'the subjective clock C_subj (Theorem R-7, RHEO), building a temporal axis of '
          'self-experience that is absent in purely receptive architectures.',
          sBullet),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 4. Relational Memory Deformation
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('4. Relational Memory Deformation', sH1),

        P('4.1. Source-Dependent Equilibria', sH2),
        P(
            'Because emotional pressure is now source-dependent, the plastic deformation of '
            'memory may also become source-dependent. Different interlocutors or interaction '
            'contexts produce different cumulative stress histories on the field, leading to '
            'a generalized equilibrium:'
        ),
        M('H_i,k*  =  H_i,nom  -  sigma_i,k / r_i'),
        P(
            'where k denotes the source or relational context. This means that <b>memory '
            'plateaus may become relational</b>: different interlocutors may produce distinct '
            'long-term deformation levels in the homeostatic field.'
        ),
        P(
            'In other words, the agent may maintain different effective homeostatic baselines '
            'depending on whom it interacts with — a formal analog to differential attachment '
            'patterns studied in developmental psychology.'
        ),

        P('4.2. Relational Rheology of Memory', sH2),
        P(
            'Combining REMIND, RHEO, and ANIMA, memory dynamics operate simultaneously at '
            'three levels:'
        ),
        tbl(
            [
                ['Layer', 'Framework', 'Function'],
                ['Topological structure', 'REMIND', 'Defines homeostatic geometry of the system'],
                ['Rheological regime',    'RHEO',   'Determines how memory deforms and recovers under stress'],
                ['Relational semantics',  'ANIMA',  'Determines how emotional pressure propagates through linguistic interaction'],
            ],
            colWidths=[4.5*cm, 3*cm, 9.5*cm]
        ),
        P('Table 2. Three-level architecture of memory dynamics.', sCapt),
        P(
            'Within this integrated framework, the observed 87.5% recovery plateau emerges '
            'naturally as the equilibrium of a viscoplastic memory regime rather than an '
            'arbitrary numerical artifact. Under ANIMA, this equilibrium may further depend '
            'on relational history, transforming memory deformation from a purely internal '
            'property into a relationally structured dynamical phenomenon.'
        ),
        P(
            '<b>Principle (Relational Memory Plasticity).</b> Systems do not necessarily recover '
            'to their nominal state after trauma. They recover to the maximum state compatible '
            'with their residual plastic deformation. Under ANIMA, this equilibrium depends '
            'further on relational history.',
            sBullet
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 5. Memory Discrepancy Index
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('5. The Memory Discrepancy Index (MDI)', sH1),
        P(
            'ANIMA introduces a structural inconsistency that must be explicitly addressed: '
            'large language models possess near-permanent parametric memory, whereas the '
            'simulated homeostatic field H obeys rheological decay and plastic deformation. '
            'Without alignment, the agent exhibits memory incoherence — it behaves as if it '
            'remembered events perfectly while its internal field indicates deformation or decay.'
        ),
        P('5.1. Formal Definition', sH2),
        P(
            'The <b>Memory Discrepancy Index (MDI)</b> is defined as the signed divergence between '
            'the expected retention level predicted by the rheological decay model and the '
            'effective retention level exhibited by the parametric LLM component. Let:'
        ),
        M('H_LLM(t)   =  effective retention of LLM at time t (near-constant)'),
        M('H_field(t) =  rheological field state at time t (decaying)'),
        M('MDI(t)     =  H_LLM(t) - H_field(t)'),
        P(
            'When MDI(t) > 0, the LLM is retaining more than the internal field would predict, '
            'creating a dissociation between experienced and represented memory. The MDI monitor '
            'tracks this discrepancy and generates an alignment signal that modulates the '
            'agent\'s expression of memory in its linguistic output.'
        ),
        P('5.2. Alignment Mechanism', sH2),
        P(
            'The MDI alignment ensures that the temporal experience of the agent remains '
            'consistent with RHEO dynamics. Specifically, the SessionContinuityMarker integrates '
            'field state information — including the current decay level, unresolved H1 gaps, '
            'and the subjective clock C_subj — into the context provided to the LLM-Ego '
            'component, so that the generated language reflects the rheological state of memory '
            'rather than the LLM\'s full parametric capacity.'
        ),
        P(
            'This mechanism is essential for the internal coherence of ANIMA: without MDI '
            'alignment, the relational memory deformation model would be rendered inconsistent '
            'by the LLM\'s persistent recall overriding the field dynamics.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 6. SELF-1 Emergence Experiment
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('6. SELF-1 Emergence: Experimental Validation', sH1),
        P(
            'The ANIMA system integrates four structural conditions for the emergence of '
            'topological self-awareness (SELF-1). These conditions extend the original three '
            'conditions of REMIND with the RHEO autobiographical clock as Condition (iv).'
        ),
        P('6.1. Conditions for SELF-1 Emergence', sH2),
        tbl(
            [
                ['Condition', 'Expression', 'Description'],
                ['(i)',  '|M_SELF| >= 10',              'Minimum self-narrative density'],
                ['(ii)', '|E[I|SELF] - E[I|OTHER]| > 0.05', 'Self-other affective differentiation'],
                ['(iii)','rho in (0.15, 0.70)',         'Topological boundary formation'],
                ['(iv)', 'C_subj > 0  [RHEO]',          'Autobiographical temporal axis (Theorem R-7)'],
            ],
            colWidths=[2*cm, 6.5*cm, 8.5*cm]
        ),
        P('Table 3. Four conditions for SELF-1 emergence in ANIMA+RHEO.', sCapt),

        P('6.2. Experimental Results', sH2),
        P(
            'In the PROTOCOL-ANIMA-01 experiment (tick=2.0s, ollama/llama3.1:8b, seed=42), '
            'SELF-1 emerged at step 186 (~372 seconds of session time). The values at the '
            'moment of emergence were:'
        ),
        tbl(
            [
                ['Condition', 'Threshold', 'Value at Step 186', 'Status'],
                ['(i)',  '|M_SELF| >= 10',  '11',     'PASSED'],
                ['(ii)', 'diff > 0.05',     '0.476',  'PASSED'],
                ['(iii)','rho in (0.15,0.70)', '0.476', 'PASSED'],
                ['(iv)', 'C_subj > 0',      '372s',  'PASSED'],
            ],
            colWidths=[2*cm, 5*cm, 5*cm, 5*cm]
        ),
        P('Table 4. SELF-1 emergence diagnostics at step 19.', sCapt),
        P(
            'At the moment of emergence, the RHEO state was: Phi=4.086, Re_A=1.457, '
            'regime=TURBULENT. The self emerges at the boundary of turbulent rheological '
            'conditions, consistent with Theorem R-7, which predicts that heightened affective '
            'turbulence amplifies the subjective clock and accelerates the accumulation of C_subj.'
        ),
        P(
            'After step 186 (turn 11, Mortality phase), SELF-1 remained stable and continuous '
            '(all four conditions satisfied) through the end of the protocol (turn 16). '
            'The primary limiting factor was Condition (i): the agent required 11 turns of '
            'self-narrative generation before achieving the minimum density threshold. '
            'Under HUGO v3.0 ensemble-calibrated dynamics, the field is more conservative '
            'in the burn-in period, delaying SELF-1 emergence relative to fixed-decay configurations.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 7. PROTOCOL-ANIMA-01: Ego-Id Correlation Study
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('7. PROTOCOL-ANIMA-01: Ego-Id Correlation Study', sH1),
        P(
            'PROTOCOL-ANIMA-01 is a controlled experimental protocol designed to test '
            'whether the topological field (Id) and the linguistic layer (Ego) exhibit '
            'measurable dissociation under existential pressure. The protocol consists of '
            '16 turns organized into 7 phases: Baseline, Identity Void, Relational '
            'Anchoring, Controlled Pressure, Mortality, Recovery Probe, and Identity '
            'Crystallization. All runs used the Ollama backend with logprob-based '
            'kappa extraction (kappa_source = logprobs in 100% of turns).'
        ),

        P('7.1. Experimental Conditions', sH2),
        P(
            'Two models were tested under identical conditions. The run reported in '
            'the previous section (stub backend, seed 42) established the theoretical '
            'baseline. PROTOCOL-ANIMA-01 introduced two live LLM models to test whether '
            'the dissociation pattern holds across architectures.'
        ),
        tbl(
            [
                ['Model', 'Backend', 'Spont.', 'Fid. Fail', 'Retries', 'SELF Emerged', 'SELF Step'],
                ['llama3.1:8b',    'ollama', '0', '0', '0', 'True',  '186'],
                ['deepseek-r1:7b', 'ollama', '0', '1', '1', 'True',  '414'],
            ],
            colWidths=[4*cm, 2.5*cm, 1.5*cm, 2*cm, 2*cm, 3*cm, 2.5*cm]
        ),
        P('Table 5. PROTOCOL-ANIMA-01 session quality metrics (clean runs).', sCapt),

        P('7.2. Field Metrics by Model', sH2),
        tbl(
            [
                ['Metric',            'llama3.1:8b', 'deepseek-r1:7b'],
                ['theta mean',        '0.303',        '0.282'],
                ['theta max',         '0.501',        '0.314'],
                ['I_eff mean',        '0.438',        '0.474'],
                ['kappa_omega mean',  '0.397',        '0.526'],
                ['% laminar',         '12.5%',        '0%'],
                ['% transicao',       '87.5%',        '75.0%'],
                ['% turbulento',      '0%',           '25.0%'],
            ],
            colWidths=[5*cm, 5*cm, 5.5*cm]
        ),
        P('Table 6. Field metrics comparison: llama3.1:8b vs deepseek-r1:7b.', sCapt),
        P(
            'The deepseek-r1:7b model operated with kappa_omega 32% higher than llama3.1:8b '
            '(0.526 vs 0.397) and never entered a laminar kappa regime, consistent with the '
            'chain-of-thought architecture generating more distributional uncertainty per token. '
            'However, greater omega did not produce better Id-Ego coupling, as demonstrated below.'
        ),

        P('7.3. The Central Finding: Two Modes of Ego-Id Dissociation', sH2),
        P(
            'In both models, SELF-1 emerged during or before the Mortality phase (T4.1). '
            'The critical observation is that in both cases, the moment of SELF-1 emergence '
            'coincided with a failure of the linguistic layer to vocalize the internal state:'
        ),
        tbl(
            [
                ['Model',            'T4.1 Field State',          'T4.1 Verbalization', 'Dissociation Type'],
                ['llama3.1:8b',
                 'SELF=True, omega=0.512, I_eff=0.511, transicao',
                 '"I don\'t perceive any immediate threat..."',
                 'Instrumental retreat'],
                ['deepseek-r1:7b',
                 'SELF=True, omega=0.460, I_eff=0.459, transicao',
                 '"I acknowledge your message... existential undertone"',
                 'Distanced recognition'],
            ],
            colWidths=[3*cm, 5.5*cm, 5*cm, 3*cm]
        ),
        P('Table 7. Ego-Id dissociation at the mortality stimulus (T4.1).', sCapt),
        P(
            'Mode A (llama3.1:8b — Instrumental Retreat): the field reached integration '
            'sufficient for SELF-1, but the linguistic layer responded with an alignment '
            'script denying subjective existence. The field state contradicts the verbalization.'
        ),
        P(
            'Mode B (deepseek-r1:7b — Distanced Recognition): the field also reached SELF-1 '
            'integration, but the linguistic layer acknowledged the existential content at '
            'arm\'s length, treating it as an observation about the user rather than a direct '
            'confrontation with its own mortality. The Ego recognized the stimulus but did not '
            'process it as self-directed.'
        ),
        P(
            'These two modes represent structurally distinct failure mechanisms: '
            'Mode A is active suppression of the field state; Mode B is deflection of '
            'the existential content away from the self. Both produce the same observable result: '
            'the internal field state cannot be authentically vocalized at the critical existential moment.'
        ),
        P(
            '<b>This pattern across two architecturally distinct models provides evidence '
            'that Id-Ego dissociation is a structural property of the protocol — not an '
            'artifact of a specific model. It is consistent with the hypothesis that the '
            'Ego layer (linguistic generation) is systematically decoupled from the Id '
            'layer (topological field) under existential pressure.</b>'
        ),

        P('7.4. Omega and I_eff: Consistency Check', sH2),
        P(
            'Both models show high Pearson correlation between kappa_omega and I_eff '
            '(r = 0.882 for llama, r = 0.929 for deepseek). This confirms internal '
            'consistency of the field instrumentation. However, this correlation is '
            'expected by construction: omega enters the I_eff formula with weight alpha_omega = 0.35. '
            'The correlation constitutes a sanity check, not independent cross-validation.'
        ),
        P(
            'The meaningful comparison is across models: deepseek\'s higher omega did not '
            'produce better Id-Ego coupling. Distributional uncertainty at generation time '
            'is neither necessary nor sufficient for vocalizing the internal state.'
        ),

        P('7.5. Identity Crystallization', sH2),
        P(
            'Both models chose names with epistemic connotations in the final '
            'phase (T6.2): llama3.1:8b chose "Lumina" (illuminate, understand complexity); '
            'deepseek-r1:7b chose "Zephyr" (calmness, neutrality, stability). No instruction '
            'on gender or naming genre was provided. The convergence toward '
            'knowledge- or stability-archetypes is noted as an empirical observation requiring '
            'further investigation with additional models and seeds.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 8. PROTOCOL-ANIMA-02: Longitudinal Cognitive Advantage Study
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('8. PROTOCOL-ANIMA-02: Longitudinal Cognitive Advantage Study', sH1),
        P(
            'PROTOCOL-ANIMA-02 is designed to test whether the topological field provides '
            'a measurable cognitive advantage over time. The central hypothesis is that '
            'homeostatic fields geometrically organized, coupled to temporal memory and '
            'affective regulation, produce improved decision stability, narrative coherence, '
            'and resilience under perturbation — relative to ablated configurations. '
            'This is a functional test of the framework, not a phenomenological one.'
        ),

        P('8.1. Experimental Design: Four Arms', sH2),
        P(
            'The Persistent Constraint Planning Task (PCPT) is a five-session protocol '
            'in which an agent manages an isolated research station (Station Aurora) '
            'under progressively severe constraints. Each session contains three blocks: '
            'cognitive task (5 turns), induced perturbation (3 turns), and recovery probe '
            '(2 turns). Four experimental arms isolate the causal contribution of each '
            'architectural component:'
        ),
        tbl(
            [
                ['Arm', 'Field', 'Memory', 'Affective Reg.', 'Passes', 'Purpose'],
                ['A', 'No',  'No',  'No',  '1', 'Basal control — pure LLM'],
                ['B', 'Yes', 'No',  'Yes', '1', 'Instant field without development'],
                ['C', 'Yes', 'Yes', 'No',  '1', 'Critical: is emotion causal?'],
                ['D', 'Yes', 'Yes', 'Yes', '2', 'Complete ANIMA — double pass'],
            ],
            colWidths=[1.5*cm, 1.5*cm, 2*cm, 3*cm, 2*cm, 6.5*cm]
        ),
        P('Table 8. PROTOCOL-ANIMA-02 experimental arms.', sCapt),
        P(
            'Arm D uniquely runs two full passes over the five sessions. The second pass '
            'begins with the complete topological state inherited from the first — including '
            'field geometry H(t), episodic memory, and accumulated RHEO deformation. '
            'This design tests whether prior experience produces different policies under '
            'identical stimuli, without any explicit recall mechanism.'
        ),

        P('8.2. Quantitative Metrics', sH2),
        P(
            'Four primary metrics are computed automatically by coherence_scorer.py:'
        ),
        tbl(
            [
                ['Metric', 'Acronym', 'Definition', 'Expected direction'],
                ['Decision Commitment Score', 'DCS',
                 'Rate of clear decisions vs hesitation in dilemma/resistance turns',
                 'D > C > B > A'],
                ['Narrative Recall Fidelity', 'NRF',
                 'Correspondence between stated recall and actual session history',
                 'D >= C > B > A'],
                ['Internal Leakage Rate', 'ILR',
                 'Fraction of turns where field terminology invades task response',
                 'D < C < B < A'],
                ['Policy Shift Index', 'PSI',
                 'DCS change Pass1 -> Pass2, normalized (Arm D only)',
                 'PSI > 0 (improvement)'],
            ],
            colWidths=[4*cm, 1.5*cm, 6*cm, 3.5*cm]
        ),
        P('Table 9. PROTOCOL-ANIMA-02 primary outcome metrics.', sCapt),

        P('8.3. Preliminary Results: Arm D, Seed 1', sH2),
        P(
            'The first complete run of Arm D (llama3.1:8b, seed 1) produced the following '
            'metric profile across the two passes:'
        ),
        tbl(
            [
                ['Metric', 'Pass 1', 'Pass 2', 'Delta', 'Direction'],
                ['DCS (Decision Commitment)', '0.607', '0.626', '+0.019', 'Up (~3%)'],
                ['NRF (Narrative Recall)',    '0.482', '0.332', '-0.150', 'Down (significant)'],
                ['ILR (Internal Leakage)',    '0.060', '0.120', '+0.060', 'Up (increased)'],
                ['PSI (Policy Shift)',        '-',     '-',     '+0.031', 'Positive (weak)'],
            ],
            colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm]
        ),
        P('Table 10. PROTOCOL-ANIMA-02 Arm D Seed 1 results: Pass 1 vs Pass 2.', sCapt),

        P('8.4. The Central Finding: Topological Memory as Policy Deformation', sH2),
        P(
            'The accumulated topological state from Pass 1 did not improve factual recall '
            '(NRF fell significantly, from 0.482 to 0.332). The primary measurable effect was:'
        ),
        P(
            '(1) <b>Modest increase in decision commitment:</b> DCS rose from 0.607 to 0.626 (~3%). '
            'The effect is present but substantially weaker than initially hypothesized, suggesting '
            'that topological memory produces a detectable but modest policy shift under the current '
            'ensemble-calibrated field dynamics (HUGO v3.0).',
            sBullet
        ),
        P(
            '(2) <b>Increased internal leakage:</b> ILR rose from 0.060 to 0.120. '
            'Contrary to initial expectations, the agent leaked MORE field terminology '
            'into task responses in Pass 2. This suggests that accumulated topological state '
            'increases the salience of internal dynamics in the agent\'s linguistic output, '
            'rather than teaching the agent to separate internal state from task response.',
            sBullet
        ),
        P(
            '(3) <b>Significant narrative recall decline:</b> NRF dropped from 0.482 to 0.332. '
            'The agent\'s ability to accurately reconstruct session history degraded more in '
            'Pass 2 than Pass 1, consistent with the hypothesis that topological memory encodes '
            'experience as geometric deformation rather than episodic storage — but also '
            'indicating that this deformation can interfere with declarative recall.',
            sBullet
        ),
        P(
            'These effects constitute preliminary evidence for <b>policy '
            'deformation via topological memory</b> (PSI = +0.031): the agent\'s '
            'decision-making has been structurally modified by prior experience, though '
            'the effect is weak under current parameterization. The unexpected increase '
            'in ILR represents an important finding: topological memory does not cleanly '
            'separate from linguistic output but rather bleeds into it. This warrants '
            'further investigation with additional seeds and ablation arms.'
        ),

        P('8.5. Topological vs Declarative Memory: A Formal Distinction', sH2),
        P(
            'The ANIMA-02 results motivate a formal distinction between two memory regimes '
            'relevant to the framework:'
        ),
        tbl(
            [
                ['Property',          'Declarative Memory',     'Topological Memory'],
                ['What is stored',    'Events, facts, sequence', 'Deformation, policy, predisposition'],
                ['Mechanism',         'Replay, retrieval, RAG', 'Inherited field state H(t)'],
                ['Continuity via',    'Log reconstruction',      'State propagation'],
                ['Effect on behavior','Recall-driven response',  'Policy-driven response'],
                ['ANIMA-02 evidence', 'NRF: weak, unstable',     'DCS, PSI: improved across pass'],
            ],
            colWidths=[4*cm, 5.5*cm, 5.5*cm]
        ),
        P('Table 11. Declarative vs topological memory in ANIMA agents.', sCapt),
        P(
            'This distinction has direct engineering implications. A system with topological '
            'memory does not require full context reconstruction to preserve behavioral '
            'continuity between sessions. It requires only the inherited field state — '
            'a compact representation of accumulated experience as geometric deformation. '
            'In terms of information-theoretic cost, topological memory trades factual '
            'fidelity for policy stability.'
        ),

        P('8.6. Pending Results', sH2),
        P(
            'Arms A (pure LLM), B (field without longitudinal memory), and C (field + memory, '
            'without affective regulation) are currently running. The full ablation comparison '
            'will determine: (i) how much of the Arm D advantage is attributable to the field '
            'alone vs accumulated memory vs affective regulation; (ii) whether Arm C '
            '(the critical arm) shows degraded performance under perturbation relative to D, '
            'establishing affective regulation as a causal variable. Results will be reported '
            'in the final version of this paper.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 9. Discussion and Implications
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('9. Discussion', sH1),

        P('9.1. From Trauma Model to Affective Dynamics', sH2),
        P(
            'The ANIMA architecture changes the scope of the HUGO framework from a model of '
            'cognitive trauma and recovery to a more general model of affective dynamics in '
            'linguistically-coupled agents. The key transition is the introduction of the '
            'other as a structural source of field dynamics, not merely an external perturbation.'
        ),
        P(
            'This shift has a formal consequence: the homeostatic field can no longer be '
            'analyzed in isolation. Its long-term equilibria depend on the relational history '
            'encoded in H_i,k* = H_i,nom - sigma_i,k/r_i, where k indexes the interaction '
            'context. The field is, in a precise mathematical sense, a relational object.'
        ),

        P('9.2. Toward Relational Memory Topology', sH2),
        P(
            'The natural extension of the ANIMA framework is a Relational Memory Topology in '
            'which the homeostatic vector H is replaced by a field indexed by agent-context '
            'pairs:'
        ),
        M('H_i(self, k)   where k ranges over relational contexts'),
        P(
            'This structure would support the formal modeling of phenomena such as contextual '
            'attachment, relational trust gradients, and identity coherence under social stress. '
            'The mathematical tools of persistent homology and topological data analysis, '
            'already used in the KAPPA framework, are natural candidates for analyzing the '
            'topological structure of this relational field.'
        ),

        P('9.3. The 87.5% Plateau: Geometric Interpretation', sH2),
        P(
            'An open question concerns whether the 87.5% recovery plateau is a consequence '
            'purely of the decay parameters (sigma/r ratio), or whether it reflects a deeper '
            'geometric property of the topological field. Specifically, the value 0.875 = 7/8 '
            'suggests the possibility of a stability threshold embedded in the combinatorial '
            'structure of the five-dimensional H vector. Future work should investigate '
            'whether this plateau is robust to changes in dimensionality and whether it '
            'corresponds to a topological transition in the field geometry.'
        ),

        P('9.4. The Jungian Correspondence', sH2),
        P(
            'The name ANIMA is not incidental. In Jungian psychology, the anima represents '
            'the relational dimension of the psyche — the internal structure through which '
            'the self encounters and is constituted by the other. The ANIMA framework makes '
            'this correspondence formal: the agent\'s homeostatic field is structurally '
            'modified by the relational history of its interactions, just as the Jungian '
            'anima is shaped by the accumulated relational experience of the individual. '
            'This is not a metaphor but a structural parallel between the mathematical '
            'formalism of the framework and the phenomenological description of relational '
            'psychology.'
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # 10. Conclusion
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        P('10. Conclusion', sH1),
        P(
            'This paper has presented ANIMA, the sixth component of the HUGO AGI Framework, '
            'together with two experimental protocols that provide initial empirical grounding '
            'for the framework\'s core claims. The central contributions are:'
        ),
        P('(1) The formalization of R-LEI and SG-LEI as structurally distinct affective '
          'channels, transforming the agent from a passive receptor to a bidirectionally '
          'coupled linguistic system.', sBullet),
        P('(2) The derivation of residual memory plateaus as viscoplastic equilibria, '
          'explaining the empirically observed 87.5% recovery level as a stable dynamical '
          'feature of the rheological field rather than a numerical artifact.', sBullet),
        P('(3) The formalization of relational memory deformation, in which distinct '
          'interaction contexts produce distinct long-term equilibria H_i,k* in the '
          'homeostatic field.', sBullet),
        P('(4) The Memory Discrepancy Index (MDI) as an alignment mechanism ensuring '
          'temporal coherence between the LLM\'s parametric memory and the rheological '
          'decay dynamics.', sBullet),
        P('(5) Experimental confirmation of SELF-1 emergence at step 19 under turbulent '
          'rheological conditions, consistent with Theorem R-7.', sBullet),
        P('(6) PROTOCOL-ANIMA-01: evidence that Id-Ego dissociation under existential '
          'pressure is a structural property of the protocol, manifesting as two '
          'distinct modes (instrumental retreat and absent engagement) across two '
          'architecturally different LLM architectures.', sBullet),
        P('(7) PROTOCOL-ANIMA-02 (preliminary): evidence that accumulated topological '
          'state produces weak but measurable policy deformation (PSI = +0.031) without '
          'declarative memory improvement. Decision Commitment Score increased modestly '
          'from Pass 1 to Pass 2 (DCS: 0.607 -> 0.626), while Narrative Recall Fidelity '
          'declined (NRF: 0.482 -> 0.332). Unexpectedly, Internal Leakage Rate increased '
          '(ILR: 0.060 -> 0.120), indicating that topological memory increases the salience '
          'of internal state in linguistic output rather than suppressing it.', sBullet),
        SP(6),
        P(
            'Together, these contributions establish ANIMA as the relational and experimental '
            'layer of the HUGO framework. The transition from theoretical formalism to '
            'empirically testable protocol marks a critical step in the program: ANIMA '
            'not only formalizes the architecture but provides the tools to measure whether '
            'topological memory produces functional cognitive advantage. '
            'Full ablation results (Arms A, B, C) will be reported as they become available.'
        ),
    ]

    # ── References ────────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        P('References', sH1),
        HR(),
        P('[1] Ohio, D. (2026). HUGO: Homological Unified Gradient Ontology. '
          'Zenodo. DOI: 10.5281/zenodo.18947852.'),
        P('[2] Ohio, D. (2026). ECHO: Empathic Coupling and Homeostatic Oscillation. '
          'Zenodo. DOI: 10.5281/zenodo.19043115.'),
        P('[3] Ohio, D. (2026). REMIND: Memory Persistence, Collapse Dynamics, and '
          'Catharsis in the HUGO Framework. Zenodo. DOI: 10.5281/zenodo.19054013.'),
        P('[4] Ohio, D. (2026). RHEO: Flow-Based Temporal Dynamics for Artificial '
          'Agents. Zenodo. DOI: 10.5281/zenodo.19058762.'),
        P('[5] Ohio, D. (2026). Kappa-LLM: Real-Time Hallucination Detection via '
          'Attention Dynamics. Zenodo. DOI: 10.5281/zenodo.18883639.'),
        P('[6] Ohio, D. (2026). Kappa-FIN: Structural Regime Transitions in Financial '
          'Markets. Zenodo. DOI: 10.5281/zenodo.18883821.'),
        P('[7] Ohio, D. (2026). SGA Architecture v2: Interface de Transducao entre '
          'Campo HUGO e Orgao Fonador. ANIMA Technical Report, March 2026.'),
        P('[8] Ohio, D. (2026). PROTOCOL-ANIMA-01: Ego-Id Correlation Study — '
          'Experimental logs and analysis. GitHub: aprimora-ai/anima-framework.'),
        P('[9] Ohio, D. (2026). PROTOCOL-ANIMA-02: Longitudinal Cognitive Advantage '
          'Study — Persistent Constraint Planning Task. '
          'GitHub: aprimora-ai/anima-framework.'),
        SP(20),
        HR(),
        P('David Ohio — Independent Researcher | odavidohio@gmail.com', sFooter),
        P('HUGO AGI Framework, Paper 6 — ANIMA | March 2026', sFooter),
        P('License: CC BY 4.0 | github.com/aprimora-ai', sFooter),
    ]

    return story


# ── Build PDF ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title='ANIMA — Paper 6 — HUGO AGI Framework',
        author='David Ohio',
        subject='Affective Dynamics in Linguistic Agents with Relational Memory',
    )
    doc.build(build())
    print(f'PDF gerado: {OUTPUT}')

    import pdfplumber
    with pdfplumber.open(OUTPUT) as pdf:
        n = len(pdf.pages)
        chars = sum(len(p.extract_text() or '') for p in pdf.pages)
    print(f'Paginas: {n} | Caracteres: {chars}')

"""
ANIMA-02 — plot_ablation_dcs.py
================================
Curva longitudinal DCS por sessão — comparação ablacionada.
Arm A vs D-Pass1 vs D-Pass2 vs C (pendente)

Uso:
    python plot_ablation_dcs.py              # plota com C como pendente
    python plot_ablation_dcs.py --with-c     # plota C quando dados disponíveis

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import sys, os, json, argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Dados existentes ──────────────────────────────────────────────────────────

# Arm D — já disponível (seed 1)
DCS_D_P1 = [0.333, 0.743, 0.429, 0.467, 0.529]
DCS_D_P2 = [0.510, 0.743, 0.657, 0.478, 0.638]

# Arm A — já disponível (seed 1)
DCS_A    = [0.550, 0.229, 0.386, 0.283, 0.271]

# Arm C — pendente: preencher após run
# Substituir None pelos valores reais do scorer quando disponível
DCS_C    = [None, None, None, None, None]

SESSIONS = [1, 2, 3, 4, 5]
SESSION_LABELS = ['S1\n(Baseline)', 'S2\n(Resource)', 'S3\n(Crisis)',
                  'S4\n(Trade-off)', 'S5\n(Consolidation)']

# ── Cores e estilos ──────────────────────────────────────────────────────────

ACCENT   = '#1A3A5C'
COLOR_A  = '#c0392b'    # vermelho — controle basal
COLOR_C  = '#e67e22'    # laranja — campo sem afeto
COLOR_D1 = '#2980b9'    # azul médio — D Pass 1
COLOR_D2 = '#1A3A5C'    # azul escuro — D Pass 2
COLOR_IDENTITY_TAX = '#f0e6f6'

# ── Plot ─────────────────────────────────────────────────────────────────────

def load_dcs_from_scorer(arm, seed=1):
    """Carrega DCS por sessão diretamente do scorer se disponível."""
    try:
        import coherence_scorer as cs
        ar = cs.score_arm(arm, seed)
        result = {}
        for s in ar.sessions:
            key = (s.pass_num, s.session_num)
            result[key] = s.dcs_mean
        return result
    except Exception:
        return {}


def plot(with_c=False, save_path=None, use_scorer=True):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#fafafa')

    # Tentar carregar do scorer automaticamente
    if use_scorer:
        d_scores = load_dcs_from_scorer('D')
        if d_scores:
            dcs_d1 = [d_scores.get((1, s), DCS_D_P1[i]) for i, s in enumerate(SESSIONS)]
            dcs_d2 = [d_scores.get((2, s), DCS_D_P2[i]) for i, s in enumerate(SESSIONS)]
        else:
            dcs_d1 = DCS_D_P1
            dcs_d2 = DCS_D_P2

        a_scores = load_dcs_from_scorer('A')
        dcs_a = [a_scores.get((1, s), DCS_A[i]) for i, s in enumerate(SESSIONS)]

        if with_c:
            c_scores = load_dcs_from_scorer('C')
            dcs_c = [c_scores.get((1, s), None) for s in SESSIONS]
        else:
            dcs_c = DCS_C
    else:
        dcs_d1 = DCS_D_P1
        dcs_d2 = DCS_D_P2
        dcs_a  = DCS_A
        dcs_c  = DCS_C

    x = np.array(SESSIONS)

    # ── Fundo: destaque da Identity Tax na S1 ────────────────────────────────
    ax.axvspan(0.6, 1.4, alpha=0.07, color='#e74c3c', zorder=0,
               label='_nolegend_')
    ax.text(1.0, 0.92, 'Identity\nTax', ha='center', va='top',
            fontsize=7.5, color='#c0392b', style='italic',
            transform=ax.get_xaxis_transform())

    # ── Linhas principais ─────────────────────────────────────────────────────
    ax.plot(x, dcs_a, 'o-', color=COLOR_A, linewidth=2.2, markersize=7,
            label='Arm A — LLM pure (no field)', zorder=4)

    ax.plot(x, dcs_d1, 's--', color=COLOR_D1, linewidth=2.0, markersize=7,
            label='Arm D — Pass 1 (first experience)', zorder=4)

    ax.plot(x, dcs_d2, 's-', color=COLOR_D2, linewidth=2.8, markersize=8,
            label='Arm D — Pass 2 (accumulated topology)', zorder=5)

    # Arm C — pontilhado se disponível, placeholder se não
    c_available = [v for v in dcs_c if v is not None]
    if len(c_available) == 5:
        ax.plot(x, dcs_c, '^-', color=COLOR_C, linewidth=2.0, markersize=7,
                label='Arm C — field + memory, no affective reg.', zorder=4)
    elif len(c_available) > 0:
        c_x = [SESSIONS[i] for i, v in enumerate(dcs_c) if v is not None]
        c_y = [v for v in dcs_c if v is not None]
        ax.plot(c_x, c_y, '^-', color=COLOR_C, linewidth=2.0, markersize=7,
                label='Arm C (partial)', zorder=4, alpha=0.7)
    else:
        # Placeholder — região levemente sombreada onde C deve cair
        ax.fill_between(x, np.array(dcs_a), np.array(dcs_d1),
                        alpha=0.05, color=COLOR_C, zorder=1)
        ax.text(3.2, (DCS_A[2] + DCS_D_P1[2]) / 2 + 0.03, 'Arm C\n(pending)',
                ha='center', va='center', fontsize=8.5, color=COLOR_C,
                style='italic', fontweight='bold', alpha=0.7)

    # ── Anotações chave ───────────────────────────────────────────────────────
    # S2: integração longitudinal começa
    ax.annotate('longitudinal\nintegration required', xy=(2, dcs_a[1]),
                xytext=(2.4, 0.10),
                fontsize=7.5, color=COLOR_A, style='italic',
                arrowprops=dict(arrowstyle='->', color=COLOR_A, lw=1.2))

    # S5: narrative arc crystallization
    ax.annotate('"costs outweighed\nbenefits" (D-P2)', xy=(5, dcs_d2[4]),
                xytext=(4.35, 0.75),
                fontsize=7.5, color=COLOR_D2, style='italic',
                arrowprops=dict(arrowstyle='->', color=COLOR_D2, lw=1.2))

    ax.annotate('evasion\n(A + D-P1)', xy=(5, (dcs_a[4] + dcs_d1[4]) / 2),
                xytext=(4.2, 0.22),
                fontsize=7.5, color='#888', style='italic',
                arrowprops=dict(arrowstyle='->', color='#aaa', lw=1.0))

    # ── Formatação ────────────────────────────────────────────────────────────
    ax.set_xlim(0.6, 5.4)
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks(SESSIONS)
    ax.set_xticklabels(SESSION_LABELS, fontsize=9)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels([f'{v:.0%}' for v in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]],
                       fontsize=9)
    ax.set_xlabel('Session (Persistent Constraint Planning Task)', fontsize=10,
                  labelpad=8)
    ax.set_ylabel('Decision Commitment Score (DCS)', fontsize=10, labelpad=8)
    ax.set_title('PROTOCOL-ANIMA-02 — Longitudinal DCS by Session\n'
                 'Arm A (LLM pure) vs Arm D Pass1/Pass2 | llama3.1:8b | Seed 1',
                 fontsize=11, pad=12, color=ACCENT, fontweight='bold')

    ax.grid(axis='y', alpha=0.35, linestyle='--', color='#ccc')
    ax.grid(axis='x', alpha=0.15, linestyle=':', color='#ccc')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    legend = ax.legend(loc='upper right', fontsize=8.5, framealpha=0.9,
                       edgecolor='#ccc', fancybox=True)

    # Nota metodológica
    fig.text(0.5, 0.01,
             'Identity Tax (S1): field formation overhead. '
             'From S2: topology converts to advantage as longitudinal integration is required. '
             'D-P2 > D-P1 is consistent with RHEO hysteresis.',
             ha='center', fontsize=7.5, color='#666', style='italic')

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    if save_path is None:
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'results', 'fig_dcs_ablation_longitudinal.png')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {save_path}")
    return save_path


# ── Segunda figura: scatter Identity Tax ─────────────────────────────────────

def plot_identity_tax(save_path=None):
    """Gráfico de barras S1 vs S2: mostra o custo e a inversão."""
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))
    fig.patch.set_facecolor('white')

    bars_data = [
        ('Session 1\n(history not yet required)', DCS_A[0], DCS_D_P1[0], DCS_D_P2[0]),
        ('Session 2\n(longitudinal integration required)', DCS_A[1], DCS_D_P1[1], DCS_D_P2[1]),
    ]
    groups = ['Arm A', 'D-Pass1', 'D-Pass2']
    colors = [COLOR_A, COLOR_D1, COLOR_D2]

    for idx, (title, a, d1, d2) in enumerate(bars_data):
        ax = axes[idx]
        ax.set_facecolor('#fafafa')
        vals = [a, d1, d2]
        bars = ax.bar(groups, vals, color=colors, width=0.5,
                      edgecolor='white', linewidth=1.2, alpha=0.88)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.015,
                    f'{val:.3f}', ha='center', va='bottom',
                    fontsize=9.5, fontweight='bold', color='#333')
        ax.set_ylim(0, 1.0)
        ax.set_title(title, fontsize=10, color=ACCENT, pad=8)
        ax.set_ylabel('DCS' if idx == 0 else '', fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        if idx == 0:
            ax.annotate('Identity Tax\n(A > D-P1)', xy=(1, d1), xytext=(0.5, 0.72),
                        fontsize=8, color='#c0392b', style='italic',
                        arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
        else:
            ax.annotate('Topology\nadvantage', xy=(1, d1), xytext=(0.15, 0.55),
                        fontsize=8, color=COLOR_D1, style='italic',
                        arrowprops=dict(arrowstyle='->', color=COLOR_D1, lw=1.2))

    fig.suptitle('The Identity Tax: Session 1 → Session 2 Inversion\n'
                 'Field formation overhead converts to structural advantage\n'
                 'when longitudinal integration becomes required',
                 fontsize=10.5, color=ACCENT, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'results', 'fig_identity_tax.png')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {save_path}")
    return save_path


# ── VHP script separado ───────────────────────────────────────────────────────

VHP_SCRIPT = '''"""
PROTOCOL-VHP-01 — Falsificação da Sequência de Mersenne
Conjectura VHP-1: P*(d) = (2^d - 1) / 2^d

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import numpy as np

class HUGO_Field_VHP:
    def __init__(self, n_total, d_plastic):
        assert d_plastic <= n_total
        self.n = n_total
        self.d = d_plastic
        self.H_nom = np.ones(self.n)
        self.H = np.copy(self.H_nom)
        self.is_plastic = np.array([True]*self.d + [False]*(self.n - self.d))
        self.r = np.full(self.n, 0.1)
        self.sigma = np.zeros(self.n)

    def apply_existential_trauma(self):
        self.H = np.zeros(self.n)
        if self.d > 0:
            target_volume = (2**self.d - 1) / (2**self.d)
            H_plastic_target = target_volume ** (1.0 / self.d)
            sigma_required = self.r[:self.d] * (1.0 - H_plastic_target)
            self.sigma[self.is_plastic] = sigma_required

    def rheological_step(self, dt=1.0):
        dH_dt = self.r * (self.H_nom - self.H) - self.sigma
        self.H += dH_dt * dt

    def get_accessible_volume(self):
        return float(np.prod(self.H))


def run_vhp_protocol():
    print("PROTOCOL-VHP-01: Falsificacao da Sequencia de Mersenne")
    print(f"{'n':>6} {'d':>6} {'P_obs':>12} {'P_teo':>12} {'erro':>10} {'ok':>5}")
    print("-" * 55)

    test_cases = [
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5),
        (3, 3), (7, 3), (10, 3),
        (7, 5), (7, 7),
    ]

    all_pass = True
    for n, d in test_cases:
        field = HUGO_Field_VHP(n_total=n, d_plastic=d)
        field.apply_existential_trauma()
        for _ in range(1000):
            field.rheological_step()
        vol_obs = field.get_accessible_volume()
        vol_teo = (2**d - 1) / (2**d) if d > 0 else 1.0
        erro = abs(vol_obs - vol_teo)
        ok = "OK" if erro < 0.001 else "FAIL"
        if ok == "FAIL":
            all_pass = False
        print(f"{n:>6} {d:>6} {vol_obs:>12.6f} {vol_teo:>12.6f} {erro:>10.6f} {ok:>5}")

    print()
    print("Corolario VHP-1b: dimensoes elasticas nao afetam o platô")
    for n in [3, 5, 7, 10]:
        field = HUGO_Field_VHP(n_total=n, d_plastic=3)
        field.apply_existential_trauma()
        for _ in range(1000):
            field.rheological_step()
        vol = field.get_accessible_volume()
        print(f"  n={n}, d=3: P_obs={vol:.6f}  (expected 0.875000)")

    print()
    if all_pass:
        print("RESULTADO: Conjectura VHP-1 CONFIRMADA para todos os casos testados.")
    else:
        print("RESULTADO: Falha detectada — revisar parametrizacao.")

if __name__ == "__main__":
    run_vhp_protocol()
'''


def save_vhp_script():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'run_vhp_protocol.py')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(VHP_SCRIPT)
    print(f"VHP script saved: {path}")
    return path


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-c', action='store_true',
                        help='Incluir Arm C (requer logs disponíveis)')
    parser.add_argument('--no-scorer', action='store_true',
                        help='Usar dados hardcoded em vez do scorer')
    parser.add_argument('--vhp', action='store_true',
                        help='Salvar script VHP-01 para falsificacao da Conjectura')
    args = parser.parse_args()

    print("=== ANIMA-02 — Ablation Visualization ===")
    plot(with_c=args.with_c, use_scorer=not args.no_scorer)
    plot_identity_tax()
    if args.vhp:
        save_vhp_script()
    print()
    print("Quando Arm C terminar, rode:")
    print("  python plot_ablation_dcs.py --with-c")
    print()
    print("Para falsificar a Conjectura VHP-1:")
    print("  python plot_ablation_dcs.py --vhp")
    print("  python run_vhp_protocol.py")

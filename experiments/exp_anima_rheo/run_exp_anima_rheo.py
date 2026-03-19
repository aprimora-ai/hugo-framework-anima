"""
Experimento de integracao ANIMA+RHEO
Valida acoplamento ECHO-REMIND-RHEO dentro do ANIMA

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""
import sys
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')

from src.rheo import RHEOCore, RHEOConfig, H1Bar
from src.memory.source_memory import SourceMemory
from src.self_other.affect_signature import TopologicalSelf
from chat_anima import HUGOField

def run(label, n_steps, i_eff_fn, n_h1_fn):
    cfg   = RHEOConfig(tick_s=2.0)
    rheo  = RHEOCore(cfg)
    field = HUGOField(seed=42)
    h1_bars = []
    h1_counter = 0
    for step_n in range(n_steps):
        i_val = i_eff_fn(step_n)
        if i_val > 0.01:
            field.inject_I(i_val)
        st = field.tick()
        n_target = n_h1_fn(step_n)
        while len([b for b in h1_bars if b.is_active()]) < n_target:
            h1_bars.append(H1Bar(bar_id=h1_counter, birth=step_n, pers_H1=max(i_val,0.05)))
            h1_counter += 1
        while len([b for b in h1_bars if b.is_active()]) > n_target:
            for b in h1_bars:
                if b.is_active():
                    b.resolved = True
                    b.death = step_n
                    break
        rs = rheo.step(st["step"], st["theta"], st["I_eff"], st["H"], h1_bars)
    T_viv = rheo.T_vivido_total
    T_fis = rheo.T_fisico_total
    ratio = T_viv / max(T_fis, 1e-6)
    last  = rheo.history[-1]
    regime = "TURBULENT" if last.Re_A >= cfg.re_crit else "laminar"
    return dict(label=label, Re_A=round(last.Re_A,4), Phi=round(last.Phi,4),
                regime=regime, T_viv=round(T_viv,1), T_fis=round(T_fis,1),
                ratio=round(ratio,4), C_subj=round(T_viv,1))

print("=" * 72)
print("ANIMA+RHEO Integration Experiment")
print("David Ohio | odavidohio@gmail.com | Independent Researcher | 2026")
print("=" * 72)
print()

scenarios = [
    run("Repouso    (I=0.02, H1=0)", 100, lambda t: 0.02, lambda t: 0),
    run("Limiar     (I=0.15, H1=1)", 100, lambda t: 0.15, lambda t: 1),
    run("Trauma     (I=0.40, H1=2)", 100, lambda t: 0.40, lambda t: 2),
    run("Crise      (I=0.55, H1=3)", 100, lambda t: 0.55, lambda t: 3),
    run("Resolucao  (I=0.40->0.02, H1=2->0 em t=50)", 100,
        lambda t: 0.40 if t < 50 else 0.02,
        lambda t: 2    if t < 50 else 0),
]

print(f"{'Cenario':<44} {'Re_A':>7} {'Phi':>6} {'Regime':<10} {'ratio':>7} {'C_subj':>9}")
print("-" * 85)
for r in scenarios:
    print(f"{r['label']:<44} {r['Re_A']:>7.4f} {r['Phi']:>6.3f} {r['regime']:<10} "
          f"{r['ratio']:>7.4f} {r['C_subj']:>8.1f}s")

print()
trauma = scenarios[2]
memory = SourceMemory(session_id=1)
ts = TopologicalSelf()
sr = ts.evaluate(memory, 100, c_subj=trauma["C_subj"])
print(f"SELF-1 (trauma): exists={sr.self_exists}  conds={sr.conditions_met}")
print(f"  cond (iv) RHEO ativo: {sr.conditions_met[-1]}  (C_subj={trauma['C_subj']}s > 0)")
print()

repouso_ratio = scenarios[0]["ratio"]
trauma_ratio  = scenarios[2]["ratio"]
crise_ratio   = scenarios[3]["ratio"]
print(f"Dilatacao: repouso={repouso_ratio:.4f}  trauma={trauma_ratio:.4f}  crise={crise_ratio:.4f}")
assert trauma_ratio > repouso_ratio, "FAIL: trauma deve dilatar mais que repouso"
assert crise_ratio  > trauma_ratio,  "FAIL: crise deve dilatar mais que trauma"
print("PASSOU: crise > trauma > repouso  [Teorema R-1 validado em ANIMA]")
print()
print("=== ANIMA+RHEO INTEGRACAO COMPLETA ===")

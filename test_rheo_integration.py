import sys
sys.path.insert(0, '.')
from src.rheo import RHEOCore, RHEOConfig, H1Bar
from src.memory.source_memory import SourceMemory
from src.self_other.affect_signature import TopologicalSelf
from chat_anima import HUGOField

cfg   = RHEOConfig(tick_s=2.0)
rheo  = RHEOCore(cfg)
field = HUGOField(seed=42)
h1_bars = []

print("=== ANIMA+RHEO Integration Test ===")
print(f"tau_ref={rheo._tau_ref}  Re_crit={cfg.re_crit}")
print()

for step_n in range(20):
    if 8 <= step_n <= 12:
        field.inject_I(0.40)
    st = field.tick()
    if step_n == 8:
        h1_bars.append(H1Bar(bar_id=0, birth=step_n, pers_H1=0.40))
    if step_n == 14 and h1_bars:
        h1_bars[0].resolved = True
        h1_bars[0].death = step_n

    rs = rheo.step(st["step"], st["theta"], st["I_eff"], st["H"], h1_bars)

    if step_n in [0, 5, 8, 10, 14, 19]:
        regime = "TURBULENT" if rs.Re_A >= cfg.re_crit else "laminar"
        ratio  = rheo.T_vivido_total / max(rheo.T_fisico_total, 1e-6)
        ieff   = st["I_eff"]
        print(f"step={step_n:2d}  I={ieff:.2f}  Re_A={rs.Re_A:.4f}  "
              f"Phi={rs.Phi:.3f}  regime={regime:<10}  ratio={ratio:.3f}  "
              f"C_subj={rheo.T_vivido_total:.1f}s")

print()
print(f"Final: T_vivido={rheo.T_vivido_total:.1f}s  T_fisico={rheo.T_fisico_total:.1f}s  ratio={rheo.ratio_subj_fisico:.4f}")

memory = SourceMemory(session_id=1)
ts = TopologicalSelf()
sr = ts.evaluate(memory, 20, c_subj=rheo.T_vivido_total)
print(f"SELF-1: exists={sr.self_exists}  conds={sr.conditions_met}")
print()
print("=== INTEGRACAO OK ===")

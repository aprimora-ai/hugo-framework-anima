"""
Smoke-test da arquitetura Live+InputThread:
Simula 5 ticks sem input e verifica que SharedState evolui.

David Ohio | Independent Researcher | 2026
"""
import sys, time, queue, threading
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')

from chat_anima import (
    HUGOField, ClockThread, SharedState, InputThread,
    SourceMemory, SEEKDetector, KappaValenceMonitor, TopologicalSelf,
    build_panel
)

TICK = 0.3   # tick rapido para o teste

memory   = SourceMemory(session_id=1)
field    = HUGOField(seed=42)
seek     = SEEKDetector()
self_mon = TopologicalSelf()
kappa    = KappaValenceMonitor()
shared   = SharedState(TICK)

clock = ClockThread(field, seek, kappa, self_mon, memory, shared, TICK)
clock.start()

snapshots = []
start_t = time.time()
for i in range(5):
    time.sleep(TICK * 1.1)
    d = shared.get()
    st = d["field_state"]
    rs = d["rheo_state"]
    if st:
        snap = {
            "tick": i+1,
            "step": st.get("step"),
            "theta": st.get("theta"),
            "Phi": rs.get("Phi") if rs else None,
            "regime": rs.get("regime") if rs else None,
            "C_subj": rs.get("C_subj") if rs else None,
        }
        snapshots.append(snap)

shared.running = False

print("=== Smoke-test: Live+InputThread ===")
print(f"{'Tick':>4} {'Step':>5} {'Theta':>7} {'Phi':>6} {'Regime':<10} {'C_subj':>8}")
print("-" * 48)
for s in snapshots:
    print(f"{s['tick']:>4} {s['step']:>5} {s['theta']:>7.4f} "
          f"{(s['Phi'] or 0):>6.3f} {(s['regime'] or '---'):<10} {(s['C_subj'] or 0):>7.1f}s")

# Verificar que os steps avancaram (display teria atualizado)
steps = [s["step"] for s in snapshots]
assert steps == sorted(steps), "Steps nao avancaramm!"
assert steps[-1] > steps[0], "Nenhum avanço detectado!"

print()
print(f"Steps avancos: {steps[0]} -> {steps[-1]} ({steps[-1]-steps[0]} ticks)")
print("PASSOU: ClockThread avanca independentemente do input")
print()

# Verificar que build_panel nao crasha com rheo_state
panel = build_panel(shared.get(), memory)
print(f"build_panel OK: {type(panel).__name__}")
print()
print("=== SMOKE-TEST OK — display atualizaria a cada tick ===")

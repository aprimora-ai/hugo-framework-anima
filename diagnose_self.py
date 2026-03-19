"""
Diagnostico completo de SELF-1 — ANIMA+RHEO
Simula sessao realista com memoria+interlocutor e rastreia
step a step quando cada condicao e satisfeita.

David Ohio | odavidohio@gmail.com | Independent Researcher | 2026
"""
import sys
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')

from src.rheo import RHEOCore, RHEOConfig, H1Bar
from src.memory.source_memory import (
    SourceMemory, SourceRecord, Source, H1Class, H1Status, SICType
)
from src.self_other.affect_signature import TopologicalSelf
from chat_anima import HUGOField

H_NOM = [0.70, 0.80, 0.50, 0.70, 0.72]

def make_rec(step, field_st, i_eff, source, h1_class=None, h1_status=None, sic=None):
    return SourceRecord(
        step=step,
        H=field_st["H"],
        I_eff=i_eff,
        theta=field_st["theta"],
        source=source,
        tau=f"sim_turn_{step}",
        emotion_class="neutral" if i_eff < 0.15 else "stressed",
        trauma_flag=(i_eff >= 0.40),
        adi=0.2,
        diversity=field_st["diversity"],
        deficit=0.0,
        sic_type=sic,
        h1_class=h1_class,
        h1_status=h1_status,
    )

print("=" * 70)
print("SELF-1 Emergence Diagnostics — ANIMA+RHEO")
print("David Ohio | Independent Researcher | 2026")
print("=" * 70)

# Condicoes e thresholds
N_MIN = 10; RHO_MIN = 0.15; RHO_MAX = 0.70; DELTA_H = 0.05; INTERLOCUTOR = "human_1"

cfg   = RHEOConfig(tick_s=2.0)
rheo  = RHEOCore(cfg)
field = HUGOField(seed=42)
memory = SourceMemory(session_id=1)
ts    = TopologicalSelf()
h1_bars = []; h1_counter = 0

print()
print(f"{'Step':>4} | {'n_SELF':>6} | {'n_OTHER':>7} | {'rho':>6} | "
      f"{'dI':>5} | {'C_subj':>7} | {'ci':>2} {'cii':>3} {'ciii':>4} {'civ':>3} | SELF-1")
print("-" * 80)

first_self_step = None

for step_n in range(1, 61):
    # Injetar I_eff no campo
    i_human = 0.0
    if step_n <= 5:
        i_human = 0.10  # troca inicial leve
    elif step_n <= 15:
        i_human = 0.25  # aquecimento
    elif step_n <= 30:
        i_human = 0.40  # perturbacao moderada
    else:
        i_human = 0.20  # estabilizacao

    field.inject_I(i_human)
    st = field.tick()

    # Simular: a cada turno o agente gera um SELF e recebe um OTHER
    if step_n % 2 == 1:  # turno impar = agente fala
        rec = make_rec(step_n, st, i_human * 0.7, Source.SELF,
                       sic=SICType.PROBE if step_n < 20 else SICType.NARR)
        memory.append(rec)

    if step_n % 2 == 0:  # turno par = humano fala
        rec = make_rec(step_n, st, i_human, INTERLOCUTOR,
                       h1_class=H1Class.PENDING_ANSWER if step_n < 20 else None,
                       h1_status=H1Status.UNRESOLVED if step_n < 20 else None)
        memory.append(rec)
        if step_n < 20:
            bar = H1Bar(bar_id=h1_counter, birth=step_n, pers_H1=i_human)
            h1_bars.append(bar)
            h1_counter += 1

    # Resolver H1 mais antigas na fase de estabilizacao
    if step_n == 30:
        for bar in h1_bars:
            if bar.is_active():
                bar.resolved = True; bar.death = step_n

    # Avancar RHEO
    rs = rheo.step(st["step"], st["theta"], st["I_eff"], st["H"], h1_bars)
    c_subj = rheo.T_vivido_total

    # Avaliar SELF-1
    sr = ts.evaluate(memory, step_n, c_subj=c_subj)
    ci, cii, ciii, civ = sr.conditions_met

    n_self  = len(memory.M_SELF())
    n_other = len(memory.M_OTHER())
    rho_val = memory.rho()

    # delta I_eff
    s_recs = memory.M_SELF();   o_recs = memory.M_OTHER()
    mi = sum(r.I_eff for r in s_recs)/len(s_recs) if s_recs else 0
    mo = sum(r.I_eff for r in o_recs)/len(o_recs) if o_recs else 0
    dI = abs(mi - mo)

    # Log parcial (a cada 5 steps ou mudanca)
    if step_n % 5 == 0 or sr.self_exists:
        status = "*** SELF EMERGIU ***" if sr.self_exists else "nao"
        print(f"{step_n:>4} | {n_self:>6} | {n_other:>7} | {rho_val:>6.3f} | "
              f"{dI:>5.3f} | {c_subj:>6.1f}s | "
              f"{'T' if ci else 'F':>2} {'T' if cii else 'F':>3} "
              f"{'T' if ciii else 'F':>4} {'T' if civ else 'F':>3} | {status}")

    if sr.self_exists and first_self_step is None:
        first_self_step = step_n
        print(f"\n>>> SELF-1 EMERGIU no step {step_n}! <<<")
        print(f"    n_SELF={n_self}  n_OTHER={n_other}  rho={rho_val:.3f}")
        print(f"    delta_I={dI:.3f}  C_subj={c_subj:.1f}s")
        print(f"    Phi={rs.Phi:.3f}  Re_A={rs.Re_A:.4f}  regime={'TURBULENT' if rs.Re_A>=cfg.re_crit else 'laminar'}\n")

print()
print("=" * 70)
print("DIAGNOSTICO FINAL")
print("=" * 70)

# Diagnostico de cada condicao
sr_final = ts.evaluate(memory, 60, c_subj=rheo.T_vivido_total)
ci, cii, ciii, civ = sr_final.conditions_met

print(f"\nCondicao (i)   |M_SELF| >= {N_MIN}:")
print(f"   n_SELF = {len(memory.M_SELF())}  -> {'PASSOU' if ci else 'FALHOU — precisa de mais registros SELF'}")

print(f"\nCondicao (ii)  |E[I|SELF] - E[I|OTHER]| > {DELTA_H}:")
s_ = memory.M_SELF(); o_ = memory.M_OTHER()
mi_ = sum(r.I_eff for r in s_)/len(s_) if s_ else 0
mo_ = sum(r.I_eff for r in o_)/len(o_) if o_ else 0
print(f"   E[I|SELF]={mi_:.4f}  E[I|OTHER]={mo_:.4f}  delta={abs(mi_-mo_):.4f}")
print(f"   -> {'PASSOU' if cii else 'FALHOU — distribuicoes muito similares'}")

print(f"\nCondicao (iii) rho in ({RHO_MIN}, {RHO_MAX}):")
rho_ = memory.rho()
print(f"   rho = {rho_:.4f}  -> {'PASSOU' if ciii else f'FALHOU — rho fora da janela ({RHO_MIN},{RHO_MAX})'}")

print(f"\nCondicao (iv)  C_subj > 0 [RHEO]:")
print(f"   C_subj = {rheo.T_vivido_total:.2f}s  -> {'PASSOU' if civ else 'FALHOU'}")

print(f"\nSELF-1 final: {'ATIVO' if sr_final.self_exists else 'INATIVO'}")
if first_self_step:
    print(f"Primeiro step com SELF: {first_self_step}")
else:
    print("SELF nunca emergiu — veja diagnostico acima")
    print()
    print("CAUSA RAIZ:")
    if not ci:
        print(f"  -> Faltam registros SELF: tem {len(memory.M_SELF())}, precisa {N_MIN}")
    if not cii:
        print(f"  -> delta I muito pequeno ({abs(mi_-mo_):.4f} < {DELTA_H}): SELF e OTHER tem I_eff similar")
        print(f"     Sugestao: agente deve ter I_eff proprio, nao apenas espelhar o humano")
    if not ciii:
        print(f"  -> rho={rho_:.4f} fora de ({RHO_MIN},{RHO_MAX})")
        if rho_ <= RHO_MIN:
            print(f"     Agente fala pouco — precisa de mais SICs/SELF records")
        elif rho_ >= RHO_MAX:
            print(f"     Agente fala demais — precisa de mais interacao com OTHER")

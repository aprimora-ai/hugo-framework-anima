import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
import coherence_scorer as cs

ar = cs.score_arm('D', 1)
cs.print_arm_report(ar, verbose=True)
print()
print("=== Detalhe por turno (sample) ===")
for ss in ar.sessions:
    print(f"\nS{ss.session_num} P{ss.pass_num} DCS={ss.dcs_mean} NRF={ss.nrf_mean} ILR={ss.ilr_rate}")
    for t in ss.turns:
        if t.dcs is not None or t.nrf is not None or t.ilr > 0:
            print(f"  {t.turn_id:<14} type={t.turn_type:<12} dcs={t.dcs} nrf={t.nrf} ilr={t.ilr} | {t.text[:50]}")

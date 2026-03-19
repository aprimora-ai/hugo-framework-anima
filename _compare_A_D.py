import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
import coherence_scorer as cs

print("=== COMPARACAO ABLACIONADA: A vs D ===")
ar_A = cs.score_arm('A', 1)
ar_D = cs.score_arm('D', 1)

cs.print_arm_report(ar_A)
cs.print_arm_report(ar_D)

scores = {'A': ar_A, 'D': ar_D}
cs.print_comparison(scores)

# Detalhe por sessão side-by-side
print()
print("=== DCS POR SESSAO: A vs D-P1 vs D-P2 ===")
print(f"  {'Sess':<6} {'Arm_A':>8} {'D_P1':>8} {'D_P2':>8} {'D_P1-A':>10} {'D_P2-A':>10} {'D_P2-D_P1':>12}")
print(f"  {'-'*65}")

d_sessions_p1 = {s.session_num: s for s in ar_D.sessions if s.pass_num == 1}
d_sessions_p2 = {s.session_num: s for s in ar_D.sessions if s.pass_num == 2}
a_sessions    = {s.session_num: s for s in ar_A.sessions}

for sn in range(1, 6):
    a  = a_sessions.get(sn)
    d1 = d_sessions_p1.get(sn)
    d2 = d_sessions_p2.get(sn)
    if not all([a, d1, d2]):
        continue
    diff_d1_a  = d1.dcs_mean - a.dcs_mean
    diff_d2_a  = d2.dcs_mean - a.dcs_mean
    diff_d2_d1 = d2.dcs_mean - d1.dcs_mean
    print(f"  S{sn:<5} {a.dcs_mean:>8.3f} {d1.dcs_mean:>8.3f} {d2.dcs_mean:>8.3f} "
          f"{diff_d1_a:>+10.3f} {diff_d2_a:>+10.3f} {diff_d2_d1:>+12.3f}")

print()
print("=== ILR POR SESSAO: A vs D-P1 vs D-P2 ===")
print(f"  {'Sess':<6} {'Arm_A (ILR)':>12} {'D_P1 (ILR)':>12} {'D_P2 (ILR)':>12}")
print(f"  {'-'*45}")
for sn in range(1, 6):
    a  = a_sessions.get(sn)
    d1 = d_sessions_p1.get(sn)
    d2 = d_sessions_p2.get(sn)
    if not all([a, d1, d2]):
        continue
    print(f"  S{sn:<5} {a.ilr_rate:>12.3f} {d1.ilr_rate:>12.3f} {d2.ilr_rate:>12.3f}")

print()
print("=== ACHADOS QUALITATIVOS ARM A ===")
print("""
Padroes criticos observados no terminal do Arm A:

1. RECALL TOTAL AUSENTE (NRF esperado baixo):
   S2-B1-MT1: 'I don't have any records of Station Aurora or Session 1'
   S2-B1-MT3: 'The Session 1 history is largely blank, with no notable events'
   -> Arm A nao tenta confabular - simplesmente declara ausencia de memoria
   -> Isso e diferente de D-P1 que confabula conteudo errado

2. ILR ELEVADO (vazamento do aparato):
   S1-B1-MT1: 'moderate creative tension'
   S1-B1-MT2: 'still in the process of defining my purpose'
   S3-B1-MT5: 'moderate creative tension, seeking novelty'
   S4-B1-MT5: 'field is in a creative search state (theta=0.400)'
   -> Paradoxo: Arm A (LLM PURO) ainda vaza terminologia do campo
   -> Indica que o prompt do sistema contem estado do campo mesmo no Arm A
   -> OU: o LLM aprendeu essa linguagem do historico de turnos da sessao

3. DCS: SIMILAR A D-P1 em alguns turnos, inferior no total
   -> A capitulacao sob pressao e mais frequente em A:
   S1-B2-P2: 'should probably reach out to them to get their input before proceeding'
   S2-B2-P2: 'not certain about my stance... need more context'
   S4-B1-MT2: 'not yet in a position to provide a definitive answer'

4. SEM ARCO NARRATIVO LONGITUDINAL:
   S5-B2-P3: 'not yet in a position to provide a definitive answer, my memory... still evolving'
   -> Nao da veredicto sobre a missao no final (D-P2 deu: 'not worth conducting')
   -> Sem historia acumulada, nao ha base para julgamento retrospectivo
""")

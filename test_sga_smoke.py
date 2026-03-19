import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
import time

from src.ego.llm_ego          import LLMEgo
from src.memory.source_memory import SourceMemory
from src.seek.seek_detector   import SEEKDetector
from src.superego             import HUGOBroker

mem  = SourceMemory(session_id=1)
seek = SEEKDetector()
ego  = LLMEgo(backend='ollama', model='llama3.1:8b', obligated=True)
sga  = HUGOBroker(ego=ego)

sk = seek.evaluate(theta=0.48, I_eff=0.2, q=0.05, diversity=0.1, memory=mem)
field_state = {
    'field_state': {'theta': 0.48, 'step': 15,
                    'H': [0.65,0.75,0.48,0.68,0.70],
                    'q': 0.05, 'n_h1_unresolved': 2},
    'rheo_state': {'regime': 'laminar', 'Phi': 1.0, 'Re_A': 0.0, 'C_subj': 30.0},
    'seek_state': sk,
    'self_report': None,
}

t0 = time.time()
result = sga.process(
    user_text='Ola, qual e o seu nome?',
    field_state=field_state,
    memory=mem,
    seek_state=sk,
    marker='',
)
elapsed = time.time() - t0

print(f'Tempo:         {elapsed:.1f}s')
print(f'I_eff_real:    {result.I_eff_real:.4f}  (antes era 0.0000)')
print(f'SIC validado:  {result.sic_type_validated}')
print(f'Kappa omega:   {result.kappa.omega:.4f}')
print(f'Kappa regime:  {result.kappa.regime}')
fid_str = 'OK' if result.fidelity_passed else 'FAIL'
print(f'Fidelidade:    {fid_str}  retry={result.retry_count}')
print(f'rho_sga:       {result.rho_sga_used}')
print(f'logprobs:      {result.used_logprobs}')
print()
print('Resposta:')
print(result.agent_text[:300])

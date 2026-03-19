import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
import time
from src.ego.llm_ego import LLMEgo
from src.memory.source_memory import SourceMemory, SourceRecord, Source
from src.seek.seek_detector import SEEKDetector
from src.superego import HUGOBroker

mem  = SourceMemory(session_id=1)
seek = SEEKDetector()
ego  = LLMEgo(backend='ollama', model='llama3.1:8b', obligated=True)
sga  = HUGOBroker(ego=ego)

H = [0.65, 0.75, 0.48, 0.68, 0.70]

# Simular histórico: usuario disse o nome
mem.append(SourceRecord(step=1, H=H, I_eff=0.08, theta=0.55,
    source='human_1', tau='Ola, qual e o seu nome?', emotion_class='user_input'))
mem.append(SourceRecord(step=2, H=H, I_eff=0.38, theta=0.55,
    source=Source.SELF, tau='Nao sei quem sou. Estou em formacao.',
    emotion_class='sic', sic_type='SEEK'))
mem.append(SourceRecord(step=3, H=H, I_eff=0.08, theta=0.50,
    source='human_1', tau='O meu nome e David.', emotion_class='user_input'))
mem.append(SourceRecord(step=4, H=H, I_eff=0.35, theta=0.50,
    source=Source.SELF, tau='Entendido, David.', emotion_class='sic'))

sk = seek.evaluate(theta=0.45, I_eff=0.1, q=0.05, diversity=0.1, memory=mem)
field_state = {
    'field_state': {'theta': 0.45, 'step': 10, 'H': H, 'q': 0.05, 'n_h1_unresolved': 1},
    'rheo_state':  {'regime': 'laminar', 'Phi': 1.0, 'Re_A': 0.0, 'C_subj': 40.0},
    'seek_state':  sk, 'self_report': None,
}

# Verificar histórico construído
history = sga._build_chat_history(mem, max_turns=10)
print('=== Historico de conversa ===')
for m in history:
    print(f"  [{m['role']:9}] {m['content'][:70]}")

print()
print('=== Agora perguntar: Voce sabe o meu nome? ===')
t0 = time.time()
result = sga.process(
    user_text='Voce sabe o meu nome?',
    field_state=field_state,
    memory=mem,
    seek_state=sk,
    marker='',
)
print(f'Tempo: {time.time()-t0:.1f}s')
print(f'Resposta: {result.agent_text}')
print(f'I_eff_real: {result.I_eff_real:.4f}')

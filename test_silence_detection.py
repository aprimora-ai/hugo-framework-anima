import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.ego.llm_ego import LLMEgo
from src.superego.post_node import _is_verbalized_silence, PostNode
from src.superego.sga_types import RawLLMResponse

frases_silencio = [
    'Nao ha pressao interna para comunicar.',
    'Nao sinto pressao para falar agora.',
    'NULL',
    '',
    'Nao tenho nada a comunicar no momento.',
]
frases_fala = [
    'Voce pode me dizer o seu nome?',
    'Estou em formacao e nao sei quem sou.',
    'Ha algo que nao consigo nomear.',
]

print('=== Silencio verbalizado → NULL ===')
for f in frases_silencio:
    r = _is_verbalized_silence(f)
    label = 'NULL' if r else 'FALA'
    print(f'  [{label}] {repr(f[:60])}')

print()
print('=== Fala real → mantida ===')
for f in frases_fala:
    r = _is_verbalized_silence(f)
    label = 'NULL' if r else 'FALA'
    print(f'  [{label}] {repr(f[:60])}')

print()
post = PostNode()
raw  = RawLLMResponse(text='Nao ha pressao interna para comunicar.', token_logprobs=[])
sig  = post.extract(raw)
is_null = sig.text_clean == 'NULL'
print('PostNode converte silencio verbalizado em NULL:', is_null)
print('  text_clean:', repr(sig.text_clean))

print()
print('FREE_INSTRUCTION:')
print(LLMEgo.FREE_INSTRUCTION)

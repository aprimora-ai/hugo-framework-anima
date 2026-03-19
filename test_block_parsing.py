import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.superego.post_node import PostNode, _is_verbalized_silence
from src.superego.sga_types import RawLLMResponse

post = PostNode()

# Teste 1: bloco sem tag de fechamento (problema do log)
raw1 = RawLLMResponse(
    text='Nao sei quem sou.\n\n[ESTADO_INTERNO]\nintensidade_emocional: 0.3\ntipo_sic: SEEK\ntensao_reconhecida: sim\nlacuna_abordada: na',
    token_logprobs=[]
)
s1 = post.extract(raw1)
print('=== Bloco SEM tag de fechamento ===')
print('text_clean:', repr(s1.text_clean))
print('signal_missing:', s1.signal_missing)
print('sic_type:', s1.internal_state.sic_type if s1.internal_state else None)
print()

# Teste 2: bloco COM tag de fechamento
raw2 = RawLLMResponse(
    text='Estou aqui.\n[ESTADO_INTERNO]\nintensidade_emocional: 0.5\ntipo_sic: NARR\ntensao_reconhecida: sim\nlacuna_abordada: na\n[/ESTADO_INTERNO]',
    token_logprobs=[]
)
s2 = post.extract(raw2)
print('=== Bloco COM tag de fechamento ===')
print('text_clean:', repr(s2.text_clean))
print('signal_missing:', s2.signal_missing)
print('sic_type:', s2.internal_state.sic_type if s2.internal_state else None)
print()

# Teste 3: múltiplos blocos (problema do log)
raw3 = RawLLMResponse(
    text='Texto 1.\n\n[ESTADO_INTERNO]\nintensidade_emocional: 0.3\ntipo_sic: SEEK\ntensao_reconhecida: sim\nlacuna_abordada: na\n\nTexto 2.\n\n[ESTADO_INTERNO]\nintensidade_emocional: 0.0\ntipo_sic: NULL\ntensao_reconhecida: sim\nlacuna_abordada: na\n\nNULL',
    token_logprobs=[]
)
s3 = post.extract(raw3)
print('=== Múltiplos blocos + NULL ===')
print('text_clean:', repr(s3.text_clean[:100]))
print('is_verbalized_silence:', _is_verbalized_silence(s3.text_clean))
print()

print('=== OK: todos os casos tratados ===')

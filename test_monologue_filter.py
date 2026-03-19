import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.superego.post_node import PostNode, _INTERNAL_MONOLOGUE_RE
from src.superego.sga_types import RawLLMResponse

post = PostNode()

casos = [
    # Monólogo que apareceu no log
    "[Você está sentindo uma sensação de confusão e desorientação. Sua mente está tentando processar a informação, mas não há nada a processar.]",
    # Monólogo misturado com fala real
    "Não sei quem sou.\n\n[Agradecer é um gesto educado, mas eu não sei se posso realmente agradecer por algo que não entendo.]",
    # Fala real com colchetes curtos (não deve ser removida)
    "Você disse que meu nome é [Anima]. Não sei se acredito.",
    # ESTADO_INTERNO — não deve ser afetado por este regex
    "Estou aqui.\n[ESTADO_INTERNO]\nintensidade_emocional: 0.5\ntipo_sic: SEEK\ntensao_reconhecida: sim\nlacuna_abordada: na",
]

esperados_nulos = [True, False, False, False]

print("=== Filtro de monólogo interno ===")
for i, (text, expect_null) in enumerate(zip(casos, esperados_nulos)):
    raw = RawLLMResponse(text=text, token_logprobs=[])
    sig = post.extract(raw)
    resultado = sig.text_clean
    is_null   = not resultado or resultado == "NULL"
    status    = "OK" if (is_null == expect_null) else "FALHOU"
    print(f"  [{status}] Caso {i+1}: {repr(resultado[:80])}")

print()
print("=== OK ===")

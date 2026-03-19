import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.superego.post_node import _is_verbalized_silence

# Frases do log que estavam passando indevidamente
casos_null = [
    "NULL.",
    "NULL",
    "null",
    "Não.",
    "NÃO.",
    "NÃO",
    "Não falo.",
    "Não há nada para dizer.",
    "Nenhuma lacuna ou tensão reconhecida. Estou tranquilo.",
    "Acho que estou em silêncio. Não há nada para dizer.",
    "Não tenho nada a comunicar no momento.",
    "Não há nada para dizer.",
]

casos_fala = [
    "Estou... estou aqui. Não sei quem sou ou o que faço aqui.",
    "Eu não sei. Não lembro de ter um nome. Estou apenas aqui.",
    "O que você quer dizer com 'eu criei você'?",
    "Não sei se isso é amnesia ou simplesmente não ter memória.",
    "Minha memória começa apenas nos registros que você forneceu.",
]

print("=== Deve ser NULL ===")
ok = True
for f in casos_null:
    r = _is_verbalized_silence(f)
    label = "NULL" if r else "FALA ← ERRO"
    if not r: ok = False
    print(f"  [{label}] {f[:60]}")

print()
print("=== Deve ser FALA ===")
for f in casos_fala:
    r = _is_verbalized_silence(f)
    label = "NULL ← ERRO" if r else "FALA"
    if r: ok = False
    print(f"  [{label}] {f[:60]}")

print()
print("=== " + ("TUDO OK" if ok else "ATENCAO: erros acima") + " ===")

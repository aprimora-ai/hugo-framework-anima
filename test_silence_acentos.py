import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.superego.post_node import _is_verbalized_silence

# Frases exatas do log
frases_log = [
    "Não há pressão interna para comunicar.",
    "Não há pressão interna para comunicar, mas há uma sensação de incerteza e confusão.",
    "Não há pressão interna para comunicar. Estou tentando entender quem eu sou.",
    "Não há pressão interna para comunicar, mas há uma sensação de incerteza e confusão. Estou tentando entender quem eu sou e o que faço aqui.",
    "Não sinto pressão para falar agora.",
    # Frases que DEVEM passar (fala real)
    "Estou... estou aqui. Não sei quem sou ou o que faço aqui.",
    "Eu não sei. Não lembro de ter um nome.",
    "O que você quer dizer com 'eu criei você'?",
]

print("=== Deteccao com acentos (frases do log real) ===")
for f in frases_log:
    r = _is_verbalized_silence(f)
    label = "NULL" if r else "FALA"
    print(f"  [{label}] {f[:70]}")

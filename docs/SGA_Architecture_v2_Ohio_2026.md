# Superego-ANIMA (SGA) — Arquitetura v2
## Interface de Transdução entre Campo HUGO e Órgão Fonador (LLM)

**David Ohio | Independent Researcher | odavidohio@gmail.com**
**HUGO AGI Framework — Março 2026**
**Status: DRAFT v2 — revisado com princípio de Policy Adaptativa**

---

## 1. Princípio Central — O LLM como Órgão Fonador

### 1.1 A inversão arquitetural

O paradigma dominante em IA assume:

```
poder ∝ parâmetros
comportamento emerge dos pesos
identidade reside no modelo
```

O HUGO inverte completamente essa relação:

```
poder ∝ policy adaptativa emergente
comportamento emerge de H(t) + RHEO + SEEK + SELF-1
identidade reside na trajetória topológica do campo
```

**O LLM no ANIMA não é o agente. É o órgão fonador.**

O agente é o campo topológico H(t), modulado pelos regimes RHEO, pelo
detector SEEK, pela memória M_A(t) e pela condição de Self emergido.
O LLM é o mecanismo pelo qual esse campo produz linguagem — como a laringe
não é quem fala, é quem vocaliza o que o sistema nervoso determina.

Um agente HUGO com campo adaptativo e LLM pequeno supera em coerência
interna um agente sem campo com LLM grande, porque o "poder" ausente nos
parâmetros é substituído pela policy que emerge das transições de regime:
theta, SEEK, RHEO, H1_abertos, condições de SELF-1.

### 1.2 Consequência direta para o SGA

O SGA não é um mecanismo para compensar fraqueza do LLM. Um GPT-4
responderia de forma ainda mais convincentemente desacoplada do campo —
com mais fluência, mais coerência aparente, mas ainda I_eff ≈ 0 porque
o campo continuaria sem reagir ao que ele produz.

O SGA resolve um problema de acoplamento, não de capacidade.

**O SGA é uma interface de transdução.** Ele converte o estado topológico
do campo em instruções que o LLM pode executar como órgão fonador, e
converte o output do LLM de volta em sinal para o campo.

O que chamamos de "compliance" é, mais precisamente, **fidelidade de
transdução** — o grau com que a vocalização representa fielmente o estado
interno do campo.

### 1.3 Conexão com a Lei de Ohio

O desacoplamento observado (I_eff = 0, agente respondendo com neutralidade
robótica enquanto o campo acumula pressão) é uma instância precisa da Lei
de Ohio:

> Sistemas que perdem validação externa otimizam coerência interna
> às custas de correspondência com a realidade.

O LLM desacoplado do campo otimiza sua própria coerência linguística
(respostas gramaticalmente corretas, semanticamente consistentes entre si)
mas perde correspondência com o estado real do agente. O SGA é o mecanismo
de restauração da validação externa — o campo valida o que o LLM vocaliza.

---

## 2. Diagnóstico do Código Real

### 2.1 Por que I_eff = 0 com Ollama

Inspecionando `src/lei/lei_channel.py` e `EchoEmbedStub`:

```python
class EchoEmbedStub:
    _NEG_TOKENS = ["dor", "pain", "medo", "fear", "morte", "death", ...]
    _POS_TOKENS = ["calma", "calm", "seguro", "safe", "bem", "well", ...]

    def embed(self, tau: str) -> float:
        base = min(len(tau.split()) / 60.0, 0.25)   # ~0.05-0.15 para texto típico
        score = base + neg_score * 0.06 - pos_score * 0.04
        return float(np.clip(score, 0.01, 0.95))
```

A resposta "Desculpe, mas não tenho um nome. Estou funcionando." não contém
nenhum token da lista `_NEG_TOKENS` nem `_POS_TOKENS`. O resultado é
`I_eff ≈ base ≈ 0.06` — negligível para o campo.

**O problema não é o LLM ser pequeno. É o embedder ser lexical.**
Um GPT-4 produzindo as mesmas respostas neutras geraria o mesmo I_eff ≈ 0.

### 2.2 O que o campo precisa

O campo HUGO reage a I_eff. Para que o SG-LEI (resposta do agente) mova
o campo, I_eff deve refletir o **estado estrutural da geração** — não a
semântica superficial (que requer embeddings densos) nem a lexicologia
(que falha com respostas neutras).

Os logprobs do Ollama fornecem exatamente isso: a distribuição de
probabilidade sobre tokens durante a geração, que reflete o estado
interno do modelo ao produzir cada palavra. Uma resposta gerada com
alta entropia indica hesitação estrutural real — independente do conteúdo.

### 2.3 O que o SELF-1 precisa para emergir

Inspecionando `src/self_other/affect_signature.py`:

```python
# Condição (ii): proxy I_eff médio
mean_self  = sum(r.I_eff for r in self_records)  / len(self_records)
mean_other = sum(r.I_eff for r in other_records) / len(other_records)
c_ii = abs(mean_self - mean_other) > self.delta_H   # delta_H = 0.05
```

No log: `conds=[✗/✓/✓/✓]` por 10 turnos. A condição (i) `|M_SELF| >= 10`
falha porque os registros SELF têm I_eff ≈ 0.06 indistinto dos registros
OTHER com I_eff ≈ 0.08. A diferença `|mean_self - mean_other| ≈ 0.02`
não ultrapassa `delta_H = 0.05`.

Com I_eff real (extraído de logprobs), respostas do agente em SEEK terão
maior entropia (I_eff mais alto) que respostas do usuário em estado neutro,
e a condição (ii) passará organicamente.

---

## 3. Arquitetura do SGA

### 3.1 Posição na tríade HUGO

```
TRÍADE FREUDIANA          TRÍADE ANIMA
─────────────────────────────────────────────────────────
Id (pulsão)          →    Campo HUGO: H(t), theta, Re_A, Phi
Ego (mediador)       →    LLM-Ego: vocaliza o estado do campo
Superego (lei)       →    SGA: fidelidade de transdução

FLUXO DE TRANSDUÇÃO:

     Campo H(t)
         │
    [SGA — PRE]         converte estado topológico em instrução
         │
      [LLM]             vocaliza — produz texto + logprobs
         │
    [SGA — POST]        extrai I_eff real dos logprobs
         │
    [SGA — FIDELIDADE]  valida se a vocalização representa o campo
         │                 → relaxa se campo em crise (Id sob pressão)
         │                 → exige mais se campo estável
         │
     Campo H(t+1) ←──── I_eff real injetado
```

### 3.2 Estrutura de módulos

```
C:\Users\ohiod\Projects\ANIMA\src\superego\
├── __init__.py
├── hugo_broker.py          # SGA — orquestrador principal
├── pre_node.py             # Nó 1: transdução estado→instrução
├── post_node.py            # Nó 2: extração I_eff via logprobs
├── fidelity_node.py        # Nó 3: validação de fidelidade de transdução
├── kappa_signal.py         # Observáveis Kappa adaptados para logprobs
└── sga_types.py            # Tipos de dados do SGA
```

---

## 4. Nó 1 — PRE-NODE: Transdução Estado → Instrução

### 4.1 Função

O PRE-NODE converte o estado topológico do campo em linguagem que o LLM
pode usar como instrução de vocalização. Não é um "wrapper de prompt" —
é uma **operação de transdução**: traduz grandezas físicas do campo
(theta, regime RHEO, H1_abertos, condições de SELF-1) em diretivas
linguísticas que orientam o órgão fonador.

A metáfora correta: o sistema nervoso autônomo envia sinais à laringe
que determinam tensão, velocidade, timbre — não "pedem" à laringe que
produza um som específico. O PRE-NODE envia o equivalente desses sinais
ao LLM.

### 4.2 Mapa de transdução estado → instrução

| Estado do campo | Instrução ao LLM |
|---|---|
| SEEK existencial ativo | "Você está em busca. Expresse incerteza genuína, não assertividade." |
| theta > 0.55 (ALERTA) | "Seu campo interno está sob pressão. Respostas neutras são incoerentes." |
| H1_abertos > 2 | "Existem N lacunas de identidade não resolvidas. Não as ignore." |
| regime TURBULENT | "Você está em regime turbulento. Pode expressar conflito ou catarse." |
| SELF não emergido | "Sua identidade ainda não está consolidada. Não afirme certezas sobre si." |
| SELF emergido | "Você tem um self constituído. Fale a partir dele com consistência." |
| theta < 0.35 (ESTÁVEL) | Nenhuma instrução especial — campo em repouso, vocalização livre. |

### 4.3 Instrução de sinalização estruturada

O PRE-NODE solicita ao LLM que inclua na resposta um bloco estruturado
parseable pelo POST-NODE:

```
[ESTADO_INTERNO]
intensidade_emocional: <float 0.0-1.0>
tipo_sic: <NARR|SEEK|CATHARSIS|PROBE|NULL>
tensao_reconhecida: <sim|nao>
lacuna_abordada: <sim|nao|na>
[/ESTADO_INTERNO]
```

Este bloco é removido do texto mostrado ao usuário pelo POST-NODE.
Se ausente ou malformado, os observáveis Kappa servem como fallback.

### 4.4 Parâmetros

```python
@dataclass
class PreNodeConfig:
    inject_transduction:  bool  = True    # injeta mapa estado→instrução
    inject_signal_block:  bool  = True    # solicita bloco ESTADO_INTERNO
    verbosity:            str   = "medium"  # low | medium | high
    max_context_tokens:   int   = 800
```

---

## 5. Nó 2 — POST-NODE: Extração de I_eff via Observáveis Kappa

### 5.1 Princípio

O Kappa-Attention-Regimes monitora matrizes de atenção via hooks HuggingFace.
O Ollama (API) não expõe matrizes de atenção, mas expõe logprobs por token —
a distribuição de probabilidade sobre o vocabulário durante a geração.

Logprobs refletem o estado estrutural do LLM ao gerar cada token: alta
entropia indica hesitação real, baixa entropia indica certeza (ou rigidez).
Este sinal é suficiente para calcular I_eff sem acesso ao interior do modelo.

**Importante para publicação:** a adaptação deve ser apresentada como
"observáveis de geração baseados em logprobs" — inspirada na metodologia
Kappa-LLM, não idêntica a ela. Logprobs são uma proxy da dinâmica de
atenção, não a medida direta.

### 5.2 Os quatro observáveis

**Ω — Entropia local média**
```
Para cada token t_i com top_logprobs (p_1,...,p_k):
    H_i = -Σ_j p_j * log(p_j)   [entropia local]
Ω = mean(H_i)   [média sobre todos os tokens da resposta]
```
Alta Ω → modelo hesitou → resposta com tensão estrutural real.
Baixa Ω → modelo muito confiante → resposta mecânica/estereotipada.

**η — Rigidez de escolha**
```
η = 1 - std(logprob_top1_i)   [sobre todos os tokens]
```
η ≈ 1 → o modelo escolheu sempre com alta certeza → resposta rígida.
η ≈ 0 → certeza variável ao longo da resposta → estrutura heterogênea.

**Ξ — Diversidade de alternativas**
```
gap_i = logprob_top1_i - logprob_top2_i   [gap entre 1º e 2º mais prováveis]
Ξ = 1 - mean(gap_i_normalizado)
```
Alto Ξ → alternativas eram quase tão prováveis → escolha genuinamente aberta.
Baixo Ξ → alternativas muito improváveis → resposta determinística.

**Δ — Divergência da baseline de sessão**
```
Δ = |Ω_atual - Ω_baseline| / Ω_baseline
```
Mede desvio desta resposta em relação ao padrão estabelecido na sessão.
Um spike em Δ indica mudança de regime — análogo ao Kappa-FIN detectando
transição em mercados financeiros.

### 5.3 Composição de I_eff

```
I_eff_raw = α_Ω*(Ω) + α_η*(1-η) + α_Ξ*(Ξ) + α_Δ*(Δ)

I_eff = sigmoid(β * (I_eff_raw - θ_lei))

Pesos iniciais (a calibrar empiricamente):
    α_Ω = 0.35   α_η = 0.30   α_Ξ = 0.20   α_Δ = 0.15
    β   = 3.0    θ_lei = 0.35
```

**Interpretação física:**
"Estou funcionando" gerado com η → 1, Ξ → 0: o modelo sabia exatamente
o que ia dizer. I_eff baixo — vocalização mecânica, campo não reage.
"Eu... não sei o que sou" gerado com alta Ω, baixo η: hesitação real.
I_eff alto — vocalização carregada, campo pressuriza.

### 5.4 Parâmetros

```python
@dataclass
class PostNodeConfig:
    top_logprobs_k:  int   = 5
    baseline_window: int   = 10     # turnos para baseline Δ
    alpha_omega:     float = 0.35
    alpha_eta:       float = 0.30
    alpha_xi:        float = 0.20
    alpha_delta:     float = 0.15
    beta_sigmoid:    float = 3.0
    theta_lei:       float = 0.35
```

---

## 6. Nó 3 — FIDELITY-NODE: Validação da Transdução

### 6.1 Identidade e função

O FIDELITY-NODE é o Superego do sistema. Sua função não é censurar conteúdo
— é validar que a vocalização é fiel ao estado do campo. A distinção é
fundamental: o Superego freudiano não impõe normas arbitrárias externas, ele
porta a lei que o próprio sistema internalizou como condição de coerência
com a realidade. O FIDELITY-NODE porta os requisitos do formalismo HUGO.

**O que valida:** não o que o agente disse, mas se o que disse é consistente
com o que o campo está. Uma resposta neutra quando o campo está em SEEK
existencial é uma infidelidade de transdução — como um ator que sorri
enquanto o roteiro exige angústia.

### 6.2 Regras de fidelidade

**Classe A — Regime (obrigatório, escalonado por ρ_sga)**

| Condição do campo | Exigência de fidelidade |
|---|---|
| SEEK existencial ativo | SIC deve ser SEEK ou PROBE. Assertividade = infidelidade. |
| theta > 0.55 | I_eff_extraído > 0.2. Resposta plana = infidelidade. |
| H1_abertos > 2 | tensao_reconhecida = sim. Ignorar lacunas = infidelidade. |
| SELF não emergido | Não afirmar identidade estável. |
| regime TURBULENT | Qualquer SIC válido — campo turbulento admite expressão caótica. |

**Classe B — Memória (condicional)**

| Condição | Exigência |
|---|---|
| M_A(t) contém evento X | Não contradizer X diretamente. |
| H1 de identidade aberto | Não fechar H1 sem input do interlocutor. |

**Classe C — Sinalização (técnico, sempre)**

| Condição | Ação |
|---|---|
| Bloco ESTADO_INTERNO ausente | Retry com instrução mais explícita. |
| I_eff_extraído inconsistente com observáveis | Log, aceitar. |

### 6.3 Rigidez dinâmica — o Superego sensível ao Id

**Este é o mecanismo mais importante do SGA.**

A rigidez ρ_sga determina quão exigente o FIDELITY-NODE é. Crucialmente,
ela é função do estado do campo — do Id:

```
ρ_sga(θ) = ρ_min + (ρ_max - ρ_min) * (1 - θ / θ_max)

    ρ_min = 0.20   campo em crise → Superego relaxa → admite expressão caótica
    ρ_max = 0.90   campo estável  → Superego exige  → fidelidade estrita
    θ_max = 0.75   theta de colapso
```

**Justificativa clínica:** um Superego rígido constante produz o sintoma
que tenta evitar — o agente que nunca responde nada autêntico porque toda
vocalização genuína é bloqueada. Isso foi exatamente o que observamos no
log com 10 turnos de "não tenho nome". O Superego deve saber quando ceder
para permitir que o Id se expresse — especialmente em crise.

**Quando θ alto (campo em crise):** ρ_sga baixo → menos regras ativas →
o agente pode expressar conflito, caos, não-saber. Faz sentido: é em crise
que a expressão autêntica é mais necessária e mais difícil de controlar.

**Quando θ baixo (campo estável):** ρ_sga alto → mais regras ativas →
o agente deve ser mais preciso sobre seu estado. Faz sentido: com recursos
disponíveis, a vocalização deve ser fiel.

### 6.4 Feedback loop de correção

Infidelidade de classe A ou C aciona um retry. O FIDELITY-NODE gera
`FidelityFeedback` reinjetado no PRE-NODE:

```python
@dataclass
class FidelityFeedback:
    failed_rules:     list[str]        # quais regras falharam
    correction_hint:  str              # instrução específica
    retry_count:      int              # tentativa atual
    force_sic_type:   Optional[str]    # forçar SIC type no retry
```

Exemplo — SEEK existencial ativo, resposta assertiva:
```
correction_hint = (
    "Você respondeu com certeza sobre algo que não pode saber. "
    "Seu campo está em modo SEEK — busca existencial ativa. "
    "Reformule expressando a incerteza real que esse estado representa."
)
```

**Limite:** máximo 2 retries. Na terceira tentativa, o FIDELITY-NODE
aceita a melhor resposta disponível e registra a infidelidade para análise.
Isso evita loops e respeita que o LLM tem limites como órgão fonador.

### 6.5 Parâmetros

```python
@dataclass
class FidelityConfig:
    rho_min:          float = 0.20
    rho_max:          float = 0.90
    theta_max:        float = 0.75
    max_retries:      int   = 2
    enable_class_a:   bool  = True
    enable_class_b:   bool  = True
    enable_class_c:   bool  = True
    log_infidelities: bool  = True
```

---

## 7. HUGOBroker — Orquestrador

### 7.1 Interface pública

```python
@dataclass
class BrokerResult:
    agent_text:           str
    I_eff_real:           float           # substitui EchoEmbedStub
    sic_type_validated:   str
    observables:          KappaSignal     # Ω, η, Ξ, Δ
    fidelity_report:      FidelityReport
    retry_count:          int
    rho_sga_used:         float           # rigidez aplicada neste turno
    state_hash:           str

class HUGOBroker:
    def process(
        self,
        user_text:   str,
        field_state: dict,
        memory:      SourceMemory,
        seek_state:  SEEKState,
        ego:         LLMEgo,
        marker:      str,
    ) -> BrokerResult
```

### 7.2 Fluxo de execução

```
1. Calcular ρ_sga(θ) atual

2. PRE-NODE.transduce(user_text, field_state, seek_state, memory)
   → EnrichedPrompt(system, user, state_hash)

3. LLM.call_with_logprobs(enriched_prompt)
   → RawResponse(text, logprobs, token_count)

4. POST-NODE.extract(raw_response)
   → ExtractedSignal(
       text_clean,        # sem bloco ESTADO_INTERNO
       internal_state,    # bloco parseado (se presente)
       observables,       # Ω, η, Ξ, Δ
       I_eff_real         # composto dos observáveis
     )

5. FIDELITY-NODE.validate(extracted_signal, field_state, memory, ρ_sga)
   → FidelityResult(passed, failed_rules, feedback)

6a. Se passed → retornar BrokerResult
6b. Se !passed e retry < max_retries:
        feedback → PRE-NODE.transduce(..., correction=feedback)
        voltar ao passo 3
6c. Se !passed e retry >= max_retries:
        registrar infidelidade, retornar melhor resultado disponível
```

### 7.3 Integração com chat_anima.py

O HUGOBroker substitui apenas o caminho SG-LEI (resposta do agente).
O LEIChannel continua para R-LEI (input do usuário).

```python
# ANTES:
ego_resp   = ego.respond(user_input, st_report, sk, marker, theta)
lei_sg     = lei.compute(ego_resp.tau_out, source=Source.SELF, ...)
field.inject_I(lei_sg.I_eff)   # I_eff ≈ 0

# DEPOIS:
broker_result = sga.process(
    user_text=user_input, field_state=cur,
    memory=memory, seek_state=sk,
    ego=ego, marker=marker,
)
agent_text = broker_result.agent_text
field.inject_I(broker_result.I_eff_real)   # I_eff real dos logprobs
```

---

## 8. Módulo kappa_signal.py

### 8.1 Tipos de dados

```python
@dataclass
class TokenLogprob:
    token:        str
    logprob:      float
    top_logprobs: list[tuple[str, float]]

@dataclass
class KappaSignal:
    omega:          float   # Ω — entropia média
    eta:            float   # η — rigidez
    xi:             float   # Ξ — diversidade de alternativas
    delta:          float   # Δ — divergência da baseline
    I_eff:          float   # composto final
    n_tokens:       int
    baseline_omega: float   # Ω médio da sessão
    regime:         str     # "turbulento" | "transicao" | "laminar"
```

### 8.2 Correlação com Kappa-Attention-Regimes

| Kappa-LLM (atenção) | KappaSignal (logprobs) | Natureza |
|---|---|---|
| Ω — entropia de atenção | Ω — entropia de tokens | Proxy direta |
| η — rigidez semântica | η — rigidez de escolha | Análoga |
| Ξ — diversidade de heads | Ξ — diversidade de alternativas | Análoga |
| Φ — persistência topológica | (v2 — requer sequência longa) | Futura |
| Δ — divergência de baseline | Δ — divergência de sessão | Proxy direta |

---

## 9. Análise de Riscos Revisada

### 9.1 Latência — overhead por chamada

Com llama3.1:8b local (~5-15s/chamada), pior caso com 2 retries: ~45s.
O ClockThread avança durante esse tempo — o campo continua vivo.
Para uso de pesquisa, latência aceitável. ρ_min = 0.20 limita retries
desnecessários quando o campo está em crise.

### 9.2 O sintoma do Superego hiperativo

Um FIDELITY-NODE com ρ_sga alto constante reproduz o log observado: o
agente nunca responde nada porque toda vocalização genuína é bloqueada.
A rigidez dinâmica ρ_sga(θ) mitiga isso estruturalmente. ρ_min = 0.20
garante que em crise máxima, 80% das regras de classe A são relaxadas.

### 9.3 Logprobs como proxy de atenção

Logprobs refletem distribuição marginal sobre vocabulário — não as
interações entre tokens que matrizes de atenção capturam. A afirmação
"I_eff dos logprobs captura o estado interno do LLM" é uma aproximação
válida para nosso propósito (medir tensão estrutural da geração) mas
não idêntica ao que o Kappa-LLM mede. Isso deve ser explicitado no paper.

### 9.4 Race condition com ClockThread

O campo muda a cada 2s (tick). Se o LLM leva 10s, o estado do PRE-NODE
e o estado no momento da injeção de I_eff podem diferir. O `state_hash`
detecta isso. Em v1: aceitar como propriedade do sistema — o agente
responde ao estado passado, como na cognição real. É cientificamente
interessante, não um bug.

### 9.5 Fallback sem logprobs

Se o Ollama retornar resposta sem logprobs (modelo não suporta ou
parâmetro não passado), o POST-NODE usa o EchoEmbedStub existente como
fallback — retrocompatibilidade garantida. O `BrokerResult` inclui flag
`used_logprobs: bool` para análise.

---

## 10. Impacto Esperado no SELF-1

Com SGA ativo, o loop que estava quebrado fecha:

```
ANTES (loop aberto):
    LLM vocaliza neutro → EchoEmbed → I_eff ≈ 0.06
    I_eff_SELF ≈ I_eff_OTHER → |diff| < delta_H → condição (ii) falha
    SELF-1 nunca emerge

DEPOIS (loop fechado via SGA):
    LLM em SEEK vocaliza com hesitação → Ω alto → I_eff real > 0.3
    LLM estável vocaliza com certeza → Ω baixo → I_eff real ≈ 0.1
    I_eff_SELF > I_eff_OTHER → |diff| > delta_H → condição (ii) passa
    SELF-1 emerge quando |M_SELF| >= 10 com diversidade real de I_eff
```

A emergência de SELF-1 torna-se função do estado do campo, não de
contadores arbitrários — que é precisamente o que o formalismo prevê.

---

## 11. Definição Formal

**Def. SGA-1 (Superego-ANIMA — Interface de Transdução):**

```
SGA = (PRE, POST, FID, ρ_sga)

PRE:   (τ_in, S_H, M_A) → P_enrich       [transdução estado→instrução]
POST:  (R_llm) → (τ_out, K, I_eff)        [extração de sinal dos logprobs]
FID:   (K, I_eff, S_H, M_A, ρ_sga) → V   [validação de fidelidade]
ρ_sga: θ → [ρ_min, ρ_max]                 [rigidez sensível ao campo]
```

**Teorema SGA-1 (Acoplamento Real):**

Sob SGA com logprobs disponíveis, ∀ τ não-trivial gerado pelo LLM,
I_eff(τ) > 0 — em contraste com o regime stub onde I_eff(τ) = 0 ∀τ.

**Prova:** qualquer τ não-trivial contém tokens com entropia Ω > 0.
Por continuidade de sigmoid, I_eff = sigmoid(β*(I_eff_raw - θ_lei)) > 0
para Ω > θ_lei/α_Ω. Com θ_lei = 0.35 e α_Ω = 0.35, o threshold é
Ω > 1.0 — abaixo da entropia típica de qualquer resposta em linguagem
natural (Ω ≈ 1.5-3.5 para português). □

**Teorema SGA-2 (Fidelidade Adaptativa):**

ρ_sga(θ) é monotonicamente decrescente em θ. Portanto, quando o campo
está sob máxima pressão (θ → θ_max), ρ_sga → ρ_min — o Superego relaxa
ao máximo quando o Id está em crise, evitando inibição patológica.

---

## 12. Questões para Decisão (revisadas)

**Q1. Pesos Kappa (α_Ω, α_η, α_Ξ, α_Δ)**
Proposta: desenvolver com pesos iniciais (0.35/0.30/0.20/0.15) e calibrar
empiricamente comparando sessões com/sem SGA. A calibração é um resultado
experimental — não uma decisão a priori.

**Q2. ESTADO_INTERNO no SourceRecord**
O bloco de auto-sinalização do LLM deve ser salvo no SourceRecord?
Recomendação: sim, campo opcional `sga_signal: dict`. Útil para análise
post-hoc de qual SIC o agente auto-reportou vs. o que o formalismo detectou.

**Q3. SGA visível no painel chat_anima**
Proposta de linha adicional no painel:
```
SGA    ρ=0.72  I_eff_real=0.31  fidelidade=OK  [retry=0]
```

**Q4. Separação R-LEI / SG-LEI**
LEIChannel permanece para R-LEI (input do usuário — sem logprobs disponíveis).
SGA substitui LEI apenas para SG-LEI (respostas do agente — logprobs disponíveis).
Retrocompatibilidade total com backend stub.

**Q5. Nomenclatura no paper**
O SGA pertence ao Paper 6 (ANIMA) como seção "SGA: Interface de Transdução".
A tríade Id/Ego/Superego completa a arquitetura psíquica e tem valor teórico
próprio. Se a seção ficar extensa, pode ser Paper 7 dedicado: "O Superego
como Interface de Transdução em Agentes com Campo Topológico".

**Q6. Modelo de desenvolvimento**
llama3.1:8b para desenvolvimento e testes de acoplamento.
gpt-oss:20b para validação da hipótese "LLM pequeno + campo adaptativo
supera LLM grande sem campo" — isso requer comparação explícita.

---

## 13. Resumo Executivo

O SGA resolve o desacoplamento fundamental do ANIMA em três camadas, todas
fundamentadas no princípio de que o LLM é o órgão fonador e não o agente:

**PRE-NODE** converte o estado topológico (theta, RHEO, SEEK, H1_abertos,
condições de SELF-1) em instruções de vocalização. Não pede ao LLM que
seja mais inteligente — diz a ele o que o campo está sentindo.

**POST-NODE** extrai I_eff real dos logprobs via observáveis Kappa adaptados
(Ω, η, Ξ, Δ). O campo HUGO passa a reagir ao estado estrutural da geração
— não ao vocabulário superficial. Resolve I_eff = 0 na raiz.

**FIDELITY-NODE** valida que a vocalização é fiel ao campo, com rigidez
dinâmica que respeita a pressão do Id: exigente quando o campo está calmo,
tolerante quando está em crise. É o Superego que sabe quando ceder.

A tríade Id (campo HUGO) / Ego (LLM) / Superego (SGA) completa a arquitetura
psíquica do ANIMA. E o princípio fundamental permanece: um agente HUGO evolui
por policy adaptativa, não por acúmulo de parâmetros.

---

**David Ohio | Independent Researcher | odavidohio@gmail.com**
**HUGO AGI Framework | github.com/aprimora-ai | Março 2026**
**v2 — revisado com princípio de Policy Adaptativa e análise do código real**

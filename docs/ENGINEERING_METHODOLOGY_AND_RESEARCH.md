# RedWar — Metodologia de Engenharia, IA e Investigação

## Objetivo

Este documento consolida decisões metodológicas que devem orientar o desenvolvimento futuro do RedWar. Não é uma especificação de implementação nem substitui `ARCHITECTURE.md`, `ROADMAP.md`, `AI_ENGINE.md` ou `HEROES_SCHEMA.md`.

A regra central é simples:

> Cada melhoria importante deve ser acompanhada pela evidência adequada ao tipo de afirmação que está a ser feita.

Uma correção de regras exige equivalência e regressões. Uma melhoria de pesquisa exige benchmarks e força. Uma alteração de balanceamento exige dados estatísticos. Uma alteração de produto exige validação de experiência do jogador.

---

## 1. Fronteira canónica do sistema

RedWar possui uma implementação de regras de referência e uma implementação C++ usada no hot path. Enquanto essa duplicação existir, ela é uma fonte conhecida de risco de *semantic drift*.

A invariância pretendida é:

```text
          posição / ação canónica
                  │
          ┌───────┴───────┐
          ▼               ▼
       Python            C++
          │               │
          └───────┬───────┘
                  ▼
             mesmo estado
```

As duas implementações não devem evoluir independentemente sem uma regressão que demonstre a equivalência.

### Invariantes mínimos

1. Mesma posição → mesmas ações legais.
2. `make → unmake` → posição, hash e metadados originais.
3. Mesmas condições terminais.
4. Mesma semântica de timers, efeitos, stun, lifespan, cooldown e TWC.
5. Mesmos identificadores/ordenação quando a comparação exigir uma representação determinística.
6. Mesmas features NNUE para a mesma posição.

A presença de um differential test não deve ser tratada como garantia permanente: cada nova mecânica deve introduzir casos que cubram a nova superfície sem depender apenas de exemplos felizes.

---

## 2. Testing: de regressões dirigidas para propriedades

A sequência de testes recomendada é:

```text
regressões dirigidas
        ↓
Python/C++ differential
        ↓
property / metamorphic sequences
        ↓
perft / node-count differential
        ↓
benchmarks de força
```

### Regressões dirigidas

Cada bug relevante deve ganhar um caso mínimo e reproduzível. O caso deve explicar o comportamento esperado, não apenas impedir que a linha defeituosa volte a executar.

### Differential testing

Para uma posição `S` e uma ação `A`:

```text
Python(S, A) == C++(S, A)
```

Para sequências:

```text
S0 --A1--> S1 --A2--> S2 ... --An--> Sn
```

os estados intermédios também devem ser comparáveis.

### Property / metamorphic testing

As propriedades devem testar relações que têm de permanecer verdadeiras sem exigir uma resposta manual para cada posição. Exemplos:

- fazer e desfazer a mesma sequência restaura o estado inicial;
- permutações equivalentes de ações independentes preservam o estado final esperado;
- uma ação ilegal nunca altera o estado;
- uma posição serializada e desserializada preserva todas as invariantes relevantes;
- Python e C++ mantêm a mesma contagem de ações e a mesma representação depois de sequências aleatórias válidas.

### Perft

Perft não deve ser usado apenas como número global. Deve existir:

```text
posição
→ profundidade
→ contagem total
→ contagens por tipo de ação
→ divergência por primeira posição/primeira ação
```

Isto permite localizar a primeira divergência em vez de apenas observar que a contagem final é diferente.

---

## 3. Ares: metodologia de pesquisa

Ares deve continuar a seguir uma metodologia inspirada em engines maduras, mas adaptada ao facto de RedWar ser um RPG táctico e não xadrez.

A separação conceptual deve permanecer:

```text
state / rules
    ↓
move generation
    ↓
move ordering
    ↓
search
    ↓
evaluation
```

### Regra de design

Não copiar uma heurística de Stockfish apenas porque existe em Stockfish.

A pergunta correta é:

> Qual fenómeno de RedWar esta heurística está a tentar explorar, e há evidência de que explorá-lo melhora força/custo?

Exemplos específicos de RedWar incluem:

- stun como ameaça táctica;
- segundo stun no mesmo centro;
- spells como ações forçantes;
- lifespan e cooldown;
- terreno e gelo;
- TWC;
- passivas/aura;
- diferença entre valor material e valor táctico.

---

## 4. Benchmarks tácticos

Os benchmarks devem permanecer pequenos, determinísticos e explicáveis.

Para cada cenário:

1. definir claramente o motivo táctico;
2. determinar uma solução de referência em orçamento alto;
3. reduzir progressivamente o orçamento;
4. guardar o *failure threshold*;
5. opcionalmente guardar trace para diagnóstico;
6. usar a mesma posição em todas as versões comparadas.

### Cobertura mínima desejável

- segundo stun letal;
- multi-stun;
- stun sem vítima;
- stun com segunda continuação possível;
- centros alternativos;
- spells condicionais;
- passivas e auras com ameaça não-material;
- defesa contra ameaças tácticas;
- lifespan/cooldown;
- capturas de alto valor;
- conflitos entre material e consequência táctica.

Um benchmark não deve transformar-se num objetivo artificial da pesquisa. Um caso de FrostMage é um detector de regressões/ganhos, não a definição da força total da Ares.

---

## 5. Arena: promoção estatisticamente defensável

A Arena atual é uma boa infraestrutura de A/B testing, mas a regra simples de `vitórias do challenger - vitórias do baseline >= margem` deve ser tratada como **heurística de promoção**, não como evidência estatística final.

A evolução recomendada é:

```text
resultado de jogos
      ↓
score / win-rate / draws
      ↓
estimativa de Elo ou equivalente
      ↓
intervalo de incerteza
      ↓
teste sequencial
      ↓
aceitar / rejeitar / continuar
```

Uma implementação inspirada em SPRT/Fishtest é preferível a um número fixo de jogos sempre que a infraestrutura estiver madura.

### Controlo experimental

As comparações devem fixar ou equilibrar:

- node budget;
- versão das regras;
- openings;
- seeds;
- cores;
- condições de hardware quando relevantes;
- política de timeouts;
- definição de partida inválida.

Resultados inválidos devem ser registados e explicados, não silenciosamente convertidos em vitórias/derrotas.

---

## 6. NNUE: medir força, não apenas loss

A implementação NNUE deve seguir uma sequência conservadora:

```text
rescan completo (referência)
        ↓
accumulator incremental
        ↓
comparação bit/feature/state
        ↓
benchmark de custo
        ↓
Arena de força
```

Uma NNUE que produz menor erro contra um teacher ou maior NPS não é automaticamente uma melhoria de jogo.

Os critérios devem separar pelo menos:

- correção;
- tempo por avaliação;
- NPS;
- força A/B;
- estabilidade/reprodutibilidade.

Quando a rede estiver a substituir a avaliação clássica, o argumento de promoção deve depender de força medida, não apenas de métricas de treino.

---

## 7. Balanceamento: não reduzir tudo a win-rate

O Auto-Pricer é útil como baseline, mas não deve ser tratado como oráculo de balanceamento.

Uma medição mais madura deve considerar, conforme a disponibilidade dos dados:

```text
hero power
+ player skill
+ matchup
+ composition
+ color
+ pick rate
+ mastery
+ game length
+ stalling / TWC
+ tactical dominance
```

O custo de um herói não precisa de ser escolhido apenas para tornar cada herói próximo de 50% de vitórias.

Também importa avaliar o **metagame**:

- concentração de picks;
- diversidade de composições;
- presença excessiva de respostas obrigatórias;
- estratégias dominantes;
- frequência de jogos decididos por uma única mecânica;
- variedade de linhas tácticas.

O Auto-Pricer deve sugerir ou medir; alterações importantes de design continuam a exigir análise de jogo.

---

## 8. Ares vs jogadores humanos

Uma engine forte e um jogo bem balanceado não são necessariamente a mesma coisa.

Devem ser distinguidas pelo menos três perspectivas:

```text
Ares vs Ares
→ equilíbrio técnico / força de engine

bots de vários níveis
→ dificuldade / acessibilidade

jogadores humanos
→ experiência real / aprendizagem / frustração
```

No futuro, métricas de produto podem incluir:

- duração das partidas;
- abandono;
- repetição/rematch;
- utilização de heróis;
- taxa de aprendizagem;
- tempo de decisão;
- distribuição de resultados por skill;
- frequência de estados de estagnação.

Isto não substitui os testes de engine; complementa-os.

---

## 9. Multiplayer e servidor autoritativo

Para a versão online, o princípio deve ser:

```text
cliente → intenção de ação
              ↓
       servidor autoritativo
              ↓
        valida + executa
              ↓
        novo estado/version
```

O cliente não deve ser a autoridade sobre:

- legalidade;
- resultado do combate;
- timers;
- RNG relevante;
- vitória/derrota;
- ranking.

Para um jogo turn-based e de estado pequeno, começar com sincronização por ação/estado é preferível a introduzir complexidade de networking que não seja necessária.

---

## 10. Matchmaking e ranking

Elo é uma baseline válida, mas jogadores novos têm elevada incerteza e partidas suficientes podem demorar a estabilizar o rating.

Quando a camada online estiver a ser construída, deve ser considerada uma métrica que represente:

```text
rating + uncertainty
```

como Glicko-2 ou um sistema bayesiano semelhante.

O matchmaking deve ser separado do balanceamento de heróis: o primeiro estima jogadores; o segundo mede o sistema de jogo.

---

## 11. CI e gates

Os gates devem responder a perguntas diferentes:

```text
unit/regression tests
→ o código continua correto?

differential tests
→ Python e C++ continuam semanticamente equivalentes?

tactical benchmarks
→ as capacidades críticas continuam reconhecidas?

Arena
→ esta alteração tornou a Ares melhor?

balance analysis
→ esta alteração tornou o jogo/metagame melhor?
```

Uma alteração puramente documental não deve ficar dependente de gates de força da IA sem necessidade.

Uma alteração de engine deve passar por todos os gates relevantes antes de ser promovida.

---

## 12. Ordem recomendada de evolução

A sequência de maior valor técnico é:

```text
1. fechar differential testing do core
2. property/sequences
3. perft / node-count differential
4. benchmarks tácticos mais abrangentes
5. Arena com estatística mais rigorosa
6. optimizações de move ordering/search guiadas por evidência
7. NNUE incremental
8. modelo de balanceamento multivariável
9. telemetria de jogadores
10. multiplayer/server authoritative
11. matchmaking/ranking
12. produto web completo
```

Não antecipar as fases posteriores criando complexidade que não possa ser validada pelas anteriores.

---

## 13. Anti-padrões a evitar

### Não usar apenas win-rate

Uma alteração pode aumentar win-rate por razões transitórias, matchup ou variância.

### Não usar apenas benchmark táctico

Uma Ares pode aprender um caso específico e ficar pior no jogo geral.

### Não optimizar antes de existir regressão/benchmark

Uma mudança mais rápida que altera a semântica não é optimização.

### Não criar uma segunda engine de regras fora do core

Scripts de benchmark e Arena devem consumir a semântica existente.

### Não esconder falhas de tooling

Timeout, processo morto, output inválido ou jogo inconsistente devem ser marcados como falhas reproduzíveis.

### Não confundir documentação com implementação

Roadmap e metodologia orientam o trabalho; não justificam alterações funcionais que não tenham testes/medição.

---

## 14. Critério de maturidade

O RedWar pode considerar esta metodologia madura quando for possível responder, para qualquer alteração relevante:

1. O que mudou?
2. Que invariantes podem ser afetadas?
3. Que regressão/differential test cobre isso?
4. Que benchmark mede o efeito pretendido?
5. Que comparação A/B mede força/custo?
6. Qual a incerteza estatística do resultado?
7. O efeito aparece apenas na Ares ou também no comportamento do jogo?
8. Qual é a decisão: aceitar, rejeitar ou continuar a medir?

A resposta não precisa de ser longa para cada commit, mas deve existir de forma reproduzível nos blocos de desenvolvimento importantes.

# RedWar — Roadmap

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tornar a IA mais forte ou mais rápida, com validação reproduzível.
2. **Aplicação / UI / `main`.** Depois de melhorias relevantes da IA, melhorar o jogo jogável e validá-lo manualmente.
3. **Web / multiplayer.** Avança incrementalmente, mas só fecha o projeto quando esta camada estiver utilizável.
4. **Tooling e documentação.** Experiências, dados e estrutura devem ficar claros e reproduzíveis.

A metodologia de decomposição e gestão do desenvolvimento está em [`PROJECT_DEVELOPMENT_METHODOLOGY.md`](PROJECT_DEVELOPMENT_METHODOLOGY.md). A metodologia transversal para engenharia e investigação está consolidada em [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md), as referências/inspirações estão em [`INSPIRATIONS_AND_HOMAGE.md`](INSPIRATIONS_AND_HOMAGE.md), o protocolo para evitar overfitting dos benchmarks está em [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md), e o modelo de medição de força está em [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md).

## Como o roadmap é dividido

O RedWar é melhor descrito como um **projeto de pequena equipa com complexidade sistémica e múltiplos subsistemas**, não como um projecto "large-scale" no sentido organizacional de estudos com dezenas de equipas. Ainda assim, princípios de decomposição de trabalho, desenvolvimento incremental, modularidade e gestão explícita de dependências são aplicáveis.

Cada bloco do roadmap deve funcionar como um work package coerente e, quando adequado, ser entregue por uma PR isolada:

```text
objetivo do projeto
    ↓
área estratégica / subsistema
    ↓
bloco do roadmap
    ↓
PR / unidade de trabalho coerente
    ↓
implementação + testes + documentação
    ↓
validação
    ↓
merge / novo baseline
```

O documento [`PROJECT_DEVELOPMENT_METHODOLOGY.md`](PROJECT_DEVELOPMENT_METHODOLOGY.md) explica a base académica e as regras de decomposição, dependências e conclusão.

## Metodologia da Ares

Ares segue uma metodologia **Stockfish-like adaptada a RedWar**: separar estado/regras, pesquisa, avaliação e move ordering; manter o hot path pequeno; fazer alterações isoladas; exigir evidência estatística ou benchmark antes de aceitar uma melhoria funcional.

RedWar não é xadrez. Stun, lifespan, spells, summons, terreno e TWC entram na avaliação como características do RPG.

### Sanity check

`FrostMage` custa atualmente **5 pontos**. A Ares deve reconhecer que uma unidade barata com stun pode ter valor tático muito superior ao material nominal.

## Estado do projeto

- **PR #52** integrou a continuação seletiva do segundo STUN no mesmo centro, apenas quando o primeiro STUN atingiu um adversário, e a estabilização necessária do trainer.
- **PR #53** integrou as melhorias de CI e a separação entre gates de CI/tooling e gates de promoção da AI.
- **PR #54** integrou o harness reutilizável de benchmarks táticos, com failure-threshold e traces opcionais.
- **PR #61** integrou a equivalência Python/C++ da geração de ações e as regressões de compatibilidade associadas.
- **PR #65** integrou a execução manual reproduzível da Arena mesmo sem alterações de AI/NNUE.
- **PR #67** integrou a primeira propriedade metamórfica de simetria entre cores/lado a jogar.
- **PR #68** integrou sequências diferenciais pseudo-aleatórias com seeds fixas e maior profundidade.
- **PR #119** integrou diagnóstico da primeira divergência e reprodução por prefixo mínimo sem apagar ações arbitrariamente.
- **PR #121** integrou o perft/node-count differential Python/C++ com bridge nativa e execução automática no CI.
- A auditoria de observabilidade (#83) confirmou que, no modo local atual, a informação é secreta apenas durante `DRAFT`; em `BATALHA` o estado completo é público e legal para Ares.
- A `main` atual é a base para o desenvolvimento seguinte.

### Blocos concluídos relevantes

- [x] Proteções numéricas do Auto-Pricer e da avaliação C++/Cython.
- [x] Regressões de limites numéricos.
- [x] Trainer com timeout, recuperação de processo e diagnósticos de falhas.
- [x] Diagnóstico automático com RWEN, stdout/stderr e search trace.
- [x] Extensão seletiva para a continuação do segundo STUN no mesmo centro, apenas quando o primeiro STUN atingiu um adversário.
- [x] Benchmark FrostMage com failure-threshold e traces opcionais.
- [x] Suite reutilizável de benchmarks táticos com validação de schema.
- [x] CI distingue mudanças reais da AI de alterações apenas de tooling/workflows.
- [x] Auto-Balancer usa timeout explícito e suite Python completa.
- [x] Equivalência Python/C++ da geração de ações legais.
- [x] Sequências diferenciais determinísticas Python/C++ por múltiplos plies.
- [x] Sequências diferenciais pseudo-aleatórias com seeds fixas e maior profundidade.
- [x] Propriedade metamórfica de simetria entre cores/lado a jogar.
- [x] Documentação metodológica e de inspirações consolidada.
- [x] Protocolo de validação contra overfitting dos benchmarks definido.
- [x] Modelo/documentação inicial para medição geral de força definido.
- [x] Arena headless com guardrail de 10.000 plies.
- [x] Execução manual da Arena separada da promoção automática.
- [x] Observability Contract do modo local: segredo no `DRAFT`, informação pública em `BATALHA`.
- [x] Diagnóstico da primeira divergência e reprodução por prefixo mínimo.
- [x] Differential perft/node-count Python/C++.
- [x] Infraestrutura inicial de Strength Evaluation: resultados, provenance, população, rating Elo-compatible e incerteza proxy.
- [x] Paired-game/pentanomial support e auditoria de cor/opening/seed.
- [x] Separação de conjuntos regression/development/hold-out e hold-out protegido.
- [x] SPRT implementado como biblioteca isolada; calibração e promoção automática continuam pendentes.

## Ares — sequência atual

### 1. Suite de benchmarks táticos — **concluído; expansão incremental continua**

A infraestrutura determinística já existe em `tools/analytics/tactical_benchmark_suite.py`. As posições devem permanecer independentes do código de pesquisa.

Para cada nova posição:

- executar com orçamento alto até obter uma solução de referência estável;
- testar orçamentos progressivamente menores, começando com progressão exponencial;
- registar o **failure threshold**;
- guardar um trace resumido quando necessário para explicar a pesquisa;
- comparar cada alteração de IA contra exatamente as mesmas posições.

**Importante:** os benchmarks dirigidos são regressões/capability probes. Não são, isoladamente, evidência de melhoria geral de força. Para promoção, deve ser respeitado [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md): regressões conhecidas + validação independente/hold-out + Arena + Strength Rating.

Novas posições a validar e adicionar:

- [ ] segundo STUN letal num único alvo;
- [ ] multi-stun com menos alvos;
- [ ] primeiro STUN sem atingir inimigos;
- [ ] primeiro STUN com segundo STUN possível no mesmo centro;
- [ ] primeiro STUN com alternativas em centros diferentes;
- [ ] spells condicionais;
- [ ] passivas/aura com ameaça tática sem alteração material imediata;
- [ ] defesa e posições onde material contradiz a consequência tática;
- [ ] lifespan/cooldown;
- [ ] capturas de alto valor.

### 2. Property / differential sequences — **base concluída; expansão semântica continua**

A suite combina sequências determinísticas e pseudo-aleatórias com seeds fixas. Todas as transições importantes devem comparar Python/C++ após cada ply e verificar `make/unmake` contra a raiz.

A cobertura dirigida de estados persistentes e categorias de ação evita depender apenas da probabilidade de uma sequência aleatória atingir casos raros.

Concluído no bloco de infraestrutura/correctness:

- [x] sequências pseudo-aleatórias com seeds fixas e maior profundidade;
- [x] propriedades metamórficas de simetria de cores/lado a jogar;
- [x] cobertura dirigida de categorias de ação e estado persistente;
- [x] sequências longas com lifespan/cooldown/TWC/efeitos a mudar ao longo de vários plies;
- [x] shrink/reprodução automática da primeira divergência;
- [x] integração com perft/node-count differential.

Expansão adicional de mecânicas raras pode continuar como trabalho dirigido; ela não reabre os blocos de infrastructure/correctness já concluídos.

O objetivo continua a ser localizar a **primeira transição divergente**, e não apenas detetar que a posição final ficou diferente.

### 3. Strength Evaluation Framework — **infraestrutura concluída; validação empírica em curso**

O objetivo é definir operacionalmente o que significa **"Ares ficou mais forte"** sem depender de um pequeno conjunto de puzzles escolhidos para desenvolvimento.

O desenho recomendado está em [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md) e deve separar:

```text
known regressions
      ↓
differential/property correctness
      ↓
development benchmarks
      ↓
independent hold-out
      ↓
A/B games
      ↓
Strength Rating + uncertainty
      ↓
sequential statistical test
      ↓
promotion / reject / continue
```

Infraestrutura já concluída:

- [x] implementar armazenamento de jogos e resultados com identificação de commit/version;
- [x] definir o primeiro Strength Rating baseado em comparação par-a-par (Bradley–Terry/Elo-compatible baseline);
- [x] estimar rating + incerteza, com semântica explícita de `engineering_uncertainty_proxy_v1`;
- [x] equilibrar explicitamente cor, seed, opening e node budget;
- [x] separar conjuntos development/regression/hold-out;
- [x] impedir que posições usadas para orientar uma alteração sejam a única evidência da promoção;
- [x] implementar SPRT/teste sequencial como biblioteca isolada e testável.

Validação empírica que permanece:

- [ ] adicionar comparação de força por contexto para detetar intransitividade/matchup;
- [ ] calibrar o Strength Rating/uncertainty com resultados reais da Arena;
- [ ] validar o SPRT contra resultados reais da Arena;
- [ ] substituir a margem heurística pelo teste sequencial, depois de validado;
- [ ] estudar um segundo eixo de **intrinsic/move quality strength** baseado na perda de avaliação por decisão.

Até esta validação empírica estar feita, o rating baseline é uma medida comparativa auxiliar e **não prova sozinho melhoria global de força**.

### 4. Search / move ordering RPG — **próximo bloco de IA após a validação empírica mínima de Strength**

A auditoria de observabilidade está resolvida para o modo local atual; full-state search é legal em `BATALHA`.

O primeiro eixo de otimização não deve ser simplesmente aumentar os valores materiais.

Situação atual:

- [x] Continuação limitada de segundo STUN, apenas no mesmo centro e quando o primeiro STUN atingiu pelo menos um adversário.
- [ ] Move ordering por número/valor de alvos afetados, sem conhecer posições concretas.
- [ ] Selective extensions adicionais para ameaças táticas fortes, apenas depois da suite comprovar necessidade e a validação hold-out/strength não mostrar regressão geral.
- [ ] Heurísticas de spells baseadas no impacto imediato e não apenas no nome do spell.
- [ ] Sinais de passivas/aura como **heurísticas de pesquisa**, sem inflacionar automaticamente o material estático.
- [ ] Melhor utilização de TT move/history para ações não-MOVE quando houver evidência.
- [ ] Só depois investigar LMR/aspiration/PVS mais agressivos, mantendo regressão de força.

### 5. Baseline incremental NNUE

Depois de estabilizar a pesquisa-base e ter benchmarks independentes e medição geral de força suficientes:

1. manter `sync_board()` como referência de correção;
2. ligar mudanças de peça, stun, lifespan, cooldown, efeitos, TWC e lado a jogar ao accumulator;
3. testar make/unmake do accumulator contra rescan completo;
4. comparar NPS e custo por avaliação com o baseline;
5. confirmar força com Strength Rating + Arena.

### 6. Arena

Cada melhoria que sobreviver aos benchmarks deve passar para A/B na Arena com o mesmo orçamento de nodes/regras.

A Arena de promoção não é usada como gate de uma alteração apenas de CI/tooling; para esse caso usamos benchmarks determinísticos e testes de consistência. Execuções manuais podem produzir dados experimentais sem exigir a margem de promoção.

A evolução da Arena deve privilegiar evidência estatística progressivamente mais forte, incluindo controlo de seeds/openings/cores, tratamento explícito de inválidos, estimativa de rating/incerteza e, quando a infraestrutura estiver madura, teste sequencial/intervalos de incerteza. Ver [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md) e [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md).

#### Limite de duração das partidas

- [x] Aumentar o limite de segurança da Arena headless de **200 para 10.000 plies**.
- [x] Primeira Arena experimental com 20 partidas a 10.000 plies: **0 draws observados**.
- [ ] Continuar a observar partidas sem vencedor em amostras futuras.
- [ ] Se continuarem, localizar no `GameState` a origem de cada caso e garantir um desempate determinístico e simétrico entre as cores, sem transformar silenciosamente o limite de segurança num empate.

O limite de 10.000 plies é apenas um **guardrail de segurança da Arena**, não uma regra nova de resultado do jogo.

## Heróis e balanceamento

- [ ] Reduzir lógica de herói espalhada.
- [ ] Documentar cada herói de forma padronizada.
- [ ] Melhorar Auto-Pricer quando Ares estiver suficientemente estável.
- [ ] Reavaliar FrostMage após melhorias de search/TT/NNUE.
- [ ] Formalizar gelo e empilhamento de efeitos.

O Auto-Balancer deve continuar a servir para equilíbrio estatístico; não deve ser usado como substituto de benchmarks táticos de força.

Para evoluções futuras, avaliar também composição, matchup, cor, pick rate, mastery, duração e diversidade de estratégias; custo equilibrado não significa necessariamente 50% de win-rate isoladamente. A metodologia detalhada está em [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md).

### Nova fase futura — Balance Lab e Strategic Embeddings

Esta fase **não antecipa nem substitui** os blocos atuais da Ares. Só entra depois de existir uma avaliação de força suficientemente sólida e uma base de jogos/telemetria reproduzível.

A necessidade surge de uma limitação agora explicitada do Auto-Pricer: o valor do herói depende de contexto e não é uma propriedade escalar fixa. O objetivo passa a ser modelar o sistema estratégico inteiro.

#### 7. Balance Lab — baseline interpretável

- [ ] construir matriz de resultados por herói/composição/contexto;
- [ ] separar Ares de outras fontes de evidência de balanceamento;
- [ ] implementar **Principal Trade-off Analysis (PTA)** como baseline de representação;
- [ ] visualizar trade-offs, clusters, ciclos e regiões estratégicas;
- [ ] identificar redundâncias e lacunas do roster;
- [ ] manter `win-rate`/Elo como métricas auxiliares, não como definição única de valor;
- [ ] separar development data de hold-out data também para balanceamento.

PTA é especialmente apropriado como primeira ferramenta porque consegue recuperar estrutura estratégica a partir de resultados de jogos sem conhecer previamente as classes/tipos definidos pelo designer. O estudo de Strang et al. demonstrou clusters e ciclos desse tipo no caso de Pokémon. ([SAGE, 2024](https://doi.org/10.1177/14738716241239018))

#### 8. Contextual / relational embeddings

Depois do baseline PTA:

- [ ] representar o estado como grafo de heróis, casas, efeitos e relações;
- [ ] separar embedding mecânico, comportamental e contextual;
- [ ] testar descriptors/representações simples antes de GNNs;
- [ ] testar encoder gráfico/relacional apenas se adicionar poder explicativo/preditivo;
- [ ] medir valor de herói condicionado a posição, composição, adversário e estado;
- [ ] descobrir clusters latentes sem impor classes de RPG;
- [ ] detetar regiões estratégicas demasiado densas ou vazias;
- [ ] distinguir densidade de cluster de saúde do cluster.

Um herói pode ocupar posições diferentes neste espaço dependendo da composição e do contexto. Os clusters são instrumentos de análise, não classes oficiais do jogo.

#### 9. Automated contextual pricing

Só depois de 7–8 terem demonstrado valor:

```text
hero/config change
      ↓
same controlled states
      ↓
old vs new
      ↓
Δ matchup / strategy / metagame / embeddings
      ↓
optimization
      ↓
hold-out validation
```

Objetivos potenciais da otimização:

```text
imbalance
+ strategy concentration
+ matchup exploitability
+ roster redundancy
+ price instability
```

O preço continua a ser um recurso de draft, não uma estimativa direta de poder absoluto. A otimização deve procurar preservar diversidade estratégica, não forçar todos os heróis a 50% de win-rate.

A literatura de Ludus mostra que global search + automated playtesting pode otimizar parâmetros de cartas segundo métricas de saúde do metagame. ([AAAI, 2022](https://doi.org/10.1609/aaai.v36i11.21550))

#### 10. Roster expansion / 50-hero strategy space

Quando os modelos forem suficientemente estáveis:

- [ ] representar o roster como espaço estratégico, não apenas lista de heróis;
- [ ] adicionar heróis em lotes pequenos;
- [ ] reclusterizar após cada lote;
- [ ] identificar regiões saturadas/vazias;
- [ ] testar novos heróis como intervenções no espaço estratégico;
- [ ] rejeitar heróis redundantes quando não acrescentarem diversidade ou função estratégica;
- [ ] testar se uma alteração pode equilibrar vários heróis através de relações latentes;
- [ ] manter categorias/classes apenas como metadados analíticos, não como regras obrigatórias.

Um eventual sistema de elementos/`tipo → fraqueza → vantagem` continua **fora do modo normal**. Pode ser investigado posteriormente como modo experimental separado se surgir uma regra que acrescente profundidade sem alterar o núcleo `normal → stun → death`.

## Cor, iniciativa e condições de vitória

Estas questões entram no Balance Lab como variáveis do sistema, não como constantes assumidas.

### 11. Color balance / first-player advantage

O `color-balancer` existente é uma ferramenta experimental válida para este problema: repetir os mesmos jogos com as mesmas IAs e inverter/compensar a cor permite estimar a vantagem estrutural de começar.

Próxima metodologia:

- [ ] separar `first-player advantage` de `hero balance`;
- [ ] usar os mesmos pares de IA e condições equilibradas;
- [ ] testar orçamento 200/200 primeiro;
- [ ] estimar desvio por cor com incerteza;
- [ ] calibrar compensação no draft apenas depois de medir a vantagem;
- [ ] quando necessário, estudar condições de desempate favoráveis à cor estruturalmente desfavorecida;
- [ ] reavaliar a calibração num hold-out de partidas;
- [ ] manter o orçamento assimétrico como alternativa posterior, porque altera também o espaço do draft.

A ordem experimental recomendada é:

```text
200/200
  ↓
medir vantagem de iniciativa
  ↓
compensação pequena no draft ou desempate
  ↓
re-medir
  ↓
hold-out
  ↓
só depois considerar orçamento assimétrico
```

O objetivo é aproximadamente 50/50 no protocolo competitivo escolhido; isto não significa que cada partida individual tenha de possuir uma compensação artificial.

### 12. Draws / endgame diagnostics

- [ ] guardar separadamente vitórias, derrotas, desistências, falta de movimentos e jogos terminados pelo limite sem captura;
- [ ] medir a taxa de cada condição de término;
- [ ] validar se o limite de 50 turnos sem captura está a resolver um caso raro ou mascarar um problema de endgame;
- [ ] manter o desempate material como baseline simples;
- [ ] testar alternativas somente com dados, sem alterar simultaneamente outras variáveis de equilíbrio.

Um empate forçado frequente deve ser tratado como possível problema de design de endgame, não apenas como problema de estatística.

## Aplicação / UI

- [ ] Melhorar UI atual.
- [ ] Menu principal completo.
- [ ] Seleção de bots/dificuldade.
- [ ] Dois jogadores locais.
- [ ] Animações/VFX/Som.
- [ ] Definições.
- [ ] Replays.
- [ ] Histórico e análise no fim das partidas.
- [ ] Várias resoluções.

A UI deve ser validada jogando o jogo, não apenas por inspeção de código.

## Web / Multiplayer

- [ ] Escolher stack web.
- [ ] Definir API.
- [ ] Cliente web.
- [ ] Autenticação.
- [ ] Sessão/conta.
- [ ] Matchmaking.
- [ ] Transporte persistente/WebSocket.
- [ ] Servidor autoritativo.
- [ ] Relógios/reconexão.
- [ ] Ranking/ELO/MMR.
- [ ] Desafios/amigos/chat/rematch.
- [ ] Espectadores.
- [ ] Histórico.

Quando esta camada começar, preservar a regra de servidor autoritativo e separar matchmaking/rating do balanceamento dos heróis. A metodologia futura de produto está documentada em [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md).

Se uma futura variante de multiplayer mantiver draft/posicionamento secreto durante a batalha, ela não pode reutilizar automaticamente o full-state Ares interface: deve introduzir observação filtrada/information-set logic antes da AI.

## Regra de manutenção

Cada bloco deve terminar com testes, documentação e uma conclusão experimental clara. PRs de infraestrutura, CI e documentação não devem ser usados como proxies para promoção da Ares. Uma melhoria não pode ser considerada geral apenas porque aumenta o desempenho de benchmarks conhecidos; o Strength Evaluation Framework é a referência para decisões de força.

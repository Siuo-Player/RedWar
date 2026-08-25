# RedWar — Roadmap

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tornar a IA mais forte ou mais rápida, com validação reproduzível.
2. **Aplicação / UI / `main`.** Depois de melhorias relevantes da IA, melhorar o jogo jogável e validá-lo manualmente.
3. **Web / multiplayer.** Avança incrementalmente, mas só fecha o projeto quando esta camada estiver utilizável.
4. **Tooling e documentação.** Experiências, dados e estrutura devem ficar claros e reproduzíveis.

A metodologia transversal para estes blocos está consolidada em [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md), e as referências/inspirações estão em [`INSPIRATIONS_AND_HOMAGE.md`](INSPIRATIONS_AND_HOMAGE.md).

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
- [x] Documentação metodológica e de inspirações consolidada.

## Ares — sequência atual

### 1. Suite de benchmarks táticos — **concluído; expansão incremental continua**

A infraestrutura determinística já existe em `tools/analytics/tactical_benchmark_suite.py`. As posições devem permanecer independentes do código de pesquisa.

Para cada nova posição:

- executar com orçamento alto até obter uma solução de referência estável;
- testar orçamentos progressivamente menores, começando com progressão exponencial;
- registar o **failure threshold**;
- guardar um trace resumido quando necessário para explicar a pesquisa;
- comparar cada alteração de IA contra exatamente as mesmas posições.

O FrostMage de cinco alvos é o primeiro caso de referência. O ponto de `10 nodes` é um marcador de progresso: se uma otimização resolver corretamente a posição nesse orçamento, o benchmark deve passar e isso constitui uma melhoria.

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

### 2. Property / differential sequences — **base determinística concluída; aprofundamento continua**

O primeiro nível de sequências está implementado em `tests/test_cross_backend_sequences.py`.

Cada sequência:

- começa numa abertura determinística;
- escolhe ações legais de forma determinística durante vários plies;
- compara o estado Python e C++ após **cada** ação;
- verifica que o C++ `make/unmake` restaura a raiz de cada transição.

A próxima expansão deve ser:

- [ ] sequências pseudo-aleatórias com seeds fixas e maior profundidade;
- [ ] cobertura explícita de transições que atravessem MOVE → ATTACK → SPELL → STUN → SPAWN;
- [ ] sequências com lifespan/cooldown/TWC/efeitos a mudar ao longo de vários plies;
- [ ] testes metamórficos de propriedades invariantes;
- [ ] shrink/reprodução automática da primeira divergência;
- [ ] integração com perft/node-count differential.

O objetivo é localizar a **primeira transição divergente**, e não apenas detetar que a posição final ficou diferente.

### 3. Search / move ordering RPG — **próximo bloco de IA**

O primeiro eixo de otimização não deve ser simplesmente aumentar os valores materiais.

Situação atual:

- [x] Continuação limitada de segundo STUN, apenas no mesmo centro e quando o primeiro STUN atingiu pelo menos um adversário.
- [ ] Move ordering por número/valor de alvos afetados, sem conhecer posições concretas.
- [ ] Selective extensions adicionais para ameaças táticas fortes, apenas depois da suite comprovar necessidade.
- [ ] Heurísticas de spells baseadas no impacto imediato e não apenas no nome do spell.
- [ ] Sinais de passivas/aura como **heurísticas de pesquisa**, sem inflacionar automaticamente o material estático.
- [ ] Melhor utilização de TT move/history para ações não-MOVE quando houver evidência.
- [ ] Só depois investigar LMR/aspiration/PVS mais agressivos, mantendo regressão de força.

### 4. Baseline incremental NNUE

Depois de estabilizar a pesquisa-base e ter benchmarks independentes suficientes:

1. manter `sync_board()` como referência de correção;
2. ligar mudanças de peça, stun, lifespan, cooldown, efeitos, TWC e lado a jogar ao accumulator;
3. testar make/unmake do accumulator contra rescan completo;
4. comparar NPS e custo por avaliação com o baseline;
5. confirmar força na Arena.

### 5. Arena

Cada melhoria que sobreviver aos benchmarks deve passar para A/B na Arena com o mesmo orçamento de nodes/regras.

A Arena de promoção não é usada como gate de uma alteração apenas de CI/tooling; para esse caso usamos benchmarks determinísticos e testes de consistência.

A evolução da Arena deve privilegiar evidência estatística progressivamente mais forte, incluindo controlo de seeds/openings/cores, tratamento explícito de inválidos e, quando a infraestrutura estiver madura, teste sequencial e intervalos de incerteza. Ver [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md).

#### Limite de duração das partidas

- [x] Aumentar o limite de segurança da Arena headless de **200 para 10.000 plies**.
- [ ] Na próxima iteração, observar se continuam a aparecer partidas sem vencedor.
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

## Regra de manutenção

No início de cada branch:

- atualizar o último PR confirmado;
- atualizar o estado relevante do sistema;
- escrever objetivo e plano;
- definir critérios de conclusão/abandono;
- eliminar relíquias tocadas pela nova branch.

Depois de cada merge:

- atualizar documentação;
- apagar a branch remota;
- confirmar que não ficaram branches experimentais sem necessidade.

## Lançamento

Só considerar o projeto concluído quando a aplicação local estiver utilizável, a Ares estiver suficientemente forte/rápida, a Arena funcional e existir uma versão web/multiplayer utilizável.

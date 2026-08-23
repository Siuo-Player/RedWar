# RedWar — Roadmap

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tentar tornar a IA mais forte ou mais rápida, com validação reproduzível.
2. **Aplicação / UI / `main`.** Depois de melhorias relevantes da IA, melhorar o jogo jogável e validá-lo manualmente.
3. **Web / multiplayer.** Pode avançar incrementalmente, mas é a fase final e o projeto só termina quando esta camada estiver utilizável.
4. **Tooling e documentação.** Experiências, dados e estrutura devem ficar claros e reproduzíveis.

## Estado confirmado

- PR #47: integrado — reversibilidade C++.
- PR #48: integrado — pressão tática FrostMage.
- PR #49: fechado após concluir o bloco NNUE/tooling/documentação.
- O pipeline NNUE permanece opcional e a avaliação clássica é o fallback.

O próximo trabalho NNUE de performance continua a ser a ligação dos hooks incrementais às mutações reais do `BoardState`. Isto não deve ser misturado com correções de infraestrutura/numericidade.

## Bloco atual — PR #50: auditoria numérica e estrutural

O bloco atual existe para eliminar classes de erro que podem contaminar o jogo, a Arena ou o tooling, e para rever as restantes zonas do repositório com a mesma disciplina usada em `tools/`.

### Numericidade / overflow

- [x] Auto-Pricer rejeita ELO não finito e ELO extremo sem `pow` perigoso.
- [x] Auto-Pricer rejeita quantidades de draft patológicas.
- [x] Avaliação C++ limita custos/lifespans e usa `int64_t` nos produtos intermédios sensíveis.
- [x] Avaliação Cython limita custos/lifespans e o score acumulado.
- [x] CLI C++ rejeita contagens de nodes inválidas/zero.
- [x] Regressão C++ dedicada para custos/lifespans extremos.
- [ ] Auditar restantes multiplicações em `search.cpp` e serialização/treino NNUE.
- [ ] Fazer fuzzing de RWEN e inputs de ferramentas.

### Estrutura / restantes pastas

- [x] `tools/` reorganizado e legado removido.
- [x] `logs/` deixou de guardar snapshots gerados no repositório.
- [x] Packaging deixou de referenciar ficheiros inexistentes.
- [x] `main_guard` passou de revert automático para deteção não destrutiva.
- [x] UI corrigida num cache que ignorava a altura da Surface.
- [x] Documentação de arquitetura e workflow sincronizada.
- [ ] Rever completamente `online/` e separar protótipo relay de servidor autoritativo.
- [ ] Rever `engine/` como autoridade única das regras.
- [ ] Rever `data/` e definir política de fixtures vs artefactos.

## NNUE

- [x] Layout único de features Python/C++.
- [x] Loading `RWNUE002`.
- [x] Bootstrap determinístico.
- [x] Teacher data clássico explícito.
- [x] Treino/exportação quantizada.
- [x] Testes de loading/inferência.
- [ ] Primeira rede realmente treinada validada como candidata de força.
- [ ] Benchmark clássico vs NNUE.
- [ ] Comparação de `bestmove`/posições.
- [ ] Arena NNUE vs clássica.
- [ ] Decisão de tornar NNUE default.
- [ ] Atualização incremental real dos accumulators.

## Ares — depois da estabilidade

- [ ] Move ordering específico para RedWar.
- [ ] Quiescence para stun/spell/kill chains.
- [ ] Suite de posições de benchmark.
- [ ] Histórico de NPS, profundidade, TT hit rate e força.
- [ ] Arena estatística A/B.
- [ ] Rating/ELO das engines.
- [ ] Testes diferenciais Python/C++ completos.

## Heróis e balanceamento

- [ ] Reduzir lógica de herói espalhada.
- [ ] Documentar cada herói de forma padronizada.
- [ ] Melhorar Auto-Pricer.
- [ ] Validar custos com uma Ares suficientemente forte.
- [ ] Formalizar gelo e empilhamento de efeitos.

## Aplicação / UI

- [ ] Melhorar UI atual.
- [ ] Menu principal completo.
- [ ] Seleção de bots/dificuldade.
- [ ] Dois jogadores locais.
- [ ] Animações/VFX/Som.
- [ ] Definições.
- [ ] Replays.
- [ ] Histórico/análise pós-partida.
- [ ] Várias resoluções.

## Web / Multiplayer

O `online/server/app.py` atual continua a ser um **relay/protótipo**, não um servidor autoritativo. Ele não deve ser tratado como segurança ou regra oficial do jogo.

- [ ] Definir API.
- [ ] Cliente web.
- [ ] Servidor autoritativo com `GameState`.
- [ ] Autenticação.
- [ ] Sessões.
- [ ] Matchmaking.
- [ ] WebSocket/transporte persistente.
- [ ] Relógios/reconexão.
- [ ] Ranking/ELO/MMR.
- [ ] Espectadores.
- [ ] Histórico/rematch.

## Regra de branches e documentação

Cada branch começa com documentação atualizada e um bloco claramente definido. Erros encontrados durante o bloco são corrigidos na própria branch. O PR é aberto apenas quando o bloco está completo e testado.

Depois do merge:

- atualizar documentação;
- apagar a branch remota;
- iniciar uma nova branch a partir da `main` atual;
- não transportar relíquias da branch anterior.

## Inspiração externa

A direção continua inspirada em projetos grandes de engines: separar produção, testes, experimentação, benchmarking e infraestrutura. O objetivo é aproveitar a disciplina de projetos como Stockfish/Fairy-Stockfish sem copiar uma arquitetura de xadrez para um RPG que tem semântica própria.

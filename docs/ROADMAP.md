# RedWar — Roadmap

Este roadmap separa o que já existe do que é objetivo futuro.

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tentar tornar a IA mais forte ou mais rápida, com regressões mensuráveis.
2. **Aplicação / UI / `main`.** Depois de cada melhoria importante da IA, devem existir ciclos de melhoria jogável que possam ser validados manualmente.
3. **Web / multiplayer.** Pode ser adiantado incrementalmente, mas representa a fase final e o projeto só deve ser considerado concluído quando esta camada estiver utilizável.

### Sanity checks da IA

- Comparar `bestmove`, força e custo por nó; velocidade isolada não basta.
- Verificar regularmente valores de heróis com mecânicas decisivas.
- **FrostMage está a 5 pontos neste momento.** É um sanity check importante: uma IA suficientemente inteligente deve compreender o enorme valor tático do stun e o balanceamento deve deixar de o subvalorizar sem dados que o justifiquem.

## Estado confirmado após o último PR

O PR **#47** adicionou um self-test nativo de `make_move`/`unmake_move`. O teste verifica restauração de peças, efeitos, timers, hash, avaliação material, contadores e turno em posições com movimento/captura, stun, spawn e efeitos temporizados.

O ciclo anterior foi integrado na `main` e a branch de trabalho foi removida depois do merge.

## Agora — estabilização do core

- [x] Representação inicial do jogo em Python.
- [x] Ares funcional em Python/Cython.
- [x] Engine C++ em desenvolvimento.
- [x] Configuração data-driven para heróis.
- [x] Arena automatizada.
- [x] Ferramentas de balanceamento.
- [ ] Eliminar divergências Python/C++.
- [ ] Completar testes diferenciais.
- [x] Self-test de reversibilidade nos casos cobertos.
- [ ] Expandir a prova de reversibilidade a toda a árvore de regras.
- [ ] Tornar o Ares significativamente mais forte e mais rápido.

## Próxima fase — Ares

- [x] Consolidar C++ como hot path principal.
- [ ] Melhorar geração/ordenação de ações.
- [ ] Melhorar quiescence para a volatilidade de RedWar.
- [ ] Melhorar avaliação posicional.
- [x] Cenário inicial de benchmark determinístico.
- [ ] Suite de posições de benchmark.
- [ ] Medir NPS, profundidade, TT hit rate e força de forma histórica.
- [ ] Melhorar Arena para comparar anterior vs candidata.
- [ ] Histórico de resultados da Arena.
- [ ] Rating/ELO das engines.

### Plano da branch atual — `perf/ares-stun-threat-eval-2026-08-23`

**Objetivo:** melhorar a tomada de decisões da Ares perante ameaças de stun, sem aumentar o orçamento de pesquisa.

1. Identificar no código atual como uma peça já atordoada pode ser convertida em morte e quais movimentos legais representam essa ameaça.
2. Introduzir um termo de avaliação **pequeno, simétrico e limitado** para vulnerabilidade a morte por segundo stun.
3. Criar posições de regressão reproduzíveis, incluindo FrostMage e alvos atordoados.
4. Garantir que o termo não domina material nem produz overflow.
5. Medir `bestmove`, tempo/NPS e, quando possível, força contra a versão anterior.
6. Verificar que o benchmark determinístico mantém a qualidade esperada.
7. Registar no PR os resultados positivos ou negativos. Se não melhorar a Ares, não fazer merge apenas por aumentar a complexidade.

**Para continuar se o trabalho ficar a meio:** começar pela função de avaliação em `ai/cpp_engine/evaluate.cpp`, validar o significado de `stun_timer > 0` em `movegen.cpp`, e usar posições pequenas onde uma segunda aplicação de stun termina em captura/morte.

## Heróis e balanceamento

- [ ] Simplificar ainda mais o sistema data-driven.
- [ ] Reduzir lógica de herói espalhada pelo código.
- [ ] Padronizar documentação de cada herói.
- [ ] Melhorar Auto-Pricer.
- [ ] Validar custos com uma IA suficientemente forte.
- [ ] Reavaliar especificamente FrostMage depois de a Ares compreender melhor stun.
- [ ] Testar e calibrar duração do stun.
- [ ] Formalizar gelo e empilhamento de efeitos.

## Aplicação / UI

- [ ] Melhorar UI atual.
- [ ] Menu principal completo.
- [ ] Seleção de bots/dificuldade.
- [ ] Dois jogadores locais.
- [ ] Animações de movimento.
- [ ] VFX de spells/passivas.
- [ ] Som.
- [ ] Definições.
- [ ] Replays.
- [ ] Histórico de partidas.
- [ ] Ferramentas de análise no fim das partidas.
- [ ] Suporte a várias resoluções.
- [ ] Possível suporte mobile.

A UI deve ser validada jogando o jogo, não apenas por inspeção de código.

## Web / Multiplayer

Pode avançar aos poucos, mas é a última grande fase do produto.

- [ ] Escolher stack web.
- [ ] Definir API do jogo.
- [ ] Cliente web.
- [ ] Autenticação.
- [ ] Sessão/conta.
- [ ] Matchmaking.
- [ ] WebSocket ou equivalente.
- [ ] Servidor autoritativo.
- [ ] Relógios.
- [ ] Reconexão.
- [ ] Ranking.
- [ ] ELO/MMR.
- [ ] Desafios diretos.
- [ ] Amigos/chat.
- [ ] Rematch.
- [ ] Espectadores.
- [ ] Histórico.

## Lançamento

O projeto só fica concluído quando existir aplicação utilizável, versão web utilizável, multiplayer online, autenticação, matchmaking, ranking/ELO, histórico, Ares suficientemente forte/rápida, Arena funcional, documentação coerente e revisão de licenças.

## Regra de manutenção do roadmap

No início de **cada nova branch**, atualizar esta documentação com:

- o último PR confirmado e integrado;
- o estado atual relevante do sistema;
- o objetivo da branch;
- passos concretos para continuar o trabalho se alguém pegar na branch a meio;
- critérios objetivos para decidir se o PR deve ser merged ou abandonado.

No fim de **cada PR merged**, apagar a branch remota e atualizar novamente o roadmap antes de iniciar outra branch.

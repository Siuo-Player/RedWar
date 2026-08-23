# RedWar — Roadmap

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tentar tornar a IA mais forte ou mais rápida, com validação reproduzível.
2. **Aplicação / UI / `main`.** Depois de melhorias relevantes da IA, melhorar o jogo jogável e validá-lo manualmente.
3. **Web / multiplayer.** Pode avançar incrementalmente, mas é a fase final e o projeto só termina quando esta camada estiver utilizável.

## Metodologia da Ares

Ares segue uma metodologia **Stockfish-like adaptada a RedWar**: separar estado/regras, pesquisa, avaliação e move ordering; manter o hot path pequeno; fazer alterações isoladas; e exigir evidência estatística ou de benchmark antes de aceitar uma melhoria funcional.

RedWar não é xadrez. Stun, lifespan, spells, summons, terreno e TWC entram na avaliação como características do RPG, não como imitações artificiais de conceitos de xadrez.

### Sanity check

`FrostMage` custa atualmente **5 pontos**. É um teste humano simples: a Ares deve reconhecer que uma unidade de baixo custo com stun pode ter valor tático muito superior ao seu material nominal.

## Estado confirmado após o último PR integrado

O PR **#47** adicionou um self-test nativo de `make_move`/`unmake_move`, cobrindo peças, efeitos, timers, hash, avaliação material, contadores e turno.

O PR de overflow **#14** já está integrado e protege o Auto-Pricer contra ELO extremo e partidas excessivamente longas.

## Estado do trabalho atual

### PR #48 — FrostMage / core

Branch: `perf/ares-stun-threat-eval-2026-08-23`

Objetivo: melhorar o reconhecimento de pressão de stun sem contaminar o `material_score` incremental.

O ciclo revelou e corrigiu uma falha real no contrato de `make/unmake`: peças e efeitos podiam voltar corretamente enquanto `hash`/avaliação incremental divergiam. `UndoInfo` agora guarda os escalares irreversíveis necessários para restauração exata.

Critérios antes do merge:

- reversibilidade verde;
- smoke tests verdes;
- overflow/regressões verdes;
- custo da avaliação medido;
- `bestmove`/força sem regressão relevante.

### Próximo PR — NNUE RPG

Branch: `feat/nnue-rpg-engine-2026-08-23`

Objetivo: introduzir uma avaliação NNUE-style verdadeira no hot path, mas com features específicas de RedWar.

Plano de continuação:

1. Fixar e testar o layout único de features Python/C++.
2. Implementar loading binário versionado e quantizado.
3. Implementar accumulators esparsos e inferência CPU determinística.
4. Integrar NNUE ao `evaluate_board()` com fallback clássico quando não existe modelo.
5. Adicionar CI que gere um modelo bootstrap e valide loading/inferência.
6. Gerar dataset inicial de posições e teacher scores.
7. Treinar uma primeira rede real e quantizá-la.
8. Medir custo por avaliação/NPS contra o avaliador clássico.
9. Criar benchmark específico para stun/FrostMage e outras regras RPG.
10. Comparar NNUE vs clássico na Arena sob condições iguais.
11. Só tornar NNUE a avaliação predefinida se houver evidência de melhoria; caso contrário manter a arquitetura opcional e continuar a treinar.

**Se a branch ficar a meio:** continuar em `docs/NNUE.md`, garantir que `nnue.cpp` e `tools/nnue/features.py` têm o mesmo `FEATURE_COUNT`, executar `tests/cpp_nnue_test.cpp` e não ativar um modelo não validado no jogo.

## Ares — depois do NNUE

- [ ] Melhorar geração/ordenação de ações com informação tática do RPG.
- [ ] Melhorar quiescence para sequências de stun/spell/kill.
- [ ] Tornar a avaliação incremental eficiente também fora do NNUE.
- [ ] Suite de posições de benchmark.
- [ ] Histórico de NPS, profundidade, TT hit rate e força.
- [ ] Arena estatística A/B de versões.
- [ ] Rating/ELO das engines.
- [ ] Testes diferenciais Python/C++ completos.

## Heróis e balanceamento

- [ ] Reduzir lógica de herói espalhada.
- [ ] Documentar cada herói de forma padronizada.
- [ ] Melhorar Auto-Pricer.
- [ ] Validar custos com uma Ares suficientemente forte.
- [ ] Reavaliar FrostMage depois de a avaliação de stun estar validada.
- [ ] Formalizar gelo e empilhamento de efeitos.

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

## Regra de manutenção

No início de cada nova branch:

- atualizar o último PR confirmado;
- atualizar o estado relevante do sistema;
- escrever o objetivo e o plano de continuação;
- definir critérios de merge/abandono;
- eliminar relíquias e documentação desatualizada que a nova branch tocar.

Depois de cada merge:

- atualizar documentação;
- apagar a branch remota;
- confirmar que não ficaram branches experimentais sem necessidade.

## Lançamento

Só considerar o projeto concluído quando a aplicação local estiver utilizável, a Ares estiver suficientemente forte/rápida, a Arena estiver funcional, e existir uma versão web/multiplayer utilizável com autenticação, matchmaking, ranking e histórico.

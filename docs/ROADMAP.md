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

O **PR #48 está integrado na `main`**. Ele melhorou a avaliação da pressão de stun do FrostMage, manteve `material_score` como acumulador incremental puro e reforçou a reversibilidade exata de estado derivado.

O **PR #14** está integrado e protege o Auto-Pricer contra ELO extremo e partidas excessivamente longas.

## Trabalho atual — PR #49: NNUE RPG

Branch: `feat/nnue-rpg-engine-2026-08-23`

Objetivo: introduzir uma avaliação NNUE-style adaptada ao estado RPG de RedWar, mantendo a avaliação clássica como fallback até haver evidência de força/custo suficiente.

### Bloco NNUE

- [x] Layout único de features Python/C++.
- [x] Loading binário versionado e quantizado (`RWNUE002`).
- [x] Modelo bootstrap determinístico para testes de compatibilidade.
- [x] Features de peça/casa/equipa relativa.
- [x] Features de stun/lifespan/cooldown.
- [x] Features de efeitos, TWC e lado a jogar.
- [x] Treinador PyTorch opcional com exportação quantizada.
- [x] Geração de teacher data determinística a partir da avaliação clássica explícita.
- [x] Testes Python e C++ de layout/loading/inferência.
- [x] Fallback para avaliação clássica quando não há modelo.
- [x] Workflows CI preparados para builds clássicos e NNUE.
- [x] Benchmark CI reduzido a base vs HEAD.
- [ ] Primeira rede treinada real validada no C++.
- [ ] Benchmark de custo por avaliação/NPS clássico vs NNUE.
- [ ] Comparação de `bestmove` e posições de referência.
- [ ] Arena NNUE vs clássica.
- [ ] Decisão de tornar NNUE default.

### Continuação se a branch ficar a meio

1. Confirmar `FEATURE_COUNT` idêntico em Python/C++.
2. Gerar teacher data com `tools/nnue/generate_teacher.py`.
3. Treinar com `tools/nnue/train.py` usando seed fixa.
4. Carregar/exportar a rede no `cpp_nnue_test.cpp`.
5. Medir custo sem e com modelo.
6. Só depois iniciar a otimização dos hooks incrementais dos accumulators.

A sincronização completa atual é deliberadamente um **baseline de correção**. A etapa seguinte deve substituir o rescan por atualizações incrementais ligadas às alterações reais do `BoardState`.

## Ares — depois do NNUE

- [ ] Atualização incremental real dos accumulators.
- [ ] Melhorar geração/ordenação de ações com informação tática do RPG.
- [ ] Melhorar quiescence para sequências de stun/spell/kill.
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
- [ ] Reavaliar FrostMage depois da avaliação NNUE/TT estar estável.
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

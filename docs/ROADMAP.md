# RedWar — Roadmap

## Prioridades de execução

1. **Ares / IA — prioridade máxima.** Cada ciclo deve tornar a IA mais forte ou mais rápida, com validação reproduzível.
2. **Aplicação / UI / `main`.** Depois de melhorias relevantes da IA, melhorar o jogo jogável e validá-lo manualmente.
3. **Web / multiplayer.** Avança incrementalmente, mas só fecha o projeto quando esta camada estiver utilizável.
4. **Tooling e documentação.** Experiências, dados e estrutura devem ficar claros e reproduzíveis.

## Metodologia da Ares

Ares segue uma metodologia **Stockfish-like adaptada a RedWar**: separar estado/regras, pesquisa, avaliação e move ordering; manter o hot path pequeno; fazer alterações isoladas; exigir evidência estatística ou benchmark antes de aceitar uma melhoria funcional.

RedWar não é xadrez. Stun, lifespan, spells, summons, terreno e TWC entram na avaliação como características do RPG.

### Sanity check

`FrostMage` custa atualmente **5 pontos**. A Ares deve reconhecer que uma unidade barata com stun pode ter valor tático muito superior ao material nominal.

## Estado do projeto

O **PR #49 foi concluído como bloco de desenvolvimento, mas não foi integrado na `main`**. A base NNUE/tooling/documentação dessa branch continua como referência experimental.

O **PR #50** é o bloco atual de estabilização numérica e estrutural. A criação de uma ref nova ficou temporariamente bloqueada pelo ambiente, por isso este bloco continua na ref da continuação NNUE até o merge.

## PR #50 — estabilização numérica e estrutural

### Já concluído

- [x] Auto-Pricer protegido contra ELOs extremos, drafts inválidos e quantidades patológicas.
- [x] Avaliação C++ com operações sensíveis feitas em `int64_t`/limites explícitos.
- [x] Avaliação Cython com limites de custo/lifespan/score.
- [x] CLI C++ valida `go nodes` e rejeita zero/entradas inválidas.
- [x] Regressão C++ para custos/lifespan extremos.
- [x] Regressões Python do Auto-Pricer.
- [x] Logs gerados removidos do estado versionado.
- [x] Packaging removido de referências para ficheiros apagados.
- [x] `main_guard.yml` sem mecanismo de escrita/reversão automática da `main`.
- [x] Renderer restaurado e cache VFX corrigido para considerar largura e altura.
- [x] Auto-Balancer separado do treino/benchmark NNUE.
- [x] Workflow do Auto-Balancer com timeout e outputs temporários/artefactos.
- [x] Workflow NNUE continua responsável pelo treino nightly.
- [x] Documentação do ciclo de desenvolvimento e separação dos workflows atualizada.

### Em revisão antes do merge

- [ ] Última passagem de multiplicadores/limites do `search.cpp` e inputs numéricos de NNUE.
- [ ] Revisão final de `engine/`, `online/` e `data/`.
- [ ] Confirmar CI verde do head final.
- [ ] Remover qualquer tooling/documentação ainda referenciada apenas pelo histórico antigo.

### Regra

Nenhuma correção de overflow deste bloco será misturada com a próxima otimização do hot path NNUE.

## Ares — próxima sequência após estabilização

1. **Baseline incremental NNUE:** manter `sync_board()` como referência de correção.
2. **Hooks de mutação:** ligar mudanças de peça, stun, lifespan, cooldown, efeitos, TWC e lado a jogar ao accumulator.
3. **Reversibilidade:** testar make/unmake do accumulator contra um rescan completo após sequências aleatórias.
4. **Benchmark:** comparar NPS e custo por avaliação com o baseline, sem alterar depth/node budget.
5. **Arena:** só aceitar a otimização depois de confirmar que a força permanece estável.
6. **Depois:** quiescence e move ordering RPG, mas apenas um eixo por branch.

## Heróis e balanceamento

- [ ] Reduzir lógica de herói espalhada.
- [ ] Documentar cada herói de forma padronizada.
- [ ] Melhorar Auto-Pricer quando Ares estiver suficientemente estável.
- [ ] Reavaliar FrostMage após NNUE/TT estarem estáveis.
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

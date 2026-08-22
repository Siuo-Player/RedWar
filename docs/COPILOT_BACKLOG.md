# RedWar — Backlog de Desenvolvimento

Este documento substitui o antigo backlog focado exclusivamente em tarefas do Copilot.

O backlog deve refletir trabalho real do projeto, não marcar como concluídas funcionalidades que apenas existem parcialmente.

## P0 — Correção e estabilidade

- [ ] Garantir uma única semântica de regras entre Python e C++.
- [ ] Expandir testes diferenciais Python/C++.
- [ ] Testar sistematicamente `make -> unmake`.
- [ ] Testar hash incremental contra hash recalculado.
- [ ] Cobrir timers, efeitos e condições de vitória.
- [ ] Remover exceções/fallbacks silenciosos que possam esconder configuração inválida.
- [ ] Corrigir todos os consumidores dos APIs antigos de `GameState`/actions.

## P1 — Ares

- [ ] Completar migração do hot path para C++.
- [ ] Melhorar geração e ordenação de ações.
- [ ] Melhorar avaliação.
- [ ] Criar benchmark suite.
- [ ] Medir NPS e profundidade.
- [ ] Medir força por self-play.
- [ ] Melhorar quiescence para stun/morte/efeitos.
- [ ] Melhorar transposition table.
- [ ] Melhorar Arena para comparar commit anterior com candidato.
- [ ] Guardar resultados detalhados dos torneios.
- [ ] Criar rating/ELO de engines.

## P1 — Heróis

- [ ] Reduzir casos hardcoded de heróis onde uma abstração é viável.
- [ ] Manter `heroes_config.json` como fonte de dados.
- [ ] Documentar todos os campos do schema.
- [ ] Criar testes automáticos para cada comportamento suportado.
- [ ] Criar documentação legível dos heróis sem duplicar a fonte de custos/configuração.
- [ ] Melhorar Auto-Pricer.
- [ ] Calibrar stun.
- [ ] Calibrar gelo.
- [ ] Definir empilhamento de efeitos.

## P1 — Aplicação

- [ ] Melhorar UI/UX.
- [ ] Menu principal.
- [ ] Bots/dificuldades.
- [ ] Multiplayer local.
- [ ] Animações.
- [ ] VFX.
- [ ] Som.
- [ ] Replays.
- [ ] Histórico.
- [ ] Análise.
- [ ] Responsividade.

## P1 — Web/multiplayer

- [ ] Escolher stack web.
- [ ] Escolher hosting.
- [ ] Escolher base de dados.
- [ ] Escolher autenticação Google.
- [ ] Definir protocolo de ações/estado.
- [ ] Servidor autoritativo.
- [ ] WebSocket/transporte em tempo real.
- [ ] Matchmaking.
- [ ] Relógios.
- [ ] Timeout.
- [ ] Reconexão.
- [ ] Ranking.
- [ ] ELO/MMR.
- [ ] Desafios diretos.
- [ ] Amigos/chat.
- [ ] Rematch.
- [ ] Espectadores.
- [ ] Histórico.

## P2 — Variantes

- [ ] Testar 10×10 depois de Ares ficar muito mais rápida.
- [ ] Variantes de orçamento.
- [ ] Modos especiais.
- [ ] Novos efeitos de terreno.
- [ ] Exceções controladas ao limite de uma ação.

## P3 — Futuro

- [ ] Replays públicos.
- [ ] Anti-cheat avançado.
- [ ] Temporadas.
- [ ] Cosméticos.
- [ ] Monetização, se fizer sentido.

## Política de aceitação da IA

Para futuras contribuições abertas da Ares, a pergunta principal é:

> **Esta mudança torna a Ares melhor sob condições controladas?**

Uma mudança que apenas aumenta complexidade não é uma melhoria.

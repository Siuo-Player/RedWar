# Decisão: Foco Estratégico no Motor Stockfish-like (Ares) e Plataforma Chess.com

**Data:** 2026-11-01  
**Status:** Aceite  

## Contexto

Após a conclusão e validação do marco 1.0-Lite local (PR #587 e suite de 838 testes 100% verde), é necessário direcionar o desenvolvimento dos próximos marcos principais.
RedWar tem como inspirações fundamentais:
1. O **Stockfish**, no rigor científico da inteligência artificial, separação clara de estado, pesquisa alfa-beta/PVS, LMR, move ordering, avaliação NNUE e validação estatística por Arena A/B.
2. O **Chess.com**, como modelo de produto: múltiplos modos de jogo equilibrados (8×8, 10×10, Bullet, Blitz, Rápido, Puzzles), sistema de bots com ELO graduado, matchmaking online autoritativo e suporte a aplicação web com perfis e leaderboards.

Além disso, a IA Ares deve assumir formalmente o papel de oráculo analítico do **Balance Lab**, permitindo simular milhares de partidas para balancear custos de heróis, sinergias e regras de forma empírica e reprodutível.

## Decisão

1. **Prioridade Imediata no Ares (#372):**
   - Implementar otimizações de busca inspiradas no Stockfish: Late Move Reductions (LMR), Move Ordering aprimorado (MVV-LVA para stuns letais e de alto valor, Killer Moves, History Heuristic), Quiescence Search refinado e tabelas de transposição com Zobrist hashing completo.
   - Usar a infraestrutura de Arena automatizada para aceitar alterações apenas com evidência estatística de ganho real de força.

2. **Pipeline de Balanceamento Orientado por IA (#373):**
   - O Ares será o agente de calibração do Balance Lab.
   - Ajustar orçamentos de draft (200 pts) e custos individuais de heróis a partir de matrizes contextuais de confronto (matchup, composição, iniciativa e mapa).
   - Equilibrar múltiplos modos de jogo: Standard 8×8, Grand RedWar 10×10 e controlos de tempo (Bullet, Blitz, Rápido).

3. **Arquitetura da Plataforma (#374):**
   - Servidor WebSocket autoritativo com prevenção total de batota.
   - Sistema de classificação ELO / Glicko-2 independente por modo de jogo.
   - Roster de bots com níveis de dificuldade e ELO calibrados para treino.
   - Desenvolvimento da versão Web que partilhará a mesma lógica e protocolo da aplicação desktop.

## Consequências

- O ciclo de desenvolvimento mantém a regra de que melhorias de força da IA exigem prova empírica.
- Novas regras ou heróis devem ser validados pelo pipeline de simulações antes de congelamento competitivo.
- A arquitetura de rede em `online/` deve ser desacoplada da interface gráfica local, permitindo que o cliente desktop (Pygame) e o futuro cliente Web utilizem os mesmos endpoints autoritativos.

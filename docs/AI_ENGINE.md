# Ares — AI Engine

## Autoridade

Este documento define o contrato durável da Ares. O comportamento realmente implementado é determinado pelo código/testes do `main`; [`ROADMAP.md`](ROADMAP.md) define a ordem dos gates.

## Visão e Inspiração Stockfish

Ares é o motor de busca e avaliação em C++ de alta performance de RedWar, concebido sob os mesmos princípios rigorosos que governam o **Stockfish**:
- Separação estrita entre representação de estado, geração de lances, busca e avaliação;
- Hot path mínimo e altamente otimizado;
- Busca Alfa-Beta / Principal Variation Search (PVS) com Iterative Deepening;
- Transposition Table (TT) com Zobrist hashing;
- Ordenação de lances preditiva (Move Ordering) com heurísticas Killer e History;
- Reduções em lances tardios (Late Move Reductions - LMR);
- Busca de tranquilidade (Quiescence Search) focada em cadeias de stun e mortes letais;
- Avaliação clássica como referência sólida e rede neural **NNUE** para avaliação posicional profunda.

## Oráculo do Balance Lab

Ares atua também como o motor de simulação e avaliação do **Balance Lab**:
- Avaliação de custos de draft de heróis baseada em desempenho contextual em partidas emparelhadas;
- Identificação de heróis desbalanceados ou sinergias degeneradas através de self-play e matrizes de confronto;
- Calibração de múltiplos modos de jogo (8×8 padrão, 10×10 estendido e controlos de tempo).

## Fronteira de Execução

A ordem canónica é:

```text
input action
→ normalize / canonical resolution
→ action-space membership
→ transition-domain validation
→ mutate
```

Legalidade de action-space e validade da transição são conceitos distintos. Uma otimização de pesquisa não pode contornar a autoridade de execução. `fast_clone()` não é hot path C++ nem preflight aceite do executor.

## Pesquisa e Otimizações

Alterações de search, pruning, ordering ou evaluation são hipóteses isoladas. Devem demonstrar:

```text
correção
→ capability específica
→ custo/performance controlado
→ strength independente
```

Um maior NPS ou melhor resultado pontual num puzzle não constitui prova de ganho global de força.

### Prioridades Técnicas de Busca
1. **Move Ordering:**
   - Hash Move (da Transposition Table)
   - Lances de captura letal de 2º stun ordenados por MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
   - Lances de 1º stun em heróis de alto custo
   - Spells ofensivos com impacto direto
   - Killer Moves (2 slots por profundidade ply)
   - History Heuristic para lances calmos
   - Lances calmos restantes
2. **Late Move Reductions (LMR):**
   - Reduzir a profundidade de pesquisa de lances calmos testados tardiamente na ordenação em nós com profundidade $\ge 3$.
   - Isentar lances táticos (stuns, capturas letais e respostas a ameaças imediatas).
3. **Quiescence Search:**
   - Evitar avaliar nós intermédios instáveis onde peças chave estão prestes a receber o segundo stun letal.

## Avaliação Clássica e NNUE

A avaliação clássica permanece a referência de compatibilidade e o oráculo de calibração rápida. A rede neural NNUE é validada incrementalmente e apenas promovida a padrão após demonstrar ganho estatístico comprovado na Arena por unidade de tempo de CPU.

## Níveis de Bot (Chess.com Model)

Para suportar o modelo da plataforma, Ares suporta parametrização de força e profundidade para expor bots de diferentes níveis:
- **800 ELO (Iniciante):** Profundidade restrita (1-2 plies) com jitter aleatório;
- **1400 ELO (Intermédio):** Profundidade 3-4, busca tática e avaliação clássica básica;
- **1900 ELO (Avançado):** Profundidade 5-6, TT completa e busca quiescente;
- **2500+ ELO (Mestre Ares):** Full search, TT, LMR e avaliação profunda.

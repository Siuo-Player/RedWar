# RedWar — pesquisa recente e decisões de engenharia (2026-09-08)

## Regra de evidência

Para mudanças de IA, a promoção deve seguir:

`evidence → hipótese → implementação → teste de correção → benchmark → self-play → evidência estatística`.

`implemented != tested != benchmarked != stronger`.

## Literatura relevante

### NNUE e datasets

Tan e Watkinson Medina (2024) estudam diretamente a construção de datasets NNUE e propõem gerar/filtrar posições estáveis ("quiet"), mostrando que a composição do dataset influencia o desempenho do engine. A consequência para RedWar é tornar o dataset auditável e evitar leakage entre treino e validação.

Referência: Daniel Tan; Neftali Watkinson Medina. *Study of the Proper NNUE Dataset*. arXiv:2412.17948. DOI: 10.48550/arXiv.2412.17948.

### Search clássico

Dashev, Vassilev e Penev (2025) combinam iterative deepening, alpha-beta, quiescence, transposition tables, move ordering e killer/history heuristics, com perft e benchmark de NPS/profundidade/self-play. Nair et al. (2025) estudam move ordering, transposition-table management e controlo adaptativo de profundidade como fontes de eficiência.

Referências:

- Yulian Dashev; Martin Vassilev; Alexander Penev. *A Modular Teaching-Oriented Chess Engine with Validated Move Generation and Classical Search Enhancements*. ICAI 2025. DOI: 10.1109/ICAI67591.2025.11324630.
- Rekha R. Nair et al. *Improving Alpha-Beta Pruning Efficiency in Chess Engines*. 2025. DOI: 10.1109/ITIKD63574.2025.11004942.

### Self-play e avaliação

Jiang et al. (AAAI 2024) mostram que population-based self-play com diversidade de políticas reduz a tendência para estilos limitados e local optima. Lanctot et al. (2026) estudam avaliação ativa de agentes e encontram Elo como baseline consistente para ranking em muitos cenários.

Referências:

- Yuhua Jiang et al. *Learning Diverse Risk Preferences in Population-Based Self-Play*. AAAI 2024, 38(11), 12910–12918. DOI: 10.1609/aaai.v38i11.29188.
- Marc Lanctot; Kate Larson; Ian M. Gemp; Michael Kaisers. *Active Evaluation of General Agents: Problem Definition and Comparison of Baseline Algorithms*. arXiv:2601.07651. DOI: 10.48550/arXiv.2601.07651.

### Search no tempo de decisão

Sokota et al. (2025) mostram em Stratego que self-play e test-time search podem combinar-se para obter forte desempenho. Para RedWar, isto reforça a investigação conjunta de qualidade da avaliação e orçamento de search, mas não justifica substituir o alpha-beta/PVS determinístico por RL/MCTS.

Referência: Samuel Sokota et al. *Superhuman AI for Stratego Using Self-Play Reinforcement Learning and Test-Time Search*. arXiv:2511.07312.

## Alteração implementada nesta tranche

`tools/nnue/train.py` deixou de fazer split 90/10 apenas por ordem das linhas. O split agora agrupa por RWEN exato, é determinístico e verifica que nenhuma posição exata aparece simultaneamente em treino e validação.

Foi adicionado `tools/nnue/audit_dataset.py`, que mede linhas totais, posições únicas, duplicação, posições com labels conflitantes, tamanhos dos grupos, overlap exato e estatísticas dos scores.

Foi adicionado `tests/test_nnue_dataset_tools.py` para bloquear regressões nesta política.

## Próximas mudanças recomendadas

### NNUE incremental

O runtime já possui hooks incrementais para peça, efeito, lado e TWC, mas o caminho de mutação ainda não os liga sistematicamente. Não se deve remover `sync_board()` do hot path antes de:

1. ligar todos os hooks no `BoardState`;
2. provar `incremental == full resync` após make/unmake;
3. testar stuns, lifespan, cooldown, efeitos, TWC e turn;
4. medir NPS contra o baseline.

### Search

Depois da reversibilidade estar estável, avaliar aspiration windows, melhor política de substituição de TT e move ordering. Cada alteração deve ter benchmark independente antes de qualquer claim de força.

### Teacher/self-play

Quando o formato do teacher data tiver informação suficiente, adicionar filtro de estabilidade/tactical volatility. Para força, comparar várias versões do Ares, com seeds e posições iniciais fixas, e reportar Elo e incerteza em vez de apenas win-rate bruto.

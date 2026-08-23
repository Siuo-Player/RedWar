# Ares — auditoria de 100 otimizações

Esta checklist foi aplicada ao código do Ares para evitar optimizações por intuição isolada. O objetivo é distinguir ganhos de engenharia de baixo risco de técnicas de pesquisa que podem alterar a força.

Legenda: ✅ já aplicado; 🟡 aplicável, mas exige medição/teste; ❌ não aplicável ao desenho actual; ⏭️ próximo alvo.

## A. Compilação e runtime

1. ✅ `-O3` no build Linux do Ares.
2. ✅ `-march=native` no build Linux.
3. ✅ `-mtune=native` no build Linux.
4. ✅ LTO no build Linux da Arena/Auto-Balancer.
5. ✅ `NDEBUG` no build de produção do Ares.
6. ✅ `O2`/flags optimizadas para o avaliador Cython.
7. 🟡 PGO do motor C++.
8. 🟡 medição de NPS com benchmark fixo.
9. 🟡 perf/callgrind para perfis de CPU.
10. 🟡 perf de cache misses/branch misses.

## B. Representação de estado

11. ✅ avaliação incremental do material.
12. ✅ contagem incremental de peças.
13. ✅ hashing incremental.
14. ✅ chave TT inclui contador de 50 movimentos.
15. ✅ geração determinística das tabelas de hash.
16. ✅ TT com chave compacta da melhor jogada.
17. ⏭️ substituir strings do `Move` por enums/códigos internos.
18. ⏭️ substituir `unordered_map<string, HeroBehavior>` por acesso directo por `Piece.id`.
19. ⏭️ substituir nomes de efeitos por IDs inteiros no hot path.
20. ⏭️ eliminar cópias de `Piece` quando apenas timers mudam.

## C. Make/unmake

21. 🟡 undo compacto e orientado apenas às células alteradas.
22. ⏭️ não percorrer as 64 casas para cada actualização de timers.
23. ⏭️ manter listas de peças/efeitos temporizados.
24. ⏭️ actualizar apenas timers activos.
25. 🟡 reduzir chamadas repetidas a `update_piece`.
26. 🟡 tornar restauração de timers O(número de timers afectados).
27. 🟡 evitar rehash de estados inalterados.
28. 🟡 evitar recalcular material durante alteração exclusiva de timer.
29. 🟡 compactar `UndoInfo`.
30. ❌ lock-free undo partilhado: pesquisa actualmente single-threaded.

## D. Geração de movimentos

31. ✅ capacidade reservada no vector de movimentos.
32. ✅ quiescence filtra moves in-place.
33. 🟡 staging: TT → captures/forcing → quiet.
34. 🟡 geração directa de forcing moves para quiescence.
35. ⏭️ evitar geração de moves que serão imediatamente descartados.
36. 🟡 tabelas pré-computadas de offsets/rays.
37. 🟡 máscaras de silêncio pré-computadas.
38. 🟡 arrays fixos para listas pequenas.
39. 🟡 eliminar allocations do `std::vector` por nó.
40. 🟡 move generation incremental/cached.

## E. Move ordering

41. ✅ TT move first.
42. ✅ MVV-LVA simplificado para ataques.
43. ✅ killer moves.
44. ✅ history heuristic.
45. 🟡 counter-move heuristic.
46. 🟡 capture history.
47. 🟡 continuation history.
48. 🟡 ordering por valor de stun/morte.
49. 🟡 selection sort/staged picker para evitar ordenar a lista inteira.
50. 🟡 SEE simplificado para ataques/stuns.

## F. Alpha-beta / pesquisa

51. ✅ alpha-beta.
52. ✅ iterative deepening.
53. ✅ quiescence search.
54. ✅ transposition table.
55. ✅ principal variation search (PVS).
56. 🟡 aspiration windows.
57. 🟡 null-move pruning, com guards adequados ao RedWar.
58. 🟡 late move reductions.
59. 🟡 futility pruning.
60. 🟡 reverse futility pruning.
61. 🟡 razoring.
62. 🟡 probcut.
63. 🟡 singular extensions.
64. 🟡 multi-cut pruning.
65. 🟡 IID (internal iterative deepening).
66. 🟡 check/forcing extensions adaptadas ao stun.
67. 🟡 improving flag para modular poda/selectividade.
68. 🟡 mate-distance/terminal score mais informativo.
69. 🟡 pesquisa com janelas zero para cut nodes.
70. 🟡 pesquisa de resposta única com extensão/shortcut.

## G. Transposition table

71. ✅ TT com slots de tamanho fixo.
72. ✅ chave de posição separada da chave da move.
73. ✅ replacement depth-preferred.
74. 🟡 replacement por profundidade + idade.
75. 🟡 TT bucket com 2–4 entradas.
76. 🟡 lockless/thread-safe TT se houver SMP.
77. 🟡 packed TT entries menores.
78. 🟡 hash full-key + partial-key em buckets.
79. 🟡 prefetch da entrada TT.
80. 🟡 clear/aging de TT entre partidas conforme workload.

## H. Avaliação

81. ✅ avaliação incremental no C++.
82. ✅ PST no C++.
83. ✅ custos de peça com acesso rápido.
84. 🟡 lazy evaluation com margens seguras.
85. 🟡 cache de avaliação por posição.
86. 🟡 avaliação por fases do jogo.
87. 🟡 tabelas pré-computadas para efeitos/timers.
88. 🟡 mobilidade incremental.
89. 🟡 threat maps incrementais.
90. 🟡 avaliação específica de forcing moves.

## I. Python/Cython e integração

91. ✅ processo C++ persistente no `CppEngineBot`.
92. ✅ lazy-loading do processo.
93. ✅ comunicação UCI simples por stdin/stdout.
94. 🟡 reduzir encode/decode Python ↔ C++.
95. 🟡 benchmark de serialização RWEN.
96. 🟡 cache de `rwen` quando a posição não mudou.
97. ✅ boundscheck/wraparound desligados no avaliador Cython.
98. 🟡 tipagem Cython completa no evaluator.
99. 🟡 evitar clones repetidos em `ai/search.py`.
100. 🟡 multiprocessing/parallel search para workloads longos, somente depois de estabilizar o single-thread.

## Resultado desta passagem

Foram aplicadas nesta linha de optimização as alterações de baixo risco com impacto estrutural claro: compilação optimizada, quiescence sem segunda lista, TT com best-move compacto, PVS e replacement depth-preferred. As restantes estão classificadas para implementação incremental e benchmark, sobretudo os itens 17–25 e 33–40, que atacam directamente o custo por nó.

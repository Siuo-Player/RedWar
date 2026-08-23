# Ares — auditoria e próxima passagem

Esta checklist deve ser mantida junto das optimizações do Ares. Itens marcados como aplicados foram implementados sem reduzir deliberadamente o limite de nós. Itens de poda agressiva (LMR, null move, futility, etc.) continuam separados porque podem alterar a força.

## Estado
- ✅ Build otimizado do C++ (`-O3 -march=native -mtune=native -flto -DNDEBUG`).
- ✅ Quiescence com filtragem in-place.
- ✅ TT compacta e depth-preferred.
- ✅ PVS com re-search.
- ✅ Avaliação Cython compilada com optimização.
- ⏭️ Hash incremental sem `std::string` no hot path.
- ⏭️ Timers incrementais, sem scan/`update_piece()` de 64 casas por nó.
- ⏭️ Hero lookup por ID em vez de `unordered_map<string,...>`.
- ⏭️ Geração de moves com menos allocations.
- ⏭️ Representação de tipos de move sem strings no hot path.
- ⏭️ Máscaras pré-calculadas para auras/áreas.

## Checklist de 100 pontos

### Compilação e runtime
1. ✅ `-O3`
2. ✅ `-march=native`
3. ✅ `-mtune=native`
4. ✅ LTO
5. ✅ `NDEBUG`
6. ✅ Cython compiler optimization
7. 🟡 PGO
8. 🟡 CPU-specific build matrix
9. ✅ evitar I/O durante pesquisa
10. ✅ processo C++ persistente

### Representação de estado
11. ⏭️ IDs inteiros para heroes no hot path
12. ⏭️ enums inteiros para tipo de move
13. ⏭️ evitar `std::string` em `Move`
14. ✅ TT sem `Move` completo
15. 🟡 compactar `Piece`
16. 🟡 compactar `TileEffect`
17. ✅ arrays de tamanho fixo onde apropriado
18. 🟡 separar estado mutável de metadados
19. 🟡 cache de hero behavior por ID
20. 🟡 evitar cópias de `Piece`

### Hash / TT
21. ⏭️ Zobrist O(1) por ID
22. ⏭️ Zobrist O(1) por efeito
23. ✅ hash incremental
24. ✅ hash inclui `twc`
25. ✅ TT depth-preferred
26. ✅ TT move compacto
27. ✅ flag exact/lower/upper
28. 🟡 buckets de TT
29. 🟡 aging de TT
30. ✅ máscara power-of-two

### Make / unmake
31. ⏭️ não actualizar células inalteradas
32. ⏭️ timers apenas em peças que têm timers
33. ⏭️ efeitos apenas quando activos
34. 🟡 undo com arrays compactos
35. 🟡 evitar cópia de Piece em cada caminho
36. 🟡 fast path para MOVE simples
37. 🟡 fast path para ATTACK simples
38. 🟡 fast path para SPELL sem AOE
39. 🟡 evitar lookup de hero por string
40. 🟡 reduzir recomputação de material

### Move generation
41. 🟡 pré-calcular raios
42. 🟡 pré-calcular adjacências
43. 🟡 pré-calcular knight offsets
44. ⏭️ máscaras de aura
45. 🟡 evitar bounds checks repetidos
46. 🟡 gerar captures/forcing directamente
47. ⏭️ vector reutilizável por ply
48. 🟡 inline de checks de casa
49. 🟡 evitar `std::string` nos moves
50. 🟡 separar move/capture generation

### Move ordering
51. ✅ TT move primeiro
52. ✅ MVV-LVA
53. ✅ killer moves
54. ✅ history heuristic
55. ✅ score de stun
56. ✅ score de ignite
57. 🟡 counter move
58. 🟡 continuation history
59. 🟡 SEE
60. 🟡 ordenar apenas quando necessário

### Search
61. ✅ alpha-beta
62. ✅ iterative deepening
63. ✅ PVS
64. 🟡 aspiration windows
65. 🟡 null move pruning (validar zugzwang)
66. 🟡 late move reductions (validar força)
67. 🟡 futility pruning
68. 🟡 razoring
69. 🟡 delta pruning em qsearch
70. 🟡 singular extensions

### Quiescence
71. ✅ limite de profundidade
72. ⏭️ forcing-only generation
73. 🟡 delta pruning
74. 🟡 SEE capture filter
75. ✅ move ordering
76. 🟡 evitar geração completa antes do filtro
77. 🟡 qsearch TT
78. 🟡 qsearch killer/counter
79. 🟡 early stand-pat cutoff
80. 🟡 evitar cópias de vector

### Evaluation
81. ✅ avaliação incremental
82. ✅ material counters
83. ✅ PST
84. 🟡 cache por Piece kind
85. 🟡 integer arithmetic
86. 🟡 pré-calcular valores derivados
87. 🟡 lazy evaluation
88. 🟡 king/hero safety cache
89. 🟡 mobility cache
90. 🟡 threat cache

### Python/Cython/integration
91. ✅ engine persistente
92. ✅ sem restart por turno
93. ✅ stdout line-buffered
94. ✅ parsing mínimo de bestmove
95. ✅ Cython evaluator
96. ✅ boundscheck desligado
97. ✅ wraparound desligado
98. ⏭️ reduzir object access Cython
99. 🟡 cache de catálogo de draft
100. 🟡 benchmark automatizado NPS/regressão

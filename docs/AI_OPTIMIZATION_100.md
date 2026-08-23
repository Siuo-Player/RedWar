# Ares — auditoria de 100 otimizações

Legenda: ✅ aplicado; 🟡 aplicável mas requer medição/validação; ⏭️ próximo alvo; ❌ não aplicável.

1 ✅ O3
2 ✅ march=native
3 ✅ mtune=native
4 ✅ LTO C++
5 ✅ NDEBUG
6 ✅ flags Cython otimizadas
7 🟡 PGO
8 🟡 CPU-specific builds
9 ✅ sem I/O na pesquisa
10 ✅ processo C++ persistente
11 ⏭️ hero IDs no hot path
12 ⏭️ enums para move types
13 ⏭️ remover strings de Move
14 ✅ TT sem Move completo
15 🟡 compactar Piece
16 🟡 compactar TileEffect
17 ✅ arrays fixos onde apropriado
18 🟡 separar estado de metadados
19 ⏭️ cache de behavior por ID
20 🟡 reduzir cópias de Piece
21 ⏭️ Zobrist por ID
22 ⏭️ Zobrist de efeitos por tabela
23 ✅ hash incremental
24 ✅ hash inclui twc
25 ✅ TT depth-preferred
26 ✅ TT move compacto
27 ✅ flags TT
28 🟡 TT buckets
29 🟡 TT aging
30 ✅ power-of-two TT
31 ⏭️ não atualizar células inalteradas
32 ⏭️ timers só quando ativos
33 ⏭️ efeitos só quando ativos
34 🟡 undo mais compacto
35 🟡 fast paths de make/unmake
36 🟡 MOVE fast path
37 🟡 ATTACK fast path
38 🟡 SPELL fast path
39 ⏭️ lookup por ID
40 🟡 material incremental adicional
41 🟡 raios pré-calculados
42 🟡 adjacências pré-calculadas
43 🟡 knight offsets
44 ⏭️ máscaras de aura
45 🟡 bounds checks reduzidos
46 ⏭️ forcing/captures directos
47 ⏭️ buffers reutilizados por ply
48 🟡 checks inline
49 ⏭️ strings fora de Move
50 🟡 geração separada de captures
51 ✅ TT move ordering
52 ✅ MVV-LVA
53 ✅ killer
54 ✅ history
55 ✅ stun scoring
56 ✅ ignite scoring
57 🟡 counter move
58 🟡 continuation history
59 🟡 SEE
60 🟡 sort condicional
61 ✅ alpha-beta
62 ✅ iterative deepening
63 ✅ PVS
64 🟡 aspiration windows
65 🟡 null move (validar força)
66 🟡 LMR (validar força)
67 🟡 futility
68 🟡 razoring
69 🟡 qsearch delta pruning
70 🟡 singular extensions
71 ✅ qsearch depth limit
72 ⏭️ forcing-only generator
73 🟡 qsearch delta pruning
74 🟡 qsearch SEE
75 ✅ qsearch ordering
76 ⏭️ não gerar moves irrelevantes
77 🟡 qsearch TT
78 🟡 qsearch killer/counter
79 🟡 stand-pat cutoffs
80 ✅ qsearch vector in-place
81 ✅ avaliação incremental C++
82 ✅ material counters
83 ✅ PST
84 🟡 cache por kind
85 ✅ integer arithmetic no evaluator Cython
86 🟡 valores derivados pré-calculados
87 🟡 lazy eval
88 🟡 hero safety cache
89 🟡 mobility cache
90 🟡 threat cache
91 ✅ engine persistente
92 ✅ sem restart por turno
93 ✅ stdout simples
94 ✅ parsing mínimo de bestmove
95 ✅ Cython evaluator
96 ✅ boundscheck=False
97 ✅ wraparound=False
98 ⏭️ reduzir object access Cython
99 🟡 cache de catálogo de draft
100 ✅ benchmark NPS/regressão

Os itens 11/21/31/32/39/44/46/47/49/72 são os próximos alvos estruturais de maior impacto. Não foram aplicados nesta passagem porque alteram a representação do motor e devem ser validados por posição/hash/melhor-jogada antes do merge.

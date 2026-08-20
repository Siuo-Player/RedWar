FASE 1 — Formalizar modularidade dos heróis (CONCLUÍDO)
------------------------------------------------------------
- [x] Substitui parser JSON pelo nlohmann/json REAL.
- [x] Acrescenta `behavior.movement`/`behavior.attack` no `heroes_config.json`.
- [x] Acrescenta as passivas declarativas (Berserker, Templar, Inquisitor).
- [x] Formaliza os feitiços ativos (Purify, Swap, Barricada, Ignite, Salto, Silêncio).

FASE 2 — Portar a IA completamente para C++ (CONCLUÍDO)
-------------------------------------------------
- [x] Implementa geração de STUN/SPAWN/SPELL em `engine.cpp`.
- [x] Zobrist Hashing + Tabela de Transposição reais e Otimização de tempo.

FASE 5 — Habilidades Passivas Data-Driven (CONCLUÍDO)
--------------------------------------------------------
- [x] Desacoplar a física de combate: Invocação on-kill (BoneLord), Dano em Área (Berserker).
- [x] Lógica complexa de movimento: Salto Dracónico (Dragoon).
- [x] Auras dinâmicas: Filtro de silêncio em raio (Inquisitor).

FASE 6 — Refactoring Modular e Inteligência Posicional (EM CURSO)
--------------------------------------------------------
- [x] Atualizar script de compilação para suportar múltiplos ficheiros `.cpp`.
- [ ] Dividir o monólito `engine.cpp` em: `types.hpp`, `board.cpp`, `movegen.cpp`, `evaluate.cpp`, `search.cpp` e `main.cpp`.
- [ ] Mudar os includes globais do `SmokeTest.cpp`.
- [ ] Implementar Piece-Square Tables (PST) no `evaluate.cpp` nativo em C++ para compreensão tática de terreno.
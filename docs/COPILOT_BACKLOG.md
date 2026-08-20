REDWAR — BACKLOG PARA O COPILOT
================================

FASE 1 — Modularidade dos Heróis (CONCLUÍDO)
------------------------------------------------------------
- [x] Substituir parser JSON pelo nlohmann/json REAL.
- [x] Declarar `behavior.movement`/`behavior.attack` para todos os heróis.
- [x] Passivas declarativas (Berserker, Templar, Inquisitor).
- [x] Feitiços ativos formalizados (Purify, Swap, Barricada, Ignite, Salto, Silêncio).

FASE 2 — Motor C++ e Memória (CONCLUÍDO)
-------------------------------------------------
- [x] Geração nativa de STUN/SPAWN/SPELL no gerador de lances.
- [x] Despacho de passivas (On-Kill, Dano em Área, etc.).
- [x] Zobrist Hashing (Peças, Fogo, Gelo) + Transposition Table (TT).
- [x] Controlo de tempo e Orçamento de Busca.

FASE 3 — Inteligência e Arquitetura Posicional (CONCLUÍDO)
--------------------------------------------------------
- [x] Refactoring: Dividir o monólito em módulos (`board.cpp`, `movegen.cpp`, `search.cpp`, etc.).
- [x] Piece-Square Tables (PST) para compreensão tática de terreno e posicionamento.

FASE 4 — Consolidar Ecossistema Python (EM CURSO)
--------------------------------------------------------
- [ ] Atualizar scripts de Analytics (`arena_tournament.py`, `calibrate_elo.py`, `trainer.py`, `game_analyzer.py`). Muitos têm bugs legado por chamarem `make_action` em vez de `execute_action` ou usarem a versão antiga do `ActionParser`.
- [ ] Atualizar o README.md com a nova arquitetura modular, sistema de passivas e os caminhos corretos.

FASE 5 — Quiescence Search (O Efeito Horizonte) (PENDENTE)
--------------------------------------------------------
- [ ] Implementar a "Pesquisa de Apaziguamento" no `search.cpp`. A IA atual sofre do Efeito Horizonte (para de avaliar no `depth=0` mesmo que haja uma captura óbvia no turno seguinte). A Quiescence Search obriga a IA a continuar a pesquisar apenas "capturas" até o tabuleiro estabilizar.

FASE 6 — Multiplayer + Empacotamento (PENDENTE)
---------------------------------------------------------------------------
- [ ] Otimizar protocolo cliente/servidor (`online/network/client.py` e `online/server/app.py`).
- [ ] Corrigir referências a ficheiros antigos no spec de compilação do executável.
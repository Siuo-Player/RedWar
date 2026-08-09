REDWAR — BACKLOG PARA O COPILOT
================================

Como usar este ficheiro: no início de qualquer sessão, diz "abre docs/COPILOT_BACKLOG.md,
encontra o próximo item não marcado na fase atual, faz só esse, verifica, marca [x], e para."
Não avances para a fase seguinte sem autorização explícita — mesmo que todos os itens da
fase atual estejam marcados. As fases são propositadamente sequenciais.

REGRAS FIXAS (aplicam-se sempre):
1. Terminal: verifica com "echo SHELL_CHECK_OK" antes de qualquer comando. Resposta diferente do esperado = terminal errado, abre um novo.
2. Depois de um comando de compilação funcionar, reusa exatamente essa sintaxe. Não inventes variações a meio.
3. Confirma que edições já estão escritas em disco antes de compilar/testar a seguir a elas, não apenas pendentes da minha aprovação manual no editor.
4. Máximo 3 tentativas por erro. Ao 3º, PARA — relata comando+erro exato de cada tentativa e a tua hipótese da causa.
5. Última frase, sempre: lista exatamente que ficheiros alteraste/criaste/apagaste.
6. Não inventes deltas, nomes de função, ou factos sobre o código sem confirmar por leitura direta.
7. Tens acesso a estrutura_atual.txt para a árvore do projeto. Se precisares de confirmar que está atual, tens autorização para correr python tools/scripts/gerar_estrutura.py.
8. Scripts de tools/analytics/ (arena_tournament.py, calibrate_elo.py, calibrate_elo_chain.py, trainer.py, game_analyzer.py) simulam dezenas a centenas de jogos e demoram muito — nunca os corras com os valores por omissão só para "testar que funciona". Se precisares de confirmar que um deles corre sem erro, usa o mínimo de jogos possível (1 a 5): via --jogos se tiver argparse, ou chamando a função diretamente (ex: python -c "from tools.analytics.game_analyzer import correr_diagnostico_profundo; correr_diagnostico_profundo(3)") em vez de correr o __main__ com o valor de produção. A verificação de qualquer tarefa sobre engine.cpp é sempre e só o SmokeTest de C++ abaixo, nunca estes scripts, a menos que a tarefa seja explicitamente sobre eles.


TAREFA PARALELA — README.md (pode ser feita em qualquer altura, não bloqueia as fases)
------------------------------------------------------------------------------------------
- [ ] O README descreve `ai/trainer.py` e `ai/game_analyzer.py` — já não é onde estão,
      é `tools/analytics/trainer.py` e `tools/analytics/game_analyzer.py`. Corrige os
      caminhos na árvore de arquitetura e em qualquer menção solta no texto.
- [ ] "Zobrist Hashing + Tabela de Transposição" está listado em "✅ Concluído Recentemente"
      — isto só é verdade no lado Python (`game_state.py`). O motor C++ ainda não tem
      Zobrist nem TT nenhuma (é a Fase 2 deste backlog). Corrige para não sobrestimar:
      ou remove de "Concluído" ou explicita "lado Python apenas, C++ pendente".
- [ ] A tabela "Presets oficiais da Arena" (100/140/200/250/300 ELO) não bate certo com
      os thresholds reais em `ai/bot.py` (`gerar_bot_por_elo`: 800/1400/1900) nem com os
      pesos em `tools/analytics/trainer.py` (`POOL_BOTS`: 100/900/1500/2000). Não inventes
      um número novo — sinaliza a inconsistência num comentário e pergunta-me qual escala
      é a atual antes de escolheres uma.
- [ ] Roadmap "🔴 Em Curso": "Cythonização Extrema" está desatualizado — o caminho real
      já não é cythonizar mais o Python, é o motor C++ em `ai/cpp_engine/`. Substitui essa
      linha por uma descrição fiel às 4 fases deste backlog (heróis modulares → IA
      completa em C++ → ajustes de jogo se necessário → multiplayer/packaging).
- [ ] Acrescenta uma secção breve sobre o sistema de passivas declarativas
      (`HEROES_SCHEMA.md`, `behavior.passives`) — não existe menção nenhuma a isto hoje.
- [ ] Não inventes funcionalidades que não existem. Se tiveres dúvida sobre se algo está
      feito, confirma no código antes de escrever que está.


FASE 0 — Limpeza rápida (antes de tudo)
--------------------------------------------
- [ ] Remove os `std::cerr` de debug deixados em `ai/cpp_engine/engine.cpp` e em
      `ai/cpp_engine/SmokeTest.cpp` (procura por "DEBUG"). Confirma que o SmokeTest
      continua PASS depois de os tirares.


FASE 1 — Formalizar modularidade dos heróis (em curso)
------------------------------------------------------------
Lê `engine/pieces.py` (BehaviorCompiler) e `engine/HEROES_SCHEMA.md` antes de tocar em
qualquer coisa aqui — a semântica de cada `type` já existe em Python, o objetivo é
espelhá-la no JSON, não reinventá-la.

- [ ] Substitui `ai/cpp_engine/nlohmann/json.hpp` pela biblioteca nlohmann/json REAL
      (single header, repositório oficial), não o parser escrito à mão que lá está agora
      — esse já teve pelo menos duas rondas de bugs reativos (arrays com espaços, tokens
      não suportados). Atualiza includes se a API diferir da versão placeholder.
- [ ] Acrescenta `behavior.movement`/`behavior.attack` no `heroes_config.json` para os
      heróis que ainda não têm (caem hoje no fallback ortogonal genérico do C++): Bone,
      FrostMage, Lich, Ranger, Templar, Berserker, Pyromancer, Dragoon, Cleric, Trickster,
      Geomancer, StoneWall, Nightshade, Inquisitor, e o movement/attack do BoneLord (já
      tem `passives`, falta o padrão em 'V' do ataque — lê `pieces.py` para a forma exata).
      Um herói de cada vez, corre o SmokeTest depois de cada um.
- [ ] Acrescenta a passiva do Berserker ao `heroes_config.json`, seguindo o exemplo já
      escrito em `HEROES_SCHEMA.md` (trigger on_attack, effect aoe_damage, pattern adjacent).
- [ ] Acrescenta a passiva do Templar, também já exemplificada em `HEROES_SCHEMA.md`
      (trigger on_attacked, effect redirect_damage, `cooldown_turns` — não uses `chance`,
      já foi decidido que reflete determinístico, sem RNG).
- [ ] Formaliza os feitiços ativos (Purify, Swap, Barricada, Ignite, Salto, Silêncio) no
      contentor `spell` já documentado em `HEROES_SCHEMA.md`, um por herói: Cleric,
      Trickster, Geomancer, Pyromancer, Dragoon, Inquisitor.
- [ ] Migra a passiva do Inquisitor (já tem código real em `pieces.py`:
      `get_aura_positions`, `get_valid_spells`, `get_threat_area`) para a forma declarativa
      `aura_passive` — é o exemplo já pronto em `HEROES_SCHEMA.md`. Preserva o
      comportamento, não o reescrevas do zero.

Checkpoint antes da Fase 2: todos os itens acima marcados, SmokeTest com um caso por
herói novo, tudo PASS. Para e espera confirmação antes de avançar.


FASE 2 — Portar a IA completamente para C++
-------------------------------------------------
Só começa depois do checkpoint da Fase 1 confirmado.

- [ ] Implementa geração de STUN/SPAWN/SPELL em `engine.cpp` (hoje só existe MOVE/ATTACK),
      lendo os blocos `stun`/`spawn`/`spell` do JSON com o mesmo padrão usado para
      movement/attack.
- [ ] Implementa o despacho de passivas em C++ (`on_kill`, `on_attack`, `on_attacked`,
      `aura_passive`, etc.), espelhando o dispatcher já feito em `game_state.py`
      (`_get_attack_spawn_piece`) — mesmo padrão de registo (nome → handler), não uma
      cadeia de if/else fechada.
- [ ] Zobrist Hashing + Transposition Table reais no `engine.cpp`:
      - tabela de chaves estáticas de 64-bits para peça+equipa+stun_timer+lifespan+
        spawn_cooldown+turno (o Python já usa este 7-tuplo, replica a mesma chave)
      - TranspositionTable real (substitui o unordered_map vazio atual): guarda
        zobrist_key, depth, value, flag (EXACT/LOWERBOUND/UPPERBOUND), best_move
      - `alpha_beta` lê da TT no início (corta com cache-hit de depth suficiente) e
        grava antes de retornar
      - não inventes heurísticas novas aqui, só a memória e os cortes
- [ ] Node-count como orçamento de busca (em vez de, ou a par de, profundidade fixa) —
      liga isto à discussão de ELO/dificuldade já tida; se precisares de relembrar o
      raciocínio, está nas notas de calibração ELO mais atrás nesta conversa.
- [ ] Só depois de tudo isto passar nos testes: revisita `tools/analytics/arena_tournament.py`,
      `calibrate_elo.py`, `calibrate_elo_chain.py`, `trainer.py`, `game_analyzer.py`,
      `color_balancer.py` — vários têm bugs de compatibilidade com o `bot.py` atual (stun
      que nunca tem efeito porque chamam `make_action` em vez de `execute_action`;
      `KeyError` porque esperam o formato antigo do `ActionParser`; `calibrate_elo_chain.py`
      usa um `BotConfig` que já não existe como tal). Corrige-os agora que há uma versão
      final para serem compatíveis — antes disto seria trabalho a refazer.

Checkpoint antes da Fase 3: SmokeTest completo PASS, e pelo menos um torneio pequeno
via `arena_tournament.py` a correr sem erro até ao fim. Para e espera confirmação.


FASE 3 — Ajustar jogo/tabuleiro (só se necessário)
--------------------------------------------------------
- [ ] Não começar nada aqui sem instrução explícita minha depois da Fase 2. O objetivo
      desta fase é decidir, com a IA já forte, se o tabuleiro/regras precisam de ajuste
      para caber a diversidade de heróis — não é um item de código à partida.


FASE 4 — Multiplayer + empacotamento (última prioridade, confirmada)
---------------------------------------------------------------------------
- [ ] `online/network/client.py` envia `{"tipo": "acao", ...}` estruturado;
      `online/server/app.py` só reage a `{"tipo": "acao_agnostica", "acao": "..."}`
      (string já formatada). Alinha os dois pelo design do documento de contexto: servidor
      stateless que só retransmite strings RWEN/algébricas — o cliente deve enviar a
      string já formatada, não campos separados.
- [ ] `online/client/multiplayer_main.py` importa `from network.client import
      NetworkClient` — devia ser `from online.network.client import NetworkClient`
      desde a reorganização de pastas.
- [ ] `deploy/packaging/main.spec` referencia `engine/mobs_config.json` (não existe,
      é `engine/heroes_config.json`) e `ai/elo_config.json` (é
      `tools/analytics/elo_config.json`). Corrige antes do próximo build do executável.

# RedWar

RedWar é um jogo tático em grelha 8x8 com heróis, stun, lifespan, spells, summons e IA Ares.

## Estado atual

A Ares tem um motor C++ próprio, avaliação clássica e uma pipeline NNUE experimental. A avaliação NNUE é opcional e continua atrás da avaliação clássica enquanto força, custo e estabilidade não estiverem demonstrados.

A disciplina de desenvolvimento segue blocos isolados: branch → implementação → regressões → validação → PR → merge → nova branch a partir da `main` atual.

## Validação e experimentação

Os workflows têm responsabilidades separadas:

- `auto_balancer.yml`: regressões numéricas, build mínimo do motor usado pelo trainer, telemetria e Auto-Pricer;
- `ai_arena.yml`: comparação de força entre AIs;
- `ai_quality_gate.yml`: gate de qualidade nos PRs de AI;
- `nnue_nightly.yml`: geração de teacher data e treino NNUE experimental;
- `main_guard.yml`: proteção/política da `main`.

Uma falha de treino NNUE não deve ser apresentada como falha do Auto-Balancer.

## Desenvolvimento

A documentação técnica principal está em `docs/`.

- `docs/ARCHITECTURE.md` — arquitetura e responsabilidades;
- `docs/AI_ENGINE.md` — Ares, pesquisa e avaliação;
- `docs/NNUE.md` — pipeline NNUE;
- `docs/ROADMAP.md` — sequência de desenvolvimento;
- `docs/DEVELOPMENT_WORKFLOW.md` — regras de branches, PRs e validação;
- `docs/TOOLING.md` — ferramentas e contratos.

## Princípios da Ares

Ares segue uma abordagem inspirada em engines open-source maiores: estado, geração de ações, pesquisa, avaliação e tooling experimental devem ter fronteiras claras; melhorias de performance precisam de benchmark; melhorias de força precisam de Arena/evidência; e regressões devem ser reproduzíveis.

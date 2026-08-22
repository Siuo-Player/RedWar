# RedWar — Documentação

A documentação está dividida por público e por responsabilidade.

## Para jogadores

- [`GAME_RULES.md`](GAME_RULES.md) — regras atuais, combate, stun, efeitos e vitória.
- [`GAME_DESIGN.md`](GAME_DESIGN.md) — filosofia de design e razões por trás das mecânicas.

## Para desenvolvedores

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitetura atual e arquitetura alvo.
- [`AI_ENGINE.md`](AI_ENGINE.md) — Ares, pesquisa, avaliação, hashing e Arena.
- [`HERO_SYSTEM.md`](HERO_SYSTEM.md) — heróis, `heroes_config.json` e modelo data-driven.
- [`WEB_MULTIPLAYER.md`](WEB_MULTIPLAYER.md) — aplicação, web, servidor, contas e multiplayer.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — fluxo de desenvolvimento e testes.
- [`CONTRIBUTION_POLICY.md`](CONTRIBUTION_POLICY.md) — política de contribuição e separação Ares/produto.

## Planeamento

- [`ROADMAP.md`](ROADMAP.md) — trabalho atual, fases seguintes e decisões ainda abertas.
- [`COPILOT_BACKLOG.md`](COPILOT_BACKLOG.md) — backlog técnico detalhado.
- [`Estrutura_Projeto.md`](Estrutura_Projeto.md) — mapa da estrutura do repositório.
- [`Documento_Design_Jogo.md`](Documento_Design_Jogo.md) — documento de design histórico/compatível com decisões atuais.

## Fontes autoritativas

Quando existir conflito entre documentos:

1. o comportamento implementado e testado do jogo é a fonte operacional;
2. `engine/heroes_config.json` é a fonte de dados dos heróis;
3. `engine/HEROES_SCHEMA.md` define a estrutura técnica dessa configuração;
4. `GAME_RULES.md` documenta as regras que o projeto pretende considerar atuais;
5. `ROADMAP.md` documenta o que é futuro e ainda não implementado.

Não assumir que algo planeado já existe apenas porque aparece no roadmap.

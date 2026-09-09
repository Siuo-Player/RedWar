# RedWar — Modelo de progresso do produto 1.0

Este documento define como interpretar as percentagens usadas em `docs/ROADMAP.md`.

## Princípio

A percentagem mede **distância ponderada ao produto 1.0**, não linhas de código, número de PRs ou quantidade de subsistemas já iniciados.

RedWar tem uma dimensão de engine/IA muito mais madura do que a percentagem global pode sugerir porque o 1.0 inclui um produto online completo.

## Ordem

```text
Fundação
  ↓
Gameplay
  ↓
Ares
  ↓
Produto
  ↓
Online
  ↓
Release
```

UI, replay, tooling e preparação de infraestrutura podem avançar em paralelo quando os contratos usados já são estáveis. Isso não permite saltar um correctness blocker.

## Métricas de referência

- Fundação: ~70%
- Gameplay: ~85%
- Ares: ~60%
- Produto: ~30%
- Online: ~5%
- Release: ~10%
- Global: ~38%

Estes números são aproximações para gestão do projecto. Devem subir com mudanças materiais de estado e evidência adequada.

## Distinções obrigatórias

- benchmark não é strength;
- dataset maior não é automaticamente dataset melhor;
- CI verde não é prova de correctness total;
- engine funcional não é produto completo;
- servidor funcional não é ecossistema online completo;
- investigação de Ares não é automaticamente uma melhoria do bot.

## Critério final

RedWar chega a 100% apenas quando o jogo, a Ares aceite, a aplicação, o replay/análise, o multiplayer autoritativo, as contas/matchmaking/rating previstos e os requisitos de QA, segurança, licenciamento e distribuição foram integrados num produto público suportado.

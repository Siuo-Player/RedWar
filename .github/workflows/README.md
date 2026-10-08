# RedWar — Actions workflow/task routing

Este documento é o ponto de entrada para escolher o workflow de GitHub Actions correto. O roadmap continua a ser a fonte única da ordem dos gates; este ficheiro apenas responde a **“qual workflow executo para este objetivo?”**.

## Regra operacional

Antes de iniciar qualquer trabalho experimental, de treino, calibração ou diagnóstico caro:

```
Issue aberta e governante
    ↓
inputs congelados / commit / seed / orçamento
    ↓
workflow correto
    ↓
artefacto/evidence destination explícito
    ↓
critério de aceitação e decisão
```

Não usar resultados de workflows diagnósticos ou experimentais como se fossem required checks de promoção. A única autoridade Action-based strength-sensitive para PRs é `.github/workflows/ai_quality_gate.yml`.

## Matriz de routing

| Workflow | Objetivo | Trigger | Tipo | Autoridade / gate | Quem deve chamar |
|---|---|---|---|---|---|
| `test_suite.yml` | Testes funcionais, regressões e contratos Python/C++ | PR, push de branches não-`main`, manual | CI automático | Required/general correctness | Toda alteração de código |
| `lite_windows_acceptance.yml` | Aceitação real desktop 1.0-Lite em Windows | PR/push-`main` em paths relevantes, manual | CI de produto | Aceitação Lite/Windows | Alterações em produto/UI/replay/launcher |
| `ai_quality_gate.yml` | Qualidade e strength-sensitive Ares em PRs | PR, manual | Gate automático | **Autoridade de promoção Ares** | PRs que alterem IA/qualidade protegida |
| `codeql.yml` | Análise de segurança | PR, push-`main`, semanal, manual | Segurança automática | Security evidence | Segurança/código; execução normal também é automática |
| `arena_diagnostics.yml` | Lifecycle/TT diagnostics da Arena | Manual | Diagnóstico | Não-authoritativo | Issue de diagnóstico com inputs fixos |
| `arena_experiments.yml` | Experiências A/B, protected holdout e datasets | Manual | Experimento | Não-authoritativo | Issue experimental com hipótese e holdout |
| `historical_bridge_dispatch.yml` | Dispara exclusivamente o plano predeclarado #488 (100 jogos A/B) através de `arena_experiments.yml` | Push com branch e mensagem de commit exatas | Trigger one-shot com inputs fixos | Não-authoritativo; não altera promoção | Só a Issue #488 e o plano versionado correspondente |
| `strength_calibration.yml` | Calibração A/A de strength | Manual ou push em branches `calibration/strength/**` | Pesquisa controlada | Não-authoritativo | Protocolo de calibração previamente definido |
| `lite_baseline_selection.yml` | Seleção do baseline Ares Lite | Manual | Experimento de seleção | Evidência de baseline; não substitui #372 | Issue de baseline com pares/replay checks fixos |
| `lite_balance_development.yml` | Campanha Balance Lab de desenvolvimento | Manual | Experimento | Desenvolvimento, não holdout/promoção | Issue de balanceamento |
| `lite_balance_matched_development.yml` | Campanha emparelhada de desenvolvimento | Manual | Experimento | Desenvolvimento, não holdout/promoção | Issue de balanceamento que exige cores/condições matched |
| `nnue_experimental_training.yml` | Teacher data, treino e modelos NNUE experimentais | Manual | Treino/pesquisa | Não-authoritativo | Issue NNUE com revisão/policy e destino de artefactos |
| `auto_balancer.yml` | Trainer, telemetria e auto-pricer diagnóstico | Manual | Diagnóstico | **Não é autoridade de balanceamento** | Issue explícita de Balance Lab/tooling |

## O que é automático

`test_suite.yml`, `ai_quality_gate.yml`, `lite_windows_acceptance.yml` e `codeql.yml` podem iniciar automaticamente porque verificam contratos ou segurança de forma repetível.

A execução semanal de CodeQL é deliberadamente mantida: é uma atividade de segurança, não uma experiência de treino/calibração.

## O que é manual

Arena, calibração, baseline selection, Balance Lab, NNUE training e Auto-Balancer são normalmente acionados manualmente (exceto o trigger de branch explicitamente predeclarado de `strength_calibration.yml`). `historical_bridge_dispatch.yml` é uma exceção one-shot restrita ao branch `run/historical-bridge-48dd4df-to-3826b3` e à mensagem de commit exata `dispatch predeclared historical bridge v1`; valida o plano #488 congelado e só então despacha `arena_experiments.yml` com 100 jogos/10.000 nós. O run resultante continua não-autoritativo. Esses workflows devem começar com uma Issue aberta que contenha objetivo, dependências, inputs congelados, orçamento, destino da evidência e critério de aceitação.

## Autoridade

- **Correção funcional:** `test_suite.yml`.
- **Promoção strength-sensitive de Ares:** `ai_quality_gate.yml`.
- **Segurança:** `codeql.yml`.
- **Aceitação de produto Lite em Windows:** `lite_windows_acceptance.yml`.
- **Arena diagnostics/experiments, calibration, Balance Lab, NNUE training e Auto-Balancer:** produzem evidência, nunca promoção automática.

Um resultado experimental positivo **não** fecha #372 nem substitui a cadeia `#370 → #371 → #372 → #373 → #374 → #375`.

## Checklist para uma nova Issue

Uma nova Issue deve responder, sem depender da conversa:

1. **Goal** — o que queremos aprender/mudar?
2. **Governing Issue** — qual Issue controla o bloco?
3. **Dependencies** — quais gates, commits, configs ou decisões são pré-requisitos?
4. **Workflow / evidence** — qual workflow e onde ficam os artefactos?
5. **Frozen inputs** — baseline/ref, seed, orçamento, população, ruleset ou dataset.
6. **Acceptance** — qual resultado permite aceitar, rejeitar ou abrir uma nova decisão?

Quando o trabalho for apenas um bug/produto, não preencher uma experiência científica falsa: usar o template correspondente e indicar o workflow de CI relevante.

## Relação com o roadmap

`docs/ROADMAP.md` continua a definir a ordem e o bloqueio entre gates. Este routing guide não cria uma segunda roadmap e não reclassifica #372, #365 ou outras Issues canónicas.

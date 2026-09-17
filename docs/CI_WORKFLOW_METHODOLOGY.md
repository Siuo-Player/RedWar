# RedWar — GitHub Actions workflow methodology

## Objetivo

Os workflows do RedWar são infraestrutura experimental e de engenharia, não apenas automatização de comandos. Devem ser reproduzíveis, diagnósticos, baratos quando possível e separados por responsabilidade.

## Referências de investigação

### An Empirical Study of the Evolution of GitHub Actions Workflows
Rostami Mazrae, Decan, Mens, Wessel — *Journal of Systems and Software*, 236 (2026), 112824.

- DOI: https://doi.org/10.1016/j.jss.2026.112824
- arXiv: https://arxiv.org/abs/2602.14572
- Preprint: https://orbi.umons.ac.be/handle/20.500.12907/55626

O estudo analisou mais de 267 mil históricos de alteração de workflows em 49 mil repositórios e 3,4 milhões de versões. A evidência mostra que as alterações são frequentemente pequenas e concentram-se na configuração/especificação dos jobs. Para o RedWar isto reforça a regra de fazer mudanças de workflow pequenas, isoladas e semanticamente claras.

### Why Do GitHub Actions Workflows Fail? An Empirical Study
Zheng et al. — *ACM Transactions on Software Engineering and Methodology*, 35(5), 2026, Article 139.

- DOI: https://doi.org/10.1145/3749371

O estudo analisou 375 execuções falhadas de GitHub Actions em 260 projetos e identificou 16 categorias de causa. Para o RedWar, uma falha de workflow deve preservar evidência suficiente para distinguir configuração, ambiente, dependências, build, teste, timeout, artefactos e lógica do projeto.

### GitHub Actions: The Impact on the Pull Request Process
*Empirical Software Engineering* (2023).

- DOI: https://doi.org/10.1007/s10664-023-10369-w

O estudo encontrou efeitos mensuráveis da adoção de GitHub Actions no processo de PR, incluindo alterações na taxa de rejeição, comunicação e tempo de aceitação. Isto reforça que CI é parte do processo de desenvolvimento e deve ser tratado como produto de engenharia, não como detalhe periférico.

### Como estes trabalhos influenciam o RedWar

1. **Workflows pequenos e ortogonais.** Um workflow deve ter uma responsabilidade principal: testes, quality gate, Arena, tooling, NNUE, etc.
2. **Gates explícitos.** Uma mudança de documentação/tooling não deve pagar o custo de uma Arena de promoção, e uma mudança de AI não deve escapar aos gates de força.
3. **Execução manual como ferramenta experimental.** Workflows experimentais caros, como a Arena, devem poder ser executados manualmente sem criar commits artificiais só para satisfazer um filtro de paths.
4. **Diagnóstico preservável.** Logs, traces e artefactos devem permitir reproduzir a razão da falha sem depender de uma segunda execução.
5. **Falhas classificáveis.** Erros de workflow devem ser distinguíveis de regressões do produto; não esconder falhas através de `|| true`, `continue-on-error` ou conversões silenciosas de resultado.
6. **Mudanças pequenas.** Alterações de workflow devem evitar refactors funcionais misturados com alterações de CI.
7. **Custos controlados.** Pushes comuns devem usar o gate mínimo necessário; experiências caras como Arena devem ter triggers explícitos e execução concorrente controlada.

## Topologia atual de workflows

A arquitetura atual usa uma responsabilidade principal por workflow:

```text
GATES
├── test_suite.yml
└── ai_quality_gate.yml

SECURITY
└── codeql.yml

DIAGNOSTICS
└── arena_diagnostics.yml

EXPERIMENTS
└── arena_experiments.yml

NIGHTLY
├── nnue_nightly.yml
└── auto_balancer.yml

TEMPORARY RESEARCH
└── strength_calibration.yml
```

`ai_quality_gate.yml` é a **única autoridade de promoção strength-sensitive em PRs**. O GitHub Ruleset `Protect main` permanece a autoridade estrutural sobre a proteção de `main`.

`arena_diagnostics.yml` é observacional e não decide promoção. `arena_experiments.yml` é manual e não-authoritativo; serve para investigação, datasets, holdout e experiências controladas. `strength_calibration.yml` permanece separado enquanto o protocolo de calibração ainda não tiver closeout metodológico.

## Arena experimental

O workflow `arena_experiments.yml` substitui as antigas superfícies `ai_arena.yml` e `ai_strength_experiment.yml`.

A superfície experimental é `workflow_dispatch`-only e tem modos explícitos, incluindo:

- **experiment:** comparação A/B com baseline e challenger escolhidos por ref/SHA explícito, seeds declaradas, validação do dataset, contexto de população, provenance e artefactos;
- **protected_holdout:** validação do holdout protegido a partir do `main` canónico, com `candidate_sha` explícito.

Os resultados experimentais carregam explicitamente `promotion_authority=false`. O workflow experimental **não é required check** e não pode substituir `ai_quality_gate.yml`.

A Arena experimental não é disparada automaticamente em pushes normais de branches AI. Isto evita execuções longas e caras sem uma hipótese experimental explícita.

## Diagnóstico Arena

O workflow `arena_diagnostics.yml` existe para observabilidade da infraestrutura Arena, incluindo diagnósticos de lifecycle e TT. É evidence-only.

Uma descoberta experimental de lifecycle não altera por si só a autoridade de promoção. A sequência correta é:

```text
observação
 ↓
evidência
 ↓
interpretação metodológica
 ↓
decisão de protocolo, se necessária
```

## Calibração

`strength_calibration.yml` é temporário e não-authoritativo. O protocolo usa A/A e valida explicitamente que challenger e baseline correspondem à mesma revisão congelada, que o dataset é válido e que a provenance declara `promotion_authority=false`.

O workflow só deve ser removido depois de:

```text
execução
→ análise
→ decisão metodológica
→ closeout documentado
```

## Política futura

Antes de adicionar complexidade a um workflow, perguntar:

```text
esta mudança melhora cobertura, isolamento, reprodutibilidade,
diagnóstico ou custo?
```

Se a resposta for não, a alteração provavelmente pertence ao código de produto ou deve ser eliminada.

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
3. **Execução manual como ferramenta experimental.** Workflows como a Arena devem poder ser executados manualmente sem criar commits artificiais só para satisfazer um filtro de paths.
4. **Diagnóstico preservável.** Logs, traces e artefactos devem permitir reproduzir a razão da falha sem depender de uma segunda execução.
5. **Falhas classificáveis.** Erros de workflow devem ser distinguíveis de regressões do produto; não esconder falhas através de `|| true`, `continue-on-error` ou conversões silenciosas de resultado.
6. **Mudanças pequenas.** Alterações de workflow devem evitar refactors funcionais misturados com alterações de CI.
7. **Custos controlados.** Pushes comuns devem usar o gate mínimo necessário; experiências caras como Arena devem ter triggers explícitos e execução concorrente controlada.

## Aplicação atual à Arena

O `ai_arena.yml` mantém duas vias:

- **Automática:** alterações relevantes em `ai/`, `tools/nnue/` ou `arena_tournament.py` podem disparar a Arena de promoção.
- **Manual:** `workflow_dispatch.force_arena=true` permite executar a Arena mesmo sem alteração de AI.

A via manual é importante para experiências sobre o estado atual do jogo, como observar se o aumento do guardrail para 10.000 plies produz partidas sem vencedor, sem introduzir alterações artificiais em `ai/`.

A execução manual não deve ser tratada como evidência de promoção de AI. O objetivo é produzir dados experimentais reproduzíveis.

## Política futura

Antes de adicionar complexidade a um workflow, perguntar:

```text
esta mudança melhora cobertura, isolamento, reprodutibilidade,
diagnóstico ou custo?
```

Se a resposta for não, a alteração provavelmente pertence ao código de produto ou deve ser eliminada.

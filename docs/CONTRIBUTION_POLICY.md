# RedWar — Política de Contribuições

## Princípio

O RedWar é um repositório público, mas a política de contribuição depende da área.

### Fluxo normal

```text
feature branch
    → pull request
    → required CI
    → review
    → merge
```

`main` é protegida. Alterações normais não devem ser feitas diretamente em `main`.

Ser um repositório público não concede a visitantes permissões de escrita. O acesso de escrita continua limitado aos utilizadores explicitamente autorizados pelo proprietário.

## Ares / IA

`ai/` é o subsistema Ares e a única área destinada a contribuições automatizadas/competitivas.

O agente pode escrever no repositório quando explicitamente autorizado pelo proprietário, mas:

```text
write access ≠ merge authority
```

Ares deve continuar a usar branches e PRs. Uma alteração de Ares só é considerada melhoria quando a evidência correspondente mostra melhoria relevante; testes e elegância de código não substituem benchmark/Arena quando a alegação é de força/desempenho.

Não reduzir thresholds, métricas, seeds, node budgets, testes ou gates para obter uma conclusão favorável.

### Jogo/produto

O restante projeto continua sob revisão manual do autor.

Isto inclui:

- `engine/`;
- `ui/`;
- `online/`;
- `main.py`;
- regras e heróis;
- multiplayer;
- infraestrutura;
- balanceamento;
- documentação e direção do produto.

Contribuições podem ser propostas por PR, mas a decisão de integrar alterações desta área permanece com o proprietário.

## Proteção de `main`

O ruleset GitHub `Protect main` deve manter, no mínimo:

- enforcement `Active`;
- pull request obrigatória;
- pelo menos 1 approval;
- dismiss de approvals stale quando são feitos novos pushes;
- resolução de conversations obrigatória;
- status checks obrigatórios `tests` e `ai-quality-gate`;
- branch atualizada antes do merge;
- force-push bloqueado;
- eliminação do branch bloqueada.

As workflows experimentais de Arena/Strength não são, por si só, required checks normais de PR.

## Evidência e ciência

Separar sempre:

```text
implementação
→ validação
→ evidência experimental
→ decisão de promoção
```

Uma implementação existente não prova a propriedade pretendida. Um teste verde não prova que Ares ficou mais forte. Um resultado neutro ou inconclusivo é um resultado válido.

Experimentos devem preservar provenance, seeds, datasets, manifests, versões e resultados brutos. Não alterar evidência depois de observada para produzir uma conclusão favorável.

## Continuidade do conhecimento

Uma contribuição não deve introduzir conhecimento essencial que só exista na conversa entre o autor e a pessoa/IA que a produziu.

Decisões relevantes devem seguir `docs/DECISION_AND_KNOWLEDGE_PROTOCOL.md`:

```text
problema / descoberta
 → evidência
 → opções
 → decisão
 → implementação
 → teste
 → resultado
```

## Licenças e terceiros

A política de licença e atribuição está em `docs/LEGAL_AND_LICENSES.md`.

- código geral próprio: MIT;
- código próprio Ares em `ai/`: GPL-3.0-or-later;
- terceiros mantêm as suas próprias licenças;
- não adicionar conteúdo externo sem verificar licença e atribuição.

## Política de IA assistida

Uso de IA para ajudar a escrever código é permitido.

A responsabilidade pela alteração continua a ser humana. Uma contribuição assistida por IA deve:

- compilar;
- ter testes adequados;
- ser compreensível para revisão;
- não introduzir conteúdo de terceiros incompatível com a licença;
- não introduzir secrets;
- preservar a razão das decisões relevantes no repositório.

## Segurança de um repositório público

Assumir que todo o conteúdo comprometido é publicamente visível. Nunca adicionar:

- API keys;
- access tokens;
- passwords;
- private keys;
- credenciais;
- secret configuration.

Nunca fazer force-push de `main` nem contornar a proteção de branches.

## Futuro split de repositórios

O projeto pode vir a separar:

```text
RedWar        → jogo/produto
RedWar-Ares   → engine de IA
```

Não é necessário fazer essa separação imediatamente.

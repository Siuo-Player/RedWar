# Contribuir para RedWar

## Papel deste documento

Este documento descreve **como executar um bloco de desenvolvimento** e preparar uma contribuição. As regras de aceitação, revisão e autoridade de merge pertencem a [`CONTRIBUTION_POLICY.md`](CONTRIBUTION_POLICY.md).

## Modelo de desenvolvimento

O projeto usa branches curtas e blocos de trabalho coerentes. `main` deve permanecer num estado utilizável e documentado.

O princípio é semelhante ao usado em projetos de engines maiores: mudar uma hipótese por vez, medir, corrigir regressões e só promover alterações com evidência suficiente.

## Ciclo de uma branch

1. Ao criar/abrir uma branch, atualizar o `docs/ROADMAP.md` com o estado confirmado, objetivo, passos seguintes e critérios de aceitação.
2. Desenvolver o bloco inteiro na própria branch.
3. Qualquer erro encontrado durante o bloco é corrigido **na mesma branch**, antes do PR.
4. Atualizar documentação e testes à medida que o comportamento real muda.
5. Quando o bloco estiver completo e validado, abrir/atualizar o PR.
6. Depois do merge, fechar/apagar a branch remota e atualizar novamente o roadmap para o próximo ciclo.

Um bug descoberto apenas depois de sair da branch original é corrigido na branch onde foi encontrado, com a documentação correspondente atualizada.

Não abrir PRs intermédios apenas para guardar código parcialmente desenvolvido, salvo quando o PR tem deliberadamente esse papel e isso está documentado.

## Ares / `ai/`

Uma alteração da Ares não é aceite apenas porque compila.

Deve procurar pelo menos uma destas metas:

- maior força;
- melhor desempenho sem perda de força;
- correção necessária;
- avaliação mais forte;
- menor custo de memória sem perda significativa.

Para alterações funcionais, guardar `bestmove`, posições/referências, orçamento de nodes/tempo e resultados comparáveis.

O objetivo final é **Elo por CPU-segundo**, não NPS isolado.

## Antes do PR

Executar os testes relevantes do bloco e, antes de o fechar, a suite global disponível:

```bash
pytest tests/
```

Para C++:

```bash
python tools/scripts/build_cpp_engine.py
python tools/scripts/build_cpp_engine.py --smoke
```

Para alterações que possam afetar Arena/NNUE, executar também o benchmark/Arena correspondente.

## Tools

`tools/` é tooling de desenvolvimento, experimentação e análise. Não deve duplicar as regras do `engine/`.

Preferir ferramentas pequenas e composicionais:

```text
tools/analytics  -> experiências, Arena, análise e treino
tools/balance    -> balanceamento
tools/nnue       -> dataset/features/train/export
tools/scripts   -> build e auditoria
```

Scripts obsoletos devem ser removidos, não escondidos atrás de caminhos alternativos indefinidos.

## Regras de estrutura

- `engine/` é a fonte das regras durante a migração.
- `ai/` é a fonte da pesquisa/avaliação.
- `tests/` verifica invariantes.
- `tools/` executa processos externos ao jogo.
- `data/` guarda dados/datasets/artifacts apropriados.
- `docs/` descreve o estado real e decisões.

Não criar dependências circulares entre UI, regras e IA.

## Alterações de regras

Antes de adicionar lógica específica de herói:

1. verificar `engine/heroes_config.json`;
2. verificar `engine/HEROES_SCHEMA.md`;
3. verificar se a habilidade já é expressável pelos dados existentes;
4. só depois adicionar lógica nova.

Mudanças de regras devem ter regressões quando possível.

## Testes prioritários

- ações legais/ilegais;
- stun e segundo stun;
- timers e efeitos;
- vitória/ausência de movimentos;
- `make → unmake`;
- hash;
- parsing RWEN;
- limites/extremos em fronteiras numéricas;
- paridade Python/C++;
- paridade Python/C++ das features NNUE.

## Commits

Preferir commits semanticamente focados:

```text
fix: correct stun timer expiration
refactor: isolate move ordering
perf: reduce allocations in move generation
test: add fire effect regression
docs: update AI workflow
```

## Documentação

Sempre que o código mudar uma arquitetura, fluxo, regra ou interface importante, atualizar o documento canónico correspondente na mesma branch.

Antes de criar um novo documento, consultar [`docs/00_INDEX.md`](00_INDEX.md) e verificar se já existe uma fonte de verdade para o assunto. Não criar documentos paralelos só para contornar um documento longo.

Nunca documentar uma funcionalidade futura como se já existisse.

## Inspiração externa

A organização e a metodologia devem ser comparadas regularmente com projetos maduros de código aberto. Stockfish/Fishtest e Fairy-Stockfish são referências especialmente úteis para separação de engine, testes, tooling, NNUE e medição estatística.

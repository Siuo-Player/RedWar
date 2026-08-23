# RedWar — Development Workflow

## Branches

Cada branch deve representar um **bloco de desenvolvimento completo**.

No início:

```text
main
 ↓
branch nova
 ↓
atualizar ROADMAP
 ↓
desenvolver
```

O roadmap é obrigatório porque a intenção da branch deve ser recuperável sem depender do histórico da conversa.

## Durante o bloco

Um erro encontrado enquanto o bloco está ativo é corrigido na própria branch.

A documentação acompanha a implementação:

```text
código muda
  ↓
teste muda
  ↓
documentação muda
```

Não acumular bugs conhecidos para “depois do PR”.

## PR

O PR é a fronteira de revisão do bloco terminado. Deve conter:

- objetivo;
- resumo das alterações;
- testes executados;
- benchmarks/Arena quando aplicável;
- limitações conhecidas;
- próximo passo do roadmap.

Uma branch pode receber vários commits antes do PR. O número de commits não é o objetivo; a unidade importante é a hipótese validada.

## Depois do PR

Depois de merge:

1. atualizar `ROADMAP.md`;
2. fechar/apagar a branch remota;
3. criar a próxima branch a partir da `main` atual;
4. rever documentação antes de continuar.

## Bugs descobertos depois

Se um problema só for descoberto noutra branch, é corrigido onde foi descoberto. O novo PR deve referenciar o problema e atualizar a documentação/regressão respetiva.

Não reabrir artificialmente branches antigas só para preservar uma sequência histórica.

## Alterações experimentais

Experimentos de Ares, NNUE, Arena e balanceamento devem ser reproduzíveis:

- seed conhecida;
- inputs versionados;
- configuração explícita;
- orçamento explícito;
- saída guardada quando o resultado for relevante.

## Critério de conclusão

Um bloco termina quando a alteração pretendida funciona **e** as regressões relevantes estão cobertas. Código “quase pronto” permanece desenvolvimento e não deve ser tratado como concluído pela documentação.

## Modelo de projetos grandes

A disciplina aproxima-se de práticas visíveis em Stockfish/Fishtest/Fairy-Stockfish: engine separada dos testes, experimentos separados da execução normal, CI especializada e decisões baseadas em medições reproduzíveis.

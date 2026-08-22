# RedWar — Sistema de Heróis

## Objetivo

O sistema de heróis deve permitir adicionar conteúdo novo sem obrigar o programador a alterar dezenas de ficheiros.

A fonte de dados principal é:

`engine/heroes_config.json`

O formato técnico está em:

`engine/HEROES_SCHEMA.md`

## Dados de um herói

Dependendo do herói, a configuração pode definir:

- custo;
- acronym;
- draftability;
- lifespan;
- cooldowns;
- movimento;
- ataque;
- passivas;
- outros parâmetros específicos.

## Data-driven design

O objetivo é que comportamentos comuns sejam descritos por configuração.

Exemplos de movimentos:

- `none`;
- `orthogonal`;
- `diagonal`;
- `adjacent`;
- `knight`;
- `ray`;
- `forward_cone`;
- padrões por deltas.

Ataques podem usar tipos semelhantes.

## Onde o modelo ainda falha

Passivas verdadeiramente únicas são difíceis de expressar numa DSL genérica sem criar um sistema de programação dentro do JSON.

Por isso, atualmente existe uma abordagem híbrida:

```text
configuração declarativa
        +
implementação especializada quando necessário
```

Isto é aceite temporariamente.

A meta é diminuir o código especial, não fingir que todas as mecânicas podem ser expressas por JSON.

## Princípio para novos heróis

Um herói novo deve primeiro tentar ser implementado através da configuração existente.

Só deve exigir código novo quando introduzir uma mecânica genuinamente nova.

Se dez heróis novos necessitarem todos do mesmo novo bloco de código, a abstração deve ser melhorada em vez de criar dez exceções.

## Passivas

Passivas podem representar coisas como:

- spawn após morte;
- dano/efeito em área;
- alterações ao atacar;
- alterações ao ser atacado;
- auras;
- alterações no terreno.

As passivas podem ser únicas por herói.

Não é necessário que todos os heróis tenham exatamente o mesmo conjunto de sistemas.

## Efeitos de área

Um herói pode alterar o que é permitido numa região sem consumir uma ação a cada turno.

O silêncio do Inquisitor é um exemplo importante: a aura deve ser pensada como parte do estado/ambiente, não como uma sequência de ataques.

## Custos

O custo não representa “stats”.

É uma medida de valor estratégico usada pelo draft.

O objetivo é permitir uma distribuição ampla, aproximadamente desde unidades muito baratas até unidades extremamente caras, sem que preço seja simplesmente uma recompensa por ter mais HP/dano.

## Invocações

Unidades invocadas podem ser configuradas como não draftáveis.

Normalmente possuem uma duração de existência ou outra limitação.

## Critérios de qualidade

Ao adicionar um herói, verificar:

- todas as ações legais funcionam;
- ações impossíveis são recusadas;
- efeitos/timers são reversíveis;
- hash representa o novo estado;
- Python e C++ mantêm o mesmo comportamento durante a migração;
- o custo é coerente com o poder demonstrado;
- existe teste de regressão para qualquer mecânica nova.

## Regra importante

`heroes_config.json` deve ser a fonte de verdade dos **dados**, mas não deve ser usado para esconder lógica que só existe no código.

Quando uma regra essencial só funciona porque existe um `if hero == ...` longe da configuração, isso deve ser documentado ou refatorado posteriormente.

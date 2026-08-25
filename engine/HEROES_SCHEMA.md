# HEROES_SCHEMA

Este documento descreve o formato de `engine/heroes_config.json` usado para definir dados dos heróis e alimentar o compilador de comportamentos.

> **Importante:** o schema é a especificação do formato dos dados, não garante que todas as habilidades descritas estejam completamente data-driven em Python e C++. Quando uma mecânica ainda precisa de implementação especializada, isso deve ser considerado durante a migração.

## Chave de topo

Cada nome de herói corresponde a um objeto:

```json
{
  "Bone": {
    "cost": 8,
    "acronym": "Bo",
    "behavior": {}
  }
}
```

## Metadados comuns

- `cost` — inteiro não negativo usado no draft.
- `acronym` — string curta usada na representação visual.
- `descricao` — descrição humana.
- `passiva` — texto humano da passiva.
- `draftable` — indica se o herói aparece no draft.
- `lifespan` — duração de existência de uma unidade temporária, quando aplicável.
- `spawn_cooldown` — cooldown de sistemas de invocação, quando aplicável.
- `jump_max` — alcance máximo de habilidades de salto que o implementem.
- `aura_radius` — raio de uma aura que use esse parâmetro.
- `spells` — nomes das habilidades ativas do herói. Uma habilidade escolhida pelo jogador não deve ser descrita apenas por `passiva`.

## `behavior`

`behavior` contém a descrição declarativa de movimento, ataque básico, spells geométricas e passivas.

A ausência de uma secção não deve inventar um comportamento.

## Movimento

`behavior.movement` pode usar:

- `orthogonal`
- `diagonal`
- `adjacent`
- `knight`
- `ray`
- `none`
- `forward_cone`
- padrões baseados em `deltas`

Campos frequentes:

- `type`
- `max_steps`
- `min_steps`
- `deltas`
- `dirs`
- `forward_dir_by_team`
- `ghost_move`

## Ataque básico

`behavior.attack` representa a geometria de um ataque normal quando a ação continua a ser um `ATTACK`.

Ataques básicos devem ser simples e intrínsecos. Normalmente atingem uma casa e não introduzem uma resolução especial.

Tipos suportados incluem:

- `orthogonal`
- `diagonal`
- `adjacent`
- `knight`
- `ray`
- `pattern`
- `forward_cone`
- `none`
- padrões com `deltas`

Quando uma geometria de ataque é especial e deve ser executada como spell, `behavior.attack` pode manter a geometria mas declarar:

```json
"attack_action": "spell",
"spell_name": "aimed_shot"
```

Nesse caso a ação produzida pelo backend é `SPELL aimed_shot`, não `ATTACK`.

Isto evita duplicar toda a DSL apenas para mudar a natureza da ação.

## Spells

`spells` enumera as ações ativas escolhidas pelo jogador.

Exemplos:

- `ignite`;
- `purify`;
- `swap`;
- `barricade`;
- `jump`;
- `spawn_ghoul`;
- `nevada`;
- ataques especiais classificados como spell, como tiros de longo alcance ou padrões especiais.

Uma spell pode causar stun ou morte. O efeito final não muda a classificação: se o jogador escolhe a habilidade e ela possui resolução especial, é uma spell.

## Passivas

`behavior.passives` descreve efeitos automáticos/event-driven quando o comportamento já está suportado.

Exemplos de triggers:

- `on_kill`
- `on_attack`
- `on_attacked`
- `on_turn_start`
- `on_turn_end`
- `on_death`
- `aura_passive`

Exemplos de efeitos:

- `spawn_unit`
- `aoe_damage`
- `redirect_damage`
- `disable_spells`

Uma passiva não deve ser usada para esconder uma spell ativa. “Lança stun”, “mata”, “purifica”, “troca”, “salta” e “ergue barricada” são descrições de ações quando dependem de uma escolha do jogador.

## FrostMage

O FrostMage usa a spell `nevada`. A implementação atual da habilidade deve manter o centro selecionável, a área de stun existente e acrescentar gelo no centro da resolução.

O stun produzido pela Nevada é consequência da spell e não uma ação `STUN` independente.

## Dados versus lógica

A intenção é que `heroes_config.json` seja a fonte de verdade dos **dados** do herói.

Não é objetivo forçar toda a lógica única para dentro de JSON.

Uma boa regra é:

```text
geometria / parâmetros comuns → JSON
mecânica completamente única → código especializado
```

Quando vários heróis precisarem do mesmo código especializado, deve-se reconsiderar a abstração.

## Consistência Python/C++

Durante a migração, qualquer campo que altere movimentos, ações ou resultado de uma posição deve ser refletido nos dois lados.

Os testes devem verificar:

- movimentos legais;
- ataques básicos;
- spells;
- classificação da ação (`ATTACK` vs `SPELL`);
- passivas suportadas;
- estado após ação;
- timers;
- efeitos;
- hash.

## Validação

Uma configuração inválida deve falhar cedo. Não criar silenciosamente um herói incompleto, ignorar erros de parsing ou atribuir um comportamento genérico sem que isso esteja explicitamente definido.

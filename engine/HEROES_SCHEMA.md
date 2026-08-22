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

## `behavior`

`behavior` contém a descrição declarativa de movimento, ataque e passivas.

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

`forward_dir_by_team` permite representar movimentos direcionais de forma independente da cor.

`ghost_move` permite que uma regra de movimento atravesse peças onde a mecânica explicitamente o permite.

## Ataques

`behavior.attack` utiliza essencialmente os mesmos conceitos de geometria.

Tipos suportados pelo compilador atual incluem:

- `orthogonal`
- `diagonal`
- `adjacent`
- `knight`
- `ray`
- `pattern`
- `forward_cone`
- `none`
- padrões com `deltas`

Campos:

- `type`
- `max_steps`
- `min_steps`
- `deltas`
- `dirs`
- `forward_dir_by_team`

A geometria define **onde** um ataque pode alcançar. A regra de resultado — stun ou morte, e as interações de passivas — pertence à lógica do jogo.

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

A lista não é fechada: novos mecanismos podem exigir novos triggers/effects.

## Spells

Alguns heróis possuem spells ativadas pelo jogador.

A implementação atual ainda mantém parte da execução destas habilidades no estado do jogo.

Exemplos de conceitos existentes:

- `ignite`
- `purify`
- `swap`
- `barricade`
- `jump`

## Unidades invocadas

Unidades como `Bone`, `Ghoul` ou outras peças não draftáveis podem ser criadas por heróis.

É possível configurar `lifespan` para limitar a existência.

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
- ataques;
- passivas suportadas;
- estado após ação;
- timers;
- efeitos;
- hash.

## Exemplo

```json
"Inquisitor": {
  "cost": 127,
  "acronym": "In",
  "aura_radius": 2,
  "behavior": {
    "movement": {
      "type": "adjacent",
      "max_steps": 1
    },
    "attack": {
      "type": "adjacent",
      "max_steps": 1
    },
    "passives": [
      {
        "trigger": "aura_passive",
        "effect": "disable_spells",
        "params": {
          "radius": 2,
          "target_team": "enemy"
        }
      }
    ]
  }
}
```

## Validação

Uma configuração inválida deve falhar cedo. Não criar silenciosamente um herói incompleto, ignorar erros de parsing ou atribuir um comportamento genérico sem que isso esteja explicitamente definido.

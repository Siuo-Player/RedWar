# RedWar — Sistema de Heróis

## Objetivo

O sistema de heróis deve permitir adicionar conteúdo novo sem obrigar o programador a alterar dezenas de ficheiros.

A fonte de dados principal é:

`engine/heroes_config.json`

O formato técnico está em:

`engine/HEROES_SCHEMA.md`

## Taxonomia de ações

As capacidades de um herói devem ser classificadas pela forma como o jogador as utiliza, e não simplesmente pelo efeito que produzem.

### Ataque básico

`attack` representa o ataque normal/intrínseco do herói.

Por regra, deve ser uma ação simples e direta, normalmente contra uma peça a **uma casa** de distância. Padrões de uma casa como ortogonal, diagonal, adjacente ou cone frontal de uma única casa continuam a poder representar ataques básicos quando não introduzem uma mecânica adicional.

Um ataque com alcance especial, padrão complexo, teleporte/salto, AoE própria, stun especial, terreno, ou outra resolução diferente do combate normal deve ser modelado como `SPELL` ou outra mecânica especializada, e não como um `ATTACK` básico.

### Spell

Uma `SPELL` é uma ação ativa escolhida pelo jogador que faz algo além de um ataque básico: dano/remoção especial, stun em área, criação ou alteração de terreno, purificação, troca, salto, invocação, ataque de longo alcance especial, padrões complexos, etc.

Uma spell pode causar exatamente o mesmo resultado material de um ataque normal; o que a distingue é a natureza especial da ação.

### Passiva

Uma passiva é automática, reativa, contínua ou ligada a uma condição do jogo. Não deve ser apenas uma forma alternativa de escrever uma ação que o jogador escolhe e executa.

Exemplos corretos:

- spawn após morte;
- AoE automática ao atacar;
- reflexão/redirect ao ser atacado;
- atravessar peças;
- aura de silêncio;
- alterações permanentes ou condicionais ao comportamento.

Descrições como “Purifica aliados”, “Troca de lugar”, “Ergue barricada”, “Lança stun” ou “Salta” não devem aparecer como passivas quando são ações escolhidas pelo jogador: são spells.

Um herói pode ter **ataque básico + passiva**, **ataque básico + spells + passiva**, ou **spells sem ataque básico**. Um herói pode também ser essencialmente definido por uma única passiva muito poderosa, desde que essa passiva seja realmente automática e não uma ação disfarçada.

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

Ataques básicos podem usar tipos semelhantes quando continuam a obedecer à semântica de ataque normal. Ações especiais devem declarar explicitamente que são spells.

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

## Passivas

Passivas podem representar coisas como:

- spawn após morte;
- dano/efeito em área automático;
- alterações ao atacar;
- alterações ao ser atacado;
- auras;
- alterações no terreno;
- modificações permanentes/condicionais do comportamento.

Uma passiva não deve existir apenas porque o efeito final da habilidade é stun ou morte. Se existe uma escolha ativa de alvo/centro/destino para produzir esse efeito, a capacidade é uma spell.

## Silêncio

O silêncio do Inquisitor é uma restrição ao **caster**: impede o herói dentro da aura de lançar spells.

Não é uma barreira anti-mágica no tabuleiro. Uma spell lançada fora da aura pode atingir uma casa dentro dela, e efeitos já existentes, como fogo, não são removidos simplesmente porque uma unidade está silenciosa.

Uma futura mecânica de anti-magia/barreira pode ser diferente e bloquear a passagem ou resolução de spells numa área, mas isso deve ser modelado como outro efeito.

## FrostMage

O FrostMage não deve possuir uma ação `STUN` especial separada do sistema de spells.

A habilidade `Nevada` é uma **SPELL ativa**:

- o jogador escolhe o centro;
- a área de stun é aplicada pela mecânica da spell;
- o centro recebe gelo;
- o gelo permanece segundo as regras de efeitos de terreno;
- estar dentro de Silêncio impede o FrostMage de lançar `Nevada`.

O stun produzido por `Nevada` não transforma a própria habilidade numa ação `STUN`: a ação escolhida pelo jogador continua a ser a spell.

## Critérios de qualidade

Ao adicionar um herói, verificar:

- a ação principal está corretamente classificada;
- passivas são realmente automáticas/reativas;
- ações especiais são spells ou outras ações especializadas;
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

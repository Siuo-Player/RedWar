# RedWar — Game Design

## Visão

RedWar pretende ser um **RPG de tabuleiro tático sem atributos tradicionais**.

A profundidade vem da combinação de peças assimétricas, informação escondida no draft, posicionamento, controlo de terreno, stun, morte e passivas.

## O que torna RedWar diferente

### 1. Sem HP

Não há barras de vida, defesa, ataque ou estatísticas que precisem de ser comparadas durante o combate.

A complexidade nasce do estado:

```text
normal → stun → normal
normal → stun → morte
```

### 2. Heróis assimétricos

Os heróis devem ser muito diferentes.

A intenção não é criar vinte unidades com pequenos modificadores, mas permitir que cada uma obrigue o jogador e a IA a pensar de maneira diferente.

### 3. Economia como balanceamento

Cada herói tem um custo.

O custo é uma abstração do valor da peça no jogo. O Auto-Pricer e os jogos de IA podem ajudar a descobrir custos apropriados, mas não substituem análise do design.

### 4. Informação escondida

O exército e posicionamento inicial são definidos antes da partida e não são revelados ao adversário até o jogo começar.

Isto permite que o draft faça parte da estratégia e impede que o jogador construa imediatamente uma resposta perfeita ao adversário.

## Filosofia de equilíbrio

A prioridade não é tornar todas as peças igualmente fortes.

É aceitável existir uma grande variedade de custos e poder:

```text
5 → 37 → 63 → 72 → 99 → 178 → ...
```

O importante é que o custo corresponda aproximadamente ao valor estratégico.

Custos extremamente baixos ou altos podem ser válidos, mas devem ser analisados. O objetivo é evitar que o orçamento possa ser explorado por simplesmente escolher uma única peça claramente superior.

## IA como instrumento de design

A IA tem duas funções:

1. adversário;
2. instrumento de análise do próprio jogo.

Uma IA forte ajuda a descobrir:

- peças demasiado fortes;
- peças que estão a ser subvalorizadas;
- posições aparentemente boas mas taticamente perdedoras;
- padrões de repetição/stalling;
- vantagens de primeira jogada/cor;
- problemas nas condições de vitória.

A IA não define sozinha o design. Ela fornece evidência.

## Filosofia de evolução

O modo normal não deve ser alterado apenas porque uma ideia experimental parece interessante.

O projeto deve preferir:

```text
modo normal estável
        +
modos experimentais separados
```

em vez de substituir continuamente a regra principal.

Isto é especialmente importante para tabuleiros diferentes, como 10×10.

## 10×10

10×10 é uma hipótese importante porque o número de heróis e possibilidades pode começar a pressionar o 8×8.

No entanto, aumentar o tabuleiro aumenta também o espaço de pesquisa da IA.

Por isso a ordem pretendida é:

1. melhorar Ares;
2. tornar Ares rápida;
3. testar 10×10;
4. comparar a qualidade do jogo;
5. decidir se 10×10 substitui o normal ou se fica como modo separado.

## Passivas

As passivas devem permitir identidade forte entre heróis.

Não há problema em existir lógica especializada quando a mecânica é verdadeiramente única. O problema é espalhar pequenas exceções pelo projeto para representar variações que poderiam ser expressas na configuração.

O objetivo é um equilíbrio entre:

- configuração simples para regras comuns;
- código especializado para comportamentos realmente especiais.

## Regras que devem permanecer fortes

Mesmo com evolução do jogo, algumas ideias são consideradas fundamentais:

- não usar HP tradicional;
- stun + segundo stun como mecanismo de eliminação;
- uma ação normal por turno;
- heróis com identidade própria;
- economia de pontos;
- condições de vitória que evitem empates;
- capacidade de criar modos variantes sem destruir o modo normal.


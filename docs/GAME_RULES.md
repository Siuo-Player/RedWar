# RedWar — Regras do Jogo

> Documento destinado principalmente a jogadores. Quando uma regra estiver marcada como **a definir**, ela é intencionalmente aberta e não deve ser tratada como especificação final.

## 1. Formato normal

- Tabuleiro: **8×8**.
- Orçamento de draft: **200 pontos por cor**.
- Draft e posicionamento acontecem antes da partida.
- O adversário não conhece a tua composição/posição inicial antes do início da partida.
- Cada jogador executa normalmente **uma ação por turno**.

Tamanhos e orçamentos diferentes poderão existir como modos futuros.

## 2. Heróis

Os heróis diferenciam-se por:

- movimento;
- ataques;
- passivas;
- spells;
- invocações;
- efeitos de terreno.

Não existem HP nem atributos numéricos tradicionais.

## 3. Ações

Uma ação normal consiste em selecionar um herói e uma casa de destino/alvo para executar uma ação legal.

Exemplos:

- mover;
- atacar por stun;
- atacar por morte;
- usar uma spell;
- executar outra habilidade ativa.

Uma passiva verdadeira não precisa necessariamente de consumir um turno.

## 4. Combate

Existem dois resultados fundamentais de ataque:

### Stun

O alvo fica atordoado durante um número definido de turnos.

Enquanto estiver atordoado:

- não pode executar as ações normais que o estado de stun bloquear;
- continua presente no tabuleiro;
- pode ser atacado novamente.

### Morte

Uma morte remove a peça do tabuleiro.

### Segundo stun

Aplicar um novo stun a uma peça que ainda está atordoada causa **morte**.

Isto é uma regra essencial do jogo.

O valor exato do timer de stun continua a ser calibrado, mas deve sempre existir uma janela que permita explorar dois stuns como forma de eliminar uma peça.

## 5. Efeitos das casas

Uma casa pode conter uma peça e efeitos.

O sistema foi pensado para suportar vários efeitos simultâneos.

### Fogo

O fogo:

- é criado por habilidades como `ignite`;
- permanece por tempo limitado;
- aplica stun quando uma peça entra/é afetada;
- pode causar morte quando aplicado a uma peça que já esteja atordoada.

### Gelo

O gelo deve comportar-se como uma barreira/estado de congelamento:

- pode impedir atravessar diretamente a casa;
- pode bloquear certos movimentos/ataques;
- uma habilidade especial pode explicitamente atravessá-lo;
- pode deixar um herói congelado/atordoado conforme a regra da habilidade.

A duração e todas as interações do gelo ainda estão em calibração.

### Silêncio

Silêncio é principalmente um efeito de área criado por uma passiva.

Uma peça dentro da área de silêncio pode ficar impedida de executar determinadas habilidades, sem que o jogador que mantém a aura precise de gastar uma ação a cada turno.

## 6. Spells atualmente conhecidas

As habilidades existentes incluem conceitos como:

- `ignite`;
- `purify`;
- `swap`;
- `barricade`;
- `jump`;
- `spawn` através de heróis apropriados.

As condições concretas de utilização são definidas pelo herói e pela posição.

Não existe atualmente um sistema geral de “mana” ou custo de spell.

## 7. Invocações

Heróis podem criar outras peças.

Uma peça invocada pode:

- ter lifespan;
- ter cooldown associado ao invocador;
- não ser draftável;
- ocupar normalmente uma casa do tabuleiro;
- participar do jogo enquanto existir.

Peças temporárias não reiniciam o contador de turnos sem captura quando morrem.

## 8. Fim da partida

A partida termina quando um jogador:

- fica sem peças;
- fica sem qualquer ação legal;
- desiste.

Não existe uma condição de vitória baseada num “rei” específico.

## 9. Ausência de empates

O projeto procura eliminar empates por design.

Existe um contador de turnos sem captura para impedir partidas potencialmente infinitas.

O contador só reinicia quando ocorre a **morte de uma peça permanente**.

O limite atual é de **50 turnos sem captura**.

Quando o limite é atingido, aplica-se o desempate material atualmente definido.

## 10. Desempate material

Quando necessário, comparam-se os valores das peças permanentes que permanecem no tabuleiro.

A regra de qual cor recebe a vitória nesse caso é uma variável de balanceamento. Atualmente existe uma preferência por dar o desempate à cor que demonstrar desvantagem estatística, em vez de assumir que uma cor é sempre a correta.

O objetivo de longo prazo é manter as duas cores aproximadamente equilibradas, com uma tolerância de cerca de 4% durante os testes.

## 11. Balanceamento

O custo dos heróis representa o seu valor estratégico esperado no jogo, não um conjunto de atributos.

Existe tooling para experimentar alterações automáticas de custos. No entanto, custos extremos podem ser um sintoma de uma habilidade intrinsecamente desbalanceada.

Por isso, o projeto pode alterar a mecânica do herói em vez de simplesmente continuar a mover o seu preço.

## 12. Modos futuros

A arquitetura deverá permitir variantes sem substituir o modo normal, incluindo possíveis combinações de:

- 10×10;
- orçamento diferente;
- regras de vitória alternativas;
- efeitos de terreno adicionais;
- exceções ao número de ações;
- regras especiais.

# RedWar — Documento de Design do Jogo

## 1. Identidade

RedWar é um **RPG de tabuleiro tático** em grelha, com forte inspiração no xadrez e em motores de estratégia como Stockfish, mas com identidade própria baseada em heróis.

O jogo não usa HP nem atributos tradicionais. Cada herói é definido principalmente por:

- movimentação;
- ataques;
- passivas;
- spells/ações especiais;
- efeitos que produz ou sofre.

O objetivo é criar muitas possibilidades estratégicas através de regras relativamente simples e peças muito diferentes entre si.

## 2. Filosofia de combate

O combate tem apenas dois resultados de ataque fundamentais:

- **Stun:** o alvo fica atordoado durante um número de turnos.
- **Morte:** a peça é removida do tabuleiro.

Um herói atordoado ainda pode ser atacado. Um segundo stun aplicado enquanto o primeiro continua ativo causa **morte**.

Isto cria deliberadamente uma espécie de sistema de “duas vidas” sem transformar o jogo num RPG de atributos: a primeira ocorrência cria um estado temporário; a segunda elimina a peça.

A duração exata do stun continua a ser um parâmetro de balanceamento. O design, no entanto, exige que exista tempo suficiente para que seja possível explorar a sequência “stun → segundo stun → morte”.

## 3. Estrutura da partida

O formato normal atual é:

- tabuleiro 8×8;
- 200 pontos iniciais para cada cor;
- draft antes da partida;
- posicionamento antes da partida;
- informação sobre a composição adversária permanece secreta até ao início;
- uma ação por turno.

Uma ação é a seleção de um herói e de um destino/alvo para executar uma ação legal.

A regra de uma ação por turno pode receber exceções no futuro quando uma passiva justificar uma exceção claramente definida.

## 4. Draft e composição

Os jogadores escolhem o seu exército antes da partida dentro de um orçamento de pontos.

Atualmente o orçamento normal é 200, mas modos futuros poderão alterar:

- tamanho do tabuleiro;
- orçamento;
- condições de vitória;
- outras regras.

Não existem limites artificiais de quantidade de heróis draftados além do espaço disponível e das regras de cada modo.

Heróis não draftáveis normalmente existem porque são **invocados por outras peças** e podem possuir duração limitada.

O custo de um herói é uma variável de balanceamento e não uma medida de atributos. A intenção é que o valor final reflita a força real da peça no jogo.

## 5. Invocações e peças temporárias

Uma peça invocada pode ser completamente funcional no tabuleiro mas não fazer parte da economia inicial do draft.

Peças temporárias:

- podem existir além do exército inicial;
- podem ter lifespan/cooldown próprio;
- contam para o resultado material enquanto estiverem no tabuleiro quando a regra de desempate assim o exigir;
- não reiniciam o contador de turnos sem captura quando morrem, se tiverem existência temporária.

## 6. Condições de vitória

Uma partida termina quando um jogador:

1. perde todas as suas peças;
2. fica sem qualquer ação legal disponível;
3. desiste.

O jogo procura ser **sem empates**.

Quando é necessário um desempate, a versão atual usa o valor material das peças permanentes restantes no tabuleiro. A cor vencedora resultante pode mudar conforme o balanceamento das cores seja testado.

A ideia não é favorecer permanentemente uma cor, mas usar as condições de vitória e o orçamento como ferramentas para aproximar o resultado das cores de 50/50, aceitando aproximadamente 4% de diferença como margem de equilíbrio.

## 7. Contador sem captura

O contador de turnos sem captura existe para evitar partidas que nunca terminem.

Só uma **morte de uma peça permanente** reinicia o contador.

Não reiniciam:

- stun;
- spawn;
- purify;
- swap;
- barricade;
- ignite sem morte permanente;
- outras ações que não eliminem uma peça permanente.

O limite atualmente utilizado é 50 turnos sem captura. Quando esse limite é atingido, aplica-se o desempate material definido para a versão atual.

O valor de 50 não deve ser considerado imutável: é uma variável de balanceamento.

## 8. Efeitos das casas

Uma casa pode conter uma peça e efeitos simultaneamente.

A intenção é permitir vários efeitos sobrepostos, cada um com:

- tipo;
- duração;
- regra própria;
- possível interação com outros efeitos.

### Fogo

O fogo é atualmente criado principalmente por `ignite` e passivas relacionadas.

A função atual pretendida é:

- persistir durante uma duração limitada;
- aplicar stun a uma peça que o atravesse/ocupe;
- permitir que um segundo stun mate uma peça que já esteja atordoada.

### Gelo

O gelo é uma mecânica de terreno pensada como uma barreira física/estado de congelamento.

A intenção é que ele possa bloquear movimento ou ataques que dependam de atravessar as casas intermédias. Regras especiais de movimento podem continuar a permitir atravessá-lo quando explicitamente definido.

O gelo também pode produzir um estado equivalente a stun/congelamento numa peça atingida.

A duração e interações exatas do gelo continuam abertas a testes.

### Silêncio

O silêncio é um exemplo de efeito de área produzido por uma passiva verdadeira.

Ao contrário de uma ação, o herói que cria a área não precisa de selecionar uma ação todos os turnos. O efeito modifica as ações que podem ser executadas dentro da sua área.

## 9. Passivas

As passivas são deliberadamente diferentes entre heróis. Existe uma tentativa de normalizar a representação em `heroes_config.json`, mas habilidades únicas podem exigir código especializado.

O objetivo de longo prazo é que:

> adicionar dez heróis novos seja possível através de uma extensão/configuração sem espalhar alterações por vários ficheiros.

Não é uma obrigação permitir que colaboradores externos definam novas regras de jogo; a definição das regras permanece sob controlo do projeto.

## 10. Modos futuros

O modo normal é 8×8/200 pontos.

A arquitetura deve permitir experimentar variantes sem destruir o modo normal, por exemplo:

- 10×10;
- orçamentos diferentes;
- regras de vitória diferentes;
- efeitos adicionais;
- regras especiais por modo.

A possibilidade de versões diferentes do jogo é preferível a obrigar uma alteração experimental a substituir imediatamente a versão normal.

## 11. Balanceamento

O balanceamento deve ser baseado em dados sempre que possível.

Existe interesse em que o custo dos heróis seja continuamente ajustado por ferramentas de análise/auto-pricer, em vez de depender apenas da intuição.

Ainda assim, uma IA fraca não é um árbitro suficientemente bom para concluir que um herói está equilibrado. Por isso:

1. primeiro melhora-se a IA;
2. depois mede-se o herói contra adversários fortes;
3. depois ajusta-se o custo ou, quando necessário, a mecânica intrínseca do herói.

Um custo extremamente baixo ou alto não deve ser usado como substituto permanente para uma mecânica mal balanceada.

## 12. Estado de maturidade

As regras do jogo são **estáveis o suficiente para orientar o desenvolvimento**, mas não congeladas.

Mudanças futuras são esperadas principalmente em:

- duração dos stuns;
- duração/funcionamento do gelo;
- duração/empilhamento de efeitos;
- condições de desempate;
- equilíbrio entre cores;
- custos dos heróis;
- novas passivas e efeitos;
- modos alternativos.

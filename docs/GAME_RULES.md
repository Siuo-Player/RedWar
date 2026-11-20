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

### Invariante Fundamental: Proibição de Fogo Amigo e Auto-captura
Peças da mesma equipa são aliadas intransponíveis:
- **Movimento**: Um movimento só pode ter como destino uma casa **vazia** (`board[r][c] == None`). Não é permitido saltar sobre aliados a menos que a peça possua habilidade de transposição espectral (como `Shadowblade` ou `Phantom`).
- **Ataque**: Um ataque só pode ter como alvo uma peça **inimiga**. Peças da mesma cor nunca podem ser atacadas ou capturadas por aliados. Clicar numa peça aliada na interface apenas altera a seleção ativa.

### Invariante de Alternância Estrita de Turnos
- No turno das Brancas, apenas as Brancas podem selecionar e mover peças.
- Ao concluir o lance, o turno passa deterministicamente para as Pretas. No cliente web/singleplayer, o tabuleiro bloqueia e a IA Ares executa o seu lance de forma autónoma antes de devolver o controlo.

Exemplos:

- mover;
- atacar por stun;
- atacar por morte;
- usar uma spell;
- executar outra habilidade ativa.

Uma passiva verdadeira não precisa necessariamente de consumir um turno.

**Desistência (`surrender`) é uma ação canónica não associada a casas do tabuleiro.** Não possui origem/destino e termina imediatamente a partida, atribuindo a vitória ao adversário. A ação de surrender não faz parte da enumeração normal de ações de tabuleiro.

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
- desiste através da ação canónica `surrender`.

Uma desistência é terminal e não altera o tabuleiro, os efeitos ou o contador de turnos sem captura; apenas regista a ação e atribui a vitória ao adversário.

Não existe uma condição de vitória baseada num “rei” específico.

## 9. Ausência de empates

O projeto procura eliminar empates por design.

Existe um contador de turnos sem captura para impedir partidas potencialmente infinitas. O contador só reinicia quando ocorre a **morte de uma peça permanente**; a morte ou expiração de uma invocação temporária não o reinicia.

O limite atual é de **50 turnos sem captura**. O limite e a repetição de uma posição são terminais e resolvem-se pelo desempate material; não produzem um resultado de empate.

## 10. Desempate material

O valor material do desempate é a soma dos custos configurados das **peças permanentes** que continuam no tabuleiro. Invocações temporárias não contam para esse valor. A regra de reinício do contador e a regra de contagem material são distintas: uma peça temporária não reinicia o contador quando morre, e também não altera o material usado no desempate.

A regra determinística atual é:

- se o material branco for estritamente superior ao preto, vencem as Brancas;
- caso contrário, vencem as Pretas, incluindo quando os totais são exatamente iguais.

Isto é uma regra fixa do ruleset atual, não uma política adaptativa que calcula em tempo real qual cor está estatisticamente em desvantagem. Qualquer futura alteração ao material contado ou à compensação de cor deve ser sustentada por evidência de balanceamento controlada e registada numa decisão própria.

O objetivo de longo prazo é manter as duas cores aproximadamente equilibradas, com uma tolerância de cerca de 4% durante os testes; essa meta não altera implicitamente a regra terminal executada.

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


## 13. Notação RedWar (RWN — RedWar Notation)

A **Notação RedWar (RWN)** é o formato padrão canónico (análogo ao PGN do xadrez) para registo, exportação, partilha e análise reproduzível de partidas de RedWar.

Exemplo de cabeçalho e lances RWN:
```rwn
[Event "RedWar 2.0 Match"]
[Site "RedWar Platform"]
[Date "2026.11.07"]
[White "Jogador"]
[Black "Ares AI"]
[Roster "Paladin,Shadowblade,Valkyrie,Arcanist,Duelist,Warden,Illusionist,Marksman"]

1. Wa e2-e3 Du d7-d6
2. Il c2-c4 Ma f7-f5
```

O cliente Web permite tanto a **Exportação RWN** (com cópia direta para o clipboard) como a **Importação RWN** para análise retrospetiva lance a lance no **Game Review**.

## 14. Roster Expandido de 30 Heróis Táticos

O RedWar conta com um catálogo dinâmico de 30 heróis e unidades táticas, cada um com geometria posicional e custo de draft calibrados:
- **Flanqueadores Aéreos e Rápidos**: `Valkyrie` (Custo 22), `Shadowblade` (Custo 18/65), `Duelist` (Custo 24), `Dragoon` (Custo 193).
- **Controladores e Artilharia à Distância**: `Arcanist` (Custo 23), `Marksman` (Custo 28), `Ranger` (Custo 40), `Stormcaller` (Custo 72), `Pyromancer` (Custo 17), `FrostMage` (Custo 5).
- **Âncoras, Guardiões e Vanguardas**: `Warden` (Custo 25), `Paladin` (Custo 16/55), `Templar` (Custo 15), `Inquisitor` (Custo 128), `Stonewall` (Custo 14).
- **Disruptores e Mestres de Transposição**: `Illusionist` (Custo 27), `Hookmaster` (Custo 15/52), `Timekeeper` (Custo 16/59), `Trickster` (Custo 12/26), `Geomancer` (Custo 21).
- **Necromancia e Invocações Estruturais**: `BoneLord` (Custo 86), `Lich` (Custo 11), `Ghoul` (Custo 5), `Bone` (Custo 8), `Obelisk` (Custo 16).

## 15. Motor de IA Ares 2.0 Max

O motor **Ares** opera com técnicas contemporâneas de motores de jogos abstratos de tabuleiro de alto nível:
- **Tabela de Transposição Zobrist (64-bit)**: Chaves hash aleatórias que preservam o estado e evitam re-exploração de transposições.
- **Ordenação MVV-LVA com Priorização do Horizonte de Stun**: Lances que eliminam peças atordoadas ("um segundo enquanto atordoado mata") têm prioridade absoluta ($300.000 + 100 \times \text{custo\_vitima} - \text{custo\_atacante}$).
- **Quiescence Search**: Estabilização tática das folhas para evitar o efeito de horizonte em trocas críticas.
- **Late Move Reductions (LMR)**: Redução seletiva de profundidade em lances silenciosos profundos para maximizar a profundidade efetiva.
- **Opening Book Tático**: Desenvolvimento estruturado de centros e flancos nas primeiras 4 jogadas.

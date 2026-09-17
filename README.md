# ⚔️ RedWar

**RedWar** é um RPG de tabuleiro tático em grelha, inspirado no xadrez e em jogos de estratégia, mas construído à volta de heróis com movimentações, ataques, passivas e efeitos de terreno diferentes.

Não existem HP, força, defesa ou outros atributos numéricos tradicionais. O combate é definido por **stun** e **morte**: uma peça pode ser atordoada e perder a capacidade de agir durante alguns turnos; um segundo stun enquanto continua atordoada transforma-se em morte.

O objetivo a longo prazo é criar uma experiência semelhante ao modelo de **Chess.com**: aplicação, versão web, partidas contra IA, análise de partidas, multiplayer online, matchmaking, ranking e replays.

> **Estado atual:** projeto em desenvolvimento. As regras continuam a poder mudar. O primeiro objetivo de produto é um **1.0-Lite local**, enquanto o Ares continua a evoluir como open-project separado.

## O projeto em duas partes

O repositório contém atualmente o jogo e a IA no mesmo projeto, mas a separação desejada é mais clara:

| Parte | Objetivo | Política de alterações |
|---|---|---|
| `ai/` — **Ares** | Pesquisa, avaliação, bots e ferramentas específicas de IA | Deve poder receber contribuições automatizadas, desde que demonstrem melhoria quando a alteração pretende ser strength-sensitive; a investigação competitiva continua aberta após o 1.0-Lite |
| `engine/`, `ui/`, `online/`, `main.py` e restante produto | Regras, aplicação, multiplayer, interface e infraestrutura | O autor decide manualmente o que entra em `main` |

A ideia é semelhante ao modelo do Stockfish: a IA pode tornar-se uma zona aberta de otimização competitiva, enquanto a definição do jogo e o produto permanecem sob controlo do projeto.

## 🎮 O jogo

### Estado atual

- Tabuleiro normal: **8×8**.
- Orçamento inicial normal: **200 pontos por cor**.
- Cada jogador faz **uma ação por turno**.
- O draft e o posicionamento acontecem antes da partida e são secretos para o adversário.
- Não existe compra durante a partida.
- Não existem limites artificiais de quantidade de peças durante o jogo além do espaço disponível e das próprias regras.
- Algumas peças são invocáveis e temporárias e, por isso, não aparecem no draft.

### O que é uma ação?

Uma ação é uma decisão do jogador em que um herói é selecionado e uma casa de destino/alvo é escolhida para executar uma ação legal.

Isto inclui:

- movimento;
- ataque por stun;
- ataque por morte;
- spells;
- outras habilidades ativas que venham a ser introduzidas.

Existem também passivas verdadeiramente passivas. Um exemplo é o **silêncio**, que altera o que pode ser feito numa área sem precisar de uma ação do jogador.

### Combate e “duas vidas” sem HP

O jogo não usa pontos de vida. A mecânica pode ser entendida como um sistema de dois estados de sobrevivência:

```text
Normal
  ↓ stun
Atordoado
  ↓ novo stun enquanto continua atordoado
Morto
```

O stun dura um número de turnos a definir/calibrar. Quando o efeito termina, a peça volta ao estado normal. O valor e a forma exata de contagem dos turnos continuam a ser parâmetros de design, mas a regra fundamental é fixa: **dois stuns consecutivos na mesma janela de atordoamento equivalem a uma morte**.

### Vitória

Uma partida termina quando uma das cores:

1. perde todas as suas peças;
2. deixa de ter qualquer ação legal disponível;
3. desiste.

O projeto procura eliminar empates. As regras de desempate são portanto consideradas parte do design oficial, embora ainda sejam um sistema em calibração.

Quando é necessário desempatar por material, a cor vencedora atual é determinada pelo maior valor das peças permanentes que continuam no tabuleiro. O balanceamento de cores é validado empiricamente e pode levar a alterações no orçamento ou nas condições de desempate.

### Contador sem captura

O contador de turnos sem captura só é reiniciado quando ocorre **morte de uma peça permanente colocada no tabuleiro**. Invocações temporárias não reiniciam esse contador.

Stun, spawn, spells e outras ações que não produzem uma morte permanente não o reiniciam.

O limite atualmente usado para o desempate é de 50 turnos sem captura, mas este número é considerado um parâmetro de balanceamento e pode mudar.

## 🧊🔥 Efeitos de terreno

As casas podem possuir efeitos. Atualmente os conceitos principais são:

### Fogo

O fogo é criado por habilidades como `ignite`.

- permanece durante um número de turnos;
- pode aplicar stun a uma peça que entre na casa;
- um novo stun sobre uma peça já atordoada pode matar essa peça;
- efeitos futuros podem ser acumulados na mesma casa.

### Gelo

O gelo representa uma barreira/estado de congelamento da casa.

A intenção de design é que o gelo possa impedir a passagem direta de movimento ou ataque, salvo quando a regra da habilidade permitir atravessar casas intermédias.

Se um herói for atingido pelo efeito correspondente, pode ficar atordoado/congelado.

A duração exata e todas as interações do gelo ainda estão em definição.

### Sistema de efeitos futuro

O modelo pretendido permite ter vários efeitos numa mesma casa, cada um com duração e consequência próprias. Efeitos opostos poderão futuramente interagir ou anular-se quando isso fizer sentido para o design.

## 🧙 Heróis

Cada herói pode ter:

- movimento próprio;
- ataques próprios;
- passivas;
- spells;
- invocações;
- efeitos de terreno;
- limitações e cooldowns.

A intenção de design é que adicionar um herói novo seja tão simples quanto possível, idealmente alterando apenas `engine/heroes_config.json` e evitando mudanças espalhadas por vários ficheiros.

A realidade atual ainda não atingiu esse objetivo: algumas passivas especiais continuam a exigir lógica fora da configuração.

A configuração oficial encontra-se em:

`engine/heroes_config.json`

O formato está documentado em:

`engine/HEROES_SCHEMA.md`

## 🧠 Ares Engine

**Ares** é a IA especializada de RedWar.

O objetivo de longo prazo é criar uma IA suficientemente forte e rápida para adversário, análise de posições, análise pós-partida e benchmarking competitivo. Esse trabalho continua como open-project para além do primeiro lançamento local.

Funções pretendidas:

- adversário contra o jogador;
- diferentes níveis de bot;
- análise de posições;
- análise pós-partida;
- benchmarking de novas versões da IA;
- Arena automática para aceitar apenas melhorias reais no caminho competitivo.

A implementação está em transição para um núcleo C++ mais rápido, mantendo ferramentas Python onde isso for conveniente.

A metodologia de desenvolvimento segue uma abordagem **Stockfish-like adaptada ao RPG**: separar estado, pesquisa, avaliação e move ordering, manter o hot path pequeno e exigir evidência antes de aceitar alterações strength-sensitive.

O Ares suporta atualmente uma avaliação clássica e um caminho **NNUE opcional**. A rede não é considerada superior só por existir: o objetivo é demonstrar ganho de força por CPU-segundo antes de a tornar default.

### Princípio de otimização

> **Uma alteração na IA só deve sobreviver como melhoria strength-sensitive se houver evidência adequada para a afirmação pretendida.**

Não interessa se o código parece mais elegante, mais complexo ou mais “Stockfish-like” se o resultado prático for pior.

## 🏟️ Arena

A Arena é a infraestrutura que deverá permitir uma comunidade aberta a melhorar o Ares.

O modelo pretendido é comparar:

```text
versão anterior da Ares
        VS
versão proposta no Pull Request
```

usando condições equivalentes de pesquisa e alternando cores para evitar que a primeira jogada determine artificialmente o resultado.

A Arena mede **força relativa entre versões da IA**, não qualidade do jogo como produto nem equilíbrio intrínseco de heróis.

Resultados históricos devem guardar, quando disponíveis:

- versão da IA;
- cores;
- resultado de cada jogo;
- tempo/nodes utilizados;
- composição das peças;
- posição inicial;
- métricas relevantes.

A longo prazo, os resultados deverão alimentar um sistema de rating/ELO válido para engines.

## ⚖️ Balance Lab

O Balance Lab é uma responsabilidade distinta da Ares.

**Ares é um agente dentro do Balance Lab; não é o Balance Lab.** O objetivo do laboratório é estudar como alterações de roster, custos e regras afetam o jogo como sistema.

Hero strength deve ser tratada como contextual, preservando quando disponível:

```text
hero
× position
× allied composition
× opponent / matchup
× initiative / colour
× ruleset
× seed
× Ares policy / player-skill context
× outcome / terminal reason
```

Por isso:

```text
hero → global win rate
```

é apenas uma marginalização grosseira e não é suficiente para decidir balanceamento.

Para uma alteração de balanceamento, o processo de referência é:

```text
controlled baseline
→ matched games / seeds / colours
→ selection + provenance audit
→ contextual matchup / composition / counter analysis
→ candidate intervention
→ independent hold-out
→ manual/design decision
```

Para preço, a intervenção normal começa em **custos inteiros** e usa procura coarse-to-fine. Quando custo não resolve o defeito estratégico, a análise pode escalar para a menor alteração de mecânica capaz de atacar a causa observada.

`tools/balance/auto_pricer.py` é tooling diagnóstico/legado. Não é uma autoridade de balanceamento e não deve, sozinho, justificar uma alteração de preço, mecânica ou roster.

O equilíbrio de cor/iniciativa é tratado como uma calibração experimental separada, com condições emparelhadas e distinção entre amostras de calibração e hold-out.

O Balance Lab também deve distinguir:

```text
competitive strength
≠ intrinsic hero value
≠ player-perceived balance
```

O primeiro 1.0-Lite usa um **Ares Balance Baseline congelado** apenas para tornar estes experimentos reprodutíveis. O baseline não é uma certificação de que Ares é competitivamente ótima.

## 🔬 Workflows e validação

Os workflows do projeto são intencionalmente separados por responsabilidade. Uma falha experimental não deve mascarar a saúde de outro subsistema.

```text
GATES
├── test_suite.yml          -> correção funcional e regressões gerais
└── ai_quality_gate.yml     -> única autoridade strength-sensitive nos PRs

SECURITY
└── codeql.yml              -> análise de segurança

DIAGNOSTICS
└── arena_diagnostics.yml   -> evidência observacional, sem promoção

EXPERIMENTS
└── arena_experiments.yml   -> experiências manuais, datasets e holdout

NIGHTLY
├── nnue_nightly.yml        -> teacher data, treino NNUE e modelos experimentais
└── auto_balancer.yml       -> trainer, telemetria e tooling de balanceamento diagnóstico

TEMPORARY RESEARCH
└── strength_calibration.yml -> calibração A/A, sem autoridade de promoção
```

A proteção estrutural de `main` pertence ao GitHub Ruleset `Protect main`; não existe um `main_guard.yml` paralelo. `ai_quality_gate.yml` é a única autoridade Action-based para promoção strength-sensitive em PRs.

`arena_diagnostics.yml` e `arena_experiments.yml` não são required checks de promoção. A Arena experimental é manual e não dispara automaticamente em pushes normais de branches AI.

O **Auto-Balancer não treina NNUE**. O treino PyTorch pertence ao workflow nightly NNUE. O tooling de balanceamento não deve ser interpretado como uma autoridade automática sobre custos de heróis.

## 🛠️ Tooling e desenvolvimento

As ferramentas estão separadas por função:

```text
tools/analytics  -> Arena, trainer e análise de jogos
tools/balance    -> tooling diagnóstico do Balance Lab / pricing
tools/nnue       -> features, teacher data, treino e export
tools/scripts    -> build e auditorias de desenvolvimento
```

Scripts obsoletos não devem permanecer apenas porque “podem ser úteis um dia”. Nesta fase foram removidos os caminhos legados de opening testing, calibração ELO e reorganização destrutiva.

O ciclo de branch é deliberadamente simples:

```text
branch nova
   ↓
roadmap atualizado
   ↓
bloco completo
   ↓
testes + benchmark
   ↓
PR
   ↓
merge
   ↓
apagar branch
   ↓
próxima branch
```

Erros encontrados durante o bloco são corrigidos na própria branch.

## 🌐 Aplicação e web

O objetivo final é uma experiência semelhante a Chess.com.

### Aplicação

- jogo contra IA;
- escolha de bot/dificuldade;
- dois jogadores locais;
- análise;
- replays;
- histórico de partidas;
- menus e definições;
- som, VFX e animações;
- suporte a diferentes resoluções;
- possível suporte mobile.

### Web

A versão web é um objetivo real e deverá partilhar o máximo possível da lógica do jogo com a aplicação.

A tecnologia final ainda não foi escolhida. A decisão deve privilegiar:

1. custo gratuito ou muito baixo;
2. simplicidade de desenvolvimento;
3. baixa latência;
4. suporte a WebSocket/multiplayer;
5. capacidade de manter o core do jogo autoritativo e consistente.

## 🌐 Multiplayer

O multiplayer online é uma funcionalidade principal do produto final.

O objetivo inclui:

- partidas públicas;
- matchmaking;
- partidas 1v1;
- convites por utilizador/link;
- login Google;
- ranking de jogadores;
- ELO/MMR calculado através do matchmaking;
- vários controlos de tempo, inspirados em Chess.com;
- reconnect quando a ligação cai;
- derrota por abandono/timeout;
- rematch;
- espectadores;
- histórico de partidas.

A arquitetura de servidor ainda está em definição. A intenção é usar serviços gratuitos/low-cost quando possível.

O servidor deverá, por princípio, validar as ações recebidas pelo cliente e impedir que o cliente possa simplesmente declarar um estado impossível.

## 🧪 Desenvolvimento local

### Testes Python

```bash
pytest tests/
```

### Build do avaliador Cython

```bash
python setup.py build_ext --inplace
```

### Build C++ recomendado

```bash
python tools/scripts/build_cpp_engine.py
python tools/scripts/build_cpp_engine.py --smoke
```

O script usa uma lista explícita de fontes e inclui o caminho NNUE quando aplicável.

## 📚 Documentação atual

| Documento | Conteúdo |
|---|---|
| `README.md` | Visão geral, jogo, produto e estado atual |
| `docs/Documento_Design_Jogo.md` | Filosofia e decisões de design do jogo |
| `docs/Estrutura_Projeto.md` | Estrutura do projeto |
| `docs/ARCHITECTURE.md` | Fronteiras e dependências técnicas |
| `docs/AI_ENGINE.md` | Ares, search, avaliação, NNUE e Arena |
| `docs/NNUE.md` | Arquitetura, formato, treino e validação NNUE |
| `docs/TOOLING.md` | Ferramentas e contratos de tooling |
| `docs/DEVELOPMENT_WORKFLOW.md` | Ciclo branch → validação → PR → merge |
| `docs/CONTRIBUTING.md` | Regras de contribuição e validação |
| `docs/ROADMAP.md` | Estado, prioridades e próximos blocos |
| `engine/HEROES_SCHEMA.md` | Formato técnico de `heroes_config.json` |

## 🗺️ Estado do projeto

RedWar ainda não é um produto lançado.

A prioridade atual é:

1. definir e congelar o **Ares Balance Baseline** e o protocolo mínimo do Balance Lab para o 1.0-Lite;
2. completar a aplicação local 1.0-Lite: fluxo de partida, draft, Battle UI, VFX/som, dificuldades, replay básico e usabilidade;
3. manter regras, legalidade e regressões continuamente protegidas;
4. manter Arena, datasets e tooling reproduzíveis;
5. lançar a primeira versão local jogável sem depender de servidor ou matchmaking;
6. continuar o desenvolvimento competitivo da Ares como open-project sob #372;
7. desenvolver a versão web e o multiplayer;
8. criar contas, matchmaking, ranking e histórico;
9. só então considerar o lançamento público completo/Full.

### 10×10 e outros modos

8×8 continua a ser o formato normal.

Um tabuleiro 10×10 é uma possibilidade futura, mas só depois de a base 1.0-Lite e a Ares serem suficientemente rápidas/estáveis para justificar o modo. Também é possível que diferentes tamanhos, orçamentos e regras se tornem modos separados, em vez de substituir o modo normal.

## Licenças e conteúdo de terceiros

A política de licenciamento ainda precisa de uma revisão formal antes do lançamento público.

O projeto foi desenvolvido com assistência de sistemas de IA e utiliza arte baseada em recursos externos, incluindo referências a **game-icons.net**. Antes de uma distribuição pública, devem ser auditadas as licenças do código, dos assets e de qualquer conteúdo gerado/derivado para garantir que os direitos e atribuições estão corretos.

## Projeto em evolução

Quando este documento disser **“atual”**, significa o comportamento que o projeto pretende tratar como regra neste momento.

Quando disser **“planeado”**, é uma intenção futura.

Quando disser **“a definir”**, não existe ainda uma decisão suficientemente sólida para ser considerada especificação.

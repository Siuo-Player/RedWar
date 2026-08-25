# Discovery / Decision — RedWar observability and imperfect information

Data: 2026-08-25
Estado: descoberta confirmada; decisão de investigação aceite
Origem: auditoria do código + README + Project Studies upstream alert

## Facto observado

`README.md` especifica que o draft e o posicionamento inicial são secretos para o adversário.

A cadeia atual da Ares, porém, envia o estado completo para o motor C++:

```text
CppEngineBot.escolher_jogada(game_state)
    ↓
game_state.to_rwen()
    ↓
position rwen <estado completo>
    ↓
Ares / search
```

`GameState.to_rwen()` serializa cada célula do tabuleiro incluindo equipa, nome da peça, stun timer, lifespan e cooldown. Portanto o RWEN recebido pela Ares representa também peças do adversário.

## Evidência local

- `ai/bot.py`: `CppEngineBot.escolher_jogada()` envia `game_state.to_rwen()` para o processo C++.
- `engine/game_state.py`: `to_rwen()` serializa todas as peças e efeitos do tabuleiro sem distinção entre informação pública e secreta.
- `docs/AI_ENGINE.md`: descreve alpha-beta/PVS, TT, avaliação e NNUE, mas não define information sets, belief states ou um observability contract para Ares.

## Evidência externa

Perolat et al., *Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning*, Science 378(6623), 2022, 990–996. DOI: 10.1126/science.add4679. Public preprint: https://arxiv.org/abs/2206.15378

A ficha `_sources/cards/perolat2022-deepnash.md` no repositório `Siuo-Player/Siuo-Player-PROJECT-STUDIES` identifica a relevância de hidden information, long horizons e deployment em jogos de tabuleiro e alerta que RedWar deve formalizar a observabilidade antes de assumir que perfect-information search é a formulação correta.

## Interpretação

Ainda não está demonstrado qual destas três situações é a especificação pretendida:

1. **Perfect-information by design after setup** — o segredo só existe durante draft/placement e todas as peças tornam-se públicas quando a partida começa.
2. **Imperfect-information during play** — a identidade/posição de algumas peças continua secreta e Ares não pode receber o estado completo.
3. **Information leak atual** — o design pretende segredo durante a partida, mas a implementação passa o estado completo à Ares.

O código atual prova apenas que a representação interna da Ares é full-state. Não prova qual destas interpretações é a regra de produto correta.

## Decisão

Antes de novas alterações de search, NNUE ou RL que dependam da observabilidade, criar um **Observability Contract** explícito e verificar a cadeia completa:

```text
rules / design
    ↓
what a player can observe
    ↓
information set
    ↓
AI-visible state
    ↓
search root
    ↓
move generation
    ↓
evaluation / NNUE
```

Não implementar DeepNash neste bloco.

## Critério de aceitação da próxima etapa

A auditoria deve conseguir responder, para cada campo do estado:

- é observável pelo jogador?
- é observável pela Ares?
- se não é público, existe razão de design para a Ares recebê-lo?
- o campo influencia movegen, search, evaluation ou NNUE?
- existe teste que impeça leakage futuro?

## Impacto no desenvolvimento atual

Branches de Ares que alteram search/representação devem tratar esta auditoria como uma dependência metodológica:

- `feat/ares-action-aware-ordering-2026-08-25`
- `feat/ares-holdout-validation-2026-08-25`
- `feat/arena-statistical-contract-2026-08-25`

NNUE incremental e novas otimizações de search não devem usar a validação de força como prova final enquanto a observabilidade legal não estiver especificada.

## Resultado esperado

Depois de formalizar a regra, o projeto deverá possuir uma destas arquiteturas explícitas:

```text
public/full state
→ Ares pode receber full state
```

ou

```text
hidden state
→ player observation
→ information set / belief representation
→ Ares search/evaluation
```

A implementação e os testes serão tratados em PRs posteriores, depois de a especificação ser aceite.

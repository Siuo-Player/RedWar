# RedWar — Tooling

## Objetivo

`tools/` contém processos externos ao jogo: medir, treinar, balancear, construir e diagnosticar.

A regra principal é que uma ferramenta deve consumir interfaces do projeto em vez de criar uma segunda implementação das regras.

## Organização

```text
tools/
├── analytics/
│   ├── arena_tournament.py
│   ├── opening_book.py
│   ├── game_analyzer.py
│   └── trainer.py
├── balance/
│   └── auto_pricer.py
├── nnue/
│   ├── features.py
│   ├── io.py
│   ├── generate_teacher.py
│   ├── train.py
│   └── bootstrap_model.py
└── scripts/
    ├── build_cpp_engine.py
    ├── build_pipeline.py
    └── audit_structure.py
```

## Analytics

### Arena

`arena_tournament.py` executa o confronto A/B e pode guardar JSONL com cada jogo.

O registo deve ser suficiente para reconstruir a experiência:

- seed/opening;
- engines e configuração;
- cores;
- posição inicial/final;
- ações;
- resultado;
- contadores úteis.

A Arena não deve ser usada como parser/relatório. Produz dados.

### Análise

`game_analyzer.py` recebe os JSONL produzidos pela Arena e calcula agregados. Não executa o jogo novamente.

Esta separação evita um erro clássico de tooling: alterar involuntariamente o experimento enquanto se tenta analisá-lo.

### Trainer

O trainer produz telemetria e resultados para o Auto-Pricer. Partidas inválidas devem ser marcadas como inválidas e nunca reinterpretadas silenciosamente como derrotas.

O trainer aceita `--jogos`, `--seed` e `--output` e grava o JSON de forma atómica, permitindo experiências repetíveis sem depender de estado global do processo.

## Balanceamento

O Auto-Pricer deve preferir uma função pura:

```text
stats + hero config
        ↓
 proposed changes
        ↓
 optional write
```

`--no-write` deve continuar a ser o modo seguro para CI.

Valores de fronteira numérica são responsabilidade do boundary: inputs não finitos devem ser rejeitados e intervalos extremos devem ter regressões específicas.

O antigo `color_balancer.py` foi removido porque era um simulador de orçamento baseado em lógica antiga e não tinha consumidor ativo no fluxo atual.

## NNUE

O tooling NNUE está separado do jogo normal porque PyTorch e checkpoints não são requisitos para executar a Ares.

```text
features.py -> representação
io.py       -> formato RWNUE002
generate_*  -> dataset
train.py    -> treino/export
bootstrap   -> compatibilidade
```

Modelos e checkpoints gerados não devem entrar no hot path nem ser tratados como código-fonte.

## Build

`build_cpp_engine.py` usa uma lista explícita de fontes. Não deve compilar todos os `.cpp` encontrados numa pasta porque isso faria uma nova ferramenta/teste alterar silenciosamente o executável de produção.

`build_pipeline.py` faz apenas build, smoke build, testes e auditoria de estrutura. Trainer e Auto-Balancer ficam fora da pipeline local por defeito porque podem produzir/mutar dados experimentais.

## Estrutura

`audit_structure.py` é deliberadamente não destrutivo. Auditorias devem dizer o que está errado; mover/apagar ficheiros é uma mudança arquitetural que precisa de revisão e testes.

## Ferramentas removidas nesta fase

Foram removidos:

- `opening_tester.py`: duplicava a abertura/Arena atual;
- `calibrate_elo_chain.py`: calibrador antigo, fora do fluxo atual de medição;
- `elo_config.json`: estado pertencente ao calibrador removido;
- `color_balancer.py`: balanceador de cor antigo sem consumidor ativo;
- `reorganize.py`: script destrutivo que podia substituir ficheiros automaticamente.

## Regras para novas ferramentas

Antes de adicionar um script:

1. procurar se a funcionalidade já existe;
2. definir explicitamente a entrada e a saída;
3. evitar escrita por defeito;
4. tornar seeds/configuração explícitas quando existe aleatoriedade;
5. acrescentar uma regressão se o script manipular dados críticos;
6. documentar o consumidor do script.

Ferramentas que não tenham consumidor identificável durante algum tempo devem ser candidatas a remoção.

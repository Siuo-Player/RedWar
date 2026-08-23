# Estrutura e Arquitetura do Projeto RedWar

Este documento é um mapa operacional do repositório. Caminhos descritos como atuais devem existir; objetivos futuros estão explicitamente marcados.

## 1. Estrutura atual

```text
RedWar/
├── ai/                 # Ares, bots e engine C++
│   └── cpp_engine/     # hot path da pesquisa/avaliação
├── engine/             # estado e regras autoritativas durante a migração
├── ui/                 # aplicação visual local
├── online/             # cliente/rede/servidor em desenvolvimento
├── tools/
│   ├── analytics/      # Arena, trainer, openings determinísticas, análise
│   ├── balance/        # auto-pricer e balanceamento
│   ├── nnue/           # features, teacher data, treino e exportação
│   └── scripts/        # build e auditorias de desenvolvimento
├── tests/              # regressões e invariantes
├── docs/               # documentação técnica e de produto
├── data/               # dados gerados, datasets e modelos
├── logs/               # saídas de diagnóstico locais/geradas
├── deploy/             # packaging/release
└── main.py             # entrada da aplicação local
```

## 2. Regra de propriedade

### `engine/`

Define o que uma posição é e o que uma ação faz.

### `ai/`

Decide que ação procurar e como avaliar uma posição. Pode conter otimizações específicas de engine, mas não deve introduzir uma segunda semântica das regras.

### `tools/`

Executa experiências, builds, treino, Arena e análise. Não deve ser importado pelo caminho normal de uma partida salvo quando existe uma razão explícita.

### `tests/`

Testa comportamento e invariantes. Não é uma camada funcional do jogo.

### `data/` e `logs/`

Contêm resultados produzidos. Dados reprodutíveis usados como fixtures pertencem ao repositório; grandes artefactos de treino/build devem ser ignorados ou publicados como artifacts/releases conforme a necessidade.

## 3. Convenção de `tools/`

```text
tools/analytics/
  arena_tournament.py       # confronto A/B
  opening_book.py           # posições determinísticas
  game_analyzer.py          # análise de JSONL já gravado
  trainer.py                # geração de dados de treino

tools/balance/
  auto_pricer.py            # cálculo puro + aplicação opcional

tools/nnue/
  features.py               # layout de features
  io.py                     # formato RWNUE002
  generate_teacher.py       # targets clássicos
  train.py                  # treino/exportação
  bootstrap_model.py        # compatibilidade, não força

tools/scripts/
  build_cpp_engine.py       # build explícito
  build_pipeline.py         # pipeline de desenvolvimento
  audit_structure.py        # auditoria não destrutiva
```

Scripts antigos que simulavam o mesmo fluxo com regras diferentes devem ser removidos em vez de mantidos “por segurança”. Um caminho antigo só deve sobreviver quando ainda tiver um consumidor real ou desempenhar uma função de compatibilidade documentada.

## 4. O que não deve acontecer

- `tools/` redefinir regras de `engine/`;
- UI validar ações por uma implementação própria;
- Arena ter uma opening book diferente do fluxo oficial sem motivo documentado;
- scripts de build compilar automaticamente qualquer `.cpp` encontrado numa pasta;
- scripts de reorganização apagarem/substituírem ficheiros sem confirmação explícita;
- dados gerados serem tratados como fonte de verdade do código;
- documentação declarar um estado que o código não implementa.

## 5. Reestruturação futura

Uma reestruturação maior poderá separar mais claramente:

```text
src/                 # produção Python/C++/bindings
scripts/              # comandos de desenvolvimento
benchmarks/           # posições e referências de medição
training/             # datasets/checkpoints NNUE
```

Não vamos fazer esta migração toda de uma vez. Primeiro estabiliza-se a semântica, as dependências e os consumidores; depois movem-se diretórios em blocos que possam ser testados e revertidos facilmente.

## 6. Inspiração externa

Projetos grandes de engines seguem uma separação semelhante: Stockfish mantém o motor concentrado em `src` e os testes/infraestrutura fora dele; Fairy-Stockfish separa `src`, `tests` e scripts/CI, e mantém tooling de NNUE em repositórios e pastas próprias. A principal lição para RedWar não é copiar nomes, mas manter o código executável, os testes e as experiências com responsabilidades diferentes.

# RedWar — Arquitetura Técnica

## 1. Princípio central

RedWar deve ter **uma semântica única do jogo**. A UI, a IA, a Arena e o servidor não devem inventar regras próprias.

A divisão atual é:

```text
                      Produto / interfaces
                ┌────────────┬────────────┐
                ▼            ▼            ▼
               UI         Online        CLI/tools
                │            │            │
                └────────────┼────────────┘
                             ▼
                      Game Core / Rules
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
             Ares                      Services
          search/eval                telemetry/data
```

`engine/` é a referência das regras durante a migração. `ai/` deve consumir o estado e as regras, não reimplementá-los sem uma razão explícita de performance/portabilidade.

## 2. Estado atual — 2026-08-23

O projeto continua numa migração Python/Cython → C++ para o hot path da Ares.

```text
engine/
  estado, regras, heróis e parser de ações

ai/
  integração de bots + C++ Ares

ui/
  apresentação local

online/
  cliente/rede/servidor em desenvolvimento

tools/
  Arena, análise, balanceamento, NNUE, build e auditoria

tests/
  regressões Python/C++ e testes de invariantes

data/
  telemetria/datasets/modelos gerados

docs/
  decisões, arquitetura, metodologia e roadmap
```

O **PR #49** é a branch ativa de NNUE RPG. A avaliação NNUE continua opcional; sem modelo carregado, a Ares mantém a avaliação clássica.

## 3. Fronteiras

### `engine/`

Responsável por:

- representação da posição;
- legalidade de ações;
- transições de estado;
- timers e efeitos;
- condições de fim;
- configuração/data dos heróis.

Não deve depender de UI.

### `ai/`

Responsável por:

- geração e ordenação de ações quando fazem parte do motor;
- pesquisa alpha-beta/PVS;
- TT, heurísticas e quiescence;
- avaliação clássica e NNUE;
- limites de nodes/tempo;
- protocolo de comunicação com bots.

A pesquisa deve continuar separada da apresentação.

### `tools/`

Responsável por processos **fora do caminho de uma partida normal**:

```text
tools/
├── analytics/     # Arena, abertura determinística, análise de jogos, trainer
├── balance/       # auto-pricer e balanceamento
├── nnue/          # features, teacher data, treino/exportação
└── scripts/       # build e auditorias de desenvolvimento
```

Uma ferramenta não deve duplicar a definição de regras do `engine/` apenas para facilitar um script.

### `tests/`

Os testes verificam invariantes. Não são uma segunda implementação do jogo.

Prioridades:

- make/unmake;
- hash incremental vs estado restaurado;
- ações legais/ilegais;
- timers/effects/stun;
- diferenças Python/C++;
- overflow/valores extremos em fronteiras de dados;
- paridade Python/C++ das features NNUE.

## 4. Direção de longo prazo

O objetivo é chegar a uma fronteira estável:

```text
                    Game Core
                ┌───────┼────────┐
                ▼       ▼        ▼
              Ares    Server      UI
                │       │
                ▼       ▼
              Tools / telemetry
```

O detalhe de implementação pode mudar. A interface entre estas áreas deve mudar muito menos.

## 5. Python e C++

Durante a migração, uma posição deve poder ser comparada entre as duas implementações:

```text
RWEN / BoardState
      │
      ├── Python
      └── C++
            │
            ▼
      estado equivalente
```

Invariantes importantes:

1. mesma posição → mesmas ações legais;
2. `make → unmake` → posição original;
3. hash incremental consistente;
4. mesmos estados terminais;
5. mesma interpretação dos timers/efeitos;
6. features NNUE idênticas quando alimentadas com a mesma posição.

## 6. Observabilidade

Cada experimento importante deve poder responder:

- qual versão foi testada;
- que posição/dataset foi usado;
- orçamento de nodes/tempo;
- resultado e seed;
- custo de CPU;
- se a partida foi válida;
- se a alteração foi aceite ou rejeitada e porquê.

Isto aproxima o projeto do modelo de engines maiores: o código é apenas uma parte do sistema; a medição reprodutível é outra.

## 7. Regra de modularidade

Ficheiros de produção acima de aproximadamente 1000 linhas são candidatos a divisão. A configuração extensa de heróis é uma exceção possível quando a concentração simplifica manutenção.

Não criar módulos apenas para reduzir o número de linhas. Um módulo deve ter uma responsabilidade identificável.

## 8. Reestruturação segura

A estrutura deve evoluir por blocos pequenos. Scripts de reorganização destrutivos foram removidos: o tooling de estrutura deve **auditar por defeito** e nunca apagar/substituir um ficheiro automaticamente.

Mudanças de diretórios que exijam alterar imports/workflows devem ser feitas como um bloco dedicado, com testes de referências antes e depois.

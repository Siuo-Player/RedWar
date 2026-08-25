# RedWar — Protocolo de Benchmarks da Ares

## Objetivo

Impedir que melhorias da Ares sejam avaliadas apenas por um pequeno conjunto de posições conhecidas e, consequentemente, que uma alteração fique melhor nos benchmarks escolhidos enquanto piora no jogo geral.

Este risco é uma forma de **overfitting do critério de avaliação**: quando o mesmo conjunto finito é usado repetidamente para orientar decisões e medir o resultado final, o processo de seleção pode adaptar-se ao próprio benchmark. Cawley & Talbot mostram que a seleção repetida sobre uma métrica finita pode introduzir selection bias; a literatura também recomenda conjuntos independentes para avaliação final. Ver os caminhos diretos em `docs/INSPIRATIONS_AND_HOMAGE.md` e `docs/ENGINEERING_METHODOLOGY_AND_RESEARCH.md`.

## Três camadas separadas

### 1. Regression / known cases

Casos que já expõem bugs ou capacidades importantes:

- FrostMage;
- segundo STUN;
- spells específicos;
- regressões encontradas pelo differential testing.

Objetivo: **impedir regressões conhecidas**.

Regra: passar aqui não prova melhoria geral.

### 2. Development / diagnostic cases

Posições criadas durante o desenvolvimento para explicar uma hipótese:

- nova heurística de move ordering;
- nova extensão selectiva;
- novo comportamento de spell;
- nova combinação de efeitos.

Objetivo: perceber se a alteração implementa o fenómeno pretendido.

Regra: resultados deste conjunto não devem ser usados isoladamente para declarar uma melhoria de força.

### 3. Validation / hold-out

Conjunto separado das posições usadas para orientar a alteração.

Objetivo: medir **generalização**.

Regras:

- não adicionar uma posição ao hold-out depois de observar a alteração que ela deve favorecer;
- não remover casos apenas porque a alteração falha;
- alterar o hold-out apenas através de uma atualização metodológica deliberada;
- manter seeds/casos de validação independentes dos usados para desenvolver a heurística;
- guardar a versão do conjunto usada em cada avaliação importante.

Uma alteração que melhora o conjunto de desenvolvimento mas piora o hold-out não deve ser promovida como melhoria de força.

## Arena como validação geral

A Arena fornece uma segunda camada independente porque mede partidas completas, e não apenas uma posição táctica isolada.

Uma promoção de Ares deve considerar, conforme o estágio da infraestrutura:

```text
known regressions pass
        AND
validation/hold-out não piora
        AND
Arena A/B não mostra regressão
        ↓
melhoria candidata
```

A margem simples usada atualmente é uma heurística de gate. A metodologia futura deve acrescentar incerteza estatística e teste sequencial.

## Diversidade do hold-out

O conjunto de validação deve cobrir diferentes fenómenos, e não várias versões do mesmo puzzle:

- MOVE;
- ATTACK;
- SPELL;
- SPAWN;
- STUN e consequências;
- lifespan;
- cooldown;
- TWC;
- efeitos/terreno;
- conflitos entre material e consequência táctica;
- posições defensivas;
- alternativas tácticas próximas;
- posições onde a melhor ação não é a intuição mais óbvia.

Quando possível, combinar:

```text
posições dirigidas
        +
sequências aleatórias legais
        +
posições derivadas de jogos completos
```

## Separar correção de força

Uma mudança pode ser correta e ainda assim enfraquecer a Ares.

Uma mudança pode resolver um benchmark e ainda assim ser uma regressão global.

Por isso os resultados devem ser registados separadamente:

```text
correctness
→ testes / differential / metamorphic

capability
→ tactical benchmarks

generalisation
→ hold-out

playing strength
→ Arena
```

## Regra contra benchmark overfitting

Não é aceitável justificar uma alteração com:

> “passa mais posições do benchmark”.

A afirmação mínima aceitável é:

> “passa os casos de regressão, não piora no conjunto de validação independente e não mostra regressão na Arena sob a metodologia experimental atual”.

Se a alteração for especificamente criada para corrigir um caso conhecido, isso deve ser declarado como **correção de regressão**, e não como ganho geral de força até haver evidência independente.

## Evolução futura

Antes de tornar a Ares mais agressiva no move ordering/search, completar:

1. cobertura de ação/estado persistente;
2. shrink e replay da primeira divergência;
3. perft/node-count differential;
4. conjunto de validação hold-out versionado;
5. Arena com controlo estatístico mais forte.

Só depois usar estes instrumentos para otimizar a pesquisa de forma iterativa.

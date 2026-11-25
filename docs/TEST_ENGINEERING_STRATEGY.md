# RedWar — Estratégia de Engenharia e Curadoria de Testes

**Estado:** rascunho operacional; requisitos de produto em descoberta  
**Auditoria inicial:** 2026-11-25  
**Issue governante:** [#687 — reconstruir a estratégia e a rastreabilidade](https://github.com/Siuo-Player/RedWar/issues/687)

> Este documento governa a metodologia dos testes. Não substitui os contratos de gameplay, arquitetura, Ares ou produto. Quando a intenção não estiver decidida, os testes devem registar a questão em aberto em vez de inventar uma regra.

## 1. Objetivo

A suite deve ser uma especificação executável do RedWar. Uma equipa nova deve conseguir perceber o que construir, o que significa estar correto e como medir progresso a partir de requisitos, cenários e testes — sem depender desta conversa nem de copiar a implementação atual.

Os testes têm cinco funções: especificar comportamento; impedir regressões; mostrar cobertura dos requisitos e riscos; localizar a primeira divergência; e validar também os próprios oráculos e fixtures.

Não perseguir contagem de testes, 100% de line coverage ou quantidade de workflows como objetivos autónomos.

## 2. Reconstrução de requisitos

A hierarquia de evidência existente mantém-se:

```text
comportamento + testes executáveis
          ↓
contrato canónico do domínio
          ↓
decisão histórica (ADR)
          ↓
research / hipótese / proposta
          ↓
roadmap
```

O comportamento implementado não é automaticamente o comportamento desejado: uma regra errada também pode estar implementada e coberta por um teste antigo.

Cada afirmação documental deve ser classificada como:

| Classe | Tratamento |
|---|---|
| Regra normativa | Teste bloqueante e regressão |
| Parâmetro configurável | Testar validação e limites; não congelar valor sem decisão |
| Hipótese em calibração | Experiência diagnóstica, não regra definitiva |
| Decisão de produto pendente | Não criar asserção normativa |
| Compatibilidade histórica | Testar enquanto a compatibilidade for requerida |
| Implementação acidental | Não a perpetuar como contrato |

Fontes principais: [GAME_RULES](GAME_RULES.md), [GAME_DESIGN](GAME_DESIGN.md), [HERO_SYSTEM](HERO_SYSTEM.md), [HEROES_SCHEMA](../engine/HEROES_SCHEMA.md), [heroes_config](../engine/heroes_config.json), [ARCHITECTURE](ARCHITECTURE.md), [AI_ENGINE](AI_ENGINE.md), [WEB_MULTIPLAYER](WEB_MULTIPLAYER.md), [BATTLE_UI_SIDEBAR](BATTLE_UI_SIDEBAR.md), [MECHANICS_TRACEABILITY_MATRIX](MECHANICS_TRACEABILITY_MATRIX.md), [PROJECT_REASONING](PROJECT_REASONING.md), [ROADMAP](ROADMAP.md) e [ROADMAP_2_0](ROADMAP_2_0.md).

[Documento de design legado](Documento_Design_Jogo.md) é transitional/legacy e não deve sobrepor-se aos contratos acima.

## 3. Níveis e tipos de teste

Níveis descrevem quanto do sistema é executado; tipos descrevem que propriedade se verifica. São dimensões diferentes.

| Nível | Exemplo RedWar |
|---|---|
| Unit | geometria de movimento, parser, custo |
| Component | GameState, ActionParser, RoomManager, pesquisa Ares |
| Integration | Python ↔ C++, API ↔ AuthoritativeSession |
| System / E2E | partida completa com dois browsers |
| Acceptance | instalar e jogar no Windows, jornada de produto |
| Exploratory | endgame complexo, combinações inesperadas de heróis e efeitos |

Tipos relevantes, escolhidos pelo risco:
- Specification-based: exemplos, classes de equivalência, valores-limite e tabelas de decisão.
- Invariant/contract: pré-condições, pós-condições, invariantes de estado e erros.
- Property-based e stateful/model-based: gerar entradas e sequências de ações legais.
- Metamorphic: transformar um estado e verificar relações que devem continuar verdadeiras.
- Differential/back-to-back: comparar implementações com a mesma entrada.
- Round-trip/reversibility: RWEN, import/export, make/unmake, hashes.
- Fuzzing: parsers, configuração, replay e payloads não confiáveis.
- Mutation: introduzir defeitos artificiais e verificar se os testes os detetam.
- Security/abuse, resilience/chaos, performance, accessibility, usability, visual e exploratory testing.
- Capability e competitive-strength testing da Ares são dimensões diferentes de correctness e benchmark.

## 4. Independência dos testes e dos oráculos

Cada cenário crítico deve tornar explícitos:
1. estado inicial;
2. ação;
3. precondições;
4. resultado esperado;
5. invariantes que não podem mudar;
6. fronteiras e comportamento de erro;
7. requisito de origem;
8. mecanismo de reprodução.

Formato recomendado:

```text
DADO um estado inicial válido
QUANDO ocorre uma ação
ENTÃO o resultado observável é X
E as invariantes Y e Z permanecem verdadeiras
```

Não copiar a implementação para o oracle. Quando fixture, oracle e código sob teste partilham a mesma lógica, a comparação não é independente.

O incidente [#230](https://github.com/Siuo-Player/RedWar/issues/230) demonstrou que um oracle independente também pode estar errado: a reprodução de um seed encontrou uma ação legítima de Dragoon em falta no oracle C3. Por isso, validar oráculos com exemplos normativos revistos e evidência adicional; classificar divergências como erro do produto, oracle, fixture, contrato ou adaptador.

## 5. Portefólio por subsistema

| Subsistema | Evidência principal |
|---|---|
| Regras e estado | unit/component, invariants, decision tables, boundaries |
| Heróis, movimentos e spells | matriz herói × ação × precondições; differential Python/C++ |
| Efeitos, stun, cooldown, spawn, terminal | tabelas de transição, stateful, round-trip e regressões dirigidas |
| Python ↔ C++ | ações, estado, hash, make/unmake, perft, sequências seeded |
| Ares | search correctness, terminal, TT, capability tática, benchmark e Arena A/B separados |
| Replay/RWEN/config | schema, round-trip, compatibilidade e fuzzing |
| Desktop | unit/component, smoke, jornada de utilizador, Windows acceptance |
| Web | Node para lógica local, Playwright para interação real, teclado/touch/accessibility |
| API/multiplayer | contratos HTTP/WS, autoridade do servidor, concorrência, timeout, reconnect e abuso |
| Identidade/dados | autorização, privacidade, atomicidade, persistência e falhas |
| Deploy/operação | build limpo, health, restart, rollback, observabilidade e recuperação |
| Balance Lab/Arena | schemas, seeds, provenance, holdout e estatística |

Para Ares, manter quatro afirmações separadas:
1. correctness semântica;
2. capability em cenários conhecidos sob orçamento definido;
3. eficiência medida em condições comparáveis;
4. força competitiva medida por experiências emparelhadas e análise estatística.

NPS, nodes, benchmark, training loss ou CI verde não substituem evidência de força.

## 6. Qualidade da suite

### Determinismo e isolamento
- Seeds/estados fixos nas regressões.
- Não depender da ordem entre testes nem de estado global.
- Limpar threads, sockets, subprocessos, ficheiros temporários, servidores e browser contexts.
- Injetar relógio e aleatoriedade; evitar sleeps e tempo real sempre que possível.
- Não depender de serviços externos em gates obrigatórios.

### Diagnóstico
Uma falha stateful/differential deve guardar seed, RWEN inicial, prefixo de ações, primeiro índice divergente, estado de cada backend, versão/commit e comando de reprodução.

### Granularidade e cobertura
- Uma intenção comportamental dominante por teste.
- Parametrizar famílias de casos com estrutura e intenção comuns.
- Não usar `continue` em loops de cobertura para esconder casos que nunca foram exercitados; explicitar o universo esperado e contar os casos realmente verificados.
- Não usar testes de source-code como substituto de comportamento quando seja possível exercitar a API pública. Guardrails estáticos continuam úteis para restrições arquiteturais.
- Test code tem o mesmo padrão de legibilidade e manutenção que production code.

### Flakiness
Não usar reruns como prova de correção. Registar causa, frequência, duração e responsável. Quarentena exige issue, motivo e condição de remoção. Investigar sincronização assíncrona, tempo real, sockets, sleeps, estado partilhado e dependência da ordem.

### Mutation e fuzzing
Aplicar mutation testing seletivamente a transições, legalidade, terminal, protocolos, autenticação e rollback. Fuzzing começa por RWEN, parsers, configuração, replay, payloads HTTP/WS e adaptadores. Cada crash reproduzível passa a fixture/regressão reduzida.

## 7. Gates de CI

O [routing de workflows](../.github/workflows/README.md) é autoritativo:
- Test Suite: correção funcional, regressões e contratos Python/C++.
- CodeQL: análise estática de segurança.
- AI Quality Gate: autoridade strength-sensitive da Ares.
- Windows Acceptance: aceitação do produto Windows.
- Arena, calibração, Balance Lab e treino: experiências/diagnósticos, não provas gerais de correção ou força.

Separar suites por velocidade/risco é aceitável, desde que nenhum teste crítico fique fora dos workflows autoritativos. Um gate relevante não pode ser omitido só por ser lento.

## 8. Métricas úteis

Acompanhar: requisitos críticos rastreados; riscos sem evidência; mutantes relevantes detetados/sobreviventes; cobertura de ramos em fronteiras críticas; taxa de flakiness; duração p50/p95; testes ignorados/quarentenados; bugs que escaparam e recorrência; tempo até obter reprodução mínima.

Não otimizar isoladamente: contagem de testes, line coverage, número de workflows verdes, quantidade de testes E2E ou mutation score global.

## 9. Auditoria inicial (não exaustiva)

Snapshot analisado em 2026-11-25:
- 226 ficheiros Python em `tests/`: 224 módulos `test_*.py`, mais `tests/__init__.py` e `tests/conftest.py`.
- Suite principal recente: 1 247 passed, 4 skipped; suite CPU complementar: 4 passed.
- Há cobertura relevante de invariantes de jogo, Python/C++ differential, make/unmake, perft, RWEN, Ares/Arena, replay, desktop, Web/Node, Playwright, multiplayer, API e segurança.

Achados concretos:
1. **Roster drift:** a configuração tem 30 unidades; alguns cabeçalhos/docstrings ainda dizem 24.
2. **Cobertura parcial:** `test_invariant_offensive_spells_stun_lethality` anuncia Nevada, Chain Lightning, Aimed Shot e Spectral Strike, mas o corpo só executa Nevada, Aimed Shot e Spectral Strike. Chain Lightning tem teste de execução normal noutro módulo; a condição de alvo já atordoado precisa de teste dedicado ou referência comprovada a teste equivalente.
3. **Cobertura omitível:** `test_invariant_every_hero_two_hit_stun_elimination` permite `continue` quando não encontra threat/attack; pode passar sem demonstrar todos os casos esperados.
4. **Asserção repetida:** `test_surrender_ui_contract.py` verifica duas vezes a mesma chamada. Rever outras sobreposições antes de consolidar.
5. **Lean sem evidência de CI observada:** `specs/RedWarInvariants.lean` define um modelo abstrato. Não encontrei workflow Lean no conjunto atual de Actions; as provas não demonstram por si só que o motor real satisfaz os mesmos invariantes.
6. **Rastreabilidade incompleta:** a matriz de mecânicas define uma cadeia técnica útil, mas ainda não liga cada requisito/risco a cenários, módulos de teste, fixtures, CI e evidência.

A auditoria integral dos 226 módulos está em curso na [issue #687](https://github.com/Siuo-Player/RedWar/issues/687). Estes achados não são um inventário exaustivo.

## 10. Sequência de trabalho

1. Descoberta do produto e reconciliação de contratos com respostas do responsável.
2. Inventário de todos os módulos, fixtures, imports, workflows, runtime e qualidade de diagnóstico.
3. Matriz requisito → risco → cenário → teste → gate → evidência → lacuna.
4. Corrigir lacunas P0/P1 em regras, ações, terminal, paridade, segurança, persistência e online.
5. Adicionar property/stateful, fuzzing, mutation e fault injection onde o risco justificar.
6. Completar aceitação desktop/web, acessibilidade, browsers, Windows, deploy e jornadas.
7. Atualizar requisitos e testes em cada mudança; cada bug novo deve deixar regressão permanente.

## 11. Referências

### Normas e modelos
- [ISO/IEC/IEEE 29119-1 — General concepts](https://www.iso.org/obp/ui/en/#iso:std:iso-iec-ieee:29119:-1:ed-2:v1:en): abordagem baseada em risco, níveis/tipos/técnicas, oráculos e evidência.
- [ISO/IEC/IEEE 29119-2:2021 — Test processes](https://www.iso.org/standard/79428.html).
- [ISO/IEC/IEEE 29119-4:2021 — Test techniques](https://standards.ieee.org/ieee/POSIX/7500/).
- [ISTQB CTFL](https://www.istqb.org/certifications/certified-tester-foundation-level): vocabulário e técnicas de teste estruturadas.

### Livros
- Maurício Aniche, *Effective Software Testing* (Manning, 2022): especificação, coverage, contratos, property-based, TDD e test quality.
- Steve Freeman e Nat Pryce, *Growing Object-Oriented Software, Guided by Tests* (2009): TDD como guia de desenho e evolução incremental.
- James Whittaker, Jason Arbon e Jeff Carollo, *How Google Tests Software* (2012): risco, black/white-box, exploratory, acceptance, interfaces e serviços.
- Cem Kaner, James Bach e Bret Pettichord, *Lessons Learned in Software Testing* (2001): contexto, estratégia, exploração e comunicação.

### Artigos, ferramentas e documentação
- [Martin Fowler — Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html) e [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html): equilíbrio de níveis, custo e duplicação.
- [Hypothesis — Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html) e [Hypothesis](https://hypothesis.readthedocs.io/en/latest/): geração de sequências, entradas e contraexemplos mínimos.
- Jia e Harman, [An Analysis and Survey of the Development of Mutation Testing](https://web.eecs.umich.edu/~weimerw/2024-481F/readings/mutation-testing.pdf), IEEE TSE.
- Luo et al., [An Empirical Analysis of Flaky Tests](https://mir.cs.illinois.edu/~marinov/publications/LuoETAL14FlakyTestsAnalysis.pdf).
- Lam et al., [A Study on the Lifecycle of Flaky Tests](https://www.microsoft.com/en-us/research/publication/a-study-on-the-lifecycle-of-flaky-tests/), ICSE 2020.
- [Playwright — Best practices](https://playwright.dev/docs/best-practices): comportamento observável, isolamento e auto-wait.
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html): origem, autenticação, autorização, limites, rate limiting e lifecycle.
- [WCAG 2.2](https://www.w3.org/TR/wcag/): teclado, pointer gestures, pointer cancellation e alternativa a dragging.

### Palestras e vídeos
- [James Bach — Exploratory Testing](https://www.youtube.com/watch?v=7KqvkS8y8vk).
- [James Lyndsay — There are Plenty of Ways to Manage Exploratory Testing](https://www.youtube.com/watch?v=WQnU2NkiIOw).

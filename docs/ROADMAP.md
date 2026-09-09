# RedWar — Roadmap Operacional

> Documento operacional canónico. Esta fila define a sequência principal até ao produto 1.0. O progresso é ponderado por importância real do produto; não representa ficheiros, linhas de código, número de PRs ou percentagem de funcionalidades isoladas.

## Modelo de progresso até 1.0

A evolução do RedWar passa pelas dimensões abaixo, nesta ordem operacional:

1. **Fundação** — fechar definitivamente as fronteiras de regras, estado, execução e infraestrutura que impedem evolução segura.
2. **Gameplay** — fechar a experiência de jogo local e as regras que definem uma partida RedWar.
3. **Ares** — transformar a IA num adversário/analista suficientemente forte, rápido, reproduzível e mensurável.
4. **Produto** — transformar engine + Ares numa aplicação utilizável, com UI, replays, análise e fluxos completos.
5. **Online** — tornar a experiência multiplayer autoritativa, persistente e competitiva.
6. **Release** — consolidar conteúdo, QA, segurança, licenciamento, operação e lançamento público.

A ordem é deliberada. Trabalho posterior pode avançar em paralelo quando não depender de uma decisão ainda instável, mas não pode ser usado para declarar o bloco anterior concluído sem a respectiva evidência.

### Estado de referência

**Estimativa global actual: ~38%.**

| Dimensão | Peso conceptual | Estado estimado | Regra de avanço |
|---|---:|---:|---|
| Fundação | 15% | **~70%** | fechar contratos centrais e eliminar blockers estruturais conhecidos |
| Gameplay | 20% | **~85%** | regras e experiência local suficientemente estáveis para servirem de referência |
| Ares | 20% | **~60%** | correctness primeiro, depois capability/efficiency e strength demonstrada |
| Produto | 20% | **~30%** | aplicação local, UI, replay, análise e UX integrados |
| Online | 15% | **~5%** | servidor autoritativo + multiplayer + contas/matchmaking/rating |
| Release | 10% | **~10%** | QA, conteúdo, segurança, licenciamento e distribuição pública |

As percentagens são um **baseline de produto**. Só mudam materialmente quando uma meta ponderada muda de estado. CI verde é necessária para alterações de código, mas CI verde não prova por si correctness total; benchmark não é strength; dataset maior não é automaticamente melhor IA.

---

# 1. Fundação — FECHAR A 100%

### Meta verdadeira

A fundação deve deixar de conter blockers estruturais conhecidos para a evolução do jogo e da Ares. O objectivo é que exista uma autoridade inequívoca para regras, acções, estado, transições, histórico e sessões.

A base actual já estabeleceu uma fronteira forte de execução autoritativa:

```text
input action
→ normalize canonical action
→ canonical resolution / membership
→ transition-domain validation
→ only then mutate
```

A action-space canónica deve continuar a ser coerente com `engine.legal_actions()` e com a execução, sem criar um segundo sistema de regras dentro do resolver.

### Estado actual

**~70%.** A0.1 foi efectivamente fechada nas fronteiras deliberadas: legality/execution, action-space, contratos de erro e não-mutação. A tranche independente B–G também deixou regressões importantes cobertas.

Isso não significa que toda a fundação histórica esteja matematicamente fechada. O objectivo de 100% é fechar os contratos que ainda condicionam Gameplay, Ares, replay, balanceamento e online.

### O que pertence à Fundação

- estado e transições do jogo;
- legalidade autoritativa;
- action-space;
- normalização de acções;
- contratos de erro e não-mutação;
- histórico necessário para regras de repetição;
- invariantes de serialização/replay que sejam pré-requisitos das camadas superiores;
- contratos mínimos do runtime que Ares e servidor precisam de partilhar;
- boundaries entre Python/C++ quando uma garantia depende de ambas as implementações.

### Critério de 100%

A fundação fecha quando:

1. qualquer acção executável passa pela autoridade canónica;
2. rejeições preservam o estado observável;
3. as regras de histórico/repetição têm um dono claro;
4. não existe uma segunda fonte informal de legalidade;
5. contratos usados pelo Ares, replay e servidor estão explícitos;
6. os blockers classificados como estruturais deixam de impedir o avanço de Gameplay/Ares/Produto;
7. todas as alegações correspondentes têm testes/evidência apropriados no `main`.

**Não significa congelar o código.** Significa que alterações futuras devem ser extensões justificadas por necessidades do produto.

---

# 2. Gameplay — FECHAR A 100%

### Meta verdadeira

RedWar deve ser um jogo local completo antes de se tratar a plataforma online como prioridade. O jogador tem de conseguir construir a sua composição, iniciar uma partida, executar todas as regras oficiais e terminar por uma condição de vitória válida.

A experiência 1.0 inclui, no mínimo, as regras actualmente definidas:

- tabuleiro normal 8×8;
- orçamento inicial normal de 200 pontos por cor;
- uma acção por jogador em cada turno;
- draft e posicionamento antes da partida, secretos para o adversário;
- sem compra durante a partida;
- peças configuradas sem limites artificiais de quantidade além do espaço e regras do jogo;
- peças invocáveis/temporárias fora do draft quando a regra assim determinar;
- movimento, ataque, stun, morte, spells, passivas e restantes habilidades activas suportadas pelo jogo;
- sistema sem HP/força/defesa numéricos tradicionais;
- estado de sobrevivência `Normal → Stunned → Dead`, segundo a regra de dois stuns dentro da janela de atordoamento;
- condições de vitória por eliminação, ausência de acções legais ou desistência;
- mecanismo de desempate sem depender de empates indefinidos;
- contador de turnos sem captura segundo a regra oficial actualmente definida;
- efeitos de terreno como fogo/gelo e extensibilidade para novos efeitos sem duplicar a autoridade das regras.

### Heróis

A configuração oficial permanece `engine/heroes_config.json`, com o schema em `engine/HEROES_SCHEMA.md`.

A meta não é apenas “ter muitos heróis”. É que a criação de um herói novo seja previsível e concentrada, reduzindo lógica especial espalhada pelo engine. Onde passivas especiais ainda exigem código fora da configuração, isso deve ser tratado como dívida conhecida até ser justificadamente absorvido pela arquitectura.

### Critério de fecho

- regras essenciais não estão em estado contraditório;
- todos os heróis configurados têm comportamento testável;
- efeitos e estados críticos têm casos de regressão;
- uma partida local completa pode ser jogada de início a fim;
- condições de vitória/desistência/desempate são determinísticas;
- novas regras não exigem alterações silenciosas em várias fontes de verdade.

**Depois deste gate, Ares e Produto podem tomar o gameplay como contrato estável.**

---

# 3. Ares — FECHAR CORRECTNESS, CAPABILITY E STRENGTH

### Meta verdadeira

Ares não é apenas “uma IA que faz movimentos”. É a engine de pesquisa especializada de RedWar e deve fornecer:

- adversário contra o jogador;
- níveis diferentes de força;
- análise de posições;
- análise pós-partida;
- benchmarking entre versões;
- base para Arena e eventualmente contribuições abertas.

A metodologia mantém-se inspirada no modelo Stockfish, mas adaptada ao RedWar: estado, pesquisa, avaliação, move ordering e hot path devem permanecer claramente separados.

### Ordem interna obrigatória

```text
correctness
    ↓
capability
    ↓
efficiency
    ↓
strength measurement
    ↓
default promotion
```

Não promover uma optimização porque parece mais sofisticada. Uma alteração só sobrevive como melhoria da Ares quando a evidência adequada mostra que não quebrou correctness e, quando a alegação é de força, demonstra melhoria sob condições comparáveis.

### Estado actual

**~60%.** Ares já possui avaliação clássica, caminho NNUE opcional, C++ em evolução, Arena e workflows especializados. `fast_clone()` continua deliberadamente fora do hot path C++.

O que falta é consolidar capability e eficiência de search, validar integração incremental da avaliação e produzir evidência de strength suficientemente robusta para escolhas default.

### Arena

O protocolo deve comparar:

```text
Ares base
    VS
Ares proposta
```

com condições equivalentes, cores alternadas e provenance suficiente para reproduzir a comparação. O benchmark determinístico mede custo/comportamento; a Arena mede força relativa.

Sempre que possível, resultados devem guardar:

- versão da IA;
- cores;
- resultado de cada jogo;
- tempo/nodes;
- composição das peças;
- posição inicial;
- métricas relevantes.

### NNUE

NNUE permanece experimental até existir demonstração de ganho real por CPU-segundo nas condições definidas. O caminho incremental deve provar equivalência com o oracle `sync_board()` antes de ser tratado como autoridade.

### Critérios de fecho

- correctness coberta pelos contratos do engine;
- search capability validada em posições/fixtures relevantes;
- optimizações comparadas em benchmark controlado;
- qualquer alegação de strength apoiada por Arena A/B e não por benchmark isolado;
- NNUE incremental demonstrada equivalente ao oracle e avaliada por força/custo;
- a escolha default da Ares é suportada por evidência, não por preferência de implementação.

---

# 4. Produto — TRANSFORMAR ENGINE + ARES NUM JOGO COMPLETO

### Meta verdadeira

O jogador deve poder usar RedWar sem conhecer `engine/`, scripts, fixtures ou detalhes do Ares.

O objectivo de produto local é:

```text
abrir
→ escolher modo / bot
→ construir ou carregar composição
→ jogar
→ receber feedback claro
→ rever partida
→ analisar posição/decisão
→ guardar histórico
→ voltar a jogar
```

### 4.1 Battle UI e interacção

A UI deve seguir a arquitectura já definida para a Battle UI:

- herói seleccionado persiste mesmo quando o hover muda;
- célula sob hover tem informação própria;
- regras completas do herói aparecem através da fonte canónica da Enciclopédia, não de texto duplicado;
- Action Choice permanece na sidebar, não em modal fullscreen;
- 1–9 seleccionam acções quando aplicável e `Esc` cancela;
- quando existem várias acções legais (por exemplo MOVE/ATTACK/NEVADA), a UI torna essa escolha explícita;
- destino inválido não muda silenciosamente de herói;
- estados de interacção incluem IDLE/SELECTED/HOVER/ACTION e as transições relevantes;
- layouts suportam 4:3, 16:9, 16:10 e 21:9, de 720p a 4K;
- FrostMage permanece um stress test visual;
- cores semânticas não podem ser o único canal de informação;
- efeitos, partículas e ícones têm função informativa além de ornamentação.

### 4.2 Replay e telemetria

Replays devem representar partidas reproduzíveis e não apenas screenshots/eventos incompletos. Telemetria deve preservar informação suficiente para análise sem criar dependências artificiais entre sistemas.

### 4.3 Análise e histórico

A aplicação deve permitir ao jogador consultar uma partida terminada e, progressivamente, analisar posições e decisões. O histórico precisa de um formato estável para posterior integração com contas/online.

### Critério de fecho

- UI de batalha completa e responsiva;
- regras apresentadas de forma coerente com a fonte canónica;
- jogo local contra Ares utilizável;
- replay reproduzível;
- histórico guardável e reaberto;
- análise pós-partida funcional dentro do escopo 1.0;
- menus/definições e fluxos principais deixam de depender de tooling de desenvolvimento.

---

# 5. Online — CONSTRUIR O ECOSSISTEMA MULTIPLAYER

### Meta verdadeira

O online não é simplesmente “ligar dois clientes”. Deve existir um servidor autoritativo que impede um cliente de declarar directamente um estado impossível.

O produto final pretende incluir:

- partidas públicas;
- partidas privadas/por convite ou link;
- 1v1;
- matchmaking;
- contas;
- login Google quando tecnicamente/operacionalmente adequado;
- ELO/MMR associado ao matchmaking;
- vários controlos de tempo inspirados em Chess.com;
- reconnect;
- derrota por abandono/timeout;
- rematch;
- espectadores;
- histórico online;
- ranking.

### Arquitectura desejada

```text
cliente
   ↓ acção
servidor autoritativo
   ↓ validação
estado oficial
   ↓ broadcast
outros clientes
```

O servidor deve validar as acções recebidas contra as regras oficiais. O cliente pode apresentar previsões/UX, mas não é a autoridade final.

### Ordem interna

```text
server session
→ authoritative action validation
→ 1v1 live match
→ reconnect / timeout / resignation
→ persistence
→ matchmaking
→ rating
→ spectators / rematch / public history
```

### Critério de fecho

- dois clientes conseguem completar uma partida real;
- o servidor é autoritativo sobre estado e legalidade;
- desconexões não corrompem a partida;
- tempo/abandono são determinados no servidor;
- histórico online é consistente com o replay;
- matchmaking não permite estados incompatíveis;
- rating é calculado a partir dos resultados oficiais;
- segurança e abuso têm uma superfície minimamente tratada antes de abertura pública.

---

# 6. Release — 1.0 PÚBLICO

### Meta verdadeira

RedWar 1.0 é o momento em que o jogo deixa de ser apenas um repositório de engine + investigação e passa a ser um produto que terceiros conseguem utilizar de forma suportada.

### Conteúdo e qualidade

Antes do release devem estar estabilizados:

- regras oficiais;
- catálogo de heróis e respectivas descrições;
- balanceamento dentro do escopo decidido;
- Ares default suportada por evidência;
- Arena e datasets reproduzíveis;
- replays;
- UI;
- efeitos/áudio;
- documentação;
- licenças e atribuições de assets/código/conteúdo externo.

### Release engineering

- builds reproduzíveis;
- testes de regressão;
- smoke tests de instalação e execução;
- validação de caminhos offline e online relevantes;
- segurança mínima do cliente/servidor;
- observabilidade e logs suficientes para incidentes;
- estratégia de compatibilidade de replay/estado;
- versão claramente identificada.

### Critério de fecho

Só declarar 1.0 quando:

```text
rules stable
→ gameplay complete
→ Ares accepted
→ local product complete
→ online functional
→ history/replay reliable
→ QA/release gates green
→ licensing/security reviewed
→ public release
```

---

# Ordem operacional definitiva

```text
1. Fundação   [~70%] → FECHAR 100%
        ↓
2. Gameplay   [~85%] → FECHAR 100%
        ↓
3. Ares       [~60%] → CORRECTNESS → CAPABILITY → STRENGTH
        ↓
4. Produto    [~30%] → UI + REPLAY + ANÁLISE + UX
        ↓
5. Online     [~5%]  → SERVIDOR → MULTIPLAYER → ECOSSISTEMA
        ↓
6. Release    [~10%] → QA + SEGURANÇA + LICENÇAS + LANÇAMENTO
```

### Paralelismo permitido

UI/replay podem avançar enquanto Ares ou Gameplay fecham, desde que usem contratos já definidos e não criem uma implementação paralela das regras. Tooling da Arena pode evoluir antes de Ares estar finalizada, mas não deve ser tratado como prova de strength. Infraestrutura inicial de servidor pode existir antes do multiplayer completo, mas o gate online só fecha com partidas reais e servidor autoritativo.

### Regra de percentagem

A percentagem de uma dimensão sobe quando uma **meta de produto ponderada** passa de protótipo/infraestrutura para implementação testada, validada e utilizável. Um refactor isolado ou uma pequena feature interna pode aumentar qualidade sem aumentar materialmente o global.

### Regra de evidência

Toda PR deve declarar:

1. fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese/correcção;
4. evidência esperada;
5. critério de saída;
6. documentos canónicos actualizados no mesmo pacote.

Nenhuma alegação de força, balanceamento, equivalência, segurança ou qualidade de produto deve ser inferida apenas porque “o código funciona” ou porque CI ficou verde.

# Framework de Testes de Força e Evolução do Ares AI (Inspirado no Stockfish & Fishtest)

> **Autor**: Equipe de Engenharia RedWar 2.0  
> **Referência Metodológica**: Adaptação dos princípios do Stockfish / Fishtest (SPRT de Wald, Bradley-Terry, testes pareados por inversão de cor e intervalos de confiança de 95%) às regras do RedWar.

---

## 1. Visão Geral e Filosofia: O Princípio Stockfish

No desenvolvimento de motores de estratégia de ponta (como o **Stockfish** no xadrez), **nenhuma alteração é aceite por intuição humana, estética de código ou autoridade de quem programa**. Todo o avanço é governado pelo método científico rigoroso:

```
[Observação de Fraqueza] 
         │
         ▼
[Formulação da Hipótese H₁] ──► "Adicionar X resolve a fraqueza Y e gera ΔElo > 0"
         │
         ▼
[Implementação do Candidato (Challenger)]
         │
         ▼
[Duelo Pareado vs Baseline Champion] (Aberturas idênticas com inversão de cores)
         │
         ▼
[Análise Estatística de Elo & SPRT]
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
[H₁ Aceite (ΔElo > 0)]      [H₀ Aceite (ΔElo ≤ 0)]
    │                               │
    ▼                               ▼
⭐ PROMOÇÃO A NOVO CAMPEÃO     ❌ REJEIÇÃO DA HIPÓTESE
(Baseline Atualizado)       (Código descartado / hipótese refutada)
```

Este ciclo contínuo garante duas propriedades inegociáveis:
1. **Garantia Estocástica de Evolução**: O motor melhora consistentemente versão após versão.
2. **Prevenção Absoluta de Involução**: Ideias que parecem boas teoricamente mas que em jogo real introduzem pontos cegos táticos são sumariamente rejeitadas pelas estatísticas de confronto.

---

## 2. Adaptação Matemática: Do Xadrez para o RedWar

Embora inspirado no Stockfish, o framework do Ares adapta as fórmulas fundamentais às particularidades matemáticas do **RedWar**:

### 2.1 Ausência de Empates: Do Modelo Pentanomial para o Bradley-Terry Binário
No xadrez entre motores de topo, 60% a 80% das partidas terminam em empate, exigindo modelos estatísticos pentanomiais ($WW, WD, DD, LD, LL$).

No **RedWar**, a mecânica de combate é visceral e decisiva:
- A regra de **2 golpes para morte em stun** ("um segundo enquanto atordoado mata") acelera a letalidade.
- Não existem finais de empate por material insuficiente nem afogamento (*stalemate*).
- O desfecho de cada partida é puramente **binário** ($W \in \{1, 0\}$).

Portanto, o modelo primário de força é o **Modelo Bradley-Terry Binário**:
A probabilidade de o Candidato ($A$) vencer o Baseline ($B$) dada a diferença de Elo ($\Delta \text{Elo} = \text{Elo}_A - \text{Elo}_B$) é:
$$P(A \text{ vence}) = \frac{1}{1 + 10^{-\Delta \text{Elo} / 400}}$$

Invertendo a equação para obter o ganho empírico de Elo a partir da pontuação obtida ($S = \frac{W_A}{W_A + W_B}$):
$$\Delta \text{Elo} = -400 \cdot \log_{10} \left( \frac{1}{S} - 1 \right)$$

---

## 3. Protocolo de Duelos Pareados com Inversão de Cores (*Mirror Pairs*)

Para eliminar o viés da primeira jogada (vantagem das Brancas):
1. Cada partida é jogada em **pares de espelho** a partir de uma semente de abertura $Seed_k$:
   - **Partida 1**: Candidato joga de **Brancas** vs Baseline de **Pretas**.
   - **Partida 2**: Baseline joga de **Brancas** vs Candidato de **Pretas**.
2. Desta forma, qualquer assimetria de tabuleiro ou da semente de abertura afeta igualmente ambos os motores.

---

## 4. Intervalos de Confiança a 95% e Margem de Erro

Para evitar falsos positivos resultantes de variância amostral, o ganho de Elo é sempre reportado com a sua **Margem de Erro a 95%** ($1.96 \cdot SE$):

Para $N$ partidas binárias com taxa de vitória $S$:
$$SE(S) = \sqrt{\frac{S(1 - S)}{N}}$$

Aplicando a derivada de $\Delta \text{Elo}$ em relação a $S$:
$$\frac{d(\Delta \text{Elo})}{dS} = \frac{400}{\ln(10) \cdot S(1 - S)}$$

A margem de erro a 95% em pontos de Elo é:
$$\text{Margem}_{95\%}(\Delta \text{Elo}) = 1.96 \cdot \frac{400}{\ln(10) \cdot \sqrt{N \cdot S(1 - S)}}$$

O Intervalo de Confiança é:
$$CI_{95\%} = \left[ \Delta \text{Elo} - \text{Margem}, \; \Delta \text{Elo} + \text{Margem} \right]$$

---

## 5. Teste de Razão de Probabilidade Sequencial (Wald's SPRT)

Para não desperdiçar computação em melhorias óbvias ou regressões evidentes, o Ares utiliza o **SPRT de Wald** com paragem precoce (*early stopping*):

### 5.1 Hipóteses
- **$H_0$ (Hipótese Nula / Regressão)**: $\Delta \text{Elo} \le \text{elo}_0$ (ex: $0.0$ Elo).
- **$H_1$ (Hipótese Alternativa / Ganho Alvo)**: $\Delta \text{Elo} \ge \text{elo}_1$ (ex: $+5.0$ Elo).
- Parâmetros de erro: $\alpha = 0.05$ (taxa de falso positivo), $\beta = 0.05$ (taxa de falso negativo).

### 5.2 Limites de Wald
$$A = \ln \left( \frac{1 - \beta}{\alpha} \right) = \ln \left( \frac{0.95}{0.05} \right) = \ln(19) \approx +2.944$$
$$B = \ln \left( \frac{\beta}{1 - \alpha} \right) = \ln \left( \frac{0.05}{0.95} \right) = \ln(1/19) \approx -2.944$$

### 5.3 Razão de Log-Verossimilhança (*Log-Likelihood Ratio - LLR*)
A cada partida pareada com desfecho $x_i \in \{1, 0\}$, atualiza-se o $LLR$:
$$LLR = \sum_{i=1}^N \ln \left( \frac{P(x_i \mid H_1)}{P(x_i \mid H_0)} \right)$$

- Se $LLR \ge A$: **$H_1$ Aceite** $\rightarrow$ Melhoria comprovada com 95% de confiança estatística. **Candidato promovido a Campeão**.
- Se $LLR \le B$: **$H_0$ Aceite** $\rightarrow$ Falha em provar superioridade. **Candidato rejeitado**.
- Se $B < LLR < A$: **Continuar Duelo** $\rightarrow$ Dados insuficientes para decisão.

---

## 6. Governação e Ciclo de Vida de Hipóteses no Ares

Toda a alteração submetida ao Ares deve ser documentada sob a seguinte estrutura:

```markdown
### Registo de Hipótese Ares
- **ID da Hipótese**: H-YYYYMMDD-01
- **Gargalo Observado**: "O Ares demorava a punir peças atordoadas a mais de 3 casas de distância."
- **Solução Proposta**: "Priorização de MVV-LVA e extensão de Quiescence para feitiços letais."
- **Configuração do Teste**: Candidato vs Baseline, 100 partidas pareadas, orçamentos idênticos de nós.
- **Resultado Estatístico**: Score: 62.5%, ΔElo: +89.2 ± 38.4, SPRT: H1 Aceite (LLR: +3.12 > 2.94).
- **Decisão**: PROMOVIDO A NOVO CAMPEÃO.
```

Com este protocolo rigoroso, o Ares AI desenvolve-se como um motor de classe mundial, onde cada linha de código acrescentada é empiricamente validada contra o melhor modelo existente.


---

## 7. A Ciência Estatística de Sigmas: 3-Sigma ($3\\sigma$) vs 5-Sigma ($5\\sigma$) vs Intervalos de Confiança

Uma questão central na ciência de avaliação de motores é: **devemos utilizar intervalos de confiança convencionais (ex: 95%) ou conceitos de significância da física como 3-Sigma ($3\\sigma$) ou 5-Sigma ($5\\sigma$)?**

### 7.1 Equivalência Matemática Formal
No modelo normal assintótico (pelo Teorema do Limite Central aplicado a partidas de duelos), **Intervalos de Confiança e níveis de Sigma são a exata mesma formulação matemática sob notações diferentes**:

$$\text{CI}_{1-\alpha} = \hat{\mu} \pm Z \cdot \text{SE}$$

Onde o multiplicador $Z$ corresponde ao número exato de desvios-padrão (sigmas, $\sigma$):

| Nível de Confiança | Quantil $Z$ ($\sigma$) | P-Value bicaudal ($\alpha$) | Falso Positivo Unicaudal | Multiplicador de Partidas $(Z/1.96)^2$ | Contexto Científico Típico |
|---|---|---|---|---|---|
| **95.00%** | **$1.96\\sigma$** | $0.0500$ (5.0%) | $2.50\%$ | **$1.00\\times$** (Base) | Padrão acadêmico, triagem rápida (SPRT) |
| **99.00%** | **$2.58\\sigma$** | $0.0100$ (1.0%) | $0.50\%$ | **$1.73\\times$** | Testes farmacêuticos rigorosos |
| **99.73%** | **$3.00\\sigma$** | **$0.0027$ (0.27%)** | **$0.135\%$ (1 em 740)** | **$2.34\\times$** | **Engenharia Six Sigma & Portão de Campeão Ares** |
| **99.99994%** | **$5.00\\sigma$** | $0.0000006$ ($6 \times 10^{-7}$) | $0.00003\%$ (1 em 3.5M) | **$6.51\\times$** | Física de Altas Energias (Descoberta do Higgs no CERN) |

---

### 7.2 Por que 5-Sigma ($5\\sigma$) é Inadequado e Prejudicial para Motores de Jogo

Exigir $5\\sigma$ em testes de motores de estratégia é um erro metodológico comum devido a dois fatores críticos:

1. **Explosão Amostral Quadrática**:
   $$N \propto \left( \frac{Z}{\Delta \text{Elo}} \right)^2 \implies \left( \frac{5.0}{1.96} \right)^2 \approx 6.51$$
   Para detectar um ganho real de $+5$ Elo com $5\\sigma$, são necessárias **$6.5\times$ mais partidas** do que com 95% de confiança. Se um teste em 95% requer 4.000 partidas, em $5\\sigma$ exigiria mais de **26.000 partidas por candidato**.

2. **O Contexto do *Look-Elsewhere Effect***:
   No CERN/LHC, o limiar de $5\\sigma$ é indispensável porque os aceleradores varrem milhões de canais energéticos simultaneamente através de petabytes de colisões. Se usassem $2\\sigma$ ou $3\\sigma$, a flutuação estatística produziria centenas de partículas falsas todos os anos.
   Em motores de jogo (como Ares e Stockfish), não varremos canais cegos: testamos uma hipótese atómica de cada vez contra um campeão conhecido.

3. **Assimetria Crítica do Erro Tipo II (Risco de Estagnação)**:
   Na física, anunciar uma partícula inexistente é uma catástrofe irremediável. Mas no desenvolvimento de motores, descartar uma melhoria real de $+3$ Elo porque atingiu "apenas" $3.2\\sigma$ em vez de $5.0\\sigma$ é fatal: a evolução dos motores depende da acumulação sucessiva de dezenas de pequenos ganhos de $+1$ a $+4$ Elo. Exigir $5\\sigma$ paralisa a evolução do motor.

---

### 7.3 Por que 3-Sigma ($3\\sigma$) é a Barreira Ótima de Promoção (*Champion Gate*)

O padrão **3-Sigma ($3\\sigma$, 99.73% de confiança, $p < 0.0027$)** é o ponto ideal absoluto para governança anti-involução:
- **Redução drástica de falsos positivos**: A taxa de falso positivo cai de $5\%$ (no $1.96\\sigma$) para **$0.135\%$** (menos de 1 chance em 740).
- **Custo computacional viável**: Exige apenas $2.34\\times$ o número de partidas de um teste de 95%, plenamente executável em pipelines automatizados de CI/CD.
- **Garantia Anti-Involução Inegociável**: Se um motor candidato apresentar $\Delta \text{Elo} - 3.0 \cdot SE > 0$, a probabilidade de ser uma regressão é infinitesimal.

---

### 7.4 Arquitetura Canónica de Três Níveis de Amostragem do Ares AI

Para evitar conclusões precipitadas e proteger a integridade dos dados competitivos, o desenvolvimento do Ares AI rege-se por uma hierarquia estrita de três níveis amostrais:

1. **Tier 0 — Screening Rápido Exploratório (8 a 16 partidas / 4 a 8 pares espelhados)**:
   - **Objetivo**: Triagem rápida e de baixo custo de hipóteses para descartar falhas graves de implementação, comportamentos anómalos ou regressões óbvias antes de comprometer tempo de máquina extensivo.
   - **Estatuto Epistémico**: Os números obtidos nesta fase são formalmente designados como **"Tendências de Screening Exploratório"** ($\Delta \text{Elo}_{\text{screened}}$).
   - **Margem de Erro**: Devido ao reduzido tamanho amostral ($N=8$ a $16$), a margem de erro a 95% é tipicamente de $\pm 80$ a $\pm 250\text{ Elo}$.
   - **Regra de Rigor**: **É expressamente vedado declarar "Elo comprovado em produção" a partir de duelos de Tier 0**. O valor indica apenas viabilidade para avanço na pesquisa.

2. **Tier 1 — Validação Intermédia e SPRT Experimental (20 a 99 partidas pareadas)**:
   - Utiliza SPRT de Wald com $\alpha = 0.05, \beta = 0.05$.
   - Permite rejeição precoce (*early stopping*) de candidatos inferiores ou aceitação preliminar de melhorias substanciais.

3. **Tier 2 — Bateria Amostral Ampla / Portão de Campeão de Produção (100+ partidas pareadas com critério $3\sigma$)**:
   - Para que um candidato substitua formalmente o motor campeão em produção e receba a designação oficial de **"Elo Comprovado em Produção"**, o limite inferior de $3\sigma$ deve ser estritamente positivo:
     $$\text{CI}_{3\sigma}^{\text{lower}} = \Delta \text{Elo} - 3.0 \cdot SE > 0$$
   - Esta barreira Six Sigma garante que a probabilidade de aceitar uma regressão como evolução seja inferior a $0.14\%$ ($p < 0.0027$).

---

### 7.5 Norma Ética de Comunicação de Resultados Competitivos
Nenhuma alteração, Pull Request ou nota de lançamento pode anunciar ganhos numéricos de Elo como definitivos sem explicitar o Tier de Amostragem e o respectivo Intervalo de Confiança. Resultados de screening (8 partidas) devem ser explicitamente rotulados com a anotação:
`[Tier 0 — Screening Rápido Exploratório (ΔElo_screened = +X.X ± Y.Y, N=8 partidas). Elo comprovado reservado para baterias de alto volume amostral.]`

---
## 8. Mapeamento Teórico dos Componentes do Ares 2.0 vs Motores de Elite

| Componente Ares 2.0 | Inspiração Teórica (Stockfish/Leela) | Implementação no RedWar | Impacto Prático Comprovado |
|---|---|---|---|
| **Dynamic Aspiration Windows** | Stockfish Aspiration Search | Janela inicial $\delta = 75.0$ (calibrada ao valor de peças do RedWar), com expansão geométrica $\times 1.75$ antes do fallback pleno. | Reduz nós explorados em 15-25% em posições estáveis sem perder variantes táticas. |
| **Adaptive Null-Move Pruning (NMP)** | Donninger / Stockfish Adaptive NMP | Redução adaptativa $R = 3$ para profundidades $\ge 6$ e $R = 2$ para prof. 3..5, com salvaguarda estrita anti-zugzwang de stun (bloqueia NMP se algum aliado estiver atordoado). | Poda ramos silenciosos sem sofrer o bug de passar a vez quando uma peça aliada corre risco de morte imediata. |
| **Late Move Reductions (LMR)** | Ethereal / Berserk / Stockfish LMR | Redução $R = 1..2$ em lances calmos tardios ($\ge 3$), com imunidade total para Killer Moves e lances com pontuação de histórico $\ge 3000$. | Foca o orçamento de busca nos lances mais perigosos, acelerando cortes beta. |
| **Stockfish Gravity Aging** | Modern History Tables Gravity | $H[k] \leftarrow H[k] + \Delta - \frac{H[k] \cdot \|\Delta\|}{16384}$ para amortecimento contínuo de lances antigos. | Evita saturação histórica em finais e partidas longas. |
| **MVV-LVA Stun-Lethality** | Most Valuable Victim - Least Valuable Attacker | Priorização máxima ($350.000$) para ataques que desferem o 2º golpe em peças atordoadas (morte permanente imediata). | Elimina o efeito horizonte tático em trocas letais. |
| **Gradiente de Distância de 2-Stun** | Avaliação Específica de Domínio | Peso de letalidade escala suavemente com a distância Chebyshev: dist=1 $\to 64\%$, dist=2 $\to 43\%$, dist=3 $\to 25\%$ do custo da unidade. | Corrige o ponto cego onde o motor avaliava ameaças distantes com o mesmo peso de execuções imediatas adjacentes. |
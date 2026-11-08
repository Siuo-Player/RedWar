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

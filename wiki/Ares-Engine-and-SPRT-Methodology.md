# 🤖 Motor Ares AI & Metodologia de Validação SPRT

Inspirado diretamente na metodologia de desenvolvimento do **Stockfish** (o motor de xadrez mais forte do mundo), o motor de inteligência artificial **Ares** é governado por regras estatísticas estritas de promoção: **nenhuma alteração é aceita sem prova matemática de melhoria de força de jogo**.

---

## 🔬 Metodologia SPRT (Sequential Probability Ratio Test)

O framework de testes do Ares (`ai/sprt.py` e `.github/workflows/ares_sprt.yml`) implementa o teste sequencial de Wald:

- **Hipótese Nula ($H_0$)**: $\Delta \text{Elo} \le 0.0$ (a nova versão é igual ou pior que a versão estável).
- **Hipótese Alternativa ($H_1$)**: $\Delta \text{Elo} \ge 5.0$ (a nova versão demonstra melhoria estatisticamente significativa de pelo menos 5 pontos de Elo).
- **Parâmetros de Confiança**: $\alpha = 0.05$ (risco de falso positivo de 5%), $\beta = 0.05$ (risco de falso negativo de 5%).
- **Limites de Decisão**:
  $$A = \ln\left(\frac{1 - \beta}{\alpha}\right) \approx 2.944$$
  $$B = \ln\left(\frac{\beta}{1 - \alpha}\right) \approx -2.944$$

Quando o **Log-Likelihood Ratio (LLR)** acumulado ultrapassa $A$, a hipótese $H_1$ é aceita com $95\%$ de confiança (Pull Request Aprovado). Se o LLR cair abaixo de $B$, a alteração é sumariamente rejeitada por regressão.

---

## 🎯 Perfis de IA Especializados por Modo de Jogo (`ai/profiles.py`)

Dado que diferentes modos de jogo possuem tabuleiros, orçamentos e regras distintas, o Ares dispõe de **versões de avaliação especializadas**:

1. **`StandardAresProfile` (Modo 8×8)**:
   - Focado em tempo de abertura, domínio das 16 casas centrais e conversão rápida de stuns.
2. **`GrandAresProfile` (Modo 10×10)**:
   - Ajustado para distâncias maiores, bónus de avanço territorial profundo e sincronização de flancos.
3. **`DraftAresProfile` (Tournament Snake Draft)**:
   - Avalia sinergias entre heróis (ex.: FrostMage + Dragoon para stun e abate; Paladin + Stormcaller para bloqueio e retaguarda).
4. **`HazardAresProfile` (Hazard Arena)**:
   - Ponderação ativa de perigos ambientais: penalização severa para posições adjacentes a lava e bónus para controlo de fontes sagradas de cura.

---

## ⚡ Heurísticas de Pesquisa de Alta Eficiência

- **Tabela de Killer Moves (2 slots por ply)**: Memoriza os dois melhores lances calmos que geraram cortes $\beta$ na mesma profundidade.
- **History Heuristic Quadrática**: Bonifica jogadas calmas efetivas em função de $depth^2$, antecipando a poda da árvore de busca.
- **Dynamic Time Manager**: Aloca orçamentos de nós e milissegundos com base no tempo de relógio restante e na tensão tática do tabuleiro.

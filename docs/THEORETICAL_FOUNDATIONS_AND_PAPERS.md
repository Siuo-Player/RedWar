# 📚 Fundações Teóricas, Literatura e Modelos de IA & Game Design

> Este documento estabelece o cânone teórico do **RedWar**, documentando os artigos académicos (papers), tratados de teoria dos jogos, arquiteturas de IA e literatura de game design que informam o desenvolvimento do motor **Ares** e o balanceamento dos heróis.

---

## 1. Pesquisa em Árvore de Jogos & Motores Competitivos

### 1.1 Minimax, Poda Alpha-Beta & Heurísticas de Pesquisa
- **Shannon, C. E. (1950)**. *Programming a Computer for Playing Chess*. Philosophical Magazine, Ser.7, Vol. 41, No. 314.
  - *Aplicação no RedWar*: Diferenciação fundamental entre estratégias Tipo A (busca em largura com força bruta) e Tipo B (busca seletiva guiada por quiescência e poda heurística). O Ares é rigorosamente um motor Tipo B.
- **Knuth, D. E., & Moore, R. W. (1975)**. *An Analysis of Alpha-Beta Pruning*. Artificial Intelligence, 6(4), 293-326.
  - *Aplicação no RedWar*: Prova matemática de que com ordenação ótima de lances ($O(b^{d/2})$), a árvore de pesquisa efetiva dobra de profundidade em relação à busca ingénua ($O(b^d)$). Justifica a prioridade máxima dada ao Move Ordering (MVV-LVA, Killer Moves, History Heuristic).
- **Schaeffer, J. (1989)**. *Conspiracy Numbers*. Artificial Intelligence, 43(1), 67-84.
  - *Aplicação no RedWar*: Identificação da instabilidade tática da posição (número de folhas necessárias para alterar a pontuação de raiz), utilizada para disparar extensões de busca em posições críticas com unidades atordoadas.
- **Romstad, T., Costalba, M., Kiiski, T. et al. (Stockfish Engine)**:
  - *Late Move Reductions (LMR)*: Redução de profundidade para lances calmos de baixa prioridade ordenados tarde na lista.
  - *Null Move Pruning (NMP)*: Verificação se passar a vez ainda mantém corte $\beta$ (com salvaguardas em posições de zugzwang).
  - *Transposition Tables (Zobrist Hashing)*: Reutilização de estados visitados por caminhos transpostos.

### 1.2 MCTS & Redes Neuronais Profundas (AlphaZero / MuZero)
- **Coulom, R. (2006)**. *Efficient Selectivity and Backup Operators in Monte-Carlo Tree Search*. Computers and Games (CG 2006).
- **Silver, D. et al. (2017)**. *Mastering Chess and Shogi by Self-Play with a General Reinforcement Learning Algorithm (AlphaZero)*. Science, 362(6419), 1140-1144.
  - *Aplicação no RedWar*: Comparação direta com o Minimax. Enquanto o Alpha-Beta é imbatível em táticas de horizonte forçado (ex.: stuns e mortes forçadas em 2-3 turnos), o MCTS com redes de política é a arquitetura ideal para a **fase de Draft**, onde a avaliação de combinações de exércitos tem características holísticas e não puramente sequenciais.
- **Berner, C. et al. / OpenAI (2019)**. *Dota 2 with Large Scale Deep Reinforcement Learning (OpenAI Five)*. arXiv:1912.06680.
  - *Aplicação no RedWar*: Modelação de coordenação de equipa entre heróis com papéis assimétricos e valorização de controlo de grupo (Crowd Control / CC chaining) em combates de múltiplos agentes.

---

## 2. Metodologia Estatística de Validação & Calibração

### 2.1 Teste Sequencial de Wald (SPRT)
- **Wald, A. (1945)**. *Sequential Tests of Statistical Hypotheses*. The Annals of Mathematical Statistics, 16(2), 117-186.
  - *Implementação no RedWar (`ai/sprt.py`)*: Teste de razão de verosimilhança logarítmica (LLR) contínuo. Permite decidir com o número mínimo ótimo de partidas se uma alteração proposta é superior com 95% de certeza estatística, eliminando o viés humano de aceitar "melhorias cosméticas".

### 2.2 Sistemas de Rating & Calibração de Parâmetros
- **Elo, A. E. (1978)**. *The Rating of Chessplayers, Past and Present*. Arco Publishing.
- **Spall, J. C. (1998)**. *Implementation of the Simultaneous Perturbation Algorithm for Stochastic Optimization (SPSA)*. IEEE Trans. Aerospace and Electronic Systems, 34(3), 817-823.
  - *Aplicação no RedWar*: Ajuste automático de pesos de avaliação (custo de peças, mobilidade, proximidade a terrenos) perturbando todos os parâmetros simultaneamente em dois testes por iteração, escalando eficientemente em espaços de alta dimensão.

---

## 3. Teoria de Game Design, Balanceamento e Sinergias Emergentes

### 3.1 Princípio da Curva Fácil de Aprender, Difícil de Dominar (Lei de Bushnell)
- **Bushnell, N. (1972)**. *Nolan's Law of Video Game Design*.
  - *"All the best games are easy to learn and difficult to master."*
  - *Aplicação no RedWar*: As regras essenciais são universais e imediatas: sem HP ou fórmulas de dano arcanas; 1 ação por turno; 1º stun atordoa, 2º stun elimina. A profundidade resulta da geometria de movimento, gestão de espaço e sinergias táticas entre heróis.

### 3.2 Teoria de Sinergias Não-Aritméticas (Mecânica sobre Números)
- **Schell, J. (2019)**. *The Art of Game Design: A Book of Lenses* (3rd ed.). CRC Press.
  - *Lente do Espaço Tático*: A forma e limites da grelha determinam a utilidade das peças.
  - *Lente da Emergência*: Sinergias devem surgir das regras fundamentais e não de modificadores arbitrários ("+10% dano").
- **Sirlin, D. (2005)**. *Playing to Win: Becoming the Champion*.
  - *Dinâmica Intransitiva (Pedra-Papel-Tesoura)*: Evita a existência de uma "estratégia dominante" (Dominant Strategy Solved State). Cada arquétipo tem um contra-ataque natural:
    - Tanques (Vanguarda) bloqueiam Assassinos (Flanqueadores);
    - Artilharia fustiga Tanques à distância;
    - Assassinos contornam a linha e eliminam a Artilharia;
    - Controladores anulam habilidades chave através de Silenciamento e Atordoamento.
- **Garfield, R. (1993/2000)**. *Characteristics of Games* & *Tempo/Mana Curve Theory*.
  - *Aplicação no RedWar*: O orçamento de 200 pontos (8×8) ou 300 pontos (10×10) funciona como um balanço rígido de custo de oportunidade. Peças de alto custo (ex.: Stormcaller a 72 pts) exigem proteção e retorno de tempo imediato; peões (Bone a 10 pts) funcionam como amortecedores de tempo e controlo de casas.
- **Subset Games (2018)**. *Into the Breach Design Architecture*.
  - *Mecânicas de Deslocamento*: O valor do empurrão (Knockback) não está no dano direto, mas na colisão forçada contra terrenos letais (Lava) ou obstáculos (Barreiras Mágicas).

---

## 4. Comparativo de Paradigmas de IA Aplicados ao RedWar

| Paradigma | Pontos Fortes no RedWar | Fragilidades / Limitações | Como o Ares 2.0 Resolve |
|---|---|---|---|
| **Stockfish Alpha-Beta Puro** | Cálculo ultra-rápido de linhas de tática forçada em profundidade ($>10^6$ nps em C++). | Cego para mecânica de 2 vidas se a avaliação só contar peças mortas; ignora terrenos dinâmicos. | **Avaliação Adaptada**: Ponderação do horizonte de 2 stuns, bónus de confinamento de alvos atordoados e raycasting de perigos ambientais. |
| **MCTS (AlphaZero)** | Avaliação intuitiva de padrões posicionais globais sem necessidade de funções manuais. | Lento para responder a ameaças táticas agudas em tempo real no browser; exige redes pesadas. | **Uso Especializado**: MCTS reservado para a fase de Draft e formulações de abertura; Alpha-Beta rápido no combate em tabuleiro. |
| **Reinforcement Learning Multi-Agente (OpenAI Five)** | Modelação natural de papéis de equipa e coordenação entre heróis assimétricos. | Requer milhares de horas de GPU para treino distribuído; caixa-preta difícil de depurar. | **Matriz de Arquétipos (`engine/hero_matrix.py`)**: Sinergias mecânicas formais (Silêncio + AoE, Deslocamento + Lava, Condução de Raio). |

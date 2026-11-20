# Modelos Matemáticos e Técnicas de Análise de Dados para Balanceamento e Posicionamento em Jogos Competitivos

> **Autor**: Equipe de Engenharia RedWar 2.0  
> **Referência Técnica**: Aplicação de frameworks de análise competitiva (Riot Games LoL, Teamfight Tactics, Magic: The Gathering e Opta Sports) ao RedWar.

---

## 1. Introdução: O Desafio do Balanceamento em Sistemas de Alta Dimensionalidade

Em jogos com múltiplos heróis, poderes assimétricos e geometria de tabuleiro (como *League of Legends*, *Teamfight Tactics*, *Dota 2*, *Magic: The Gathering* e *RedWar*), o balanceamento não pode depender exclusivamente da intuição humana. Com 30 heróis distintos e orçamentos de draft, o espaço combinatório de confrontos atinge centenas de milhares de configurações possíveis:
$$\binom{30}{6} = 593.775 \text{ composições possíveis por equipa}$$

Jogos de referência resolvem este desafio através de **camadas quantitativas empíricas**:
1. **Medição de Eficácia Relativa ao Custo** (Riot Balance Framework & Magic Mana Curves).
2. **Análise Espacial de Posicionamento e Coordenadas de Impacto** (LoL Spatial Heatmaps & Voronoi Influence).
3. **Modelagem de Sinergias e Counters por Pares** (Bradley-Terry & TFT Team Clustering).
4. **Atribuição Marginal Justa por Teoria dos Jogos** (Valores de Shapley).

---

## 2. O Framework de Balanceamento da Riot Games (Adaptado ao RedWar)

A Riot Games utiliza o *Champion Balance Framework* para governar as decisões de patch do *League of Legends*. Este modelo divide o jogo em métricas observáveis sem atributos hardcoded arbitrários:

### 2.1 Taxa de Presença (Presence Rate - $PR$)
$$PR = \text{Pick Rate} + \text{Ban Rate}$$
No RedWar, onde o draft ocorre por orçamento (200 pts / 300 pts), define-se a **Taxa de Presença no Draft ($DPR$)**:
$$DPR(H) = \frac{\text{Partidas em que } H \text{ foi recrutado}}{\text{Total de Partidas Analisadas}}$$

### 2.2 Rácio de Custo-Eficiência (Cost-to-Impact Ratio - $CIR$)
Nenhum herói no RedWar é "OP" por natureza; a questão é sempre se o seu custo de draft está ajustado ao seu impacto real de vitória:
$$CIR(H) = \frac{WR(H) / WR_{\text{baseline}}}{\text{Custo}(H) / \text{Custo}_{\text{médio}}}$$
- **$CIR > 1.25$ (Sub-precificado / Forte)**: O herói oferece uma contribuição de vitória desproporcionalmente alta para o seu custo no orçamento de draft.
- **$0.80 \le CIR \le 1.25$ (Equilibrado / Saudável)**: O herói está perfeitamente alinhado com o seu valor posicional esperado.
- **$CIR < 0.80$ (Sobre-precificado / Fraco)**: O herói custa mais do que o seu impacto estatístico justifica.

---

## 3. Análise Espacial de Coordenadas e "Power Tiles" ($\Delta WR(hero, r, c)$)

No *League of Legends*, o mapa de Summoner's Rift é dividido em grelhas para rastrear onde cada campeão gera eliminações, mortes ou objetivos. No RedWar, o tabuleiro $8 \times 8$ permite uma formulação discreta exata:

### 3.1 Variação de Probabilidade de Vitória por Casa ($\Delta WR$)
Para cada casa $(r, c)$ ocupada pelo herói $H$ durante a partida:
$$\Delta WR(H, r, c) = WR(H \mid \text{ocupou } (r, c)) - WR_{\text{global}}(H)$$

- **Power Tiles ($\Delta WR > +5\%$)**: Casas onde a geometria de movimento e ataque do herói maximiza o controlo territorial e as janelas de letalidade de stun.
- **Vulnerable Tiles ($\Delta WR < -5\%$)**: Casas onde o herói fica exposto a linhas de tiro ortogonais ou feitiços adversários sem proteção adequada.

### 3.2 Zonas de Influência e Projeção Geométrica (Voronoi & Manhattan)
Cada herói projeta uma **área de ameaça imediata** baseada no seu vetor de movimento e alcance:
- Peças com alcance ortogonal de raio (como `Marksman` e `Ranger`) controlam linhas e colunas completas ($2 \times 7 = 14$ casas potenciais).
- Peças com salto espectral (como `Valkyrie` e `Shadowblade`) projetam ameaças radiais que ignoram bloqueios intermediários.

---

## 4. Matrizes de Sinergia e Confrontos Diretos (Duo Affinity & Counterpicks)

Em jogos de cartas colecionáveis (como *Magic: The Gathering* e *Hearthstone*) e autobattlers (como *Teamfight Tactics*), peças individuais ganham poder quando combinadas estrategicamente.

### 4.1 Delta de Sinergia de Par ($\Delta \text{Syn}$)
Mede se dois heróis $A$ e $B$ jogando na mesma equipa têm um desempenho superior à média dos seus desempenhos individuais esperados:
$$\Delta \text{Syn}(A, B) = WR(A \cap B) - \frac{WR(A) + WR(B)}{2}$$
- $\Delta \text{Syn} > +4\%$: **Sinergia Forte** (ex: Conjurador de Stun à distância como `FrostMage` ou `Marksman` combinado com Executor rápido como `Duelist` ou `Valkyrie` para explorar a regra "um segundo enquanto atordoado mata").
- $\Delta \text{Syn} < -4\%$: **Anti-Sinergia / Redundância** (ex: dois heróis com o mesmo papel restrito competindo por espaço ou sem cobertura defensiva).

### 4.2 Vantagem de Confronto Direto ($\Delta \text{Counter}$)
Mede a eficácia de escolher o herói $A$ contra uma equipa adversária que contenha o herói $B$:
$$\Delta \text{Counter}(A \text{ vs } B) = WR(A \text{ na equipa } 1 \mid B \text{ na equipa } 2) - 0.50$$
- $\Delta \text{Counter} > +6\%$: $A$ é um **Counter Direto** de $B$ (ex: `Inquisitor` com aura de silêncio contra conjuradores como `Arcanist` ou `Pyromancer`).

---

## 5. Atribuição Justa via Teoria dos Jogos: Valores de Shapley

Na economia matemática e teoria dos jogos cooperativos, o **Valor de Shapley** determina a contribuição marginal exata de cada membro para o resultado coletivo de uma coligação:
$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

No RedWar, o Valor de Shapley $\phi_H$ atribui a cada herói a sua quota real de vitórias independentemente de ter sido o autor do último golpe, premiando guardiões de contenção (`Warden`, `Paladin`) e suportes de espaço (`Illusionist`, `Timekeeper`) com o mesmo rigor dos finalizadores.

---

## 6. Conclusão e Integração Contínua

Este arcaboiço matemático transforma a telemetria do RedWar num **laboratório empírico de balanceamento**:
1. Sem números inventados ou atributos fictícios de RPG durante as partidas.
2. Análise transparente orientada por dados reais de partidas e simulações do Ares AI.
3. Decisões de calibração de custo fundamentadas em métricas estatísticas consolidadas da indústria de videojogos competitivos.

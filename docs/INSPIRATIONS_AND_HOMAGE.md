# RedWar — Inspirações, referências e homenagem

Este projeto não nasceu num vazio. RedWar/Ares aproveita ideias desenvolvidas ao longo de décadas em algoritmos de jogos, engines, testing, machine learning, balanceamento e sistemas multiplayer, mas tenta adaptá-las a um problema próprio: um RPG táctico de informação parcial, com heróis assimétricos, stun, spells, terreno, lifespan e uma engine híbrida Python/C++.

Este documento é uma homenagem explícita a esse legado. A intenção não é apresentar RedWar como uma reinvenção das técnicas abaixo, mas reconhecer de onde vieram as ideias que estamos a adaptar.

## 1. Stockfish e a tradição das engines de xadrez

A inspiração estrutural mais direta para Ares é a tradição de engines de xadrez modernas, sobretudo Stockfish.

Do modelo de engine retiramos princípios, não as regras do xadrez:

- separação entre state/rules, move generation, search e evaluation;
- alpha-beta/PVS e iterative deepening;
- transposition tables;
- move ordering, killer/history heuristics;
- quiescence e pesquisa seletiva;
- benchmarks e testes de força para validar alterações;
- desenvolvimento incremental apoiado em dados.

A adaptação essencial é: **RedWar não é xadrez**. Stun, spells, lifespan, cooldown, terreno, TWC e passivas são fenómenos de RedWar e têm de orientar as heurísticas próprias.

Referências:

- Stockfish — introdução da NNUE: https://stockfishchess.org/blog/2020/introducing-nnue-evaluation/
- Stockfish NNUE trainer: https://github.com/official-stockfish/nnue-pytorch
- Fishtest — framework de testes de força: https://github.com/official-stockfish/fishtest
- Fishtest — matemática e métodos estatísticos: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html

## 2. Knuth & Moore — alpha-beta pruning

A pesquisa adversarial de Ares pertence à mesma família algorítmica estudada formalmente por Donald Knuth e Peter Moore. O valor desta referência para nós é recordar que eficiência de alpha-beta depende profundamente de ordenação e estrutura da pesquisa.

Ares adapta esse princípio para movimentos que não são capturas/checks tradicionais: em RedWar, certos STUN e spells são eventos forçantes.

Referência:

- Knuth & Moore, *An Analysis of Alpha-Beta Pruning*: https://webdocs.cs.ualberta.ca/~mmueller/courses/657-Fall2025/readings/1975-AIJ-Knuth-Moore-alphabeta.pdf

## 3. NNUE — Nasu / Stockfish

A arquitetura NNUE de RedWar é inspirada no princípio de uma rede que possa ser atualizada eficientemente durante a pesquisa, mas com features específicas do RPG.

A nossa lista de features inclui estado que não existe no xadrez clássico, como:

- stun;
- lifespan;
- cooldown;
- efeitos de terreno;
- TWC;
- lado a jogar;
- identidade relativa de peças.

A filosofia herdada é especialmente importante: primeiro provar correção, depois atualização incremental, depois medir custo e finalmente medir força.

Referências:

- Projeto/referência NNUE: https://github.com/asdfjkl/nnue
- Stockfish NNUE: https://stockfishchess.org/blog/2020/introducing-nnue-evaluation/
- Trainer oficial: https://github.com/official-stockfish/nnue-pytorch

## 4. Metamorphic / property testing

O esforço Python/C++ differential testing evolui naturalmente para property e metamorphic testing. A inspiração aqui é a ideia de testar relações que devem permanecer verdadeiras mesmo quando não existe um oracle manual simples para todas as posições.

No RedWar, exemplos naturais são:

```text
make → unmake → estado original
Python(state, action) == C++(state, action)
serialize → deserialize → mesmas invariantes
sequência válida Python == sequência válida C++
```

Referência:

- Chen, Cheung & Yiu, *Metamorphic Testing: A New Approach for Generating Next Test Cases*: https://arxiv.org/abs/2002.12543

## 5. MDA e teoria de game design

A organização entre mecânicas, dinâmica emergente e experiência do jogador é influenciada pelo framework MDA.

Isto é particularmente útil para RedWar porque uma mudança de uma regra pode ser tecnicamente correta e ainda assim alterar a dinâmica do jogo de uma forma indesejada.

Referência:

- Hunicke, LeBlanc & Zubek, *MDA: A Formal Approach to Game Design and Game Research*: https://www.cs.northwestern.edu/~hunicke/MDA.pdf

## 6. Balanceamento automático e metagame

O Auto-Pricer não deve ser confundido com um oráculo. O projeto procura evoluir de uma simples relação entre resultado e preço para uma análise que considere força do jogador, matchup, composição, escolha e metagame.

Esta direção é inspirada por investigação sobre automated game balancing e metagame autobalancing.

Referências:

- Volz, Rudolph & Naujoks, *Demonstrating the Feasibility of Automatic Game Balancing*: https://arxiv.org/abs/1603.03795
- Hernandez et al., *Metagame Autobalancing for Competitive Multiplayer Games*: https://arxiv.org/abs/2006.04419
- Pfau et al., *Dungeons & Replicants: Automated Game Balancing via Deep Player Behavior Modeling*: https://ieee-cog.org/2020/papers/paper_152.pdf

## 7. Assimetria em jogos multiplayer

A ideia de heróis com capacidades deliberadamente diferentes, em vez de simplesmente clones com números diferentes, é uma escolha consciente de design.

A literatura sobre assimetria em jogos multiplayer ajuda a enquadrar essa escolha como uma ferramenta de design e não apenas como um problema de balanceamento.

Referência:

- Harris, Hancock & Scott, *Leveraging Asymmetries in Multiplayer Games*: https://uwaterloo.ca/touchlab/references/leveraging-asymmetries-multiplayer-games-investigating

## 8. Matchmaking e rating

A futura camada online não deve confundir rating de jogador com força de heróis. A ideia de separar rating de incerteza inspira-se em sistemas como TrueSkill e Glicko.

Referências:

- TrueSkill 2: https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/trueskill2.pdf
- Glicko: https://www.glicko.net/glicko/glicko.pdf

## 9. CI, automação e engenharia de qualidade

A importância que damos a gates, regressões, differential testing e pipelines reprodutíveis é também inspirada pela literatura sobre continuous integration e automação de testes.

Referências:

- Soares et al., *The Effects of Continuous Integration on Software Development: A Systematic Literature Review*: https://doi.org/10.1007/s10664-021-10114-1
- *Test automation maturity improves product quality*: https://www.sciencedirect.com/science/article/pii/S0164121222000280

## 10. O que deliberadamente não copiamos

Inspirar-se não significa importar cegamente uma solução.

Não pretendemos transformar RedWar em:

- um clone de xadrez;
- uma cópia do Stockfish;
- um Auto-Balancer que só procura 50% win-rate;
- um sistema multiplayer cuja arquitetura é desnecessariamente complexa para um jogo turn-based;
- uma NNUE avaliada apenas pelo loss;
- uma coleção de benchmarks que optimiza posições artificiais em vez da força geral.

A regra é:

> **aprender dos sistemas que já resolveram problemas semelhantes, adaptar ao domínio e validar empiricamente no domínio novo.**

## Homenagem

Ares é, em grande parte, um exercício de aprender com o trabalho de muitas pessoas antes de nós.

A todos os investigadores, autores de papers, criadores de engines, maintainers de open source e designers de jogos que transformaram ideias difíceis em sistemas reutilizáveis: este documento é o reconhecimento explícito dessa influência.

RedWar tenta devolver essa inspiração através de uma implementação pequena, experimental e aberta, adaptada a um problema diferente.

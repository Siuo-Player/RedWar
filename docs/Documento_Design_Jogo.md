# Documento de Design: Projeto de Tabuleiro + IA

## 1. Visão Geral
Um jogo de tabuleiro focado em estratégia tática e sinergias de peças, desenvolvido em simultâneo com uma IA de avaliação (estilo Stockfish). O jogo funciona como um ambiente determinístico sem mecânicas de "vida/dano" tradicionais, favorecendo eliminações diretas (hit-kill) combinadas com efeitos de controlo de tabuleiro.

## 2. Mecânica de Seleção de Peças (Deckbuilding)
Após análise, o modelo ideal para este ecossistema é o **Sistema de Pontos (Drafting / Army Building)**.
* **Como funciona:** Cada jogador tem um limite de pontos (ex: 100 pontos). Cada peça tem um custo.
* **Vantagem para a IA:** O balanceamento torna-se matemático. Se a IA detetar através de self-play que uma peça tem uma taxa de vitória (win-rate) desproporcional, o "custo" da peça aumenta nas próximas versões.
* **Turno Inicial:** Para mitigar a vantagem do primeiro jogador, o Jogador 1 pode começar com uma restrição (ex: menos X pontos de exército, ou uma limitação de movimento no primeiro turno).

## 3. Dinâmica do Tabuleiro
* **Formato Base:** Tabuleiro em grelha (inicialmente 8x8, mas a arquitetura deve suportar NxN).
* **Condição de Vitória:** A definir (Eliminar o "Rei/Comandante" ou capturar um ponto central).
* **Ações por Turno:** Apenas UMA peça é movida/ativada por turno, enfatizando a importância de cada decisão.

## 4. Habilidades e Interações (Mecânicas Especiais)
A ausência de "pontos de vida" é compensada por estados e modificadores temporários:
* **Hit-Kill:** Ataques eliminam a peça alvo instantaneamente.
* **Controlo de Grupo (Imobilização):** Peças que impedem o movimento de inimigos adjacentes durante X turnos.
* **Bloqueios Físicos (Gelo/Barreiras):** Criação de entidades não-jogáveis no tabuleiro que ocupam casas e absorvem 1 ataque antes de quebrar.
* **Magias de Posição:** Puxar inimigos para casas vulneráveis, trocar de lugar com aliados, etc.
* **Desafio Técnico para a IA:** O motor terá de rastrear "Timers" (quantos turnos falta para o gelo derreter, ou para a imobilização acabar) no estado do jogo (Game State).

## 5. Avaliação da IA (O Caminho do ELO)
* **Fase 1:** Função de avaliação material (cada peça vale o seu custo em pontos).
* **Fase 2:** Avaliação de mobilidade e controlo de casas (ter peças congeladas diminui o *eval*).
* **Fase 3:** Refinamento contínuo através de Fishtest (versões da IA jogam entre si; se a versão com a nova métrica ganhar mais partidas estatisticamente, substitui a antiga).

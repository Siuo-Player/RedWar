# Arquitetura do Projeto

Para garantir que a IA consegue calcular milhões de posições, mas ao mesmo tempo teres uma interface visual (como o Chess.com), o projeto tem de ser dividido em duas camadas estritas:

## 1. O Motor (Core / Engine)
Deve ser completamente invisível, sem gráficos, apenas matemática e lógica pura.
* **Estado do Jogo (Game State):** Representa o tabuleiro, a posição de todas as peças, de quem é o turno, e os temporizadores (timers) de feitiços/gelo.
* **Gerador de Movimentos (Move Generator):** Uma função que, dada uma posição, cospe TODOS os movimentos legais possíveis. Tem de ser extremamente rápido.
* **A IA (Search & Eval):** O algoritmo Minimax com Alpha-Beta Pruning que usa o gerador de movimentos para olhar para o futuro e avaliar a melhor jogada.

## 2. A Interface Visual (Client / UI)
O "aplicativo" que o jogador vê e interage.
* Pode ser feito em Python (Pygame), JavaScript (Web), etc.
* A UI apenas desenha o tabuleiro com base na informação que o Motor fornece.
* Quando o jogador clica numa peça, a UI pergunta ao Motor: "Quais são os movimentos legais para a casa X?". O Motor responde, e a UI desenha os destaques.

## Organização de Pastas (Sugestão para repositório Git)
/meu_jogo
 ├── /engine           # Lógica do jogo e IA
 │    ├── board.py     # Representação da grelha e estado
 │    ├── moves.py     # Lógica de movimentos válidos
 │    └── ai.py        # Algoritmos de busca e avaliação
 ├── /ui               # Interface visual
 │    ├── window.py    # Desenho do ecrã e gestão de cliques
 │    └── assets/      # Imagens das peças (quando existirem)
 ├── /tests            # Onde a magia do Git acontece
 │    ├── test_moves.py
 │    └── test_rules.py
 └── main.py           # O ficheiro que liga o Motor à UI

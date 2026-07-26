# Nome Provisório: Projeto IA de Tabuleiro Aberto

Um jogo de tabuleiro tático de eliminação direta (hit-kill) focado em sinergia de peças, controlo de área e posicionamento estratégico. Este projeto está a ser desenvolvido em conjunto com uma Inteligência Artificial hiper-especializada (inspirada na filosofia do Stockfish) que serve tanto como adversário como ferramenta matemática de balanceamento do jogo.

## Arquitetura
O projeto divide-se estritamente em duas camadas para garantir máxima performance na avaliação de jogadas e modularidade para diferentes variações de regras:
1. **Engine (Motor Lógico):** Pura lógica determinística, gestão de estado do tabuleiro, temporizadores de habilidades (ex: imobilização) e validação de movimentos.
2. **UI (Interface Gráfica):** Representação visual baseada no estado fornecido pelo motor, permitindo interações humanas e desenho dos movimentos válidos.

## Modularidade e Variações
A *Engine* foi planeada para aceitar *RuleSets* (conjuntos de regras) intercambiáveis. O tamanho do tabuleiro, o limite de peças (ex: 16) e as habilidades são modulares. Diferentes IAs podem ser treinadas ou instanciadas para diferentes variações do jogo.

## Stack Tecnológico Inicial
* **Linguagem:** Python (ideal para prototipagem rápida e iteração da IA).
* **UI:** Pygame.
* **Testes:** Pytest (para testes rigorosos de regras e geração de movimentos).

## Instalação e Execução
\`\`\`bash
# 1. Clonar o repositório
# git clone <url>

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o protótipo da interface
python main.py
\`\`\`

## Autores e Contribuições
* **Desenvolvedor Principal:** [O teu nome/nick] - Arquitetura, desenvolvimento da engine, UI e regras do jogo.
* **Assistente de IA (Gemini):** Consultoria na arquitetura do motor de xadrez/tabuleiro, design de mecânicas de balanceamento (hit-kill, timers de gelo, ELO profiling) e geração da estrutura inicial do projeto.

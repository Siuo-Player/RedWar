# ⚔️ RedWar: Combat Engine & AI Simulation

Um jogo de tabuleiro tático assimétrico de eliminação direta focado em sinergia de peças, controlo de área e posicionamento estratégico. O projeto inclui um motor de Inteligência Artificial modular inspirado na arquitetura do Stockfish, suportando simulações exaustivas e balanceamento automático.

## ✨ Características Principais

### 🎮 Gameplay Tático
* **Eliminação Direta (Hit-Kill):** Não existem pontos de vida. Capturas removem a peça instantaneamente.
* **Mecânica de Stun:** Atordoamentos táticos que bloqueiam o inimigo durante o seu turno. Aplicar *Stun* num alvo já atordoado resulta em morte instantânea.
* **Fase de Draft (Economia):** Jogadores constroem o seu exército de raiz num tabuleiro vazio, usando um orçamento de 200 Pontos.

### 🧠 Inteligência Artificial Avançada
* **Minimax com Poda Alfa-Beta:** O motor de busca da IA.
* **Move Ordering:** Avaliação otimizada que testa capturas e ameaças primeiro, aumentando a profundidade de cálculo.
* **4 Perfis Heurísticos:**
  * 🗡️ *Agressiva* (Recompensa invasão inimiga)
  * 🛡️ *Defensiva* (Recompensa proteção do rei)
  * 💰 *Gulosa* (Foco estrito em material)
  * ♟️ *Estratégica* (Valoriza mobilidade e controlo do centro)
* **Auto-Balancer Automático:** Um script em Python que consome milhares de simulações (MCTS / Greedy) em `.json` para sugerir ajustes dinâmicos ao custo das peças com base na sua *Win-Rate*.

## 🏗️ Arquitetura do Projeto

| Módulo | Descrição |
| :--- | :--- |
| **`/engine`** | Lógica determinística pura. Valida regras de movimento, *Stuns*, condição dos 50-movimentos e deteção de bloqueios no tabuleiro. |
| **`/ai`** | O cérebro do projeto. Contém as avaliações heurísticas, o algoritmo de busca e simuladores exaustivos sem interface gráfica (Headless). |
| **`/ui`** | Interface gráfica construída em Pygame. Gere o ecrã de *Draft*, relógios de xadrez em tempo real e overlays de Áreas de Efeito (AoE). |
| **`/tests`** | Suite de testes unitários automatizados construídos com `pytest` para blindar as regras matemáticas do jogo. |

## 🚀 Instalação e Execução

**1. Instalar as dependências:**
```bash
pip install -r requirements.txt
```

**2. Jogar (Interface Gráfica contra IA ou Local):**
```bash
python main.py
```

**3. Correr Ferramentas de IA (Simuladores):**
```bash
# Testar Aberturas entre diferentes personalidades de IA
python ai/opening_tester.py

# Correr Simulação Exaustiva de Estruturas
python ai/exhaustive_trainer.py

# Gerar Sugestões de Balanceamento
python ai/auto_balancer.py
```

**4. Correr Testes de Lógica:**
```bash
pytest tests/
```

## 📚 Documentação Adicional

Para detalhes profundos sobre as mecânicas, peças e a estrutura completa de pastas, consulta:

* **[Documento_Design_Jogo.md](Documento_Design_Jogo.md)** — Game Design Document completo
* **[Estrutura_Projeto.md](Estrutura_Projeto.md)** — Mapeamento detalhado do repositório

---
# ⚔️ RedWar: Combat Engine & AI Simulation

Um jogo de tabuleiro tático assimétrico de eliminação direta focado em sinergia de peças, controlo de área e posicionamento estratégico. O projeto inclui um motor de Inteligência Artificial modular inspirado na arquitetura do Stockfish, suportando simulações exaustivas e balanceamento automático.

## ✨ Características Principais

### 🎮 Gameplay Tático
* **Eliminação Direta (Hit-Kill):** Não existem pontos de vida. Capturas removem a peça instantaneamente.
* **Mecânica de Stun:** Atordoamentos táticos que bloqueiam o inimigo durante o seu turno. Aplicar *Stun* num alvo já atordoado resulta em morte instantânea.
* **Fase de Draft (Economia):** Jogadores constroem o seu exército de raiz num tabuleiro vazio.
* **Efeitos de Terreno:** Peças interagem dinamicamente com zonas de Gelo (Bloqueio) e Fogo (Stun).

### 🧠 Inteligência Artificial Avançada
* **Minimax com Poda Alfa-Beta:** O motor de busca da IA.
* **Move Ordering:** Avaliação otimizada que testa capturas e ameaças primeiro, aumentando a profundidade de cálculo.
* **Auto-Balancer Automático:** Um script que consome simulações exaustivas para sugerir ajustes dinâmicos ao custo das peças.

---

## 🚀 Guia de Comandos e Execução

### ⚙️ Instalação Inicial
```bash
pip install -r requirements.txt
```

### 🎮 Jogar
**Modo Local (Tu vs IA)**

O modo clássico para jogares no teu computador.

```bash
python main.py
```

**Modo Multiplayer (Rede/LAN)**

Para jogares contra um amigo noutro computador.

1. Abre um terminal e inicia o servidor:
```bash
python server/app.py
```

2. No teu computador, conecta-te como Jogador 1 (Brancas):
```bash
python multiplayer_main.py localhost
```

3. No computador do teu amigo, ele conecta-se usando o teu IP local (exemplo):
```bash
python multiplayer_main.py 192.168.1.100
```

### 🔬 Ferramentas de IA e Balanceamento
**1. Analisar Telemetria e Gridlocks (Caixa Negra)**

Corre jogos invisíveis focados em encontrar anomalias táticas da IA.

```bash
python ai/game_analyzer.py
```

**2. Otimizar Custos (Auto-Balancer)**

Se as peças estiverem desbalanceadas, corre este comando para a IA descobrir os novos valores matemáticos ideais.

```bash
python build_pipeline.py
```

### 🧪 Testes Unitários e Controlo de Qualidade
Para garantir que regras base do motor (movimentos, stuns, etc.) não se partiram após modificares o código.

```bash
pytest tests/
```

### 💾 Git (Sincronizar Alterações)
Após realizares testes que corram bem, guarda e partilha o teu progresso no GitHub.

```bash
git add .
git commit -m "atualizacao: descricao das tuas alteracoes aqui"
git push
```

---

### Os Comandos que Precisas Agora

Como adicionámos funcionalidades gigantescas em massa para resolver os problemas passados, deves correr os comandos pela seguinte ordem no teu terminal:

1. **Joga contra a IA localmente e tenta as novas mecânicas (Verifica as imagens e a jogabilidade):**
```powershell
python main.py
```

2. **Garante que o novo BoneLord e os ossos não encravaram a IA com loops infinitos (O `jogos_encravados.txt` deve vir vazio):**

```powershell
python ai/game_analyzer.py
```

3. **Se tudo estiver perfeito, salva no GitHub:**

```powershell
git add .
git commit -m "feat: BoneLord ataca à distância via necromancia, Bones decaem após 5 turnos, e adicionados terrenos fire/ice dinâmicos com novo README"
git push
```

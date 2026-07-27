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

### 📊 Calibração de ELO
O sistema ELO não mede força absoluta; mede a probabilidade de vitória entre dois jogadores. A pontuação esperada de um jogador A contra um jogador B é calculada por:

$$E_A = \frac{1}{1 + 10^{\frac{R_B - R_A}{400}}}$$

Isto significa que uma diferença de exatamente 400 pontos de ELO indica que o jogador mais forte tem uma probabilidade matemática de vitória de aproximadamente 90,9%.

**A nossa calibração** fixa o Bot Aleatório na âncora absoluta de 100 ELO. Se quisermos que o Bot Base (profundidade 1) tenha 300 ELO, então a sua taxa de vitória empírica contra o Aleatório deve ser:

$$E_A = \frac{1}{1 + 10^{\frac{100 - 300}{400}}} \approx 0.76$$

Ou seja, para o nosso "chute" de 300 ELO estar correto, a IA base tem de ganhar cerca de 76% dos jogos contra o Bot Aleatório. Se ganhar 95% das vezes, então o seu verdadeiro ELO não é 300, mas sim aproximadamente 611.

Para descobrir a verdade empírica, o projeto usa um script que faz o inverso da fórmula, convertendo a taxa de vitória real em um ELO verdadeiro:

$$R_A = 100 - 400 \cdot \log_{10}\left(\frac{1 - E_A}{E_A}\right)$$

## 🧠 Arquitetura da IA e Escalonamento ELO

O motor tático do RedWar utiliza um sistema de ELO dinâmico calibrado matematicamente, abandonando abordagens baseadas em suposições, para fornecer diferentes níveis de dificuldade em tempo real.

### A Matemática por Trás do Nível de Dificuldade
O sistema ELO mede a probabilidade relativa de vitória usando a curva logística da Federação Internacional de Xadrez (FIDE):

$$E_A = \frac{1}{1 + 10^{\frac{R_B - R_A}{400}}}$$

Para que o slider de dificuldade do jogo refletisse a realidade estatística, a IA foi sujeita a uma bateria de testes rigorosa:
1. **A Âncora (100 ELO):** Desenvolvemos um bot aleatório que não avalia posições, assumindo a base mais baixa possível.
2. **O Teste Empírico:** Colocámos a IA no seu nível de processamento mais baixo (profundidade 1, limite de 0.05s) a jogar contra o bot aleatório.
3. **O Resultado:** O motor base obteve uma taxa de vitória de **99,5%**.
4. **Cálculo Inverso:** Aplicando o teorema do ELO de forma inversa, descobrimos que o ELO base real da IA é de **~900 ELO**.

### Gestão de Tempo Linear
Sabendo que 0.05s geram **900 ELO**, e definindo o nosso teto computacional nos **2600 ELO** a 5.0s (onde entra em ação a otimização máxima do Alpha-Beta Pruning, Quiescence Search e Iterative Deepening), qualquer ELO escolhido na interface usa uma interpolação linear para alocar milissegundos de processamento de forma exata à dificuldade pretendida.

### Escalada de Âncora (Anchored ELO Scaling)
Este é o santo graal do teste de motores de xadrez: a escalada de âncora. Se puséssemos o Nível 4 (Mestre) a jogar contra o Aleatório (100 ELO), ele ganharia 1000 em 1000 jogos, o que faria a fórmula explodir para infinito e quebrar o cálculo. Para medir a força de uma IA de topo, ela tem de jogar contra a versão imediatamente abaixo dela. Assim, subimos a escada degrau a degrau: o Nível 1 mede-se contra o Aleatório; o Nível 2 mede-se contra o Nível 1; o Nível 3 mede-se contra o Nível 2; e assim sucessivamente.

A fórmula de extração de ELO que aplicaremos é a seguinte:

$$ELO_{Superior} = ELO_{Inferior} - 400 \cdot \log_{10}\left(\frac{1 - W}{W}\right)$$

Onde $W$ é a win-rate entre $0.001$ e $0.999$ para evitar divisões por zero.

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

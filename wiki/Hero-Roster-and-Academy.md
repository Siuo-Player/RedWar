# 🧙‍♂️ Catálogo de Heróis, Matriz Tática & Análise Baseada em Dados

O RedWar conta com um total de **24 heróis e unidades**, organizados numa **Matriz Tática de 5 Arquétipos** que substitui bónus numéricos arbitrários por **sinergias puramente mecânicas e espaciais**.

---

## 🏛️ Os 5 Arquétipos Táticos

1. **Vanguarda (Vanguard / Tanques)**:
   - *Heróis*: Paladin, Golem, Guardian, Berserker.
   - *Função*: Ancorar a linha de frente, absorver pressão e projetar deslocamento físico (Knockback/Push).
2. **Flanqueadores (Strikers / Assassinos)**:
   - *Heróis*: Shadowblade, Dragoon, Rogue, Assassin.
   - *Função*: Mobilidade evasiva, salto sobre barreiras e finalização do segundo stun letal.
3. **Artilharia (Artillery / Snipers)**:
   - *Heróis*: Stormcaller, Archer, Pyromancer, Bombard.
   - *Função*: Projeção de ameaça à distância, dano em linha reta e condução elétrica em cadeia.
4. **Disruptores (Disruptors / Controladores)**:
   - *Heróis*: FrostMage, Hookmaster, Timekeeper, Banshee, Inquisitor, Illusionist.
   - *Função*: Negação de área, puxar unidades, congelamento remoto, manipulação de turnos de stun e silenciamento.
5. **Invocadores (Summoners / Criadores)**:
   - *Heróis*: BoneLord, Necromancer, Tactician.
   - *Função*: Saturação de casas com peões 'Bone', controlo de linhas de visão e criação de pontes de condução elétrica.

---

## ⚡ Sinergias Mecânicas Emergentes (Sem Bónus Artificiais)

O RedWar promove combinações orgânicas entre habilidades, sem atribuir números arbitrários:

- **Lockdown & Execução (Silenciamento + Flanqueador)**:
  - Um Disruptor (ex.: FrostMage) atordoa ou silencia o líder adversário, bloqueando as suas reações e feitiços defensivos.
  - O Striker (ex.: Shadowblade) avança livremente e aplica o 2º stun para eliminação garantida.
- **Deslocamento & Risco Ambiental (Push + Lava)**:
  - O Paladino avança com escudo e empurra o adversário 1 casa para trás.
  - Se a casa de destino for uma **Fissura de Lava**, a unidade inimiga é incinerada instantaneamente!
  - Se colidir com uma **Barreira Mágica**, sofre um atordoamento por impacto de colisão.
- **Ponte de Condução Elétrica (Conduit Bridging)**:
  - O Stormcaller dispara o feitiço *Chain Lightning*.
  - O BoneLord invoca um lacaio 'Bone' numa casa intermédia para servir de condutor elétrico, permitindo ao raio saltar através do peão aliado e atingir um atirador inimigo escondido na retaguarda.
- **Gancho e Posicionamento (Hook & Reposition)**:
  - O Hookmaster puxa uma unidade adversária 2 casas em linha reta, trazendo-a para a zona de ataque imediata de um aliado ou para a margem de um perigo de lava.
- **Distorção de Turnos (Cronomancia)**:
  - O Timekeeper atua sobre a única variável numérica do jogo: os turnos. Acelera a recuperação de aliados atordoados (-1 turno de stun) ou prolonga a vulnerabilidade de inimigos (+1 turno de stun).

---

## 📊 Estatísticas Empíricas Baseadas em Dados (Estilo Futebol)

As "classes" e "stats" das peças no RedWar não são codificadas manualmente (hardcoded). São calculadas a partir de **dados de rastreamento de partidas simuladas pelo Ares Engine**, tal como na análise avançada de futebol (Wyscout / Opta):
- **Mapas de Calor Posicionais ($8 \times 8$)**: Revelam em que casas do tabuleiro cada peça tem maior taxa de vitórias e impacto territorial.
- **Curva de Efeito por Fase de Partida**:
  - *Abertura (Turnos 1–10)*: Peças de controlo de espaço e desenvolvimento rápido.
  - *Meio-Jogo (Turnos 11–20)*: Peças de combate e aplicação de stuns.
  - *Final de Jogo (Turnos 21+)*: Peças de alta mobilidade e conversão letal.
- **Radar de Desempenho (6 Dimensões)**: Controlo Zonal, Letalidade Direta, Controlo de Stun, Mobilidade, Sobrevivência e Conversão Final. Uma peça pode pertencer a múltiplas classes em graus diferentes com base no seu perfil empírico.
- **Equilíbrio de Custo em Pontos**: Em vez de declarar peças como "OP", o sistema calcula a **relação custo-eficácia** para calibrar se o custo no draft (ex.: 50 pts, 65 pts) reflete fielmente o impacto em jogo.

---

## 🌟 Tabela de Heróis em Destaque

| Herói | Arquétipo Primário | Custo | Tipo de Movimento | Habilidade Ativa / Passiva | Papel Tático |
|---|---|---|---|---|---|
| **Paladin** | Vanguarda | 55 | Ortogonal (até 2 casas) | Avanço de Escudo: Stun e empurrão | Tanque e âncora de linha de frente |
| **Shadowblade** | Flanqueador | 65 | Diagonal (até 3 casas) | Mobilidade Fantasma: Atravessa aliados e inimigos | Assassina de flanco e finalizadora |
| **Stormcaller** | Artilharia | 72 | Ortogonal (1 casa) | Chain Lightning: Raio de 4 casas em linha reta | Artilharia e atordoamento remoto |
| **Dragoon** | Flanqueador | 60 | Salto em L estendido | Salto Draconiano: Salta sobre obstáculos | Mobilidade e execução rápida |
| **FrostMage** | Disruptor | 50 | Ortogonal (1 casa) | Nevasca: Congelamento e stun a 3 casas | Controlo de grupo (CC) e negação de área |
| **BoneLord** | Invocador | 65 | Cruz (1 casa) | Ressurreição: Invoca soldados 'Bone' adjacentes | Criação de superioridade numérica |
| **Hookmaster** | Disruptor | 52 | Adjacente (1 casa) | Gancho Tático: Puxa inimigo em linha reta | Reposicionamento e atração para perigos |
| **Timekeeper** | Disruptor | 59 | Adjacente (1 casa) | Distorção Temporal: Altera contagem de stun | Cronomancia e manipulação de turnos |
| **Pyromancer** | Artilharia | 58 | Diagonal (1 casa) | Explosão de Fogo: Atordoa alvo e casas laterais | Dano em área (AoE) |
| **Archer** | Artilharia | 45 | Ortogonal/Diagonal (1 casa) | Tiro Longo: Ataque em linha reta a 3 casas | Supressão de longo alcance |

---

## 🎓 Academia de Heróis (Hero Academy)

A **Academia de Heróis** é o centro de formação interativo do RedWar (disponível no menu principal e no cliente Web). 

Cada lição oferece:
1. **História e Identidade (Lore)**: A origem e propósito da peça.
2. **Explicação de Habilidades**: Mecânica detalhada de movimentação e poderes.
3. **Puzzle Interativo no Tabuleiro**: Um cenário tático de teste onde o jogador deve aplicar a habilidade específica da peça para garantir a vitória em 1 lance.
4. **Feedback Explicativo**: Análise estratégica pós-resolução confirmando o porquê daquele lance ser o ideal.

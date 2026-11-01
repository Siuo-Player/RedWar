# ⚔️ Bem-vindo à Wiki Oficial do RedWar

**RedWar** é um RPG de tabuleiro tático em grelha, inspirado no xadrez e em jogos de estratégia, construído com um modelo de dois pilares fundamentais:
1. **Plataforma Competitiva Completa (estilo Chess.com)**: Modos casuais e ranqueados, puzzles táticos, Academia de Heróis com tutoriais interativos, análise pós-jogo com curva de centipawns (Game Review), multiplayer online com relógios sincronizados e reconexão em voo.
2. **Motor de IA de Alta Precisão (estilo Stockfish - Ares AI)**: Pesquisa alpha-beta profunda com podas agressivas (LMR, Quiescence, Killer Moves, History Heuristics), perfis especializados por modo de jogo e validação estatística rigorosa via **SPRT** (Sequential Probability Ratio Test).

---

## 🧭 Índice da Documentação

- 📜 [Regras Oficiais do Jogo](Game-Rules) — Mecânica de 2 vidas (stun/morte), turnos, grelhas e condições de vitória.
- 🧙‍♂️ [Catálogo de Heróis & Academia](Hero-Roster-and-Academy) — Roster completo de 22 heróis, habilidades e lições táticas da Academia.
- 🤖 [Motor Ares & Metodologia SPRT](Ares-Engine-and-SPRT-Methodology) — Arquitetura de IA inspirada em Stockfish, perfis dedicados e testes de hipóteses estatísticas.
- 🎮 [Modos de Jogo Competitivos](Game-Modes) — Standard 8×8, Grand 10×10, Tournament Snake Draft e Hazard Arena.
- 🔒 [Publicação Gratuita & Segurança](Deployment-and-Security) — Hospedagem gratuita no GitHub Pages, Docker Cloud e arquitetura de segurança defensiva.

---

## ⚡ Começar a Jogar

```bash
# 1. Iniciar o cliente Desktop oficial (Pygame)
python launcher.py desktop
# ou no Windows:
run_redwar.bat

# 2. Iniciar o servidor Web & REST API
python launcher.py web --port 8000
# Abrir no browser: http://localhost:8000/
```

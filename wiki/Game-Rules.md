# 📜 Regras Oficiais do RedWar

## 1. O Princípio das Duas Vidas (Sem Pontos de Vida)

No RedWar não existem pontos de vida (HP), mana, armadura ou valores de defesa numéricos. Toda a sobrevivência e eliminação é governada pelo estado binário de **Normal**, **Atordoado (Stun)** e **Morte**:

```text
Normal
  ↓ stun (ataque inimigo ou feitiço)
Atordoado (incapaz de agir durante N turnos)
  ↓ segundo stun enquanto atordoado
Morto (removido definitivamente do tabuleiro)
```

- Uma peça normal atacada fica **Atordoada** e recebe um contador de stun (geralmente 2 turnos).
- Enquanto estiver atordoada, a peça não se pode mover nem conjurar habilidades.
- Se uma peça atordoada for atingida por **qualquer novo stun**, ela é eliminada imediatamente.
- Se o contador de stun expirar sem novas agressões, a unidade recupera a sua prontidão de combate completa.

---

## 2. Estrutura de Turno e Ações

- Cada jogador executa **uma única ação por turno**.
- Uma ação consiste em selecionar uma unidade amigável e executar:
  - Um **movimento simples** para uma casa desocupada;
  - Um **ataque de combate corporal** que atordoa o inimigo na casa destino;
  - Uma **habilidade ativa ou feitiço** (ex.: disparo em linha reta, teletransporte, invocação).

---

## 3. Formato do Tabuleiro e Orçamento

- **Modo Padrão (Standard 8×8)**:
  - Tabuleiro 8×8 (64 casas).
  - Orçamento inicial: **200 pontos** por exército.
- **Modo Grand RedWar (10×10)**:
  - Tabuleiro 10×10 (100 casas).
  - Orçamento inicial: **300 pontos** por exército.
- As peças e heróis são selecionados no início da partida, respeitando o teto orçamental.

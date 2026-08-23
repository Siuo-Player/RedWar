# RedWar — Roadmap

Este roadmap separa o que já existe do que é objetivo futuro.

## Agora — estabilização do core

- [x] Ter uma representação inicial do jogo em Python.
- [x] Ter uma Ares funcional em Python/Cython.
- [x] Ter uma engine C++ em desenvolvimento.
- [x] Introduzir configuração data-driven para heróis.
- [x] Criar Arena automatizada.
- [x] Criar ferramentas de balanceamento.
- [ ] Eliminar divergências Python/C++.
- [ ] Completar testes diferenciais.
- [ ] Tornar hashing e `make/unmake` comprovadamente reversíveis em toda a árvore de regras.
- [ ] Tornar o Ares significativamente mais forte e mais rápido.

## Próxima fase — Ares

- [ ] Consolidar C++ como hot path principal.
- [ ] Melhorar geração/ordenação de ações.
- [ ] Melhorar quiescence para a volatilidade específica de RedWar.
- [ ] Melhorar avaliação posicional.
- [ ] Criar suite de posições de benchmark.
- [ ] Medir NPS, profundidade, TT hit rate e força.
- [ ] Melhorar Arena para comparar versão anterior vs candidata.
- [ ] Criar histórico de resultados da Arena.
- [ ] Criar rating/ELO das engines.

## Heróis e balanceamento

- [ ] Simplificar ainda mais o sistema data-driven.
- [ ] Reduzir lógica de herói espalhada pelo código.
- [ ] Padronizar documentação de cada herói.
- [ ] Melhorar Auto-Pricer.
- [ ] Validar custos usando uma IA suficientemente forte.
- [ ] Testar e calibrar a duração do stun.
- [ ] Formalizar duração/interação do gelo.
- [ ] Definir política de empilhamento dos efeitos.

## Aplicação

- [ ] Melhorar UI atual.
- [ ] Menu principal completo.
- [ ] Seleção de bots/dificuldade.
- [ ] Dois jogadores locais.
- [ ] Animações de movimento.
- [ ] VFX de spells/passivas.
- [ ] Som.
- [ ] Definições.
- [ ] Replays.
- [ ] Histórico de partidas.
- [ ] Ferramentas de análise no final das partidas.
- [ ] Suporte a várias resoluções.
- [ ] Possível suporte mobile.

## Web

- [ ] Escolher stack web.
- [ ] Definir API do jogo.
- [ ] Criar cliente web.
- [ ] Integrar autenticação Google.
- [ ] Criar sessão/conta.
- [ ] Criar matchmaking.
- [ ] Criar WebSocket ou transporte equivalente.
- [ ] Criar servidor autoritativo.
- [ ] Implementar relógios.
- [ ] Implementar reconexão.
- [ ] Implementar ranking.
- [ ] Implementar ELO/MMR.
- [ ] Implementar desafios diretos.
- [ ] Implementar amigos/chat.
- [ ] Implementar rematch.
- [ ] Implementar espectadores.
- [ ] Implementar histórico.

## Multiplayer

O multiplayer é parte principal do produto final.

Ordem recomendada:

```text
servidor autoritativo
        ↓
ações legais + sincronização
        ↓
relógios + abandono
        ↓
reconexão
        ↓
matchmaking
        ↓
rating
        ↓
social
```

## Modos de jogo

- [x] Modo normal 8×8 / 200 pontos como referência atual.
- [ ] Variantes de orçamento.
- [ ] Variantes de regras de vitória.
- [ ] 10×10 experimental.
- [ ] Outros tamanhos de tabuleiro.
- [ ] Modos especiais inspirados em plataformas como Chess.com.

O modo normal não deve ser substituído por uma experiência experimental antes de esta ser validada.

## Lançamento

O projeto não deve ser considerado pronto para lançamento enquanto não existir pelo menos:

- aplicação utilizável;
- versão web utilizável;
- multiplayer online;
- autenticação;
- matchmaking;
- ranking/ELO de jogadores;
- histórico de partidas;
- Ares suficientemente forte e rápida;
- Arena da Ares funcional;
- documentação pública coerente;
- revisão das licenças de código e assets.

## Futuro / baixa prioridade

- replays públicos;
- espectador avançado;
- anti-cheat avançado;
- temporadas competitivas;
- monetização;
- conteúdo cosmético;
- outras variantes experimentais.

## Decisões ainda abertas

Não estão congeladas:

- duração final do stun;
- duração exata do gelo;
- regras completas de empilhamento de efeitos;
- stack web/backend;
- fornecedor gratuito de hosting;
- base de dados;
- modelo final de rating;
- política exata de reconexão;
- tamanho/margem definitivos da Arena;
- 10×10 como modo separado ou formato alternativo oficial.

# RedWar — Web, App e Multiplayer

## Objetivo

O objetivo final é uma experiência semelhante ao Chess.com, mas para o sistema de RPG de tabuleiro do RedWar.

A visão inclui:

- aplicação desktop;
- versão web;
- possível versão mobile;
- partidas contra IA;
- análise;
- multiplayer 1v1;
- matchmaking;
- ranking;
- replays/histórico;
- espectadores;
- contas de utilizador.

Este documento descreve a direção do produto, não uma implementação já concluída.

## Aplicação

A aplicação atual é Python/Pygame.

O objetivo é manter a tecnologia simples enquanto isso não prejudicar desempenho percebido.

Características desejadas:

- menu principal;
- seleção de IA/dificuldade;
- jogo local contra IA;
- dois jogadores locais;
- análise;
- replays;
- histórico das partidas;
- definições;
- som;
- animações;
- partículas e VFX;
- suporte a diferentes resoluções;
- possível versão mobile.

O jogador local não deve sentir lag causado pela IA ou pelo rendering.

## Estilo visual

A direção atual é minimalista, com mais qualidade visual que o protótipo existente.

Os efeitos mágicos devem utilizar partículas e animações com uma linguagem visual própria.

Movimentos de peças devem ser animados entre casas.

Spells e passivas importantes devem ter VFX claros.

O restante pode permanecer minimalista quando não existir uma identidade visual específica para a habilidade.

## Web

A tecnologia da versão web ainda não foi escolhida.

Critérios:

1. baixo custo;
2. simplicidade;
3. suporte adequado a 1v1 em tempo real;
4. WebSocket ou tecnologia equivalente;
5. possibilidade de reutilizar a lógica do jogo;
6. boa experiência desktop e mobile.

O projeto deve evitar escolher uma stack apenas porque é popular. A decisão deve ser comparada com a necessidade real do jogo.

## Autenticação

O plano atual é utilizar **Google Login** como mecanismo principal.

A solução concreta de identidade e armazenamento ainda precisa ser escolhida.

## Multiplayer 1v1

O multiplayer é uma funcionalidade principal do produto final.

O fluxo pretendido é:

```text
login
  ↓
matchmaking / desafio
  ↓
criação da partida
  ↓
draft + posicionamento
  ↓
partida 1v1
  ↓
resultado
  ↓
rating / histórico / rematch
```

## Servidor autoritativo

A arquitetura recomendada é **servidor autoritativo**.

Isto significa:

- o cliente envia uma ação/intenção;
- o servidor verifica se a ação é legal para o estado atual;
- o servidor aplica a ação;
- o servidor transmite o novo estado/resultado.

O cliente não deve poder simplesmente dizer ao servidor que “capturou” uma peça sem passar pela validação das regras.

Esta decisão reduz cheating e mantém clientes diferentes sincronizados.

## Protocolo

A solução concreta ainda está aberta.

O objetivo é ter mensagens pequenas e determinísticas, por exemplo:

```text
AUTH
CREATE_MATCH
JOIN_MATCH
STATE
ACTION
ACTION_RESULT
CLOCK
RESIGN
DRAW_REQUEST
GAME_END
RECONNECT
```

Os nomes são ilustrativos e não constituem ainda um protocolo final.

## Tempo

No matchmaking devem existir vários ritmos de jogo, inspirados no conceito de Chess.com.

O jogo deverá suportar:

- limite por jogador;
- timeout;
- consumo correto do relógio;
- reconexão sem pausar automaticamente o relógio;
- perda quando o jogador não regressa a tempo.

## Reconexão

Quando uma conexão cai:

1. o servidor mantém a partida viva durante uma janela definida;
2. o relógio continua a contar;
3. o cliente tenta reconectar;
4. se voltar, continua do estado atual;
5. se não voltar dentro da regra do modo, perde por abandono/timeout.

Os valores exatos da janela de reconexão ainda serão definidos.

## Matchmaking

O objetivo é matchmaking baseado em rating.

Devem existir:

- procura automática;
- desafios diretos a outro utilizador;
- aceitar/rejeitar desafio;
- rematch;
- rating separado para partidas de matchmaking.

## Ranking / ELO de jogadores

O rating de jogadores deve ser obtido a partir de partidas reais entre jogadores, não inferido a partir da força da IA.

O modelo concreto de rating ainda precisa de ser escolhido e documentado antes do lançamento.

## Social

Funcionalidades desejadas:

- amigos;
- desafios diretos;
- chat;
- espectadores;
- ranking;
- histórico;
- rematch.

Replays públicos ficam para uma fase posterior.

## Anti-cheat

Anti-cheat avançado não é prioridade inicial.

A primeira defesa deverá ser estrutural:

- servidor autoritativo;
- validação de ações;
- cliente incapaz de escolher diretamente o estado final;
- logs suficientes para investigar partidas suspeitas.

Soluções anti-cheat mais pesadas serão consideradas apenas quando forem necessárias.

## Hosting

Pretende-se usar infraestrutura gratuita ou de custo muito baixo.

O fornecedor de hosting, banco de dados e backend ainda não está decidido.

A seleção deve considerar:

- free tier real;
- WebSocket;
- capacidade de manter partidas em tempo real;
- persistência;
- autenticação Google;
- facilidade de deploy;
- limites de utilização.

## Banco de dados

É esperado que o produto venha a precisar de persistência para:

- utilizadores;
- contas Google associadas;
- ratings;
- histórico de partidas;
- amigos;
- desafios;
- replays, se forem ativados;
- resultados de matchmaking.

A tecnologia ainda está por decidir.

## O que não é prioridade

Não são prioridade inicial:

- microtransações;
- conteúdo pago;
- temporadas competitivas;
- anti-cheat de nível avançado;
- replay público completo;
- monetização.

O jogo será gratuito.

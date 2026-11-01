# RedWar — Web Platform, Online Multiplayer & Free Hosting

## 1. Visão Geral e Arquitetura

O RedWar oferece um ecossistema competitivo completo inspirado no modelo do **Chess.com**, suportando tanto a aplicação Desktop nativa em Pygame como a versão Web acessível no navegador sem necessidade de instalação:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          RedWar Ecosystem                              │
├───────────────────────────────────┬────────────────────────────────────┤
│         Desktop Platform          │            Web Platform            │
│         (Pygame Client)           │      (HTML5 Canvas / Vanilla JS)   │
├───────────────────────────────────┴────────────────────────────────────┤
│                       Launcher Unificado                               │
│                 (launcher.py / run_redwar.bat)                         │
├────────────────────────────────────────────────────────────────────────┤
│                     Authoritative Server Layer                         │
│  - WebSocket Multi-Room Manager (online/server/room.py)                │
│  - Authoritative Rules Engine (online/server/authority.py)             │
│  - Synchronized Match Clocks (GameClock with flag-fall timeouts)        │
│  - REST Web API & Leaderboard Service (online/server/web_app.py)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Modos de Jogo e Protocolos PvP

### 2.1 Gestão de Salas Autoritativas (`online/server/room.py`)
- **Salas com Código Privado**: Os jogadores podem criar salas personalizadas ou juntar-se através de códigos alfanuméricos de 6 caracteres.
- **Isolamento de Estado**: Cada sala instancia a sua própria `AuthoritativeSession`, garantindo que nenhuma mutação vaze entre partidas paralelas.
- **Suporte a Modos**: Suporte nativo aos modos **Standard 8×8** e **Grand 10×10**, além de controlos de tempo pré-definidos (Bullet 1+0, Blitz 3+2, Rápido 10+5).

### 2.2 Relógios de Partida Sincronizados (`GameClock`)
- **Contagem Decrescente**: O relógio do jogador com a vez ativa decrementa segundo a segundo com base em timestamps monotónicos do servidor.
- **Incremento por Lance**: Segundos de incremento (ex: +2s no Blitz 3+2) são adicionados imediatamente após a validação e execução de cada lance legal.
- **Queda de Bandeira (`flag_fall`)**: Se o tempo de um jogador esgotar (tempo <= 0), o servidor declara derrota imediata por timeout, atribuindo a vitória ao adversário.

### 2.3 Resiliência e Reconexão em Voo (`reconnect_token`)
- Ao entrar numa sala, cada jogador recebe um token de sessão criptográfico único (`reconnect_token`).
- Caso a ligação de rede caia brevemente (ex: alternância de rede ou perda temporária de pacotes), o jogador pode reconectar-se enviando `{"tipo": "reconnect", "token": "...", "room_id": "..."}`.
- O relógio continua a correr durante a desconexão, mas a partida não é cancelada imediatamente, permitindo ao jogador retomar o controlo dentro do seu tempo restante.

### 2.4 Desforra (Rematch) e Modo Espectador
- **Desforra**: Após o fim da partida (`game_over`), os jogadores podem propor desforra. Caso ambos aceitem, o tabuleiro é reiniciado com alternância de cores (quem jogou de Pretas joga agora de Brancas).
- **Espectadores**: Conexões adicionais à sala são admitidas como espectadores, recebendo todos os broadcasts de tabuleiro e relógios sem capacidade de interferir nas jogadas. O número de espectadores ativos é transmitido para os jogadores.
- **Emotes & Pings**: Suporte a reações rápidas (`gg`, `well_played`, `thinking`, `wow`) com proteção de rate limit para comunicação desportiva e sem abuso de texto livre.

---

## 3. Guia de Publicação Gratuita na Internet (Zero-Cost Hosting)

O RedWar foi desenhado para ser publicado e jogado gratuitamente na internet sem custos de infraestrutura:

### 3.1 Frontend Web (GitHub Pages — 100% Gratuito)
- A pasta `deploy/web/` contém uma aplicação estática completa em HTML5 Canvas, CSS e JavaScript sem necessidade de compilação ou bundlers pesados.
- Através do workflow automatizado `.github/workflows/deploy_web.yml`, cada push na branch `main` pode atualizar automaticamente o site publicado em `https://<utilizador>.github.io/RedWar/`.
- No cliente web, a URL do WebSocket do servidor pode ser configurada ou detetada automaticamente.

### 3.2 Backend WebSocket & REST API (Cloud Free Tiers)
O servidor pode ser executado em plataformas de nuvem gratuitas através de Docker:
- **Render.com**: Suporta Web Services gratuitos com WebSockets e portas expostas.
- **Fly.io**: Suporta containers Docker com alocação gratuita permanente de 3 instâncias partilhadas.
- **HuggingFace Spaces**: Suporta containers Docker gratuitos com HTTPS e WSS automáticos.
- **Railway / Koyeb / Glitch**: Ambientes com camadas gratuitas para execução de daemons Node/Python.

---

## 4. Segurança e Integridade

A segurança do servidor e a privacidade dos dados estão formalmente documentadas em [`../SECURITY.md`](../SECURITY.md):
- Todas as ações do cliente são validadas pelo motor de regras antes de qualquer mutação.
- Rate limiting por token-bucket para prevenir inundações de mensagens.
- Limite máximo de payload de 64 KB por mensagem WebSocket.
- Isolamento total de sessões sem recolha de PII ou dados sensíveis.

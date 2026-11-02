# 🔒 Publicação Gratuita & Arquitetura de Segurança

O RedWar foi desenhado para ser publicado de forma **100% gratuita na Internet** e com padrões defensivos de segurança de nível industrial.

---

## 🌐 Publicação Frontend no GitHub Pages

O cliente Web HTML5 Canvas é publicado automaticamente no GitHub Pages:
- **Pipeline**: Configurado no workflow `.github/workflows/deploy_web.yml`.
- **Gatilho**: Qualquer commit ou merge aprovado na branch `main`.
- **Acesso**: Disponível publicamente no endereço `https://<utilizador>.github.io/RedWar/`.
- **Custos**: 0 € (completamente gratuito e hospedado pela infraestrutura global do GitHub).

---

## 🐳 Servidor Backend em Docker

Para suportar multiplayer WebSocket em tempo real e a API REST:
- **`Dockerfile` multi-stage**: Imagem minimalista baseada em Python Alpine.
- **Compatibilidade**: Pronto para implantação em plataformas na nuvem com planos gratuitos permanentes (ex.: Render.com, Fly.io ou HuggingFace Spaces).
- **Comando de arranque local ou remoto**:
  ```bash
  docker-compose up --build
  ```

---

## 🛡️ Endurecimento de Segurança

1. **Proteção Anti-DoS via Token Bucket Rate Limiting**:
   - Limite estrito de 30 mensagens por segundo por conexão IP (com tolerância a bursts de até 50).
   - Bloqueio automático de sockets abusivos.
2. **Teto de 64 KB por Payload WebSocket**:
   - Rejeição imediata de frames gigantes para impedir ataques de exaustão de memória heap.
3. **Validação Rigorosa de Esquemas JSON**:
   - Tratamento seguro de inputs malformados com rejeição limpa e mascaramento defensivo de tracebacks.
4. **Zero Recolha de Dados Pessoais (PII)**:
   - Sem palavras-passe, sem e-mails e sem cookies de rastreio de terceiros.

---

## 🛡️ Federação de Identidade & Contenção de Raio de Explosão (Zero Blast Radius)

Em conformidade com o **OpenID Connect Core 1.0 (Secção 8)** e os padrões do **NIST SP 800-63B**, o RedWar adota uma arquitetura de identidade federada em 3 níveis:

1. **Conta Convidado / Guest ID (Privacidade Total)**:
   - Identificador aleatório e efémero (`UUIDv4`) gerado localmente.
   - Zero registo e zero partilha de e-mail ou dados pessoais.

2. **Conectar com Google (OIDC Seguro com Pairwise ID)**:
   - Sincroniza ELO e partidas entre browser e telemóvel com proteção multi-fator (2FA) da Google.
   - **Garantia de Raio de Explosão Zero**: O identificador do jogador no RedWar é derivado através de um HMAC com salt específico:
     $$\\text{PlayerID} = \\text{HMAC-SHA256}(\\text{Google Sub}, \\text{Salt}_{\\text{RedWar}})$$
   - Se o RedWar sofrer uma invasão, **o atacante NUNCA obtém acesso à conta Google do utilizador nem consegue correlacionar os dados com qualquer outro jogo**.

3. **Conta Dedicada Studio RedWar**:
   - Para utilizadores que preferem não usar Google.
   - Palavra-passe protegida por **Argon2id** / PBKDF2-HMAC-SHA256 com 600.000 iterações (OWASP 2023).
   - Verificação em tempo constante (`hmac.compare_digest`) para eliminar ataques de temporização (*timing attacks*).

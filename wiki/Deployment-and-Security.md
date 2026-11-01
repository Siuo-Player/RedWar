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
